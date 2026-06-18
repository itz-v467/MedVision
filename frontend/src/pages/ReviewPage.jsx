import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { clinicalApi } from "../api/clinicalApi";
import { ErrorBanner } from "../components/ErrorBanner";
import { ClinicalSignalsList } from "../components/ClinicalSignalsList";
import { ExtractedTextPanel } from "../components/ExtractedTextPanel";
import { LabResultsTable } from "../components/LabResultsTable";
import { PatientTimeline } from "../components/PatientTimeline.jsx";
import { ClinicalFindingsPanel } from "../components/review/ClinicalFindingsPanel";
import { CorrelationCards } from "../components/review/CorrelationCards";
import { SymptomTriagePanel } from "../components/review/SymptomTriagePanel";
import { EvidenceChain } from "../components/review/EvidenceChain";
import { IdentityCard } from "../components/review/IdentityCard";
import { PremiumImagingViewer } from "../components/review/PremiumImagingViewer";
import { AppRoutes } from "../enums/routes";
import { Messages } from "../enums/messages";
import { usePermissions } from "../hooks/usePermissions";
import { enrichBiomarkers } from "../utils/labInterpretation";
import { buildEvidenceSources } from "../utils/evidenceFormat";
import { plainDocType, UI_LABELS } from "../utils/plainLanguage";

function caseTypeOf(detail) {
  return (
    detail?.encounter?.case_type
    || detail?.results_overview?.case_type
    || detail?.correlation?.case_type
    || ""
  );
}

function documentManifest(detail) {
  if (detail?.document_manifest?.length) return detail.document_manifest;
  return (detail?.documents || []).map((doc) => ({
    file_name: doc.file_name,
    file_type: doc.file_type,
    document_id: doc.id,
  }));
}

function hasDocumentType(detail, type) {
  return documentManifest(detail).some((doc) => doc.file_type === type)
    || (detail?.documents || []).some((doc) => doc.file_type === type);
}

function xrayDocument(detail) {
  return (detail?.documents || []).find((doc) => doc.file_type === "xray");
}

function overallConfidence(detail) {
  const ocr = detail?.ocr?.confidence ?? 0;
  const nlp = detail?.nlp?.confidence ?? 0;
  const imaging = detail?.imaging?.confidence ?? 0;
  const caseType = caseTypeOf(detail);

  if (caseType === "multimodal") {
    const score = imaging * 0.4 + ocr * 0.4 + nlp * 0.2;
    return score > 0 ? score : null;
  }
  if (caseType === "single_xray" || hasDocumentType(detail, "xray")) {
    if (imaging > 0) return imaging;
    return ocr || null;
  }
  const score = ocr * 0.65 + nlp * 0.35;
  return score > 0 ? score : null;
}

function inferRisk(alerts) {
  if (!alerts?.length) return "low";
  if (alerts.some((a) => !a.is_acknowledged && (a.priority === "CRITICAL" || a.priority === "HIGH")))
    return "critical";
  if (alerts.some((a) => !a.is_acknowledged && (a.priority === "MODERATE" || a.priority === "MEDIUM")))
    return "moderate";
  return "low";
}

function caseTypeBadge(caseType) {
  if (caseType === "multimodal") return "Multimodal case";
  if (caseType === "single_xray") return "Chest X-ray case";
  if (caseType === "symptom_triage") return "Symptom triage case";
  return null;
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
  const [reanalyzingImaging, setReanalyzingImaging] = useState(false);
  const [regeneratingSynthesis, setRegeneratingSynthesis] = useState(false);
  const [approvingCarePlan, setApprovingCarePlan] = useState(false);
  const [requestingConsult, setRequestingConsult] = useState(false);

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

  const handleReanalyzeImaging = async () => {
    if (!encounterId) return;
    setReanalyzingImaging(true);
    setError("");
    try {
      const result = await clinicalApi.reanalyzeImaging(encounterId);
      setDetail((prev) => (prev ? { ...prev, imaging: result.imaging } : prev));
      setSuccess("Chest X-ray re-analyzed with ChestNet.");
    } catch (err) {
      setError(err.message || "Could not re-analyze chest X-ray.");
    } finally {
      setReanalyzingImaging(false);
    }
  };

  const handleRegenerateSynthesis = async () => {
    if (!encounterId) return;
    setRegeneratingSynthesis(true);
    setError("");
    try {
      await clinicalApi.regenerateSynthesis(encounterId);
      await load();
      setSuccess("Case synthesis refreshed from all inputs.");
    } catch (err) {
      const msg =
        err.status === 500
          ? "Could not refresh case synthesis. Please try again."
          : (err.message || "Could not refresh case synthesis.");
      setError(msg);
    } finally {
      setRegeneratingSynthesis(false);
    }
  };

  const handleApproveCarePlan = async () => {
    if (!encounterId) return;
    setApprovingCarePlan(true);
    setError("");
    try {
      await clinicalApi.approveCarePlan(encounterId);
      await load();
      setSuccess("Care plan approved by physician.");
    } catch (err) {
      setError(err.message || "Could not approve care plan.");
    } finally {
      setApprovingCarePlan(false);
    }
  };

  const handleRequestConsult = async (payload) => {
    if (!encounterId) return;
    if (payload?.external_link_used) return;
    setRequestingConsult(true);
    setError("");
    try {
      await clinicalApi.requestConsult(encounterId, payload);
      await load();
      setSuccess("Consult request submitted.");
    } catch (err) {
      setError(err.message || "Could not submit consult request.");
    } finally {
      setRequestingConsult(false);
    }
  };

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

  const derived = useMemo(() => {
    if (!detail) return null;
    const caseType = caseTypeOf(detail);
    const structuredData = detail?.ocr?.structured_data || {};
    const biomarkers = enrichBiomarkers(structuredData.biomarkers || []);
    const labAnalysis = structuredData.lab_analysis;
    const manifest = documentManifest(detail);
    const showLab = hasDocumentType(detail, "lab_report") || biomarkers.length > 0;
    const showImaging = Boolean(detail?.imaging && !detail.imaging.skipped);
    const primaryDocType = caseType === "multimodal"
      ? "multimodal"
      : (detail?.documents?.[0]?.file_type || "");

    return {
      caseType,
      structuredData,
      biomarkers,
      labAnalysis,
      manifest,
      showLab,
      showImaging,
      primaryDocType,
      badge: caseTypeBadge(caseType),
      xrayFile: xrayDocument(detail)?.file_name,
      confidence: overallConfidence(detail),
      sources: buildEvidenceSources(detail),
      risk: inferRisk(detail?.alerts),
    };
  }, [detail]);

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
  const initials = patient?.full_name
    ? patient.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : "?";
  const updated = detail?.encounter?.created_at
    ? new Date(detail.encounter.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })
    : "—";
  const alerts = detail?.alerts || [];

  return (
    <article className="cv-case">
      <header className="cv-case-header">
        <div className="cv-case-patient">
          <div className="cv-case-avatar" aria-hidden="true">{initials}</div>
          <div>
            <h1 className="cv-case-name">{patient?.full_name || "Unknown patient"}</h1>
            <div className="cv-case-meta-row">
              <span>ID {patient?.external_id || "—"}</span>
              {patient?.date_of_birth && <span>Age {patient.date_of_birth}</span>}
              {patient?.gender && <span>{patient.gender}</span>}
              {derived?.badge && <span className="cv-case-badge">{derived.badge}</span>}
              {!derived?.badge && derived?.primaryDocType && (
                <span>{plainDocType(derived.primaryDocType)}</span>
              )}
              <span>Updated {updated}</span>
            </div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--cv-space-2)", flexWrap: "wrap" }}>
          <span className={`cv-priority cv-priority-${derived?.risk || "low"}`}>
            {derived?.risk || "low"} priority
          </span>
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

      {derived?.structuredData.extraction_warning && (
        <div className="cv-identity cv-identity-unverified">
          <strong>Extraction notice:</strong> {derived.structuredData.extraction_warning}
        </div>
      )}

      <ClinicalFindingsPanel
        summaryText={detail?.summary?.summary_text}
        synthesis={detail?.summary?.clinical_synthesis || detail?.summary}
        labAnalysis={derived?.labAnalysis}
        docType={derived?.primaryDocType}
        imaging={detail?.imaging}
        correlation={detail?.correlation}
        confidence={derived?.confidence}
        isFinalized={detail?.summary?.status === "FINALIZED"}
        canReview={canReview}
        onFinalize={handleFinalize}
        finalizing={finalizing}
        onRegenerateSynthesis={handleRegenerateSynthesis}
        regeneratingSynthesis={regeneratingSynthesis}
        clinicalFactors={
          detail?.summary?.clinical_factors
          || detail?.summary?.evidence_sources?.global_context?.clinical_factors
        }
        carePlan={detail?.summary?.care_plan}
        possibleDiseasesReport={detail?.summary?.possible_diseases_report || []}
        consultRecommendation={detail?.summary?.consult_recommendation}
        consultConfig={detail?.consult?.config}
        consultRequest={detail?.consult?.request}
        documents={detail?.documents || []}
        patternMatches={
          detail?.summary?.evidence_sources?.global_context?.pattern_matches?.pattern_matches
          || []
        }
        onApproveCarePlan={canReview ? handleApproveCarePlan : undefined}
        approvingCarePlan={approvingCarePlan}
        onRequestConsult={handleRequestConsult}
        requestingConsult={requestingConsult}
      />

      <CorrelationCards
        correlation={detail?.correlation}
        narrative={detail?.summary?.correlation_narrative}
      />

      <SymptomTriagePanel
        triage={detail?.triage}
        encounterId={encounterId}
        canReview={canReview}
        onUpdated={load}
      />

      {derived?.showLab && (
        <section className="cv-lab-panel" aria-labelledby="lab-results-heading">
          <LabResultsTable biomarkers={derived.biomarkers} variant="clinical" />
        </section>
      )}

      {derived?.sources.length > 0 && (
        <section className="cv-section" aria-labelledby="evidence-heading">
          <h2 className="cv-section-title" id="evidence-heading">Supporting evidence</h2>
          <p className="cv-section-sub">
            Each step explains what the system reviewed — in clinical language, not raw technical data.
          </p>
          <EvidenceChain
            sources={derived.sources}
            activeId={evidenceId || derived.sources[0]?.id}
            onSelect={setEvidenceId}
            detail={detail}
          />
        </section>
      )}

      {derived?.showImaging && (
        <PremiumImagingViewer
          imaging={detail.imaging}
          fileName={derived.xrayFile}
          onReanalyze={handleReanalyzeImaging}
          reanalyzing={reanalyzingImaging}
        />
      )}

      {derived?.manifest.length > 1 && (
        <section className="cv-section" aria-labelledby="documents-heading">
          <h2 className="cv-section-title" id="documents-heading">Documents in this case</h2>
          <ul className="cv-document-manifest">
            {derived.manifest.map((doc) => (
              <li key={doc.document_id || doc.file_name}>
                <strong>{plainDocType(doc.file_type)}</strong>
                <span>{doc.file_name}</span>
                {typeof doc.biomarker_count === "number" && doc.file_type === "lab_report" && (
                  <span>{doc.biomarker_count} lab value(s)</span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

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

          {deepTab === "raw" && (derived?.showLab || derived?.structuredData.raw_text) && (
            <ExtractedTextPanel structuredData={derived.structuredData} />
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
