import { useState } from "react";

export function ConsultDoctorCard({
  consultRecommendation,
  consultConfig,
  existingRequest,
  onRequestConsult,
  requesting = false,
}) {
  const [requested, setRequested] = useState(Boolean(existingRequest));
  const urgency = consultRecommendation?.urgency || consultConfig?.default_urgency || "within_24h";
  const telehealthUrl = consultConfig?.telehealth_booking_url;
  const reason = consultRecommendation?.reason || "Physician review recommended for your case.";

  const handleInApp = async () => {
    if (onRequestConsult) {
      await onRequestConsult({ urgency, reason, external_link_used: false });
      setRequested(true);
    }
  };

  return (
    <section className="cv-consult-card" aria-labelledby="consult-heading">
      <h3 id="consult-heading">Consult a doctor</h3>
      <p className="cv-consult-reason">{reason}</p>
      <p className="cv-consult-urgency">
        Recommended urgency: <strong>{urgency.replace(/_/g, " ")}</strong>
      </p>

      <div className="cv-consult-actions">
        <button
          type="button"
          className="cv-btn cv-btn-primary"
          onClick={handleInApp}
          disabled={requesting || requested}
        >
          {requested ? "Consult request sent" : requesting ? "Sending…" : "Request in-app consult"}
        </button>
        {telehealthUrl && (
          <a
            href={telehealthUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="cv-btn cv-btn-secondary"
          >
            Book telehealth visit
          </a>
        )}
      </div>

      {existingRequest && (
        <p className="cv-consult-status">
          Request status: {existingRequest.status} · submitted {new Date(existingRequest.created_at).toLocaleString()}
        </p>
      )}
    </section>
  );
}
