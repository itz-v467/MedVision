import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { clinicalApi } from "../api/clinicalApi";
import { ErrorBanner } from "../components/ErrorBanner";
import { HeatmapImage } from "../components/HeatmapImage";
import { PatientTimeline } from "../components/PatientTimeline.jsx";
import { AppRoutes } from "../enums/routes";
import { Messages } from "../enums/messages";
import { usePermissions } from "../hooks/usePermissions";

export function ReviewPage() {
  const { encounterId } = useParams();
  const { canReview } = usePermissions();
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [finalizing, setFinalizing] = useState(false);
  const [acknowledgingId, setAcknowledgingId] = useState(null);
  const [success, setSuccess] = useState("");

  const load = useCallback(async () => {
    if (!encounterId) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await clinicalApi.getEncounter(encounterId);
      setDetail(data);
    } catch (err) {
      setError(err.message || Messages.LOAD_ERROR);
    } finally {
      setLoading(false);
    }
  }, [encounterId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleFinalize = async () => {
    const summaryId = detail?.summary?.id;
    if (!summaryId) {
      setError("No summary available to finalize.");
      return;
    }
    setFinalizing(true);
    setError("");
    setSuccess("");
    try {
      await clinicalApi.finalizeSummary(summaryId);
      setSuccess("Summary finalized successfully.");
      await load();
    } catch (err) {
      setError(err.message || "Failed to finalize summary.");
    } finally {
      setFinalizing(false);
    }
  };

  const handleAcknowledge = async (alertId) => {
    setAcknowledgingId(alertId);
    setError("");
    try {
      await clinicalApi.acknowledgeAlert(alertId);
      setSuccess("Alert acknowledged.");
      await load();
    } catch (err) {
      setError(err.message || "Failed to acknowledge alert.");
    } finally {
      setAcknowledgingId(null);
    }
  };

  if (loading) {
    return <div className="chart-skeleton" />;
  }

  const summary = detail?.summary;
  const imaging = detail?.imaging;
  const isFinalized = summary?.status === "FINALIZED";

  return (
    <div>
      <header className="page-header">
        <h2>Physician Review</h2>
        <p>
          Encounter {encounterId} · Patient {detail?.patient?.full_name || "—"}
        </p>
        <Link to={AppRoutes.ENCOUNTERS}>← Back to triage queue</Link>
      </header>

      <ErrorBanner message={error} onRetry={load} />
      {success ? <div className="success-banner">{success}</div> : null}

      <section className="panel review-grid">
        <article>
          <h3>AI Clinical Summary</h3>
          <p className="summary-text">{summary?.summary_text || "No summary generated."}</p>
          <p>
            <strong>Status:</strong> {summary?.status || "—"}
          </p>
          {canReview && summary && !isFinalized ? (
            <button type="button" onClick={handleFinalize} disabled={finalizing}>
              {finalizing ? "Finalizing..." : "Approve & Finalize"}
            </button>
          ) : null}
        </article>

        <article>
          <h3>Imaging Findings</h3>
          {imaging?.findings ? (
            <ul className="findings-list">
              {Object.entries(imaging.findings).map(([name, data]) => (
                <li key={name}>
                  {name}: {(data.probability * 100).toFixed(1)}%
                  {data.detected ? " (detected)" : ""}
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-state">No imaging analysis for this encounter.</p>
          )}
          <h4>Explainability Heatmap</h4>
          <HeatmapImage url={imaging?.heatmap_url} />
        </article>

        <article>
          <h3>Patient Timeline</h3>
          <PatientTimeline timeline={detail?.timeline} />
        </article>

        <article>
          <h3>OCR / Labs</h3>
          <pre>{JSON.stringify(detail?.ocr?.structured_data || {}, null, 2)}</pre>
        </article>

        <article>
          <h3>NLP Entities</h3>
          <pre>{JSON.stringify(detail?.nlp?.entities || {}, null, 2)}</pre>
        </article>

        <article>
          <h3>Alerts</h3>
          {detail?.alerts?.length ? (
            <ul className="findings-list">
              {detail.alerts.map((alert) => (
                <li key={alert.id}>
                  [{alert.priority}] {alert.title}: {alert.message}
                  {alert.is_acknowledged ? (
                    " — Acknowledged"
                  ) : (
                    <>
                      {" "}
                      <button
                        type="button"
                        onClick={() => handleAcknowledge(alert.id)}
                        disabled={acknowledgingId === alert.id}
                      >
                        {acknowledgingId === alert.id ? "Saving..." : "Acknowledge"}
                      </button>
                    </>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-state">No alerts.</p>
          )}
        </article>
      </section>
    </div>
  );
}
