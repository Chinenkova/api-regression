# API Regression Tool

A web-based tool for running regression tests against REST APIs using OpenAPI 3.x specifications.

## Features

- Import OpenAPI 3.x specifications from JSON URLs.
- Browse available API operations.
- Configure path parameters, query parameters, and JSON request bodies.
- Configure optional Bearer token authorization.
- Execute selected operations concurrently.
- Configure the number of workers and request timeout.
- Validate HTTP status codes against OpenAPI responses.
- Validate JSON response bodies against JSON Schema.
- Display execution results and validation errors.
- Save test results as JSON reports.
- Run tests from the command line.

## Tech Stack

### Frontend

- React
- TypeScript
- Vite
- SCSS Modules

### Backend

- Python
- FastAPI
- Requests
- jsonschema
- pytest

## Project Structure

```text
api-regression/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── cli.py
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
├── configs/
│   └── example.json
├── reports/
└── README.md
```

## Requirements

- Python 3.10 or newer
- Node.js 20 or newer
- npm

## Installation

### Backend

From the project root:

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Running the Application

### Start the backend

From the project root, activate the virtual environment:

```bash
source backend/.venv/bin/activate
```

Start FastAPI:

```bash
uvicorn app.main:app --reload --app-dir backend
```

The API will be available at:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs

### Start the frontend

In a separate terminal:

```bash
cd frontend
npm run dev
```

Open the local URL printed by Vite.

## CLI Usage

The CLI uses the same test runner as the web application.

From the project root:

```bash
cd backend
source .venv/bin/activate

python -m app.cli run \
  --config ../configs/example.json \
  --report ../reports/report.json
```

For APIs requiring Bearer authorization, provide the token through an environment variable:

```bash
API_TOKEN="your-token" python -m app.cli run \
  --config ../configs/example.json \
  --report ../reports/report.json
```

The CLI returns:

- Exit code `0` when all tests pass.
- Exit code `1` when tests fail or execution cannot be completed.

## Configuration

Example configuration: `configs/example.json`.

| Field              | Description                                     |
| ------------------ | ----------------------------------------------- |
| `spec_url`         | URL of the OpenAPI JSON specification           |
| `base_url`         | Base URL of the target API                      |
| `operations`       | Selected operation keys in `METHOD-path` format |
| `parameters`       | Path parameters for each operation              |
| `query_parameters` | Query parameters for each operation             |
| `request_bodies`   | JSON request bodies for each operation          |
| `workers`          | Maximum number of concurrent requests (1–32)    |
| `timeout`          | Request timeout in seconds                      |

Bearer tokens can be supplied through the `API_TOKEN` environment variable.

### Environment Variables

| Variable          | Description                                 | Default   |
| ----------------- | ------------------------------------------- | --------- |
| `MAX_WORKERS`     | Maximum number of concurrent requests       | `5`       |
| `REQUEST_TIMEOUT` | Request timeout in seconds                  | `15`      |
| `VERIFY_SSL`      | Enable TLS certificate verification         | `true`    |
| `MAX_SPEC_SIZE`   | Maximum OpenAPI specification size in bytes | `5242880` |
| `API_TOKEN`       | Bearer authorization token                  | Not set   |

## Test Reports

Reports are saved as JSON files.

Each report contains:

- Overall status: `passed` or `failed`.
- Total, passed, and failed operation counts.
- Total execution duration.
- Individual operation results.
- HTTP status codes.
- Request details without authorization tokens.
- Response bodies.
- JSON Schema validation errors.
- Execution timestamps.

## Running Tests

From the project root:

```bash
cd backend
python -m pytest -q
```

The project also uses Ruff for linting and formatting:

```bash
ruff check .
ruff format .
```

## Supported OpenAPI Features

The current version supports:

- OpenAPI 3.0 and 3.1 JSON specifications.
- Local references such as `#/components/schemas/...`.
- Recursive schema references.
- Path-level and operation-level parameters.
- Path and query parameters.
- JSON request bodies.
- JSON response schema validation.
- Bearer token authorization.

## Current Limitations

- Swagger 2.0 is not supported.
- YAML specifications are not supported.
- External `$ref` references are not supported.
- JSON is the supported request and response body format.
- Header, cookie, multipart, and form parameter handling is not implemented.
- TLS certificate verification is enabled by default.
- The application is intended for local development and testing.

## Security Notes

The application accepts user-provided OpenAPI and target API URLs. Do not expose the backend publicly without implementing appropriate SSRF protection and access controls.

Authorization tokens are not included in generated JSON reports.

The frontend keeps the Bearer token in session storage for the current browser session. For CLI usage, tokens can be provided through the `API_TOKEN` environment variable.
