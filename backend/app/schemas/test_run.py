from pydantic import BaseModel, Field, HttpUrl


class TestRunRequest(BaseModel):
    spec_url: HttpUrl
    operations: list[str] = Field(min_length=1)
    base_url: HttpUrl

    token: str | None = None

    parameters: dict[str, dict[str, str]] = Field(default_factory=dict)
    query_parameters: dict[str, dict[str, str]] = Field(default_factory=dict)
    request_bodies: dict[str, str] = Field(default_factory=dict)

    workers: int = Field(default=5, ge=1, le=32)
    timeout: float = Field(default=15.0, gt=0, le=300)
