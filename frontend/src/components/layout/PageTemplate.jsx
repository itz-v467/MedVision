export function PageTemplate({ title, subtitle, actions, children, className = "" }) {
  return (
    <div className={`cv-page ${className}`.trim()}>
      {(title || subtitle || actions) && (
        <header className="cv-page-header">
          <div className="cv-page-header-row">
            <div>
              {title && <h1 className="cv-page-title">{title}</h1>}
              {subtitle && <p className="cv-page-subtitle">{subtitle}</p>}
            </div>
            {actions}
          </div>
        </header>
      )}
      {children}
    </div>
  );
}
