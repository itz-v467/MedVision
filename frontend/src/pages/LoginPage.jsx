import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AppRoutes } from "../enums/routes";
import { useAuth } from "../hooks/useAuth";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@medvision.health");
  const [password, setPassword] = useState("Admin@12345");
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    try {
      await login(email, password);
      navigate(AppRoutes.DASHBOARD);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="login-page">
      <form onSubmit={handleSubmit} className="login-card">
        <h2>MedVision Clinical AI</h2>
        <p>Enterprise multimodal CDSS platform</p>
        {error ? <div className="error-banner">{error}</div> : null}
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button type="submit">Sign In</button>
      </form>
    </div>
  );
}
