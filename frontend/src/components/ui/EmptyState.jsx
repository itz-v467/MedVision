import { Link } from "react-router-dom";

export function EmptyState({ message, action }) {
  return (
    <div className="cv-empty-state">
      <p>{message}</p>
      {action?.to && (
        <Link to={action.to} className="cv-btn cv-btn-primary cv-btn-sm">
          {action.label}
        </Link>
      )}
    </div>
  );
}
