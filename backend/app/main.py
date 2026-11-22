from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.openapi import router as openapi_router
from app.api.routes.test_run import router as test_run_router

app = FastAPI(
    title="API Regression Tool",
    description="REST API regression testing platform",
    version="1.0.0",
)

app.include_router(health_router, prefix="/api")
app.include_router(openapi_router, prefix="/api/openapi", tags=["OpenAPI"])
app.include_router(test_run_router, prefix="/api/tests", tags=["Tests"])
