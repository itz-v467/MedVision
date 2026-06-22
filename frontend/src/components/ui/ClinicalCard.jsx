export function ClinicalCard({ title, action, children, className = "", padding = true }) {
  return (
    <section className={`cv-ui-card ${padding ? "is-padded" : ""} ${className}`.trim()}>
      {(title || action) && (
        <header className="cv-ui-card-head">
          {title && <h2 className="cv-ui-card-title">{title}</h2>}
          {action}
        </header>
      )}
      {children}
    </section>
  );
}
