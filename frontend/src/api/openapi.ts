const API_BASE_URL = "/api/openapi";

export type OpenAPIImportRequest = {
  spec_url: string;
};

export type OpenAPIInfo = {
  title: string;
  version: string;
  openapi_version: string;
  endpoints_count: number;
};

export type OpenAPIParameter = {
  name: string;
  in: "path" | "query" | "header" | "cookie";
  required: boolean;
  schema: Record<string, unknown>;
  description?: string;
};

export type OpenAPISchema = {
  type?: string;
  properties?: Record<string, OpenAPISchema>;
  required?: string[];
  items?: OpenAPISchema;
  enum?: (string | number | boolean)[];
  description?: string;
  format?: string;
};

export type OpenAPIRequestBody = {
  required: boolean;
  content: Record<
    string,
    {
      schema?: OpenAPISchema;
    }
  >;
};

export type OpenAPIResponse = {
  description?: string;
  content: Record<string, Record<string, unknown>>;
};

export type OpenAPIOperation = {
  path: string;
  method: string;
  operation_id: string | null;
  summary: string | null;
  tags: string[];
  parameters: OpenAPIParameter[];
  request_body: OpenAPIRequestBody | null;
  responses: Record<string, OpenAPIResponse>;
};

export type OpenAPIOperationsResponse = {
  total: number;
  operations: OpenAPIOperation[];
};

async function request<T>(endpoint: string, specUrl: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ spec_url: specUrl }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);

    throw new Error(errorData?.detail ?? `HTTP error: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function importOpenAPI(specUrl: string): Promise<OpenAPIInfo> {
  return request<OpenAPIInfo>("import", specUrl);
}

export function getOpenAPIOperations(
  specUrl: string,
): Promise<OpenAPIOperationsResponse> {
  return request<OpenAPIOperationsResponse>("operations", specUrl);
}
