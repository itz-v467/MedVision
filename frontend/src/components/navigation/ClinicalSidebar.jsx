import { Link, useLocation } from "react-router-dom";
import { NavIcon } from "../icons/NavIcons";
import { AppRoutes } from "../../enums/routes";
import { Roles } from "../../enums/roles";
import { MedVisionBrand } from "../brand/MedVisionBrand";
import { useShell } from "../../context/ShellContext";

const ROLE_LABELS = {
  [Roles.ADMIN]: "Administrator",
  [Roles.PHYSICIAN]: "Physician",
  [Roles.RADIOLOGIST]: "Radiologist",
  [Roles.TECHNICIAN]: "Lab technician",
  [Roles.ANALYST]: "Analyst",
  [Roles.VIEWER]: "Viewer",
};

const NAV = [
  {
    to: AppRoutes.DASHBOARD,
    icon: "workspace",
    label: "Workspace",
    match: (p) => p === AppRoutes.DASHBOARD,
    show: true,
  },
  {
    to: AppRoutes.UPLOAD,
    icon: "upload",
    label: "New case",
    match: (p) => p.startsWith(AppRoutes.UPLOAD),
    show: (canUpload) => canUpload,
  },
  {
    to: AppRoutes.ENCOUNTERS,
    icon: "reports",
    label: "Reports",
    match: (p) => p.startsWith(AppRoutes.ENCOUNTERS) || p.startsWith("/review"),
    show: true,
  },
];

export function ClinicalSidebar({ user, canUpload, onLogout }) {
  const location = useLocation();
  const pathname = location.pathname;
  const { sidebarExpanded, toggleSidebar } = useShell();

  const initials = user?.full_name
    ? user.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : "MV";

  const roleLabel = ROLE_LABELS[user?.role] || user?.role?.replace(/_/g, " ") || "Staff";
  const navItems = NAV.filter((item) => (typeof item.show === "function" ? item.show(canUpload) : item.show));

  return (
    <aside
      className={`cv-sidebar${sidebarExpanded ? " is-expanded" : " is-collapsed"}`}
      aria-label="Main menu"
    >
      {!sidebarExpanded ? (
        <button
          type="button"
          className="cv-sidebar-fab"
          onClick={toggleSidebar}
          aria-label="Open menu"
          title="Open menu"
        >
          <MedVisionBrand variant="icon" />
        </button>
      ) : (
        <div className="cv-sidebar-inner">
          <div className="cv-sidebar-header">
            <button
              type="button"
              className="cv-sidebar-brand-btn"
              onClick={toggleSidebar}
              aria-label="Close menu"
            >
              <MedVisionBrand variant="sidebar" />
            </button>
          </div>

          <nav className="cv-sidebar-nav" aria-label="Pages">
            <p className="cv-sidebar-nav-heading">Navigation</p>
            <ul>
              {navItems.map((item) => {
                const active = item.match(pathname);
                return (
                  <li key={item.to}>
                    <Link
                      to={item.to}
                      className={`cv-nav-link${active ? " is-active" : ""}`}
                      aria-current={active ? "page" : undefined}
                    >
                      <span className="cv-nav-icon" aria-hidden="true">
                        <NavIcon name={item.icon} />
                      </span>
                      <span className="cv-nav-label">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          <div className="cv-sidebar-footer">
            <div className="cv-sidebar-user">
              <div className="cv-sidebar-avatar">{initials}</div>
              <div className="cv-sidebar-user-text">
                <div className="cv-sidebar-user-name">{user?.full_name || "User"}</div>
                <div className="cv-sidebar-user-role">{roleLabel}</div>
              </div>
            </div>
            <button type="button" className="cv-sidebar-signout" onClick={onLogout}>
              Sign out
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
