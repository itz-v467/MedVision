import { useState } from "react";

export function ExpandableListCard({
  title,
  count = 0,
  countLabel = "in queue",
  preview,
  loading,
  defaultOpen = false,
  emptyState,
  children,
}) {
  const [open, setOpen] = useState(defaultOpen);
  const hasItems = count > 0;

  return (
    <section className="cv-ui-card cv-expandable-list-card">
      <button
        type="button"
        className={`cv-expandable-list-trigger${open ? " is-open" : ""}`}
        aria-expanded={open}
        onClick={() => setOpen((prev) => !prev)}
      >
        <span className="cv-expandable-list-title">{title}</span>
        {!loading && (
          <span className={`cv-expandable-list-badge${hasItems ? " has-items" : ""}`}>
            {hasItems ? `${count} ${countLabel}` : "None waiting"}
          </span>
        )}
        <span className="cv-expandable-list-chevron" aria-hidden="true">
          {open ? "−" : "+"}
        </span>
      </button>

      {!open && !loading && preview && (
        <div className="cv-expandable-list-preview">{preview}</div>
      )}

      {open && (
        <div className="cv-expandable-list-body">
          {loading ? (
            <div className="cv-skeleton" style={{ height: 160 }} />
          ) : hasItems ? (
            children
          ) : (
            emptyState
          )}
        </div>
      )}
    </section>
  );
}
