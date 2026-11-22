import { useState } from "react";

import type { OpenAPIOperation } from "../../api/openapi";

import styles from "./OperationsList.module.scss";

type HttpMethod =
  | "ALL"
  | "GET"
  | "POST"
  | "PUT"
  | "PATCH"
  | "DELETE"
  | "OPTIONS"
  | "HEAD"
  | "TRACE";

type QueryParameters = Record<string, Record<string, string>>;
type PathParameters = Record<string, Record<string, string>>;
type RequestBodies = Record<string, string>;

type OperationsListProps = {
  operations: OpenAPIOperation[];
  selectedOperations: string[];
  onSelectionChange: (operations: string[]) => void;
  pathParameters: PathParameters;
  onPathParametersChange: (parameters: PathParameters) => void;
  queryParameters: QueryParameters;
  onQueryParametersChange: (parameters: QueryParameters) => void;
  requestBodies: RequestBodies;
  onRequestBodiesChange: (bodies: RequestBodies) => void;
};

const methods: HttpMethod[] = [
  "ALL",
  "GET",
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
  "OPTIONS",
  "HEAD",
  "TRACE",
];

const OperationsList = ({
  operations,
  selectedOperations,
  onSelectionChange,
  pathParameters,
  onPathParametersChange,
  queryParameters,
  onQueryParametersChange,
  requestBodies,
  onRequestBodiesChange,
}: OperationsListProps) => {
  const [methodFilter, setMethodFilter] = useState<HttpMethod>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredOperations = operations.filter((operation) => {
    const matchesMethod =
      methodFilter === "ALL" || operation.method === methodFilter;

    const searchValue = searchQuery.toLowerCase();

    const matchesSearch =
      operation.path.toLowerCase().includes(searchValue) ||
      operation.method.toLowerCase().includes(searchValue) ||
      (operation.summary ?? "").toLowerCase().includes(searchValue) ||
      (operation.operation_id ?? "").toLowerCase().includes(searchValue);

    return matchesMethod && matchesSearch;
  });

  const filteredOperationKeys = filteredOperations.map(
    (operation) => `${operation.method}-${operation.path}`,
  );

  const allFilteredSelected =
    filteredOperationKeys.length > 0 &&
    filteredOperationKeys.every((key) => selectedOperations.includes(key));

  const selectedOperationsWithPathParams = operations.filter((operation) => {
    const key = `${operation.method}-${operation.path}`;

    return (
      selectedOperations.includes(key) &&
      operation.parameters.some((parameter) => parameter.in === "path")
    );
  });

  const selectedOperationsWithQueryParams = operations.filter((operation) => {
    const key = `${operation.method}-${operation.path}`;

    return (
      selectedOperations.includes(key) &&
      operation.parameters.some((parameter) => parameter.in === "query")
    );
  });

  const selectedOperationsWithRequestBody = operations.filter((operation) => {
    const key = `${operation.method}-${operation.path}`;

    return selectedOperations.includes(key) && operation.request_body !== null;
  });

  const toggleOperation = (key: string) => {
    const updatedOperations = selectedOperations.includes(key)
      ? selectedOperations.filter((item) => item !== key)
      : [...selectedOperations, key];

    onSelectionChange(updatedOperations);
  };

  const toggleAllOperations = () => {
    if (allFilteredSelected) {
      onSelectionChange(
        selectedOperations.filter(
          (key) => !filteredOperationKeys.includes(key),
        ),
      );
    } else {
      onSelectionChange(
        Array.from(new Set([...selectedOperations, ...filteredOperationKeys])),
      );
    }
  };

  const handlePathParameterChange = (
    operationKey: string,
    parameterName: string,
    value: string,
  ) => {
    onPathParametersChange({
      ...pathParameters,
      [operationKey]: {
        ...pathParameters[operationKey],
        [parameterName]: value,
      },
    });
  };

  const handleQueryParameterChange = (
    operationKey: string,
    parameterName: string,
    value: string,
  ) => {
    onQueryParametersChange({
      ...queryParameters,
      [operationKey]: {
        ...queryParameters[operationKey],
        [parameterName]: value,
      },
    });
  };

  return (
    <section className={styles.container}>
      <div className={styles.heading}>
        <div>
          <h2>API Operations</h2>
          <p className={styles.subtitle}>Browse and select endpoints to test</p>
        </div>

        <div className={styles.selectionCounter}>
          <span>{selectedOperations.length}</span>
          <span>selected</span>
        </div>
      </div>

      <div className={styles.toolbar}>
        <div className={styles.search}>
          <input
            type="search"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search by path or summary..."
            aria-label="Search operations"
          />
        </div>

        <label className={styles.filter}>
          <span>HTTP Method</span>
          <select
            value={methodFilter}
            onChange={(event) =>
              setMethodFilter(event.target.value as HttpMethod)
            }
          >
            {methods.map((method) => (
              <option key={method} value={method}>
                {method === "ALL" ? "All methods" : method}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className={styles.tableInfo}>
        <span>
          Showing <strong>{filteredOperations.length}</strong> of{" "}
          <strong>{operations.length}</strong> operations
        </span>
      </div>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.checkboxColumn}>
                <input
                  type="checkbox"
                  checked={allFilteredSelected}
                  onChange={toggleAllOperations}
                  aria-label="Select all filtered operations"
                />
              </th>
              <th>Method</th>
              <th>Path</th>
              <th>Summary</th>
            </tr>
          </thead>

          <tbody>
            {filteredOperations.map((operation) => {
              const key = `${operation.method}-${operation.path}`;

              return (
                <tr
                  key={key}
                  className={
                    selectedOperations.includes(key) ? styles.selectedRow : ""
                  }
                >
                  <td className={styles.checkboxColumn}>
                    <input
                      type="checkbox"
                      checked={selectedOperations.includes(key)}
                      onChange={() => toggleOperation(key)}
                      aria-label={`Select ${operation.method} ${operation.path}`}
                    />
                  </td>

                  <td>
                    <span
                      className={`${styles.method} ${styles[operation.method.toLowerCase()]}`}
                    >
                      {operation.method}
                    </span>
                  </td>

                  <td className={styles.path}>{operation.path}</td>

                  <td className={styles.summary}>
                    {operation.summary ?? operation.operation_id ?? "—"}
                  </td>
                </tr>
              );
            })}

            {filteredOperations.length === 0 && (
              <tr>
                <td colSpan={4} className={styles.emptyState}>
                  No operations found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selectedOperationsWithPathParams.length > 0 && (
        <section className={styles.configurationSection}>
          <h3>Path parameters</h3>

          {selectedOperationsWithPathParams.map((operation) => {
            const operationKey = `${operation.method}-${operation.path}`;

            const operationPathParameters = operation.parameters.filter(
              (parameter) => parameter.in === "path",
            );

            return (
              <div key={operationKey} className={styles.operationConfig}>
                <h4>
                  <span>{operation.method}</span> {operation.path}
                </h4>

                <div className={styles.parametersGrid}>
                  {operationPathParameters.map((parameter) => (
                    <div className={styles.parameterField} key={parameter.name}>
                      <label htmlFor={`${operationKey}-${parameter.name}`}>
                        {parameter.name}
                        {parameter.required && (
                          <span className={styles.required}> *</span>
                        )}
                      </label>

                      <input
                        id={`${operationKey}-${parameter.name}`}
                        type="text"
                        value={
                          pathParameters[operationKey]?.[parameter.name] ?? ""
                        }
                        onChange={(event) =>
                          handlePathParameterChange(
                            operationKey,
                            parameter.name,
                            event.target.value,
                          )
                        }
                        placeholder={`Enter ${parameter.name}`}
                      />

                      {parameter.description && <p>{parameter.description}</p>}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </section>
      )}

      {selectedOperationsWithQueryParams.length > 0 && (
        <section className={styles.configurationSection}>
          <h3>Query parameters</h3>

          {selectedOperationsWithQueryParams.map((operation) => {
            const operationKey = `${operation.method}-${operation.path}`;

            const operationQueryParameters = operation.parameters.filter(
              (parameter) => parameter.in === "query",
            );

            return (
              <div key={operationKey} className={styles.operationConfig}>
                <h4>
                  <span>{operation.method}</span> {operation.path}
                </h4>

                <div className={styles.parametersGrid}>
                  {operationQueryParameters.map((parameter) => (
                    <div className={styles.parameterField} key={parameter.name}>
                      <label
                        htmlFor={`${operationKey}-${parameter.name}-query`}
                      >
                        {parameter.name}
                        {parameter.required && (
                          <span className={styles.required}> *</span>
                        )}
                      </label>

                      <input
                        id={`${operationKey}-${parameter.name}-query`}
                        type="text"
                        value={
                          queryParameters[operationKey]?.[parameter.name] ?? ""
                        }
                        onChange={(event) =>
                          handleQueryParameterChange(
                            operationKey,
                            parameter.name,
                            event.target.value,
                          )
                        }
                        placeholder={`Enter ${parameter.name}`}
                      />

                      {parameter.description && <p>{parameter.description}</p>}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </section>
      )}

      {selectedOperationsWithRequestBody.length > 0 && (
        <section className={styles.configurationSection}>
          <h3>Request Body (JSON)</h3>

          {selectedOperationsWithRequestBody.map((operation) => {
            const operationKey = `${operation.method}-${operation.path}`;

            return (
              <div key={operationKey} className={styles.operationConfig}>
                <h4>
                  <span>{operation.method}</span> {operation.path}
                </h4>

                <textarea
                  className={styles.requestBody}
                  value={requestBodies[operationKey] ?? ""}
                  onChange={(event) =>
                    onRequestBodiesChange({
                      ...requestBodies,
                      [operationKey]: event.target.value,
                    })
                  }
                  placeholder='{"name": "John"}'
                  rows={8}
                  spellCheck={false}
                />

                {operation.request_body?.required && (
                  <p className={styles.requiredHint}>
                    Request body is required
                  </p>
                )}
              </div>
            );
          })}
        </section>
      )}
    </section>
  );
};

export default OperationsList;
