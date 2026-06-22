import { useState } from "react";
import { formatClinicalSummary } from "../../utils/clinicalSummaryFormat";
import { ClinicalFactorCard } from "./ClinicalFactorCard";
import { PossibleDiseasesReport } from "./PossibleDiseasesReport";
import { CarePlanPanel } from "./CarePlanPanel";
import { ConsultDoctorCard } from "./ConsultDoctorCard";
import { StructuredSummary } from "./StructuredSummary";
import { ClinicalTabs } from "../ui/ClinicalTabs";

const TABS = [
  { id: "patient", label: "For you" },
  { id: "conditions", label: "Possible conditions" },
  { id: "careplan", label: "Care plan" },
  { id: "physician", label: "For your doctor" },
  { id: "next", label: "Next steps" },
];

export function ClinicalFindingsPanel({
  summaryText,
  synthesis,
  labAnalysis,
  docType,
  imaging,
  correlation,
  confidence,
  isFinalized,
  canReview,
  onFinalize,
  finalizing,
  onRegenerateSynthesis,
  regeneratingSynthesis = false,
  clinicalFactors,
  carePlan,
  possibleDiseasesReport = [],
  consultRecommendation,
  consultConfig,
  consultRequest,
  documents = [],
  patternMatches = [],
  onApproveCarePlan,
  approvingCarePlan = false,
  onRequestConsult,
  requestingConsult = false,
  embedded = false,
}) {
  const [tab, setTab] = useState("patient");
  const formatted = formatClinicalSummary(summaryText, labAnalysis, { docType, imaging, synthesis });
  const pct = confidence != null ? Math.round(confidence * 100) : null;
  const confidenceCaption =
    docType === "xray"
      ? "Based on ChestNet image analysis signals."
      : "Based on OCR, NLP, and document quality signals.";

  const leading = synthesis?.leading_diagnosis;
  const differential = synthesis?.differential || [];
  const workup = synthesis?.recommended_workup || [];
  const correlationNarrative =
    synthesis?.correlation_narrative || correlation?.cards?.[0]?.note;
  const factorsReview = synthesis?.clinical_factors_review;
  const recovery = carePlan?.recovery || synthesis?.care_plan?.recovery || {};
  const carePlanApproved = (carePlan?.status || synthesis?.care_plan?.status) === "approved";

  return (
    <section className={`cv-findings-primary${embedded ? " is-embedded" : ""}`} aria-labelledby="findings-heading">
      <div className="cv-findings-hero">
        {!embedded && (
          <div className="cv-synthesis-header">
            <h2 id="findings-heading">Clinical case synthesis</h2>
            <p className="cv-section-sub cv-synthesis-sub">
              Unified review of symptoms, labs, and imaging.
            </p>
            <p className="cv-synthesis-disclaimer">
              AI-assisted synthesis only — not a diagnosis. A licensed physician must review all findings.
            </p>
            {onRegenerateSynthesis && (
              <button
                type="button"
                className="cv-btn cv-btn-secondary"
                onClick={onRegenerateSynthesis}
                disabled={regeneratingSynthesis}
              >
                {regeneratingSynthesis ? "Refreshing…" : "Refresh case synthesis"}
              </button>
            )}
          </div>
        )}

        {embedded && (
          <h2 id="findings-heading" className="cv-ui-card-title">Clinical synthesis</h2>
        )}

        <ClinicalFactorCard factors={clinicalFactors} documents={documents} />

        <ClinicalTabs tabs={TABS} activeId={tab} onChange={setTab} ariaLabel="Summary views" />

        {tab === "patient" && (
          <div className="cv-synthesis-panel" role="tabpanel">
            {formatted.patientHeadline && (
              <StructuredSummary
                text={formatted.patientHeadline}
                variant="patient"
                title="Your case at a glance"
              />
            )}
            {formatted.attention.length > 0 && (
              <div className="cv-finding-attention">
                <h4>What needs attention</h4>
                <ul>
                  {formatted.attention.map((item) => (
                    <li key={item.test}>
                      <strong>{item.test}</strong> ({item.flag}) — {item.text}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {leading?.condition && (
              <div className="cv-leading-diagnosis is-patient">
                <span className="cv-leading-label">Most likely pattern</span>
                <strong className="cv-leading-condition">{leading.condition}</strong>
                {leading.confidence && (
                  <span className={`cv-confidence-chip is-${leading.confidence}`}>
                    {leading.confidence} confidence
                  </span>
                )}
                {leading.rationale && (
                  <StructuredSummary text={leading.rationale} variant="rationale" />
                )}
              </div>
            )}
            {(recovery.foods_to_eat?.length > 0 || recovery.hydration_rest) && (
              <div className="cv-recovery-summary">
                <h4>Recovery guidance</h4>
                {recovery.foods_to_eat?.length > 0 && (
                  <p><strong>Eat:</strong> {recovery.foods_to_eat.slice(0, 4).join(", ")}</p>
                )}
                {recovery.foods_to_avoid?.length > 0 && (
                  <p><strong>Avoid:</strong> {recovery.foods_to_avoid.slice(0, 4).join(", ")}</p>
                )}
                {recovery.hydration_rest && <p>{recovery.hydration_rest}</p>}
              </div>
            )}
            {formatted.healthy.length > 0 && (
              <div className="cv-finding-healthy">
                <strong>Within normal range:</strong> {formatted.healthy.join(", ")}
              </div>
            )}
          </div>
        )}

        {tab === "conditions" && (
          <div className="cv-synthesis-panel" role="tabpanel">
            <PossibleDiseasesReport
              report={possibleDiseasesReport}
              patterns={patternMatches}
            />
            {differential.length > 0 && possibleDiseasesReport.length === 0 && (
              <div className="cv-differential">
                <h4>Differential diagnosis</h4>
                <ul className="cv-differential-list">
                  {differential.map((item) => (
                    <li key={item.condition} className={`is-${item.likelihood || "low"}`}>
                      <div className="cv-diff-header">
                        <strong>{item.condition}</strong>
                        <span>{item.likelihood} likelihood</span>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {tab === "careplan" && (
          <div className="cv-synthesis-panel" role="tabpanel">
            <CarePlanPanel
              carePlan={carePlan || synthesis?.care_plan}
              canReview={canReview}
              onApprove={onApproveCarePlan}
              approving={approvingCarePlan}
              showMedications={carePlanApproved || canReview}
            />
            {!carePlan && !synthesis?.care_plan && (
              <p className="cv-section-sub">
                Refresh case synthesis after uploading all reports to generate a suggested care plan.
              </p>
            )}
          </div>
        )}

        {tab === "physician" && (
          <div className="cv-synthesis-panel" role="tabpanel">
            {formatted.physicianHeadline && (
              <StructuredSummary
                text={formatted.physicianHeadline}
                variant="physician"
                title="Physician clinical summary"
              />
            )}
            {factorsReview && (
              <StructuredSummary
                text={factorsReview}
                variant="physician"
                title="Clinical factors review"
              />
            )}
            {correlationNarrative && (
              <StructuredSummary
                text={correlationNarrative}
                variant="correlation"
                title="Cross-modal correlation"
              />
            )}
            {synthesis?.root_cause_analysis && (
              <div className="cv-root-cause">
                <h4>Root cause analysis</h4>
                <StructuredSummary text={synthesis.root_cause_analysis} variant="rationale" />
              </div>
            )}
            {formatted.showFullNote && formatted.doctorNote !== formatted.physicianHeadline && (
              <details className="cv-admin-fold">
                <summary>Full physician note (verbatim)</summary>
                <div className="cv-admin-body">
                  <StructuredSummary text={formatted.doctorNote} variant="physician" />
                </div>
              </details>
            )}
            {workup.length > 0 && (
              <div className="cv-workup-list">
                <h4>Suggested workup</h4>
                <ul>
                  {workup.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ul>
              </div>
            )}
            <CarePlanPanel
              carePlan={carePlan || synthesis?.care_plan}
              canReview={canReview}
              onApprove={onApproveCarePlan}
              approving={approvingCarePlan}
              showMedications
            />
          </div>
        )}

        {tab === "next" && (
          <div className="cv-synthesis-panel" role="tabpanel">
            <NextStepsInline
              precautions={labAnalysis?.precautions || []}
              workup={workup}
              docType={docType}
            />
            <ConsultDoctorCard
              consultRecommendation={consultRecommendation}
              consultConfig={consultConfig}
              existingRequest={consultRequest}
              onRequestConsult={onRequestConsult}
              requesting={requestingConsult}
            />
          </div>
        )}

        {canReview && !isFinalized && tab !== "next" && !embedded && (
          <button
            type="button"
            className="cv-btn cv-btn-primary cv-btn-block"
            style={{ marginTop: "var(--cv-space-3)" }}
            onClick={onFinalize}
            disabled={finalizing}
          >
            {finalizing ? "Approving…" : "Physician approves summary"}
          </button>
        )}
        {isFinalized && (
          <div className="success-banner" style={{ marginTop: "var(--cv-space-2)" }}>
            Summary approved and finalized.
          </div>
        )}
      </div>

      {!embedded && (
      <aside>
        {pct != null && (
          <div className="cv-confidence-card">
            <p className="cv-confidence-label">Evidence strength</p>
            <div className="cv-confidence-value">{pct}%</div>
            <div className="cv-confidence-bar">
              <div className="cv-confidence-bar-fill" style={{ width: `${pct}%` }} />
            </div>
            <p style={{ margin: "12px 0 0", fontSize: "var(--cv-text-xs)", color: "var(--cv-slate-400)" }}>
              {confidenceCaption}
            </p>
          </div>
        )}
      </aside>
      )}
    </section>
  );
}

function NextStepsInline({ precautions, workup, docType }) {
  const steps = workup?.length
    ? workup
    : precautions.slice(0, 4).map((p) => `${p.test} (${p.flag}): ${p.precaution}`);

  if (!steps.length) {
    return (
      <div className="cv-next-steps">
        <h3>Recommended next steps</h3>
        <p style={{ margin: 0, fontSize: "var(--cv-text-sm)", color: "var(--cv-slate-500)" }}>
          {docType === "xray"
            ? "Correlate the scan with symptoms and have a radiologist or physician review the image."
            : "No urgent actions. Correlate with clinical presentation and discuss at next visit."}
        </p>
      </div>
    );
  }

  return (
    <div className="cv-next-steps">
      <h3>Recommended next steps</h3>
      <ol>
        {steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
      <p style={{ margin: "12px 0 0", fontSize: "var(--cv-text-xs)", color: "var(--cv-slate-500)" }}>
        Not a diagnosis. Physician judgment required.
      </p>
    </div>
  );
}
