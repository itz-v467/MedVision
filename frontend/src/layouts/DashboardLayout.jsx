import { Outlet, useNavigate } from "react-router-dom";
import { ClinicalSidebar } from "../components/navigation/ClinicalSidebar";
import { AppRoutes } from "../enums/routes";
import { useAuth } from "../hooks/useAuth";
import { usePermissions } from "../hooks/usePermissions";

export function DashboardLayout() {
  const { user, logout } = useAuth();
  const { canUpload } = usePermissions();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate(AppRoutes.LOGIN);
  };

  return (
    <div className="app-shell cv-app-shell">
      <ClinicalSidebar user={user} canUpload={canUpload} onLogout={handleLogout} />
      <main className="main-content cv-main">
        <Outlet />
      </main>
    </div>
  );
}
