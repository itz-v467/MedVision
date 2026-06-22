export function CaseActionRail({
  canReview,
  isFinalized,
  onRegenerate,
  regenerating,
  onFinalize,
  finalizing,
  onDelete,
}) {
  return (
    <div className="cv-case-action-rail">
      {onRegenerate && (
        <button
          type="button"
          className="cv-btn cv-btn-secondary cv-btn-sm"
          onClick={onRegenerate}
          disabled={regenerating}
        >
          {regenerating ? "Refreshing…" : "Refresh synthesis"}
        </button>
      )}
      {canReview && !isFinalized && onFinalize && (
        <button
          type="button"
          className="cv-btn cv-btn-primary cv-btn-sm"
          onClick={onFinalize}
          disabled={finalizing}
        >
          {finalizing ? "Approving…" : "Approve summary"}
        </button>
      )}
      {isFinalized && (
        <span className="cv-case-action-status">Summary finalized</span>
      )}
      {onDelete && (
        <button type="button" className="cv-btn cv-btn-danger cv-btn-sm" onClick={onDelete}>
          Delete case
        </button>
      )}
    </div>
  );
}
