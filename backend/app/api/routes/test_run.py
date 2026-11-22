from fastapi import APIRouter, HTTPException

from app.schemas.test_run import TestRunRequest
from app.services.openapi import (
    OpenAPIServiceError,
    load_openapi_spec,
)
from app.services.test_runner import (
    TestRunnerError,
    run_selected_operations,
)

router = APIRouter()


@router.post("/run")
def run_tests(request: TestRunRequest):
    try:
        spec = load_openapi_spec(str(request.spec_url))

        result = run_selected_operations(
            spec=spec,
            selected_operations=request.operations,
            base_url=str(request.base_url),
            token=request.token,
            parameters=request.parameters,
            query_parameters=request.query_parameters,
            request_bodies=request.request_bodies,
            workers=request.workers,
            timeout=request.timeout,
        )

        return {
            "message": "Test run completed",
            **result,
        }

    except (OpenAPIServiceError, TestRunnerError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
