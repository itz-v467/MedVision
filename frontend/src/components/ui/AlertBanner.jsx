export function AlertBanner({
  variant = "error",
  title,
  message,
  onRetry,
  retryLabel = "Try again",
  action,
}) {
  if (!message && !title) return null;

  return (
    <div className={`cv-alert-banner is-${variant}`} role="alert">
      <div className="cv-alert-banner-body">
        {title && <strong className="cv-alert-banner-title">{title}</strong>}
        {message && <p className="cv-alert-banner-msg">{message}</p>}
      </div>
      {(onRetry || action) && (
        <div className="cv-alert-banner-actions">
          {onRetry && (
            <button type="button" className="cv-btn cv-btn-secondary cv-btn-sm" onClick={onRetry}>
              {retryLabel}
            </button>
          )}
          {action}
        </div>
      )}
    </div>
  );
}
