import { useNavigate } from "react-router-dom";
import { IconAlert, IconLock } from "./icons/NavIcons";
import { AppRoutes } from "../enums/routes";
import { useAuth } from "../hooks/useAuth";

function isAuthErrorMessage(message) {
  if (!message) return false;
  const lower = message.toLowerCase();
  return (
    lower.includes("authentication required") ||
    lower.includes("session has expired") ||
    lower.includes("sign in again")
  );
}

export function ErrorBanner({ message, onRetry, authExpired = false }) {
  const navigate = useNavigate();
  const { logout } = useAuth();

  if (!message) return null;

  const isAuth = authExpired || isAuthErrorMessage(message);

  const handleSignIn = async () => {
    await logout();
    navigate(AppRoutes.LOGIN, { replace: true });
  };

  return (
    <div
      className={`cv-error-banner${isAuth ? " cv-error-banner-auth" : ""}`}
      role="alert"
    >
      <div className="cv-error-banner-text">
        <span className="cv-error-banner-icon" aria-hidden="true">
          {isAuth ? <IconLock /> : <IconAlert />}
        </span>
        <span>
          {isAuth
            ? "Your session has expired or is invalid. Sign in again to continue."
            : message}
        </span>
      </div>
      {isAuth ? (
        <button type="button" className="cv-btn cv-btn-primary cv-btn-sm" onClick={handleSignIn}>
          Sign in again
        </button>
      ) : (
        onRetry && (
          <button type="button" className="cv-btn cv-btn-secondary cv-btn-sm" onClick={onRetry}>
            Try again
          </button>
        )
      )}
    </div>
  );
}
