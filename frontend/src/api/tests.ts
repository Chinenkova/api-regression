const API_BASE_URL = "/api/tests";

export type TestRunRequest = {
  spec_url: string;
  base_url: string;
  operations: string[];
  token?: string | null;
  parameters: Record<string, Record<string, string>>;
  query_parameters: Record<string, Record<string, string>>;
  request_bodies: Record<string, string>;
  workers: number;
  timeout: number;
};

export type ValidationError = {
  path: string;
  message: string;
};

export type TestRunItem = {
  operation: string;
  passed: boolean;
  status_code: number | null;
  duration_ms: number;
  response: string | null;
  error: string | null;
  validation_errors: ValidationError[];
  request: {
    method: string;
    url: string;
    query_parameters: Record<string, string>;
    headers: Record<string, string>;
    body: unknown;
  } | null;
  started_at: string;
  finished_at: string;
};

export type TestRunResponse = {
  status: "passed" | "failed";
  message: string;
  summary: {
    total: number;
    passed: number;
    failed: number;
    duration_ms: number;
  };
  results: TestRunItem[];
  started_at: string;
  finished_at: string;
};

const getErrorMessage = (data: unknown): string => {
  if (typeof data === "string") {
    return data;
  }

  if (Array.isArray(data)) {
    return data
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }

        if (typeof item === "object" && item !== null) {
          const error = item as Record<string, unknown>;
          const location = Array.isArray(error.loc) ? error.loc.join(".") : "";

          return [location, error.msg]
            .filter((value) => typeof value === "string")
            .join(": ");
        }

        return String(item);
      })
      .join("\n");
  }

  if (typeof data === "object" && data !== null) {
    const error = data as Record<string, unknown>;

    if ("detail" in error) {
      return getErrorMessage(error.detail);
    }

    if (typeof error.message === "string") {
      return error.message;
    }
  }

  return "An unexpected error occurred.";
};

export const runTests = async (
  request: TestRunRequest,
): Promise<TestRunResponse> => {
  const response = await fetch(`${API_BASE_URL}/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  const data: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(getErrorMessage(data) || `HTTP error: ${response.status}`);
  }

  return data as TestRunResponse;
};
