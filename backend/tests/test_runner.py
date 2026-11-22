from app.services import test_runner
from app.services.test_runner import _validate_json


def test_validate_json_accepts_valid_data():
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name", "age"],
    }

    errors = _validate_json(
        {"name": "Alice", "age": 30},
        schema,
        "response",
    )

    assert errors == []


def test_validate_json_detects_invalid_data():
    schema = {
        "type": "object",
        "properties": {
            "age": {"type": "integer"},
        },
        "required": ["age"],
    }

    errors = _validate_json(
        {"age": "thirty"},
        schema,
        "response",
    )

    assert len(errors) == 1
    assert errors[0]["path"] == "response.age"


def test_validate_json_supports_openapi_exclusive_minimum():
    schema = {
        "type": "number",
        "minimum": 0,
        "exclusiveMinimum": True,
    }

    assert _validate_json(1, schema, "response") == []
    assert _validate_json(0, schema, "response")


def test_openapi_30_exclusive_minimum_true():
    schema = {
        "type": "number",
        "minimum": 5,
        "exclusiveMinimum": True,
    }

    assert _validate_json(6, schema, "response") == []
    assert _validate_json(5, schema, "response")
    assert _validate_json(4, schema, "response")


def test_openapi_30_exclusive_minimum_false():
    schema = {
        "type": "number",
        "minimum": 5,
        "exclusiveMinimum": False,
    }

    assert _validate_json(5, schema, "response") == []
    assert _validate_json(6, schema, "response") == []
    assert _validate_json(4, schema, "response")


def test_openapi_30_exclusive_maximum_true():
    schema = {
        "type": "number",
        "maximum": 10,
        "exclusiveMaximum": True,
    }

    assert _validate_json(9, schema, "response") == []
    assert _validate_json(10, schema, "response")
    assert _validate_json(11, schema, "response")


def test_openapi_31_exclusive_minimum():
    schema = {
        "type": "number",
        "exclusiveMinimum": 5,
    }

    assert (
        _validate_json(
            5.1,
            schema,
            "response",
            openapi_version="3.1.0",
        )
        == []
    )

    assert _validate_json(
        5,
        schema,
        "response",
        openapi_version="3.1.0",
    )


def test_openapi_31_exclusive_maximum():
    schema = {
        "type": "number",
        "exclusiveMaximum": 10,
    }

    assert (
        _validate_json(
            9.9,
            schema,
            "response",
            openapi_version="3.1.0",
        )
        == []
    )

    assert _validate_json(
        10,
        schema,
        "response",
        openapi_version="3.1.0",
    )


def test_openapi_31_const():
    schema = {
        "type": "string",
        "const": "fixed",
    }

    assert (
        _validate_json(
            "fixed",
            schema,
            "response",
            openapi_version="3.1.0",
        )
        == []
    )

    assert _validate_json(
        "other",
        schema,
        "response",
        openapi_version="3.1.0",
    )


def test_run_selected_operations_isolates_unexpected_errors(monkeypatch):
    operations = [
        {"method": "GET", "path": "/first", "responses": {}},
        {"method": "GET", "path": "/second", "responses": {}},
    ]

    monkeypatch.setattr(
        test_runner,
        "extract_operations",
        lambda spec: operations,
    )

    def mock_execute_operation(operation, **kwargs):
        if operation["path"] == "/first":
            raise RuntimeError("boom")

        return {
            "operation": "GET-/second",
            "passed": True,
            "status_code": 200,
            "duration_ms": 10,
            "response": "{}",
            "error": None,
            "validation_errors": [],
            "request": None,
            "started_at": "2026-11-22T10:00:00+00:00",
            "finished_at": "2026-11-22T10:00:00+00:00",
        }

    monkeypatch.setattr(
        test_runner,
        "_execute_operation",
        mock_execute_operation,
    )

    result = test_runner.run_selected_operations(
        spec={"openapi": "3.1.0"},
        selected_operations=["GET-/first", "GET-/second"],
        base_url="https://example.com",
        workers=1,
    )

    assert result["summary"]["total"] == 2
    assert result["summary"]["passed"] == 1
    assert result["summary"]["failed"] == 1

    assert result["results"][0]["error"] == "Unexpected error: boom"
    assert result["results"][0]["passed"] is False

    assert result["results"][1]["passed"] is True
    assert result["results"][1]["operation"] == "GET-/second"
