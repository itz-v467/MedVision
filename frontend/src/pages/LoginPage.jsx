import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AppRoutes } from "../enums/routes";
import { useAuth } from "../hooks/useAuth";
import { MedVisionBrand } from "../components/brand/MedVisionBrand";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const sessionExpired = location.state?.from === "session_expired";
  const [email, setEmail] = useState("admin@medvision.health");
  const [password, setPassword] = useState("Admin@12345");
  const [showPassword, setShowPassword] = useState(false);
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
      <aside className="login-brand-panel" aria-label="MedVision">
        <MedVisionBrand variant="login" />
        <p className="login-brand-lede">
          Physician-first clinical decision support — unified review of symptoms,
          labs, and imaging in one workspace.
        </p>
      </aside>

      <main className="login-form-panel">
        <div className="login-shell">
          {sessionExpired && !error && (
            <div className="login-banner login-banner-warning" role="status">
              Your session ended. Please sign in again.
            </div>
          )}

          <form onSubmit={handleSubmit} className="login-card" noValidate>
            <header className="login-card-head">
              <h2>Sign in</h2>
              <p>Use your hospital credentials to continue.</p>
            </header>

            {error && (
              <div className="login-banner login-banner-error" role="alert">
                {error}
              </div>
            )}

            <div className="login-fields">
              <label className="login-field" htmlFor="email-input">
                <span className="login-field-label">Email</span>
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

              <label className="login-field" htmlFor="password-input">
                <span className="login-field-label">Password</span>
                <div className="login-password-wrap">
                  <input
                    id="password-input"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                    required
                  />
                  <button
                    type="button"
                    className="login-password-toggle"
                    onClick={() => setShowPassword((prev) => !prev)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </label>
            </div>

            <button type="submit" className="login-submit" disabled={loading}>
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="login-footer-note">Protected access · Authorized staff only</p>
        </div>
      </main>
    </div>
  );
}
