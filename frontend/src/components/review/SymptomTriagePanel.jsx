import { useState } from "react";
import { clinicalApi } from "../../api/clinicalApi";

const RISK_LABELS = {
  low: "Low urgency",
  moderate: "Moderate urgency",
  high: "High urgency",
  emergency: "Emergency",
};

export function SymptomTriagePanel({ triage, encounterId, canReview, onUpdated }) {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [physicianNote, setPhysicianNote] = useState("");
  const [error, setError] = useState("");

  const session = triage?.session;
  const messages = triage?.messages || [];
  if (!session) return null;

  const risk = session.risk_level || "low";
  const assessment = session.assessment || {};

  const handleSend = async () => {
    if (!message.trim()) return;
    setLoading(true);
    setError("");
    try {
      await clinicalApi.triageAddMessage(encounterId, message.trim());
      setMessage("");
      onUpdated?.();
    } catch (err) {
      setError(err.message || "Could not send message.");
    } finally {
      setLoading(false);
    }
  };

  const handleFinalize = async () => {
    setLoading(true);
    setError("");
    try {
      await clinicalApi.triageFinalize(encounterId, physicianNote.trim() || undefined);
      onUpdated?.();
    } catch (err) {
      setError(err.message || "Could not finalize triage.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="cv-section cv-triage-panel" aria-labelledby="triage-heading">
      <h2 className="cv-section-title" id="triage-heading">Symptom triage</h2>
      <p className="cv-section-sub">
        Patient-reported symptoms collected before physician review. Triage guidance only — not a diagnosis.
      </p>

      <div className={`cv-triage-risk is-${risk}`}>
        <strong>{RISK_LABELS[risk] || risk}</strong>
        {session.recommended_disposition && <span> — {session.recommended_disposition}</span>}
      </div>

      {(assessment.rationale || []).length > 0 && (
        <ul className="cv-triage-rationale">
          {assessment.rationale.map((line, idx) => (
            <li key={`rationale-${idx}`}>{line}</li>
          ))}
        </ul>
      )}

      <div className="cv-symptom-chat-thread cv-triage-thread">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`cv-symptom-chat-bubble is-${msg.role === "patient" ? "patient" : "assistant"}`}
          >
            <span className="cv-symptom-chat-role">
              {msg.role === "patient" ? "Patient" : "Assistant"}
            </span>
            <p>{msg.message_text}</p>
          </div>
        ))}
      </div>

      {session.status !== "finalized" && (
        <div className="cv-triage-actions">
          <div className="cv-symptom-chat-input-row">
            <input
              type="text"
              className="cv-symptom-chat-input"
              placeholder="Add follow-up symptom detail…"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              disabled={loading}
            />
            <button
              type="button"
              className="cv-btn cv-btn-secondary cv-btn-sm"
              onClick={handleSend}
              disabled={loading || !message.trim()}
            >
              Add note
            </button>
          </div>

          {canReview && (
            <div className="cv-triage-physician">
              <label htmlFor="physician-triage-note">Physician triage note (optional)</label>
              <textarea
                id="physician-triage-note"
                rows={2}
                value={physicianNote}
                onChange={(e) => setPhysicianNote(e.target.value)}
                placeholder="Document clinical judgment after reviewing symptoms…"
              />
              <button
                type="button"
                className="cv-btn cv-btn-primary cv-btn-sm"
                onClick={handleFinalize}
                disabled={loading}
              >
                Finalize triage review
              </button>
            </div>
          )}
        </div>
      )}

      {session.status === "finalized" && (
        <p className="cv-triage-finalized">Triage reviewed and finalized by physician.</p>
      )}

      {error && <p className="cv-symptom-chat-error">{error}</p>}
      <p className="cv-symptom-chat-disclaimer">{triage?.disclaimer}</p>
    </section>
  );
}
