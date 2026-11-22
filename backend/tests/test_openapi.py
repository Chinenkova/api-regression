import pytest

from app.services.openapi import (
    OpenAPIServiceError,
    extract_operations,
)


def test_extract_operations_merges_path_parameters():
    spec = {
        "openapi": "3.0.3",
        "paths": {
            "/pets/{pet_id}": {
                "parameters": [
                    {
                        "name": "pet_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
                "get": {
                    "operationId": "getPet",
                    "parameters": [
                        {
                            "name": "include",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "boolean"},
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                },
            }
        },
    }

    operations = extract_operations(spec)

    assert len(operations) == 1

    parameters = operations[0]["parameters"]

    assert len(parameters) == 2
    assert parameters[0]["name"] == "pet_id"
    assert parameters[1]["name"] == "include"


def test_extract_operations_resolves_parameter_reference():
    spec = {
        "openapi": "3.0.3",
        "paths": {
            "/pets/{pet_id}": {
                "get": {
                    "parameters": [{"$ref": "#/components/parameters/PetId"}],
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
        "components": {
            "parameters": {
                "PetId": {
                    "name": "pet_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"},
                }
            }
        },
    }

    operations = extract_operations(spec)

    assert operations[0]["parameters"][0]["name"] == "pet_id"


def test_extract_operations_uses_stable_method_order():
    spec = {
        "openapi": "3.0.3",
        "paths": {
            "/pets": {
                "post": {"responses": {}},
                "get": {"responses": {}},
                "delete": {"responses": {}},
            }
        },
    }

    operations = extract_operations(spec)

    assert [item["method"] for item in operations] == [
        "GET",
        "POST",
        "DELETE",
    ]


def test_external_reference_is_rejected():
    spec = {
        "openapi": "3.0.3",
        "paths": {
            "/pets": {
                "get": {
                    "parameters": [{"$ref": "https://example.com/parameters.json"}],
                    "responses": {},
                }
            }
        },
    }

    with pytest.raises(OpenAPIServiceError):
        extract_operations(spec)


def test_extract_operations_supports_recursive_schema_refs():
    spec = {
        "openapi": "3.1.0",
        "paths": {
            "/nodes": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Node"}
                                }
                            },
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Node": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "children": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Node"},
                        },
                    },
                }
            }
        },
    }

    operations = extract_operations(spec)

    schema = operations[0]["responses"]["200"]["content"]["application/json"]["schema"]

    assert schema["type"] == "object"
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["children"]["items"]["$ref"] == (
        "#/components/schemas/Node"
    )
    assert "Node" in schema["components"]["schemas"]


def test_extract_operations_supports_mutually_recursive_schema_refs():
    spec = {
        "openapi": "3.1.0",
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            },
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "department": {"$ref": "#/components/schemas/Department"}
                    },
                },
                "Department": {
                    "type": "object",
                    "properties": {"manager": {"$ref": "#/components/schemas/User"}},
                },
            }
        },
    }

    operations = extract_operations(spec)

    schema = operations[0]["responses"]["200"]["content"]["application/json"]["schema"]

    department_schema = schema["properties"]["department"]

    assert department_schema["type"] == "object"
    assert department_schema["properties"]["manager"]["$ref"] == (
        "#/components/schemas/User"
    )
    assert "User" in schema["components"]["schemas"]
    assert "Department" in schema["components"]["schemas"]
