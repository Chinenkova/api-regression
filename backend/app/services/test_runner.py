import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from urllib.parse import quote

import jsonschema
import requests
from jsonschema import (
    Draft4Validator,
    Draft202012Validator,
    FormatChecker,
)

from app.config import settings
from app.services.openapi import (
    extract_operations,
)


class TestRunnerError(Exception):
    pass


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _operation_key(operation: dict) -> str:
    return f"{operation['method']}-{operation['path']}"


def _validate_json(
    data: object,
    schema: dict,
    location: str,
    openapi_version: str = "3.0.0",
) -> list[dict]:
    validator_class = (
        Draft202012Validator if openapi_version.startswith("3.1.") else Draft4Validator
    )

    try:
        validator_class.check_schema(schema)

        validator = validator_class(
            schema,
            format_checker=FormatChecker(),
        )

        errors = sorted(
            validator.iter_errors(data),
            key=lambda error: list(error.absolute_path),
        )

        return [
            {
                "path": (
                    f"{location}." + ".".join(str(part) for part in error.absolute_path)
                    if error.absolute_path
                    else location
                ),
                "message": error.message,
            }
            for error in errors
        ]

    except jsonschema.exceptions.SchemaError as error:
        raise TestRunnerError(
            f"Invalid JSON Schema at {location}: {error.message}"
        ) from error


def _get_json_schema(content: dict) -> dict | None:
    for content_type, media_type in content.items():
        if (
            content_type == "application/json" or content_type.endswith("+json")
        ) and isinstance(media_type, dict):
            schema = media_type.get("schema")

            if isinstance(schema, dict):
                return schema

    return None


def _validate_request_body(
    operation: dict,
    body_text: str | None,
    openapi_version: str,
) -> tuple[object | None, list[dict]]:
    request_body = operation.get("request_body")

    if not request_body:
        return None, []

    if not body_text:
        if request_body.get("required"):
            return None, [
                {
                    "path": "requestBody",
                    "message": "Request body is required.",
                }
            ]

        return None, []

    try:
        body = json.loads(body_text)
    except json.JSONDecodeError as error:
        return None, [
            {
                "path": "requestBody",
                "message": f"Invalid JSON: {error.msg}",
            }
        ]

    schema = _get_json_schema(request_body.get("content", {}))

    if schema is None:
        return body, []

    errors = _validate_json(
        body,
        schema,
        "requestBody",
        openapi_version,
    )

    return body, errors


def _find_response_definition(
    responses: dict,
    status_code: int,
) -> dict | None:
    exact = responses.get(str(status_code))

    if exact is not None:
        return exact

    status_group = f"{status_code // 100}XX"

    for code, response in responses.items():
        if code.upper() == status_group:
            return response

    return responses.get("default")


def _build_operation_path(
    operation: dict,
    parameters: dict[str, str],
) -> str:
    path = operation["path"]

    for parameter in operation.get("parameters", []):
        if parameter.get("in") != "path":
            continue

        name = parameter["name"]
        value = parameters.get(name)

        if value is None or value == "":
            if parameter.get("required", True):
                raise TestRunnerError(f"Required path parameter '{name}' is missing.")
            continue

        path = path.replace(
            f"{{{name}}}",
            quote(str(value), safe=""),
        )

    if "{" in path or "}" in path:
        raise TestRunnerError(
            f"Not all path parameters were provided for {operation['path']}."
        )

    return path


def _execute_operation(
    operation: dict,
    base_url: str,
    token: str | None,
    parameters: dict[str, str],
    query_parameters: dict[str, str],
    request_body_text: str | None,
    timeout: float,
    openapi_version: str,
) -> dict:
    operation_key = _operation_key(operation)
    method = operation["method"]
    started_at = _now()
    start_time = time.perf_counter()

    result = {
        "operation": operation_key,
        "passed": False,
        "status_code": None,
        "duration_ms": 0,
        "response": None,
        "error": None,
        "validation_errors": [],
        "request": None,
        "started_at": started_at,
        "finished_at": None,
    }

    try:
        body, request_errors = _validate_request_body(
            operation,
            request_body_text,
            openapi_version,
        )

        if request_errors:
            result["validation_errors"] = request_errors
            result["error"] = "Request body validation failed."
            return result

        path = _build_operation_path(operation, parameters)
        url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"

        headers = {
            "Accept": "application/json",
        }

        if token:
            headers["Authorization"] = f"Bearer {token}"

        if body is not None:
            headers["Content-Type"] = "application/json"

        result["request"] = {
            "method": method,
            "url": url,
            "query_parameters": query_parameters,
            "headers": {
                key: value
                for key, value in headers.items()
                if key.lower() != "authorization"
            },
            "body": body,
        }

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=query_parameters,
            json=body,
            timeout=timeout,
            verify=settings.verify_ssl,
        )

        result["status_code"] = response.status_code
        result["response"] = response.text

        response_definition = _find_response_definition(
            operation.get("responses", {}),
            response.status_code,
        )

        if response_definition is None:
            result["error"] = f"Unexpected HTTP status code: {response.status_code}."
            return result

        response_schema = _get_json_schema(response_definition.get("content", {}))

        if response_schema is not None:
            try:
                response_data = response.json()
            except ValueError:
                result["validation_errors"].append(
                    {
                        "path": "response",
                        "message": "Expected a JSON response body.",
                    }
                )
            else:
                result["validation_errors"].extend(
                    _validate_json(
                        response_data,
                        response_schema,
                        "response",
                        openapi_version,
                    )
                )

        if result["validation_errors"]:
            result["error"] = "Response validation failed."
        else:
            result["passed"] = True

    except requests.Timeout:
        result["error"] = f"Request timed out after {timeout} seconds."

    except requests.RequestException as error:
        result["error"] = f"HTTP request failed: {error}"

    except TestRunnerError as error:
        result["error"] = str(error)

    finally:
        result["duration_ms"] = round((time.perf_counter() - start_time) * 1000)
        result["finished_at"] = _now()

    return result


def run_selected_operations(
    spec: dict,
    selected_operations: list[str],
    base_url: str,
    token: str | None = None,
    parameters: dict | None = None,
    query_parameters: dict | None = None,
    request_bodies: dict | None = None,
    workers: int | None = None,
    timeout: float | None = None,
) -> dict:
    operations = extract_operations(spec)

    operations_by_key = {
        _operation_key(operation): operation for operation in operations
    }

    missing_operations = [
        key for key in selected_operations if key not in operations_by_key
    ]

    if missing_operations:
        raise TestRunnerError(
            "Selected operations were not found: " + ", ".join(missing_operations)
        )

    if not selected_operations:
        raise TestRunnerError("No operations selected.")

    parameters = parameters or {}
    query_parameters = query_parameters or {}
    request_bodies = request_bodies or {}

    worker_count = workers if workers is not None else settings.max_workers
    request_timeout = timeout if timeout is not None else settings.timeout

    if worker_count < 1 or worker_count > 32:
        raise TestRunnerError("Workers must be between 1 and 32.")

    if request_timeout <= 0:
        raise TestRunnerError("Timeout must be greater than zero.")

    openapi_version = spec.get("openapi", "3.0.0")

    started_at = _now()
    start_time = time.perf_counter()

    selected = [operations_by_key[key] for key in selected_operations]

    def execute(operation: dict) -> dict:
        key = _operation_key(operation)

        try:
            return _execute_operation(
                operation=operation,
                base_url=str(base_url),
                token=token,
                parameters=parameters.get(key, {}),
                query_parameters=query_parameters.get(key, {}),
                request_body_text=request_bodies.get(key),
                timeout=request_timeout,
                openapi_version=openapi_version,
            )

        except Exception as error:  # noqa: BLE001
            finished_at = _now()

            return {
                "operation": key,
                "passed": False,
                "status_code": None,
                "duration_ms": 0,
                "response": None,
                "error": f"Unexpected error: {error}",
                "validation_errors": [],
                "request": None,
                "started_at": finished_at,
                "finished_at": finished_at,
            }

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        results = list(executor.map(execute, selected))

    duration_ms = round((time.perf_counter() - start_time) * 1000)

    passed = sum(1 for result in results if result["passed"])
    failed = len(results) - passed

    return {
        "status": "passed" if failed == 0 else "failed",
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "duration_ms": duration_ms,
        },
        "results": results,
        "started_at": started_at,
        "finished_at": _now(),
    }
