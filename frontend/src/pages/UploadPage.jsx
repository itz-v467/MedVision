import { useEffect, useRef, useState } from "react";
import { clinicalApi } from "../api/clinicalApi";
import {
  IntakeCaseDocumentStep,
  IntakePatientStep,
  IntakeProcessingStep,
  IntakeReadyStep,
  IntakeStepIndicator,
} from "../components/intake/IntakeWizard";
import { UI_LABELS } from "../utils/plainLanguage";
import { validateImageContent, validateUpload } from "../utils/uploadValidation";

const EMPTY_SLOTS = {
  lab_report: null,
  xray: null,
  clinical_note: null,
};

function validatePatientForm({ patientName, patientAge }) {
  const name = patientName.trim();
  if (!name || name.toLowerCase() === "unknown patient") {
    return "Patient full name is required and must match the document.";
  }
  if (name.length < 2) {
    return "Enter the patient's full name as shown on the report.";
  }
  if (patientAge && (Number.isNaN(Number(patientAge)) || Number(patientAge) < 0 || Number(patientAge) > 130)) {
    return "Enter a valid age between 0 and 130.";
  }
  return "";
}

export function UploadPage() {
  const [step, setStep] = useState(1);
  const [slotFiles, setSlotFiles] = useState(EMPTY_SLOTS);
  const [patientName, setPatientName] = useState("");
  const [patientId, setPatientId] = useState("");
  const [previewId, setPreviewId] = useState("");
  const [isExistingPatient, setIsExistingPatient] = useState(false);
  const [patientAge, setPatientAge] = useState("");
  const [patientGender, setPatientGender] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [encounterId, setEncounterId] = useState(null);
  const [pipeline, setPipeline] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const inputRefs = useRef({});

  useEffect(() => {
    clinicalApi.previewPatientId()
      .then((data) => {
        if (!isExistingPatient) setPreviewId(data.patient_external_id || "");
      })
      .catch(() => {});
  }, [isExistingPatient]);

  const handleSlotFile = (slotId, file) => {
    setSlotFiles((prev) => ({ ...prev, [slotId]: file || null }));
    setError("");
  };

  const handleSelectPatient = (patient) => {
    setIsExistingPatient(true);
    setPatientId(patient.external_id);
    setPatientName(patient.full_name || "");
    setPatientAge(patient.age || "");
    setPatientGender(patient.gender || "");
    setError("");
  };

  const handleClearExistingPatient = () => {
    setIsExistingPatient(false);
    setPatientId("");
    clinicalApi.previewPatientId()
      .then((data) => setPreviewId(data.patient_external_id || ""))
      .catch(() => setPreviewId(""));
  };

  const handlePatientNext = () => {
    const patientError = validatePatientForm({ patientName, patientAge });
    if (patientError) {
      setError(patientError);
      return;
    }
    setError("");
    setStep(2);
  };

  const handleUpload = async (event) => {
    event.preventDefault();
    const entries = Object.entries(slotFiles).filter(([, file]) => Boolean(file));
    if (!entries.length) {
      setError("Add at least one document (lab report, chest X-ray, or clinical note).");
      return;
    }

    for (const [slotId, file] of entries) {
      const validation = validateUpload(file, slotId);
      if (!validation.ok) {
        setError(validation.message);
        return;
      }
      const contentValidation = await validateImageContent(file, slotId);
      if (!contentValidation.ok) {
        setError(contentValidation.message);
        return;
      }
    }

    setLoading(true);
    setError("");
    setStep(3);
    setEncounterId(null);
    setPipeline(null);
    setUploadResult(null);

    const formData = new FormData();
    entries.forEach(([, file]) => formData.append("files", file));
    entries.forEach(([slotId]) => formData.append("file_types", slotId));
    formData.append(
      "patient_external_id",
      isExistingPatient && patientId ? patientId.trim() : "AUTO"
    );
    formData.append("patient_name", patientName.trim());
    if (patientAge) formData.append("patient_age", patientAge.trim());
    if (patientGender) formData.append("patient_gender", patientGender);

    try {
      const data = entries.length === 1
        ? await clinicalApi.uploadSingleLegacy(entries[0][1], entries[0][0], formData)
        : await clinicalApi.uploadCase(formData);
      setPipeline(data.pipeline || null);
      setUploadResult(data);
      setEncounterId(data.encounter_id);
      if (data.patient_external_id) setPatientId(data.patient_external_id);
      setStep(4);
    } catch (err) {
      setError(err.message || "An error occurred during processing.");
      setPipeline(null);
      setStep(2);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setStep(1);
    setEncounterId(null);
    setSlotFiles(EMPTY_SLOTS);
    setPipeline(null);
    setUploadResult(null);
    setPatientName("");
    setPatientId("");
    setPreviewId("");
    setIsExistingPatient(false);
    setPatientAge("");
    setPatientGender("");
    setError("");
    clinicalApi.previewPatientId()
      .then((data) => setPreviewId(data.patient_external_id || ""))
      .catch(() => {});
  };

  const currentStep = encounterId ? 4 : loading ? 3 : step;

  return (
    <div className="cv-intake">
      <header className="cv-intake-header">
        <h1>{UI_LABELS.uploadTitle}</h1>
        <p>Upload lab reports, chest X-rays, and notes in one case for a unified doctor report.</p>
      </header>

      <IntakeStepIndicator currentStep={currentStep} />

      {step === 1 && !loading && !encounterId && (
        <IntakePatientStep
          patientName={patientName}
          setPatientName={setPatientName}
          patientId={patientId}
          previewId={previewId}
          isExistingPatient={isExistingPatient}
          onClearExisting={handleClearExistingPatient}
          onSelectPatient={handleSelectPatient}
          patientAge={patientAge}
          setPatientAge={setPatientAge}
          patientGender={patientGender}
          setPatientGender={setPatientGender}
          onNext={handlePatientNext}
          error={error}
        />
      )}

      {step === 2 && !loading && !encounterId && (
        <IntakeCaseDocumentStep
          slotFiles={slotFiles}
          onSlotFile={handleSlotFile}
          inputRefs={inputRefs}
          onBack={() => { setStep(1); setError(""); }}
          onSubmit={handleUpload}
          loading={loading}
          error={error}
          patientLabel={isExistingPatient ? patientId : previewId}
        />
      )}

      {(loading || (step === 3 && !encounterId)) && (
        <IntakeProcessingStep
          pipeline={pipeline}
          loading={loading}
          complete={false}
          totalLatencyMs={pipeline?.total_latency_ms}
        />
      )}

      {encounterId && step === 4 && (
        <IntakeReadyStep
          encounterId={encounterId}
          uploadResult={uploadResult}
          onReset={resetForm}
        />
      )}
    </div>
  );
}
