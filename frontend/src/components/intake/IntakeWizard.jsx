import { Link } from "react-router-dom";
import { PatientIdBadge, PatientSearchBar } from "../patients/PatientSearchBar";
import { SymptomChatPanel } from "./SymptomChatPanel";
import { AppRoutes } from "../../enums/routes";
import { suggestFileType, fileTypeLabel } from "../../utils/uploadValidation";
import { UI_LABELS } from "../../utils/plainLanguage";

const STEPS = [
  { id: 1, label: "Patient" },
  { id: 2, label: "Case inputs" },
  { id: 3, label: "Processing" },
  { id: 4, label: "Ready" },
];

export function IntakeStepIndicator({ currentStep }) {
  return (
    <div className="cv-intake-steps" aria-label="Intake progress">
      {STEPS.map((step) => {
        const done = currentStep > step.id;
        const active = currentStep === step.id;
        return (
          <div
            key={step.id}
            className={`cv-intake-step${active ? " active" : ""}${done ? " done" : ""}`}
          >
            <span className={`cv-intake-step-dot${done ? " is-done" : ""}`}>
              {!done && step.id}
            </span>
            <span className="cv-intake-step-label">{step.label}</span>
          </div>
        );
      })}
    </div>
  );
}

export function IntakePatientStep({
  patientName,
  setPatientName,
  patientId,
  previewId,
  isExistingPatient,
  onClearExisting,
  onSelectPatient,
  patientAge,
  setPatientAge,
  patientGender,
  setPatientGender,
  onNext,
  error,
}) {
  return (
    <div className="cv-intake-card">
      <PatientSearchBar onSelectPatient={onSelectPatient} />

      <div className="cv-form-section" style={{ marginTop: "var(--cv-space-3)" }}>
        <h3>Patient information</h3>
        <p>Enter details as on the document. New patients receive an auto-generated MedVision number.</p>

        <PatientIdBadge
          patientId={patientId}
          previewId={previewId}
          isExisting={isExistingPatient}
        />
        {isExistingPatient && (
          <button type="button" className="cv-btn cv-btn-ghost cv-btn-sm" onClick={onClearExisting} style={{ marginBottom: 12 }}>
            Register as new patient instead
          </button>
        )}

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="patient-name">Full name <span className="required">*</span></label>
            <input
              id="patient-name"
              type="text"
              placeholder="As printed on report"
              value={patientName}
              onChange={(e) => setPatientName(e.target.value)}
              autoComplete="name"
              required
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="patient-age">Age (years)</label>
            <input
              id="patient-age"
              type="number"
              min="0"
              max="130"
              placeholder="Optional"
              value={patientAge}
              onChange={(e) => setPatientAge(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label htmlFor="patient-gender">Gender</label>
            <select
              id="patient-gender"
              value={patientGender}
              onChange={(e) => setPatientGender(e.target.value)}
            >
              <option value="">Select…</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="cv-intake-nav">
        <span />
        <button type="button" className="cv-btn cv-btn-primary" onClick={onNext}>
          Continue to documents →
        </button>
      </div>
    </div>
  );
}

const DOCUMENT_SLOTS = [
  { id: "lab_report", label: "Lab report", hint: "PDF, CSV, or photo of results" },
  { id: "xray", label: "Chest X-ray", hint: "PNG or JPG radiograph" },
];

export function IntakeCaseDocumentStep({
  slotFiles,
  onSlotFile,
  inputRefs,
  symptomMessages,
  onSymptomMessagesChange,
  symptomAssessment,
  onSymptomAssessmentChange,
  assistantMode,
  onAssistantModeChange,
  patientName,
  patientAge,
  patientGender,
  onBack,
  onSubmit,
  loading,
  error,
  patientLabel,
}) {
  const filled = DOCUMENT_SLOTS.filter((slot) => slotFiles[slot.id]);
  const symptomTurns = (symptomMessages || []).filter((m) => m.role === "patient").length;
  const manifestParts = [
    ...filled.map((slot) => slot.label),
    ...(symptomTurns > 0 ? [`Symptom chat (${symptomTurns} message${symptomTurns === 1 ? "" : "s"})`] : []),
  ];
  const canSubmit = filled.length > 0 || symptomTurns > 0;

  return (
    <form className="cv-intake-card cv-intake-card-wide" onSubmit={onSubmit}>
      <div className="cv-form-section">
        <h3>Build your clinical case</h3>
        <p>
          Add lab or imaging documents and/or describe symptoms with the assistant.
          Together they produce a unified physician report.
          {patientLabel && (
            <> Patient: <strong>{patientLabel}</strong></>
          )}
        </p>

        <div className="cv-intake-builder">
          <section className="cv-intake-builder-panel" aria-label="Documents">
            <div className="cv-intake-builder-panel-head">
              <h4>Documents</h4>
              <span className="cv-intake-builder-panel-hint">Lab report or chest X-ray</span>
            </div>
            <div className="cv-intake-slots">
              {DOCUMENT_SLOTS.map((slot) => {
                const file = slotFiles[slot.id];
                return (
                  <div key={slot.id} className="cv-intake-slot">
                    <div className="cv-intake-slot-head">
                      <strong>{slot.label}</strong>
                      <span className="cv-intake-slot-hint">{slot.hint}</span>
                    </div>
                    <div
                      className={`cv-dropzone cv-dropzone-compact${file ? " has-file" : ""}`}
                      onClick={() => inputRefs.current[slot.id]?.click()}
                      onDrop={(e) => {
                        e.preventDefault();
                        onSlotFile(slot.id, e.dataTransfer.files?.[0] || null);
                      }}
                      onDragOver={(e) => e.preventDefault()}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === "Enter" && inputRefs.current[slot.id]?.click()}
                    >
                      <div className="cv-dropzone-title">
                        {file ? file.name : `Add ${slot.label.toLowerCase()}`}
                      </div>
                      <div className="cv-dropzone-hint">
                        {file ? `${(file.size / 1024).toFixed(1)} KB` : slot.hint}
                      </div>
                      <input
                        ref={(el) => { inputRefs.current[slot.id] = el; }}
                        type="file"
                        accept={
                          slot.id === "xray"
                            ? ".png,.jpg,.jpeg"
                            : ".pdf,.png,.jpg,.jpeg,.txt,.csv"
                        }
                        onChange={(e) => onSlotFile(slot.id, e.target.files?.[0] || null)}
                        style={{ display: "none" }}
                      />
                    </div>
                    {file && (
                      <button
                        type="button"
                        className="cv-btn cv-btn-ghost cv-btn-sm"
                        onClick={() => onSlotFile(slot.id, null)}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </section>

          <section className="cv-intake-builder-panel" aria-label="Symptom assistant">
            <div className="cv-intake-builder-panel-head">
              <h4>Symptom assistant</h4>
              <span className="cv-intake-builder-panel-hint">Optional — pre-consult triage</span>
            </div>
            <SymptomChatPanel
              messages={symptomMessages || []}
              onMessagesChange={onSymptomMessagesChange}
              assessment={symptomAssessment}
              onAssessmentChange={onSymptomAssessmentChange}
              assistantMode={assistantMode}
              onAssistantModeChange={onAssistantModeChange}
              patientName={patientName}
              patientAge={patientAge}
              patientGender={patientGender}
              disabled={loading}
            />
          </section>
        </div>

        {manifestParts.length > 0 && (
          <p className="cv-intake-manifest">
            <strong>Case includes:</strong> {manifestParts.join(" + ")}
          </p>
        )}
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="cv-intake-nav">
        <button type="button" className="cv-btn cv-btn-secondary" onClick={onBack}>
          ← Back
        </button>
        <button type="submit" className="cv-btn cv-btn-primary" disabled={loading || !canSubmit}>
          {loading ? "Starting analysis…" : "Begin unified AI analysis"}
        </button>
      </div>
    </form>
  );
}

export function IntakeDocumentStep({
  file,
  fileType,
  setFileType,
  inputRef,
  onFileChange,
  onDrop,
  onBack,
  onSubmit,
  loading,
  error,
  patientLabel,
}) {
  const suggestedType = file ? suggestFileType(file) : null;
  const typeMismatch =
    file && suggestedType && fileType && suggestedType !== fileType
      ? `This file looks like a ${fileTypeLabel(suggestedType).toLowerCase()}, but you selected ${fileTypeLabel(fileType).toLowerCase()}. Change the document type or choose a different file.`
      : null;
  const typeHint =
    typeMismatch
      ? null
      : file && suggestedType === "xray" && fileType === "xray"
        ? "Chest X-ray selected — ChestNet image analysis will run."
        : null;

  return (
    <form className="cv-intake-card" onSubmit={onSubmit}>
      <div className="cv-form-section">
        <h3>Upload clinical document</h3>
        <p>
          PDF, image, TXT, or CSV — maximum 50 MB.
          {patientLabel && (
            <> Patient: <strong>{patientLabel}</strong></>
          )}
        </p>

        <div className="form-group">
          <label htmlFor="file-type-select">Document type</label>
          <select
            id="file-type-select"
            value={fileType}
            onChange={(e) => setFileType(e.target.value)}
            required
          >
            <option value="">Select document type…</option>
            <option value="lab_report">Lab report (PDF / CSV / photo)</option>
            <option value="xray">Chest X-ray (PNG / JPG)</option>
          </select>
        </div>

        {typeMismatch && <p className="cv-intake-type-hint cv-intake-type-warning">{typeMismatch}</p>}
        {typeHint && <p className="cv-intake-type-hint">{typeHint}</p>}

        <div
          className="cv-dropzone"
          onClick={() => inputRef.current?.click()}
          onDrop={onDrop}
          onDragOver={(e) => e.preventDefault()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        >
          <div className="cv-dropzone-title">
            {file ? file.name : "Drop file here or click to browse"}
          </div>
          <div className="cv-dropzone-hint">
            {file
              ? `${(file.size / 1024).toFixed(1)} KB`
              : "Supported: PDF, PNG, JPG, TXT, CSV"}
          </div>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.txt,.csv"
            onChange={onFileChange}
            style={{ display: "none" }}
          />
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="cv-intake-nav">
        <button type="button" className="cv-btn cv-btn-secondary" onClick={onBack}>
          ← Back
        </button>
        <button type="submit" className="cv-btn cv-btn-primary" disabled={loading || !file || !fileType}>
          {loading ? "Starting analysis…" : "Begin AI analysis"}
        </button>
      </div>
    </form>
  );
}

export function IntakeProcessingStep({ pipeline, loading, complete, totalLatencyMs }) {
  const steps = pipeline?.steps || [];
  const stages = steps.length > 0 ? steps : [
    { id: "ocr", label: "Reading document", status: loading ? "active" : "pending" },
    { id: "nlp", label: "Extracting clinical data", status: "pending" },
    { id: "summary", label: "Generating summary", status: "pending" },
  ];

  return (
    <div className="cv-intake-card">
      <div className="cv-form-section">
        <h3>{complete ? "Analysis complete" : "AI is processing your case"}</h3>
        <p>
          {complete
            ? `Finished in ${totalLatencyMs ? (totalLatencyMs / 1000).toFixed(1) : "—"} seconds. Your clinical summary is ready for physician review.`
            : "Extracting biomarkers, correlating findings, and building an explainable summary. This typically takes under a minute."}
        </p>
      </div>

      <div className="cv-pipeline-milestones">
        {stages.map((step) => {
          const status = step.status === "completed" || step.status === "skipped"
            ? "done"
            : step.status === "active" || (loading && !complete && !step.status)
              ? "active"
              : complete
                ? "done"
                : "";
          return (
            <div key={step.id} className={`cv-pipeline-milestone ${status}`}>
              <span className={`cv-pipeline-milestone-dot${status ? ` is-${status}` : ""}`} />
              <div>
                <div className="cv-pipeline-milestone-label">{step.label}</div>
                {step.summary && (
                  <div className="cv-pipeline-milestone-detail">{step.summary}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function IntakeReadyStep({ encounterId, uploadResult, onReset }) {
  const headline = uploadResult?.results_overview?.headline;
  const nameValidation = uploadResult?.name_validation;

  return (
    <div className="cv-intake-card">
      <div className="cv-form-section">
        <h3>Case ready for review</h3>
        {uploadResult?.patient_external_id && (
          <p className="cv-patient-id-assigned">
            Patient number: <strong>{uploadResult.patient_external_id}</strong>
          </p>
        )}
        {headline && <p style={{ fontSize: "var(--cv-text-base)", color: "var(--cv-slate-700)" }}>{headline}</p>}
        {nameValidation?.skipped && (
          <div className="cv-identity cv-identity-unverified" style={{ marginTop: 16 }}>
            <strong>Identity check:</strong> {nameValidation.message || "Please verify patient name on the document."}
          </div>
        )}
        {nameValidation?.matched && !nameValidation?.skipped && nameValidation?.extracted_name && (
          <div className="cv-identity cv-identity-verified" style={{ marginTop: 16 }}>
            <strong>Name verified:</strong> {nameValidation.extracted_name}
          </div>
        )}
      </div>

      <div className="cv-intake-nav" style={{ flexDirection: "column" }}>
        <Link to={`${AppRoutes.REVIEW}/${encounterId}`} className="cv-btn cv-btn-primary cv-btn-block">
          Open physician review →
        </Link>
        <button type="button" className="cv-btn cv-btn-secondary cv-btn-block" onClick={onReset}>
          {UI_LABELS.uploadAnother || "Upload another case"}
        </button>
      </div>
    </div>
  );
}
