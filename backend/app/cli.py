import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from app.services.openapi import (
    OpenAPIServiceError,
    load_openapi_spec,
)
from app.services.report import save_json_report
from app.services.test_runner import (
    TestRunnerError,
    run_selected_operations,
)


def _validate_url(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Config field '{field}' must be a non-empty URL.")

    parsed = urlparse(value)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Config field '{field}' must be a valid HTTP or HTTPS URL.")


def load_config(config_path: str) -> dict:
    path = Path(config_path)

    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"Config file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in config file: {error.msg}") from error

    if not isinstance(config, dict):
        raise TypeError("Config must contain a JSON object.")

    required_fields = ("spec_url", "base_url", "operations")
    missing_fields = [field for field in required_fields if field not in config]

    if missing_fields:
        raise ValueError("Missing required config fields: " + ", ".join(missing_fields))

    _validate_url(config["spec_url"], "spec_url")
    _validate_url(config["base_url"], "base_url")

    operations = config["operations"]

    if (
        not isinstance(operations, list)
        or not operations
        or any(
            not isinstance(operation, str) or not operation.strip()
            for operation in operations
        )
    ):
        raise ValueError(
            "Config field 'operations' must be a non-empty array of non-empty strings."
        )

    for field in ("parameters", "query_parameters", "request_bodies"):
        if field in config and not isinstance(config[field], dict):
            raise ValueError(f"Config field '{field}' must be an object.")

    if "token" in config and not isinstance(config["token"], str):
        raise ValueError("Config field 'token' must be a string.")

    if "workers" in config:
        workers = config["workers"]

        if (
            not isinstance(workers, int)
            or isinstance(workers, bool)
            or not 1 <= workers <= 32
        ):
            raise ValueError("Config field 'workers' must be an integer from 1 to 32.")

    if "timeout" in config:
        timeout = config["timeout"]

        if (
            not isinstance(timeout, (int, float))
            or isinstance(timeout, bool)
            or timeout <= 0
        ):
            raise ValueError("Config field 'timeout' must be a positive number.")

    return config


def run_command(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)

        spec = load_openapi_spec(config["spec_url"])

        result = run_selected_operations(
            spec=spec,
            selected_operations=config["operations"],
            base_url=config["base_url"],
            token=os.getenv("API_TOKEN") or config.get("token"),
            parameters=config.get("parameters", {}),
            query_parameters=config.get("query_parameters", {}),
            request_bodies=config.get("request_bodies", {}),
            workers=config.get("workers"),
            timeout=config.get("timeout"),
        )

        report_path = save_json_report(result, args.report)

        summary = result["summary"]

        print("\nTest run completed")
        print(f"Total:  {summary['total']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Duration: {summary['duration_ms']} ms")
        print(f"Report: {report_path}")

        return 0 if result["status"] == "passed" else 1

    except (
        ValueError,
        TypeError,
        OpenAPIServiceError,
        TestRunnerError,
    ) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="API Regression Tool CLI",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run API regression tests.",
    )

    run_parser.add_argument(
        "--config",
        required=True,
        help="Path to JSON configuration file.",
    )

    run_parser.add_argument(
        "--report",
        default="reports/report.json",
        help="Path to output JSON report.",
    )

    args = parser.parse_args()

    if args.command == "run":
        return run_command(args)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
