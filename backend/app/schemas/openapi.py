from pydantic import BaseModel, HttpUrl


class OpenAPIImportRequest(BaseModel):
    spec_url: HttpUrl
