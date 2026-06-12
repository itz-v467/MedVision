/** Plain-language labels for doctors and patients (avoid technical jargon). */

export const PIPELINE_STEPS = {
  ocr: {
    label: "Reading your document",
    detail: "Scanning the report and finding test results and patient details",
  },
  nlp: {
    label: "Understanding medical terms",
    detail: "Identifying conditions, symptoms, and medications mentioned",
  },
  imaging: {
    label: "Checking X-ray images",
    detail: "Looking for areas that may need a doctor's attention",
  },
  correlation: {
    label: "Connecting all findings",
    detail: "Combining lab results, notes, and scans into one picture",
  },
  rag: {
    label: "Checking medical references",
    detail: "Comparing results with standard medical guidance",
  },
  summary: {
    label: "Writing your health summary",
    detail: "Preparing an easy-to-read summary for your doctor",
  },
  alerts: {
    label: "Safety checks",
    detail: "Flagging anything that may need urgent attention",
  },
};

export const STATUS_LABELS = {
  PENDING: "Waiting",
  QUEUED: "In queue",
  PROCESSING: "Processing",
  COMPLETED: "Done",
  FAILED: "Could not complete",
  REVIEW_REQUIRED: "Ready for doctor review",
  FINALIZED: "Approved by doctor",
  DELETED: "Removed",
};

export function plainStatus(status) {
  return STATUS_LABELS[status] || status || "Unknown";
}

export function plainDocType(type) {
  if (type === "lab_report") return "Blood / lab report";
  if (type === "xray") return "Chest X-ray";
  if (type === "clinical_note") return "Doctor's notes";
  return type || "Medical document";
}

export const UI_LABELS = {
  labResults: "Your test results",
  referenceRange: "Normal range",
  abnormal: "Needs attention",
  normal: "Looks good",
  precautions: "What you should know",
  wellness: "Results that look healthy",
  aiConfidence: "How sure the system is",
  recommendedActions: "Suggested next steps",
  identityVerified: "Name on form matches the report",
  identityMismatch: "Name on form does not match the report",
  identitySkipped: "Could not read name from report — please verify manually",
  analysisOverview: "Your health report at a glance",
  pipelineTrace: "How your report was processed",
  uploadTitle: "Upload a health document",
  patientSection: "About the patient",
  documentSection: "Document to upload",
  deleteRecord: "Remove this record",
  deleteConfirm:
    "Remove this case from your list? A secure log will be kept for compliance. This cannot be undone.",
};
