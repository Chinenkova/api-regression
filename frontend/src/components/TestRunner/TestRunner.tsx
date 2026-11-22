import { useState } from "react";

import { runTests, type TestRunResponse } from "../../api/tests";

import styles from "./TestRunner.module.scss";

type TestRunnerProps = {
  specUrl: string;
  token: string | null;
  operations: string[];
  pathParameters: Record<string, Record<string, string>>;
  queryParameters: Record<string, Record<string, string>>;
  requestBodies: Record<string, string>;
};

const TestRunner = ({
  specUrl,
  token,
  operations,
  pathParameters,
  queryParameters,
  requestBodies,
}: TestRunnerProps) => {
  const [baseUrl, setBaseUrl] = useState("");
  const [workers, setWorkers] = useState(5);
  const [timeout, setTimeout] = useState(15);
  const [isRunning, setIsRunning] = useState(false);
  const [runResult, setRunResult] = useState<TestRunResponse | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [expandedResponses, setExpandedResponses] = useState<string[]>([]);

  const handleRunTests = async () => {
    if (!operations.length || !baseUrl.trim()) {
      return;
    }

    setIsRunning(true);
    setRunError(null);
    setRunResult(null);
    setExpandedResponses([]);

    try {
      const result = await runTests({
        spec_url: specUrl,
        base_url: baseUrl.trim(),
        operations,
        token: token || null,
        parameters: pathParameters,
        query_parameters: queryParameters,
        request_bodies: requestBodies,
        workers,
        timeout,
      });

      setRunResult(result);
    } catch (error) {
      setRunError(
        error instanceof Error ? error.message : "Failed to run tests.",
      );
    } finally {
      setIsRunning(false);
    }
  };

  const toggleResponse = (operation: string) => {
    setExpandedResponses((current) =>
      current.includes(operation)
        ? current.filter((item) => item !== operation)
        : [...current, operation],
    );
  };

  return (
    <section className={styles.container}>
      <div className={styles.heading}>
        <h2>Test Runner</h2>
        <p>Configure the target API and run the selected operations.</p>
      </div>

      <div className={styles.runForm}>
        <div className={styles.baseUrlField}>
          <label htmlFor="base-url">Base URL</label>
          <input
            id="base-url"
            type="url"
            value={baseUrl}
            onChange={(event) => setBaseUrl(event.target.value)}
            placeholder="https://api.example.com"
          />
        </div>

        <div className={styles.baseUrlField}>
          <label htmlFor="workers">Parallel workers</label>
          <input
            id="workers"
            type="number"
            min={1}
            max={32}
            value={workers}
            onChange={(event) =>
              setWorkers(Math.min(32, Math.max(1, Number(event.target.value))))
            }
          />
        </div>

        <div className={styles.baseUrlField}>
          <label htmlFor="timeout">Timeout (seconds)</label>
          <input
            id="timeout"
            type="number"
            min={1}
            max={300}
            value={timeout}
            onChange={(event) =>
              setTimeout(Math.min(300, Math.max(1, Number(event.target.value))))
            }
          />
        </div>

        <button
          type="button"
          className={styles.runButton}
          onClick={handleRunTests}
          disabled={isRunning || !operations.length || !baseUrl.trim()}
        >
          {isRunning ? "Running..." : "Run tests"}
        </button>
      </div>

      <p className={styles.infoMessage}>
        {operations.length} operation(s) selected.
        {token
          ? " Bearer authorization will be used."
          : " Running without Bearer authorization."}
      </p>

      {runError && (
        <div className={styles.errorMessage} role="alert">
          <strong>Test run failed</strong>
          <p>{runError}</p>
        </div>
      )}

      {isRunning && (
        <div className={styles.loadingMessage}>
          Running tests. Please wait...
        </div>
      )}

      {runResult && (
        <div className={styles.resultsSection}>
          <div className={styles.resultsHeader}>
            <div>
              <h3>Test Results</h3>
              <p>Completed in {runResult.summary.duration_ms} ms</p>
            </div>

            <span
              className={`${styles.overallStatus} ${
                runResult.status === "passed" ? styles.success : styles.failure
              }`}
            >
              {runResult.status}
            </span>
          </div>

          <div className={styles.summary}>
            <div className={styles.summaryCard}>
              <span>Total</span>
              <strong>{runResult.summary.total}</strong>
            </div>

            <div className={styles.summaryCard}>
              <span>Passed</span>
              <strong className={styles.successText}>
                {runResult.summary.passed}
              </strong>
            </div>

            <div className={styles.summaryCard}>
              <span>Failed</span>
              <strong className={styles.failureText}>
                {runResult.summary.failed}
              </strong>
            </div>
          </div>

          <div className={styles.resultsList}>
            {runResult.results.map((result) => {
              const isExpanded = expandedResponses.includes(result.operation);

              return (
                <article
                  key={result.operation}
                  className={`${styles.resultCard} ${
                    result.passed ? styles.resultSuccess : styles.resultFailure
                  }`}
                >
                  <div className={styles.resultHeader}>
                    <h4>{result.operation}</h4>

                    <span
                      className={`${styles.resultStatus} ${
                        result.passed ? styles.success : styles.failure
                      }`}
                    >
                      {result.passed ? "Passed" : "Failed"}
                    </span>
                  </div>

                  <div className={styles.resultMetadata}>
                    <span>
                      Status: <strong>{result.status_code ?? "—"}</strong>
                    </span>

                    <span>
                      Duration: <strong>{result.duration_ms} ms</strong>
                    </span>
                  </div>

                  {result.error && (
                    <div className={styles.resultError}>
                      <strong>{result.error}</strong>
                    </div>
                  )}

                  {result.validation_errors.length > 0 && (
                    <div className={styles.resultError}>
                      <strong>Validation errors</strong>
                      {result.validation_errors.map((error, index) => (
                        <p key={`${error.path}-${index}`}>
                          {error.path}: {error.message}
                        </p>
                      ))}
                    </div>
                  )}

                  {result.response !== null && (
                    <div className={styles.responseSection}>
                      <button
                        type="button"
                        className={styles.responseToggle}
                        onClick={() => toggleResponse(result.operation)}
                      >
                        {isExpanded ? "Hide response" : "Show response"}
                      </button>

                      {isExpanded && (
                        <pre className={styles.responseBody}>
                          {result.response}
                        </pre>
                      )}
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
};

export default TestRunner;
