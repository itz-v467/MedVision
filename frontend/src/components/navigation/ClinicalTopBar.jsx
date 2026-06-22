import { Link } from "react-router-dom";

export function ClinicalTopBar({ breadcrumbs = [], actions = null, onMenuToggle }) {
  return (
    <header className="cv-topbar" aria-label="Page navigation">
      <div className="cv-topbar-start">
        <button
          type="button"
          className="cv-topbar-menu-btn"
          onClick={onMenuToggle}
          aria-label="Toggle sidebar"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <nav aria-label="Breadcrumb">
          <ol className="cv-topbar-breadcrumbs">
            {breadcrumbs.map((crumb, idx) => (
              <li key={`${crumb.label}-${idx}`}>
                {crumb.to ? <Link to={crumb.to}>{crumb.label}</Link> : crumb.label}
              </li>
            ))}
          </ol>
        </nav>
      </div>
      {actions && <div className="cv-topbar-actions">{actions}</div>}
    </header>
  );
}
