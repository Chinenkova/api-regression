from fastapi import APIRouter, HTTPException

from app.schemas.openapi import OpenAPIImportRequest
from app.services.openapi import (
    OpenAPIServiceError,
    extract_operations,
    load_openapi_spec,
)

router = APIRouter()


@router.post("/import")
def import_openapi(request: OpenAPIImportRequest):
    try:
        spec = load_openapi_spec(str(request.spec_url))
        operations = extract_operations(spec)

        return {
            "title": spec.get("info", {}).get("title", "Untitled API"),
            "version": spec.get("info", {}).get("version", "Unknown"),
            "openapi_version": spec["openapi"],
            "endpoints_count": len(operations),
        }

    except OpenAPIServiceError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.post("/operations")
def get_openapi_operations(request: OpenAPIImportRequest):
    try:
        spec = load_openapi_spec(str(request.spec_url))
        operations = extract_operations(spec)

        return {
            "total": len(operations),
            "operations": operations,
        }

    except OpenAPIServiceError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
