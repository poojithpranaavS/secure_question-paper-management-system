import { useState } from "react";

import {
  login,
  saveAuthentication,
  verifyMFA,
} from "../services/api";

function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [mfaRequired, setMfaRequired] =
    useState(false);

  const [mfaToken, setMfaToken] = useState("");
  const [mfaCode, setMfaCode] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(event) {
    event.preventDefault();

    setLoading(true);
    setError("");

    try {
      const data = await login(
        email,
        password
      );

      if (data.mfa_required) {
        setMfaRequired(true);
        setMfaToken(data.mfa_token);
        return;
      }

      saveAuthentication(
        data.access_token,
        data.user
      );

      onLogin(data.user);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to authenticate."
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleMFAVerification(event) {
    event.preventDefault();

    setLoading(true);
    setError("");

    try {
      const data = await verifyMFA(
        mfaToken,
        mfaCode
      );

      saveAuthentication(
        data.access_token,
        data.user
      );

      onLogin(data.user);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "MFA verification failed."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-background" />

      <div className="auth-card">
        <div className="brand-mark">
          SQ
        </div>

        <div className="auth-heading">
          <span className="eyebrow">
            SECURE EXAMINATION INFRASTRUCTURE
          </span>

          <h1>
            Secure Question Paper
            <br />
            Management System
          </h1>

          <p>
            Controlled access, encrypted storage,
            verified releases and complete
            accountability.
          </p>
        </div>

        {!mfaRequired ? (
          <form
            className="auth-form"
            onSubmit={handleLogin}
          >
            <label>
              Official Email
              <input
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="Enter your email"
                required
              />
            </label>

            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Enter your password"
                required
              />
            </label>

            {error && (
              <div className="error-box">
                {error}
              </div>
            )}

            <button
              className="primary-button"
              type="submit"
              disabled={loading}
            >
              {loading
                ? "Authenticating..."
                : "Sign in securely"}
            </button>
          </form>
        ) : (
          <form
            className="auth-form"
            onSubmit={
              handleMFAVerification
            }
          >
            <div className="mfa-header">
              <span className="mfa-icon">
                2FA
              </span>

              <div>
                <h2>
                  Multi-Factor Verification
                </h2>

                <p>
                  Enter the six-digit code from
                  your authenticator application.
                </p>
              </div>
            </div>

            <label>
              Authentication Code
              <input
                className="mfa-input"
                type="text"
                inputMode="numeric"
                maxLength="6"
                value={mfaCode}
                onChange={(event) =>
                  setMfaCode(
                    event.target.value.replace(
                      /\D/g,
                      ""
                    )
                  )
                }
                placeholder="000000"
                required
              />
            </label>

            {error && (
              <div className="error-box">
                {error}
              </div>
            )}

            <button
              className="primary-button"
              type="submit"
              disabled={
                loading ||
                mfaCode.length !== 6
              }
            >
              {loading
                ? "Verifying..."
                : "Verify identity"}
            </button>

            <button
              type="button"
              className="secondary-button"
              onClick={() => {
                setMfaRequired(false);
                setMfaToken("");
                setMfaCode("");
                setError("");
              }}
            >
              Back to login
            </button>
          </form>
        )}

        <div className="security-footer">
          <span>●</span>
          Protected communication
          <span className="footer-divider">
            |
          </span>
          AES-256
          <span className="footer-divider">
            |
          </span>
          SHA-256
        </div>
      </div>
    </div>
  );
}

export default Login;