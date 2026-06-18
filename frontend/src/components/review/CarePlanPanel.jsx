import { useState } from "react";

const CARE_PLAN_DISCLAIMER =
  "Suggestions only — not a prescription until your doctor approves this care plan.";

export function CarePlanPanel({
  carePlan,
  canReview,
  onApprove,
  approving = false,
  showMedications = false,
}) {
  const [open, setOpen] = useState(false);
  if (!carePlan) return null;

  const recovery = carePlan.recovery || {};
  const status = carePlan.status || "pending_physician_approval";
  const approved = status === "approved";

  return (
    <div className="cv-care-plan">
      <div className="cv-care-plan-banner">{CARE_PLAN_DISCLAIMER}</div>

      <button
        type="button"
        className="cv-btn cv-btn-primary"
        onClick={() => setOpen((v) => !v)}
      >
        {open ? "Hide suggested treatment plan" : "View suggested treatment plan"}
      </button>

      {open && (
        <div className="cv-care-plan-body">
          <p className={`cv-care-plan-status${approved ? " is-approved" : ""}`}>
            Status: {approved ? "Approved by physician" : "Pending physician approval"}
          </p>

          {showMedications && (carePlan.medications?.length > 0 || carePlan.otc_options?.length > 0) && (
            <section>
              <h4>Suggested medications (physician must confirm)</h4>
              <ul>
                {(carePlan.medications || []).map((med) => (
                  <li key={med.name}>
                    <strong>{med.name}</strong> — {med.purpose}
                    {med.typical_dose_range && (
                      <span> ({med.typical_dose_range})</span>
                    )}
                  </li>
                ))}
                {(carePlan.otc_options || []).map((otc) => (
                  <li key={otc}>{otc}</li>
                ))}
              </ul>
            </section>
          )}

          {!showMedications && !approved && (
            <p className="cv-section-sub">
              Full medication suggestions are visible to your doctor until the care plan is approved.
            </p>
          )}

          {recovery.foods_to_eat?.length > 0 && (
            <section>
              <h4>Foods that may support recovery</h4>
              <ul>{recovery.foods_to_eat.map((f) => <li key={f}>{f}</li>)}</ul>
            </section>
          )}
          {recovery.foods_to_avoid?.length > 0 && (
            <section>
              <h4>Foods / substances to avoid</h4>
              <ul>{recovery.foods_to_avoid.map((f) => <li key={f}>{f}</li>)}</ul>
            </section>
          )}
          {recovery.activities_to_avoid?.length > 0 && (
            <section>
              <h4>Activities to avoid</h4>
              <ul>{recovery.activities_to_avoid.map((f) => <li key={f}>{f}</li>)}</ul>
            </section>
          )}
          {recovery.hydration_rest && (
            <p><strong>Rest & hydration:</strong> {recovery.hydration_rest}</p>
          )}
          {(carePlan.monitoring || []).length > 0 && (
            <section>
              <h4>Monitor at home</h4>
              <ul>{carePlan.monitoring.map((m) => <li key={m}>{m}</li>)}</ul>
            </section>
          )}

          {canReview && !approved && onApprove && (
            <button
              type="button"
              className="cv-btn cv-btn-secondary cv-btn-block"
              onClick={onApprove}
              disabled={approving}
            >
              {approving ? "Approving…" : "Physician approves care plan"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
