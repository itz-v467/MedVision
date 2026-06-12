import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { clinicalApi } from "../api/clinicalApi";
import { ErrorBanner } from "../components/ErrorBanner";
import { ClinicalSignalsList } from "../components/ClinicalSignalsList";
import { ExtractedTextPanel } from "../components/ExtractedTextPanel";
import { LabResultsTable } from "../components/LabResultsTable";
import { PatientTimeline } from "../components/PatientTimeline.jsx";
import { ClinicalFindingsPanel } from "../components/review/ClinicalFindingsPanel";
import { EvidenceChain } from "../components/review/EvidenceChain";
import { IdentityCard } from "../components/review/IdentityCard";
import { PremiumImagingViewer } from "../components/review/PremiumImagingViewer";
import { AppRoutes } from "../enums/routes";
import { Messages } from "../enums/messages";
import { usePermissions } from "../hooks/usePermissions";
import { enrichBiomarkers } from "../utils/labInterpretation";
import { plainDocType, UI_LABELS } from "../utils/plainLanguage";

function primaryDocumentType(detail) {
  return detail?.documents?.[0]?.file_type || "";
}

function overallConfidence(detail) {
  const ocr = detail?.ocr?.confidence ?? 0;
  const nlp = detail?.nlp?.confidence ?? 0;
  const imaging = detail?.imaging?.confidence ?? 0;
  const docType = primaryDocumentType(detail);
  if (docType === "lab_report" || docType === "clinical_note") {
    const score = ocr * 0.65 + nlp * 0.35;
    return score > 0 ? score : null;
  }
  if (imaging > 0) {
    return imaging * 0.5 + ocr * 0.25 + nlp * 0.25;
  }
  return ocr || nlp || null;
}

function inferRisk(alerts) {
  if (!alerts?.length) return "low";
  if (alerts.some((a) => !a.is_acknowledged && (a.priority === "CRITICAL" || a.priority === "HIGH")))
    return "critical";
  if (alerts.some((a) => !a.is_acknowledged && (a.priority === "MODERATE" || a.priority === "MEDIUM")))
    return "moderate";
  return "low";
}

function buildEvidenceSources(detail) {
  const sources = [];
  const ocrData = detail?.ocr?.structured_data;
  if (ocrData && Object.keys(ocrData).length) {
    const preview = ocrData.raw_text_preview || ocrData.raw_text || "";
    const biomarkerCount = ocrData.biomarkers?.length ?? 0;
    sources.push({
      id: "ocr",
      label: "Document extraction (OCR)",
      meta: `${biomarkerCount} biomarkers · ${((detail.ocr.confidence ?? 0) * 100).toFixed(0)}% confidence`,
      snippet: preview || JSON.stringify(ocrData, null, 2).slice(0, 600),
    });
  }
  if (detail?.nlp?.entities) {
    const ents = detail.nlp.entities;
    const count = Array.isArray(ents) ? ents.length : Object.keys(ents).length;
    sources.push({
      id: "nlp",
      label: "Clinical NLP entities",
      meta: `${count} entities · ICD-10 / SNOMED mapped`,
      snippet: JSON.stringify(detail.nlp.entities, null, 2).slice(0, 400),
    });
  }
  if (detail?.imaging?.findings) {
    sources.push({
      id: "imaging",
      label: "Imaging AI analysis",
      meta: `Model ${detail.imaging.model_version || "v1"}`,
      snippet: JSON.stringify(detail.imaging.findings, null, 2).slice(0, 400),
    });
  }
  const evidenceBundle = detail?.summary?.evidence_sources;
  if (evidenceBundle && typeof evidenceBundle === "object") {
    const chunkCount = Array.isArray(evidenceBundle.rag_chunks)
      ? evidenceBundle.rag_chunks.length
      : Object.keys(evidenceBundle).length;
    sources.push({
      id: "rag",
      label: "Evidence retrieval (RAG)",
      meta: `${chunkCount} retrieved source(s)`,
      snippet: JSON.stringify(evidenceBundle, null, 2).slice(0, 500),
    });
  }
  return sources;
}

export function ReviewPage() {
  const { encounterId } = useParams();
  const navigate = useNavigate();
  const { canReview } = usePermissions();
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [finalizing, setFinalizing] = useState(false);
  const [acknowledgingId, setAcknowledgingId] = useState(null);
  const [success, setSuccess] = useState("");
  const [deepTab, setDeepTab] = useState("raw");
  const [evidenceId, setEvidenceId] = useState(null);

  const load = useCallback(async () => {
    if (!encounterId) return;
    setLoading(true);
    setError("");
    try {
      const data = await clinicalApi.getEncounter(encounterId);
      setDetail(data);
      const sources = buildEvidenceSources(data);
      if (sources.length) setEvidenceId(sources[0].id);
    } catch (err) {
      setError(err.message || Messages.LOAD_ERROR);
    } finally {
      setLoading(false);
    }
  }, [encounterId]);

  useEffect(() => { load(); }, [load]);

  const handleFinalize = async () => {
    const summaryId = detail?.summary?.id;
    if (!summaryId) { setError("No summary available to finalize."); return; }
    setFinalizing(true); setError(""); setSuccess("");
    try {
      await clinicalApi.finalizeSummary(summaryId);
      setSuccess("Summary finalized and approved.");
      await load();
    } catch (err) {
      setError(err.message || "Failed to finalize summary.");
    } finally {
      setFinalizing(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(UI_LABELS.deleteConfirm)) return;
    setError("");
    try {
      await clinicalApi.deleteEncounter(encounterId);
      navigate(AppRoutes.ENCOUNTERS);
    } catch (err) {
      setError(err.message || "Could not remove this record.");
    }
  };

  const handleAcknowledge = async (alertId) => {
    setAcknowledgingId(alertId); setError("");
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
    return (
      <div className="cv-case">
        <div className="cv-skeleton" style={{ height: 80 }} />
        <div className="cv-skeleton" style={{ height: 320 }} />
        <div className="cv-skeleton" style={{ height: 240 }} />
      </div>
    );
  }

  const patient = detail?.patient;
  const risk = inferRisk(detail?.alerts);
  const docType = primaryDocumentType(detail);
  const structuredData = detail?.ocr?.structured_data || {};
  const biomarkers = enrichBiomarkers(structuredData.biomarkers || []);
  const labAnalysis = structuredData.lab_analysis;
  const confidence = overallConfidence(detail);
  const sources = buildEvidenceSources(detail);
  const initials = patient?.full_name
    ? patient.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : "?";
  const updated = detail?.encounter?.created_at
    ? new Date(detail.encounter.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })
    : "—";
  const hasImaging = Boolean(detail?.imaging);
  const alerts = detail?.alerts || [];

  return (
    <article className="cv-case">
      {/* Level 4 — Admin metadata (unobtrusive) */}
      <header className="cv-case-header">
        <div className="cv-case-patient">
          <div className="cv-case-avatar" aria-hidden="true">{initials}</div>
          <div>
            <h1 className="cv-case-name">{patient?.full_name || "Unknown patient"}</h1>
            <div className="cv-case-meta-row">
              <span>ID {patient?.external_id || "—"}</span>
              {patient?.date_of_birth && <span>Age {patient.date_of_birth}</span>}
              {patient?.gender && <span>{patient.gender}</span>}
              <span>{plainDocType(docType)}</span>
              <span>Updated {updated}</span>
            </div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--cv-space-2)", flexWrap: "wrap" }}>
          <span className={`cv-priority cv-priority-${risk}`}>{risk} priority</span>
          <Link to={AppRoutes.ENCOUNTERS} className="cv-btn cv-btn-ghost cv-btn-sm">
            ← All cases
          </Link>
          <button type="button" className="cv-btn cv-btn-danger cv-btn-sm" onClick={handleDelete}>
            {UI_LABELS.deleteRecord}
          </button>
        </div>
      </header>

      <IdentityCard validation={detail?.name_validation} />

      <ErrorBanner message={error} onRetry={load} />
      {success && <div className="success-banner">{success}</div>}

      {structuredData.extraction_warning && (
        <div className="cv-identity cv-identity-unverified">
          <strong>Extraction notice:</strong> {structuredData.extraction_warning}
        </div>
      )}

      {/* Level 1 — Clinical findings (dominant) */}
      <ClinicalFindingsPanel
        summaryText={detail?.summary?.summary_text}
        labAnalysis={labAnalysis}
        confidence={confidence}
        isFinalized={detail?.summary?.status === "FINALIZED"}
        canReview={canReview}
        onFinalize={handleFinalize}
        finalizing={finalizing}
      />

      {(docType === "lab_report" || biomarkers.length > 0) && (
        <section className="cv-lab-panel" aria-labelledby="lab-results-heading">
          <LabResultsTable biomarkers={biomarkers} variant="clinical" />
        </section>
      )}

      {/* Level 2 — Supporting evidence (inline, not buried) */}
      {sources.length > 0 && (
        <section className="cv-section" aria-labelledby="evidence-heading">
          <h2 className="cv-section-title" id="evidence-heading">Supporting evidence</h2>
          <p className="cv-section-sub">
            Trace each finding to its source. Select a node to view extracted references.
          </p>
          <EvidenceChain
            sources={sources}
            activeId={evidenceId || sources[0]?.id}
            onSelect={setEvidenceId}
            detail={detail}
          />
        </section>
      )}

      {/* Level 3 — Imaging validation */}
      {hasImaging && <PremiumImagingViewer imaging={detail.imaging} />}

      {/* Active alerts */}
      {alerts.length > 0 && (
        <section className="cv-panel cv-panel-pad">
          <h2 className="cv-section-title" style={{ fontSize: "var(--cv-text-base)" }}>Clinical alerts</h2>
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`cv-alert-item${alert.priority === "MODERATE" ? " cv-alert-item-moderate" : ""}`}
              style={{ marginBottom: 8 }}
            >
              <p className="cv-alert-title">[{alert.priority}] {alert.title}</p>
              <p className="cv-alert-msg">{alert.message}</p>
              {!alert.is_acknowledged && (
                <button
                  type="button"
                  className="cv-btn cv-btn-sm cv-btn-secondary"
                  style={{ marginTop: 8 }}
                  onClick={() => handleAcknowledge(alert.id)}
                  disabled={acknowledgingId === alert.id}
                >
                  {acknowledgingId === alert.id ? "Saving…" : "Acknowledge"}
                </button>
              )}
            </div>
          ))}
        </section>
      )}

      {/* Deep dive — progressive disclosure */}
      <details className="cv-admin-fold">
        <summary>Administrative details &amp; deep exploration</summary>
        <div className="cv-admin-body">
          {detail?.pipeline?.steps?.length > 0 && (
            <div>
              <strong style={{ fontSize: "var(--cv-text-sm)" }}>Processing log</strong>
              <ul style={{ margin: "8px 0 0", paddingLeft: 18, fontSize: "var(--cv-text-sm)", color: "var(--cv-slate-500)" }}>
                {detail.pipeline.steps.map((s) => (
                  <li key={s.id}>{s.label}: {s.summary || s.status}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="cv-deep-tabs" role="tablist">
            {["raw", "nlp", "timeline"].map((tab) => (
              <button
                key={tab}
                type="button"
                role="tab"
                className={`cv-deep-tab${deepTab === tab ? " active" : ""}`}
                onClick={() => setDeepTab(tab)}
              >
                {tab === "raw" ? "Raw text" : tab === "nlp" ? "NLP entities" : "Timeline"}
              </button>
            ))}
          </div>

          {deepTab === "raw" && (docType === "lab_report" || structuredData.raw_text) && (
            <ExtractedTextPanel structuredData={structuredData} />
          )}
          {deepTab === "nlp" && detail?.nlp?.entities && (
            <ClinicalSignalsList entities={detail.nlp.entities} />
          )}
          {deepTab === "timeline" && detail?.timeline && (
            <PatientTimeline timeline={detail.timeline} />
          )}
        </div>
      </details>
    </article>
  );
}
