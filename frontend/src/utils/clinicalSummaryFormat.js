/** Turn dense AI summary text into scannable patient-friendly bullets. */

export function formatClinicalSummary(summaryText = "", labAnalysis = null) {
  const precautions = labAnalysis?.precautions || [];
  const wellness = labAnalysis?.wellness_notes || [];

  const headline =
    labAnalysis?.clinical_summary?.split(".")[0] ||
    (precautions.length
      ? `${precautions.length} test result(s) need your doctor's attention.`
      : wellness.length
        ? "Your lab results look healthy based on standard ranges."
        : "Your report has been reviewed.");

  const attention = precautions.map((p) => ({
    test: p.test,
    flag: p.flag,
    text: p.precaution,
  }));

  const healthy = wellness.slice(0, 6).map((w) => w.test);

  let doctorNote = "";
  if (summaryText) {
    doctorNote = summaryText
      .replace(/Grounded on \d+ vector-retrieved sources\.?/gi, "")
      .replace(/Physician review required\.?/gi, "")
      .replace(/Correlate with symptoms and local lab reference ranges\.?/gi, "")
      .replace(/\s+/g, " ")
      .trim();
    if (doctorNote.length > 280) {
      doctorNote = `${doctorNote.slice(0, 277)}…`;
    }
  }

  return {
    headline,
    attention,
    healthy,
    doctorNote,
    showFullNote: Boolean(doctorNote && doctorNote.length > 50),
  };
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
