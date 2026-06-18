/** Turn dense AI summary text into scannable patient-friendly bullets. */

export function formatClinicalSummary(summaryText = "", labAnalysis = null, options = {}) {
  const { docType, imaging, synthesis } = options;
  const precautions = labAnalysis?.precautions || [];
  const wellness = labAnalysis?.wellness_notes || [];

  let headline =
    synthesis?.patient_summary?.split(".")[0] ||
    labAnalysis?.clinical_summary?.split(".")[0] ||
    (precautions.length
      ? `${precautions.length} result(s) need your doctor's attention.`
      : wellness.length
        ? "Your lab results look healthy based on standard ranges."
        : "Your report has been reviewed.");

  if (docType === "xray") {
    headline =
      synthesis?.patient_summary?.split(".")[0] ||
      labAnalysis?.clinical_summary?.split(".")[0] ||
      formatImagingHeadline(imaging);
  }

  const patientHeadline = synthesis?.patient_summary || headline;
  const physicianHeadline =
    synthesis?.physician_summary ||
    synthesis?.leading_diagnosis?.condition ||
    headline;

  const attention = precautions.map((p) => ({
    test: p.test,
    flag: p.flag,
    text: p.precaution,
  }));

  const healthy = wellness.slice(0, 6).map((w) => w.test);

  let doctorNote = "";
  const physicianSource = synthesis?.physician_summary || summaryText;
  if (physicianSource) {
    doctorNote = physicianSource
      .replace(/Grounded on \d+ vector-retrieved sources\.?/gi, "")
      .replace(/Physician review required\.?/gi, "")
      .replace(/Correlate with symptoms and local lab reference ranges\.?/gi, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  return {
    headline,
    patientHeadline,
    physicianHeadline,
    attention,
    healthy,
    doctorNote,
    showFullNote: Boolean(doctorNote && doctorNote.length > 40),
  };
}

const IMAGING_LABELS = {
  pneumothorax: "Pneumothorax",
  opacity: "Lung opacity / pneumonia",
  pleural_effusion: "Pleural effusion",
  nodule: "Lung nodule",
  cardiomegaly: "Enlarged heart",
};

export function formatImagingHeadline(imaging) {
  if (!imaging || imaging.skipped) {
    return "Chest X-ray uploaded — imaging analysis did not run.";
  }
  const findings = imaging.findings || {};
  const flagged = Object.entries(findings)
    .filter(([, data]) => data?.detected || (data?.probability ?? 0) >= 0.4)
    .map(([key, data]) => {
      const label = IMAGING_LABELS[key] || key.replace(/_/g, " ");
      const pct = Math.round((data.probability ?? 0) * 100);
      return `${label} (${pct}%)`;
    });
  if (flagged.length) {
    return `Chest X-ray: ${flagged.slice(0, 3).join(", ")} — physician review required`;
  }
  return "Chest X-ray: no major flags from automatic review — doctor should still confirm";
}

export function identityStatus(validation) {
  if (!validation) return null;
  if (validation.skipped) {
    return {
      tone: "unverified",
      badge: "Please verify",
      icon: "?",
      title: "We could not read the name on this document",
      message: validation.message,
    };
  }
  if (validation.matched) {
    return {
      tone: "verified",
      badge: "Name matches",
      icon: "✓",
      title: "This report matches the patient on file",
      message: validation.message || "Name on the form matches the report.",
    };
  }
  return {
    tone: "mismatch",
    badge: "Does not match",
    icon: "!",
    title: "Name on form and report differ",
    message: validation.message,
  };
}
