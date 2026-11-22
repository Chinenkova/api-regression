import { useState } from "react";

import styles from "./Authorization.module.scss";

type AuthorizationProps = {
  token: string | null;
  onAuthorize: (token: string) => void;
  onLogout: () => void;
};

const Authorization = ({
  token,
  onAuthorize,
  onLogout,
}: AuthorizationProps) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [inputToken, setInputToken] = useState("");

  const handleAuthorize = () => {
    const normalizedToken = inputToken.trim();

    if (!normalizedToken) {
      return;
    }

    onAuthorize(normalizedToken);
    setInputToken("");
    setIsModalOpen(false);
  };

  const handleClose = () => {
    setInputToken("");
    setIsModalOpen(false);
  };

  return (
    <>
      {token ? (
        <button
          type="button"
          className={styles.authorizedButton}
          onClick={onLogout}
        >
          <span className={styles.statusDot} />
          Authorized
          <span className={styles.logoutText}>· Logout</span>
        </button>
      ) : (
        <button
          type="button"
          className={styles.authorizeButton}
          onClick={() => setIsModalOpen(true)}
        >
          Authorize
        </button>
      )}

      {isModalOpen && (
        <div
          className={styles.overlay}
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              handleClose();
            }
          }}
        >
          <div
            className={styles.modal}
            role="dialog"
            aria-modal="true"
            aria-labelledby="auth-title"
          >
            <div className={styles.modalHeader}>
              <div>
                <h2 id="auth-title">Authorize</h2>
                <p>Enter your API access token</p>
              </div>

              <button
                type="button"
                className={styles.closeButton}
                onClick={handleClose}
                aria-label="Close authorization dialog"
              >
                ×
              </button>
            </div>

            <form
              onSubmit={(event) => {
                event.preventDefault();
                handleAuthorize();
              }}
            >
              <label htmlFor="auth-token">Bearer Token</label>

              <input
                id="auth-token"
                type="password"
                value={inputToken}
                onChange={(event) => setInputToken(event.target.value)}
                placeholder="Paste your access token"
                autoComplete="off"
                autoFocus
                required
              />

              <p className={styles.hint}>
                Your token will be kept for the current browser tab session.
              </p>

              <div className={styles.actions}>
                <button
                  type="button"
                  className={styles.cancelButton}
                  onClick={handleClose}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className={styles.submitButton}
                  disabled={!inputToken.trim()}
                >
                  Authorize
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default Authorization;
