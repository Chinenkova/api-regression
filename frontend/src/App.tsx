import { useState } from "react";

import {
  getOpenAPIOperations,
  importOpenAPI,
  type OpenAPIInfo,
  type OpenAPIOperation,
} from "./api/openapi";

import Authorization from "./components/Authorization/Authorization";
import OperationsList from "./components/OperationsList/OperationsList";
import TestRunner from "./components/TestRunner/TestRunner";

import styles from "./App.module.scss";

const App = () => {
  const [specUrl, setSpecUrl] = useState("");
  const [apiInfo, setApiInfo] = useState<OpenAPIInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [operations, setOperations] = useState<OpenAPIOperation[]>([]);
  const [selectedOperations, setSelectedOperations] = useState<string[]>([]);
  const [authToken, setAuthToken] = useState<string | null>(() =>
    sessionStorage.getItem("api-token"),
  );
  const [pathParameters, setPathParameters] = useState<
    Record<string, Record<string, string>>
  >({});
  const [queryParameters, setQueryParameters] = useState<
    Record<string, Record<string, string>>
  >({});
  const [requestBodies, setRequestBodies] = useState<Record<string, string>>(
    {},
  );

  const handleImport = async () => {
    setLoading(true);
    setError(null);
    setApiInfo(null);
    setOperations([]);
    setSelectedOperations([]);
    setPathParameters({});
    setQueryParameters({});
    setRequestBodies({});

    try {
      const result = await importOpenAPI(specUrl.trim());
      const operationsResult = await getOpenAPIOperations(specUrl.trim());

      setApiInfo(result);
      setOperations(operationsResult.operations);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const handleAuthorize = (token: string) => {
    sessionStorage.setItem("api-token", token);
    setAuthToken(token);
  };

  const handleLogout = () => {
    sessionStorage.removeItem("api-token");
    setAuthToken(null);
  };

  return (
    <main className={styles.app}>
      <header className={styles.topBar}>
        <div className={styles.brand}>
          <h1>API Regression Tool</h1>
        </div>

        <form
          className={styles.importForm}
          onSubmit={(event) => {
            event.preventDefault();
            handleImport();
          }}
        >
          <input
            type="url"
            value={specUrl}
            onChange={(event) => setSpecUrl(event.target.value)}
            placeholder="Enter OpenAPI JSON URL"
            aria-label="OpenAPI specification URL"
            required
          />

          <button type="submit" disabled={loading}>
            {loading ? "Importing..." : "Import"}
          </button>
        </form>

        <div className={styles.authorization}>
          <Authorization
            token={authToken}
            onAuthorize={handleAuthorize}
            onLogout={handleLogout}
          />
        </div>
      </header>

      {error && (
        <div className={styles.error} role="alert">
          {error}
        </div>
      )}

      {apiInfo && (
        <section className={styles.apiInfo}>
          <h2>{apiInfo.title}</h2>

          <div className={styles.apiMetadata}>
            <span>Version: {apiInfo.version}</span>
            <span>OpenAPI: {apiInfo.openapi_version}</span>
            <span>Endpoints: {apiInfo.endpoints_count}</span>
          </div>
        </section>
      )}

      {apiInfo && operations.length > 0 && (
        <section className={styles.workspace}>
          <OperationsList
            operations={operations}
            selectedOperations={selectedOperations}
            onSelectionChange={setSelectedOperations}
            pathParameters={pathParameters}
            onPathParametersChange={setPathParameters}
            queryParameters={queryParameters}
            onQueryParametersChange={setQueryParameters}
            requestBodies={requestBodies}
            onRequestBodiesChange={setRequestBodies}
          />

          <TestRunner
            specUrl={specUrl}
            token={authToken}
            operations={selectedOperations}
            pathParameters={pathParameters}
            queryParameters={queryParameters}
            requestBodies={requestBodies}
          />
        </section>
      )}
    </main>
  );
};

export default App;
