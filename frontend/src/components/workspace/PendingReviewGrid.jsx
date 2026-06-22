import { Link } from "react-router-dom";
import { AppRoutes } from "../../enums/routes";
import { PendingReviewCard } from "../review/PendingReviewCard";
import { EmptyState } from "../ui/EmptyState";

const DISPLAY_LIMIT = 6;

export function PendingReviewGrid({ items = [], loading, canUpload }) {
  const visible = items.slice(0, DISPLAY_LIMIT);
  const hasMore = items.length > DISPLAY_LIMIT;

  return (
    <section className="cv-pending-section" aria-labelledby="pending-review-heading">
      <header className="cv-pending-section-head">
        <div>
          <h2 id="pending-review-heading" className="cv-pending-section-title">
            Reports pending review
          </h2>
          <p className="cv-pending-section-sub">
            Tap a card to open the case and complete physician review.
          </p>
        </div>
        {!loading && items.length > 0 && (
          <span className="cv-pending-section-badge">{items.length} waiting</span>
        )}
      </header>

      {loading ? (
        <div className="cv-pending-grid">
          {[1, 2, 3].map((n) => (
            <div key={n} className="cv-skeleton cv-pending-card-skeleton" />
          ))}
        </div>
      ) : items.length > 0 ? (
        <>
          <div className="cv-pending-grid">
            {visible.map((enc) => (
              <PendingReviewCard key={enc.id} encounter={enc} />
            ))}
          </div>
          {hasMore && (
            <p className="cv-pending-section-more">
              <Link to={`${AppRoutes.ENCOUNTERS}?status=pending`}>
                View all {items.length} pending →
              </Link>
            </p>
          )}
        </>
      ) : (
        <EmptyState
          message="No reports waiting for review. Upload a lab result or scan to get started."
          action={canUpload ? { label: "Add first case", to: AppRoutes.UPLOAD } : null}
        />
      )}
    </section>
  );
}
