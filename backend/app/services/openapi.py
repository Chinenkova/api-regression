from copy import deepcopy
from urllib.parse import urlparse

import requests

from app.config import settings

HTTP_METHODS = (
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head",
    "trace",
)


class OpenAPIServiceError(Exception):
    pass


def load_openapi_spec(spec_url: str) -> dict:
    parsed_url = urlparse(str(spec_url))

    if parsed_url.scheme not in {"http", "https"}:
        raise OpenAPIServiceError("OpenAPI specification URL must use HTTP or HTTPS.")

    if not parsed_url.netloc:
        raise OpenAPIServiceError("Invalid OpenAPI specification URL.")

    try:
        with requests.get(
            str(spec_url),
            timeout=settings.timeout,
            verify=settings.verify_ssl,
            stream=True,
            headers={"Accept": "application/json"},
        ) as response:
            response.raise_for_status()

            content_length = response.headers.get("Content-Length")

            if content_length and int(content_length) > settings.max_spec_size:
                raise OpenAPIServiceError(
                    "OpenAPI specification exceeds the maximum allowed size."
                )

            content = bytearray()

            for chunk in response.iter_content(chunk_size=8192):
                content.extend(chunk)

                if len(content) > settings.max_spec_size:
                    raise OpenAPIServiceError(
                        "OpenAPI specification exceeds the maximum allowed size."
                    )

    except requests.RequestException as error:
        raise OpenAPIServiceError(
            f"Failed to load OpenAPI specification: {error}"
        ) from error

    try:
        spec = requests.models.complexjson.loads(content)
    except (ValueError, UnicodeDecodeError) as error:
        raise OpenAPIServiceError("The URL did not return valid JSON.") from error

    if not isinstance(spec, dict):
        raise OpenAPIServiceError("OpenAPI specification must be a JSON object.")

    if "swagger" in spec:
        raise OpenAPIServiceError(
            "Swagger 2.0 is not supported. Please provide an OpenAPI 3.x specification."
        )

    openapi_version = spec.get("openapi")

    if not isinstance(openapi_version, str) or not openapi_version.startswith("3."):
        raise OpenAPIServiceError("Only OpenAPI 3.x specifications are supported.")

    if not isinstance(spec.get("paths"), dict):
        raise OpenAPIServiceError(
            "OpenAPI specification must contain a valid paths object."
        )

    return spec


def resolve_local_ref(
    ref: str,
    spec: dict,
    resolving: set[str] | None = None,
) -> dict:
    if not ref.startswith("#/"):
        raise OpenAPIServiceError(
            f"External or unsupported reference is not supported: {ref}"
        )

    pointer = ref[2:]
    parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")]

    value = spec

    try:
        for part in parts:
            value = value[part]
    except (KeyError, TypeError) as error:
        raise OpenAPIServiceError(f"Unable to resolve reference: {ref}") from error

    if not isinstance(value, dict):
        raise OpenAPIServiceError(f"Reference must point to an object: {ref}")

    return deepcopy(value)


def _resolve_object_refs(
    value: dict,
    spec: dict,
    resolving: set[str] | None = None,
    preserve_circular_refs: bool = False,
    preserve_schema_refs: bool = False,
) -> dict:
    if resolving is None:
        resolving = set()

    if "$ref" in value:
        ref = value["$ref"]

        if not isinstance(ref, str):
            raise OpenAPIServiceError("Reference value must be a string.")

        if ref in resolving:
            if preserve_circular_refs:
                return {"$ref": ref}

            raise OpenAPIServiceError(f"Circular reference detected: {ref}")

        resolving.add(ref)

        try:
            resolved = resolve_local_ref(ref, spec)

            resolved = _resolve_object_refs(
                resolved,
                spec,
                resolving,
                preserve_circular_refs,
                preserve_schema_refs,
            )

            siblings = {key: item for key, item in value.items() if key != "$ref"}

            if siblings:
                resolved.update(
                    _resolve_object_refs(
                        siblings,
                        spec,
                        resolving,
                        preserve_circular_refs,
                        preserve_schema_refs,
                    )
                )

            return resolved
        finally:
            resolving.remove(ref)

    result = {}

    for key, item in value.items():
        if preserve_schema_refs and key == "schema":
            result[key] = deepcopy(item)
        elif isinstance(item, dict):
            result[key] = _resolve_object_refs(
                item,
                spec,
                resolving,
                preserve_circular_refs,
                preserve_schema_refs,
            )
        elif isinstance(item, list):
            result[key] = [
                _resolve_object_refs(
                    element,
                    spec,
                    resolving,
                    preserve_circular_refs,
                    preserve_schema_refs,
                )
                if isinstance(element, dict)
                else element
                for element in item
            ]
        else:
            result[key] = item

    return result


def resolve_schema_refs(
    schema: dict,
    spec: dict,
    resolving: set[str] | None = None,
) -> dict:
    resolved = _resolve_object_refs(
        schema,
        spec,
        resolving,
        preserve_circular_refs=True,
    )

    components = spec.get("components")

    if isinstance(components, dict):
        resolved["components"] = deepcopy(components)

    return resolved


def resolve_parameter_refs(
    parameters: list,
    spec: dict,
) -> list[dict]:
    resolved_parameters = []

    for parameter in parameters:
        if not isinstance(parameter, dict):
            raise OpenAPIServiceError("OpenAPI parameter must be an object.")

        resolved = _resolve_object_refs(parameter, spec)

        if not resolved.get("name") or not resolved.get("in"):
            raise OpenAPIServiceError(
                "OpenAPI parameter must contain name and in fields."
            )

        resolved_parameters.append(resolved)

    return resolved_parameters


def resolve_response_refs(
    response: dict,
    spec: dict,
    resolving: set[str] | None = None,
) -> dict:
    return _resolve_object_refs(
        response,
        spec,
        resolving,
        preserve_circular_refs=True,
        preserve_schema_refs=True,
    )


def _normalize_parameters(
    path_parameters: list,
    operation_parameters: list,
    spec: dict,
) -> list[dict]:
    merged = {}

    for parameter in resolve_parameter_refs(path_parameters, spec):
        merged[(parameter["name"], parameter["in"])] = parameter

    for parameter in resolve_parameter_refs(operation_parameters, spec):
        merged[(parameter["name"], parameter["in"])] = parameter

    result = []

    for parameter in merged.values():
        schema = parameter.get("schema", {})

        if not isinstance(schema, dict):
            schema = {}

        result.append(
            {
                "name": parameter["name"],
                "in": parameter["in"],
                "required": parameter.get("required", False),
                "schema": convert_nullable(resolve_schema_refs(schema, spec)),
                "description": parameter.get("description"),
            }
        )

    return result


def _normalize_request_body(
    request_body: dict | None,
    spec: dict,
) -> dict | None:
    if request_body is None:
        return None

    resolved_body = _resolve_object_refs(
        request_body,
        spec,
        preserve_circular_refs=True,
        preserve_schema_refs=True,
    )

    content = resolved_body.get("content", {})
    normalized_content = {}

    for content_type, media_type in content.items():
        if not isinstance(media_type, dict):
            continue

        schema = media_type.get("schema")

        normalized_content[content_type] = {
            "schema": (
                convert_nullable(resolve_schema_refs(schema, spec))
                if isinstance(schema, dict)
                else None
            )
        }

    return {
        "required": resolved_body.get("required", False),
        "content": normalized_content,
    }


def convert_nullable(schema: dict) -> dict:
    schema = deepcopy(schema)

    if schema.get("nullable") is True:
        schema.pop("nullable")

        schema_type = schema.get("type")

        if isinstance(schema_type, str):
            schema["type"] = [schema_type, "null"]

    for key, value in schema.items():
        if isinstance(value, dict):
            schema[key] = convert_nullable(value)

        elif isinstance(value, list):
            schema[key] = [
                convert_nullable(item) if isinstance(item, dict) else item
                for item in value
            ]

    return schema


def _normalize_responses(
    responses: dict,
    spec: dict,
) -> dict:
    normalized = {}

    for status_code, response in responses.items():
        if not isinstance(response, dict):
            continue

        resolved_response = resolve_response_refs(response, spec)
        content = resolved_response.get("content", {})

        normalized_content = {}

        for content_type, media_type in content.items():
            if not isinstance(media_type, dict):
                continue

            schema = media_type.get("schema")

            normalized_content[content_type] = {
                "schema": (
                    convert_nullable(resolve_schema_refs(schema, spec))
                    if isinstance(schema, dict)
                    else None
                )
            }

        normalized[str(status_code)] = {
            "description": resolved_response.get("description"),
            "content": normalized_content,
        }

    return normalized


def extract_operations(spec: dict) -> list[dict]:
    operations = []

    for path, path_item in spec.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue

        if "$ref" in path_item:
            path_item = _resolve_object_refs(path_item, spec)

        path_parameters = path_item.get("parameters", [])

        if not isinstance(path_parameters, list):
            raise OpenAPIServiceError(f"Invalid path-level parameters for path: {path}")

        for method in HTTP_METHODS:
            operation = path_item.get(method)

            if not isinstance(operation, dict):
                continue

            operation_parameters = operation.get("parameters", [])

            if not isinstance(operation_parameters, list):
                raise OpenAPIServiceError(
                    f"Invalid parameters for {method.upper()} {path}"
                )

            parameters = _normalize_parameters(
                path_parameters,
                operation_parameters,
                spec,
            )

            request_body = _normalize_request_body(
                operation.get("requestBody"),
                spec,
            )

            responses = _normalize_responses(
                operation.get("responses", {}),
                spec,
            )

            operations.append(
                {
                    "path": path,
                    "method": method.upper(),
                    "operation_id": operation.get("operationId"),
                    "summary": operation.get("summary"),
                    "tags": operation.get("tags", []),
                    "parameters": parameters,
                    "request_body": request_body,
                    "responses": responses,
                }
            )

    return operations
