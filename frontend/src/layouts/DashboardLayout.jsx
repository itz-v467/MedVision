import { Outlet, useNavigate } from "react-router-dom";
import { ClinicalSidebar } from "../components/navigation/ClinicalSidebar";
import { ClinicalTopBar } from "../components/navigation/ClinicalTopBar";
import { AppRoutes } from "../enums/routes";
import { ShellProvider, useShell } from "../context/ShellContext";
import { useAuth } from "../hooks/useAuth";
import { useBreadcrumbs } from "../hooks/useBreadcrumbs";
import { usePermissions } from "../hooks/usePermissions";

function DashboardLayoutInner() {
  const { user, logout } = useAuth();
  const { canUpload } = usePermissions();
  const navigate = useNavigate();
  const breadcrumbs = useBreadcrumbs();
  const { sidebarExpanded, toggleSidebar } = useShell();

  const handleLogout = async () => {
    await logout();
    navigate(AppRoutes.LOGIN);
  };

  return (
    <div
      className={`app-shell cv-app-shell${sidebarExpanded ? " is-sidebar-expanded" : " is-sidebar-collapsed"}`}
    >
      <ClinicalSidebar user={user} canUpload={canUpload} onLogout={handleLogout} />
      <div className="cv-app-body">
        <ClinicalTopBar breadcrumbs={breadcrumbs} onMenuToggle={toggleSidebar} />
        <main className="main-content cv-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function DashboardLayout() {
  return (
    <ShellProvider>
      <DashboardLayoutInner />
    </ShellProvider>
  );
}
