import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AppRoutes } from "../enums/routes";
import { useAuth } from "../hooks/useAuth";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const sessionExpired = location.state?.from === "session_expired";
  const [email, setEmail] = useState("admin@medvision.health");
  const [password, setPassword] = useState("Admin@12345");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate(AppRoutes.DASHBOARD);
    } catch (err) {
      setError(err.message || "Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-shell">
        {sessionExpired && !error && (
          <div className="cv-error-banner cv-error-banner-auth login-session-banner">
            <div className="cv-error-banner-text">
              Your session ended. Please sign in again.
            </div>
          </div>
        )}

        <div className="login-brand">
          <div className="login-logo" aria-hidden="true">MV</div>
          <div>
            <h1 className="login-brand-title">MedVision</h1>
            <p className="login-brand-sub">Clinical decision support</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="login-card">
          <div className="login-card-head">
            <h2>Sign in</h2>
            <p>Use your hospital credentials to access the workspace.</p>
          </div>

          {error && (
            <div className="error-banner login-error">{error}</div>
          )}

          <label htmlFor="email-input">
            Email
            <input
              id="email-input"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="physician@hospital.org"
              required
            />
          </label>

          <label htmlFor="password-input">
            Password
            <input
              id="password-input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
            />
          </label>

          <button type="submit" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="login-footer">MedVision CDSS</p>
      </div>
    </div>
  );
}
