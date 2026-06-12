import { Link, Outlet, useNavigate } from "react-router-dom";
import { AppRoutes } from "../enums/routes";
import { useAuth } from "../hooks/useAuth";
import { usePermissions } from "../hooks/usePermissions";

export function DashboardLayout() {
  const { user, logout } = useAuth();
  const { canUpload, canViewAudit, canReview } = usePermissions();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate(AppRoutes.LOGIN);
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>MedVision</h1>
        <nav>
          <Link to={AppRoutes.DASHBOARD}>Dashboard</Link>
          {canUpload ? <Link to={AppRoutes.UPLOAD}>Upload & AI Workflow</Link> : null}
          <Link to={AppRoutes.ENCOUNTERS}>Encounter Triage</Link>
          {canReview ? <Link to={AppRoutes.ENCOUNTERS}>Physician Review</Link> : null}
          {canViewAudit ? <Link to={AppRoutes.AUDIT}>Audit Logs</Link> : null}
        </nav>
        <div className="user-panel">
          <p>{user?.full_name}</p>
          <small>{user?.role}</small>
          <button type="button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
