import { Link, useLocation } from "react-router-dom";
import { NavIcon } from "../icons/NavIcons";
import { AppRoutes } from "../../enums/routes";
import { Roles } from "../../enums/roles";
import { SidebarPatientSearch } from "./SidebarPatientSearch";

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

  const initials = user?.full_name
    ? user.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : "MV";

  const roleLabel = ROLE_LABELS[user?.role] || user?.role?.replace(/_/g, " ") || "Staff";

  return (
    <aside className="mv-sidebar" aria-label="Main menu">
      <div className="mv-sidebar-inner">
        <Link to={AppRoutes.DASHBOARD} className="mv-sidebar-brand">
          <div className="mv-sidebar-logo" aria-hidden="true">
            <span className="mv-sidebar-logo-ring" />
            <span className="mv-sidebar-logo-core">MV</span>
          </div>
          <div>
            <strong className="mv-sidebar-title">MedVision</strong>
            <span className="mv-sidebar-tagline">Clinical decision support</span>
          </div>
        </Link>

        <SidebarPatientSearch />

        <nav className="mv-sidebar-nav" aria-label="Pages">
          <p className="mv-sidebar-nav-heading">Navigation</p>
          <ul>
            {NAV.filter((item) => (typeof item.show === "function" ? item.show(canUpload) : item.show)).map((item) => {
              const active = item.match(pathname);
              return (
                <li key={item.to}>
                  <Link
                    to={item.to}
                    className={`mv-nav-link${active ? " is-active" : ""}`}
                    aria-current={active ? "page" : undefined}
                  >
                    <span className="mv-nav-icon" aria-hidden="true">
                      <NavIcon name={item.icon} />
                    </span>
                    <span className="mv-nav-text">
                      <span className="mv-nav-label">{item.label}</span>
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="mv-sidebar-footer">
          <div className="mv-sidebar-user">
            <div className="mv-sidebar-avatar">{initials}</div>
            <div>
              <div className="mv-sidebar-user-name">{user?.full_name || "User"}</div>
              <div className="mv-sidebar-user-role">{roleLabel}</div>
            </div>
          </div>
          <button type="button" className="mv-sidebar-signout" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </div>
    </aside>
  );
}
