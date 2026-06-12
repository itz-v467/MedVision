export function ErrorBanner({ message, onRetry }) {
  if (!message) {
    return null;
  }
  return (
    <div className="error-banner">
      <span>{message}</span>
      {onRetry ? (
        <button type="button" onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </div>
  );
}
