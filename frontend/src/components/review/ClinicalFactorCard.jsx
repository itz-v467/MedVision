/** Structured clinical factors reviewed for this case. */

export function ClinicalFactorCard({ factors, documents = [] }) {
  if (!factors) return null;

  const demo = factors.demographics || {};
  const symptoms = factors.symptoms || {};
  const fever = symptoms.fever || {};
  const reports = documents.length
    ? documents.map((d) => d.file_type || d.file_name).join(", ")
    : "Symptom chat";

  return (
    <section className="cv-factor-card" aria-label="Clinical factors reviewed">
      <h3 className="cv-factor-card-title">Factors your doctor would check</h3>
      <div className="cv-factor-grid">
        <div>
          <span className="cv-factor-label">Age</span>
          <strong>{demo.age_years != null ? `${demo.age_years} years` : "Not provided"}</strong>
          {demo.elderly && <span className="cv-factor-tag">Older adult</span>}
        </div>
        <div>
          <span className="cv-factor-label">Symptom duration</span>
          <strong>
            {symptoms.symptom_duration_days != null
              ? `${symptoms.symptom_duration_days} day(s)`
              : "Not specified"}
          </strong>
        </div>
        <div>
          <span className="cv-factor-label">Fever</span>
          <strong>
            {fever.present
              ? [
                  fever.duration_days != null ? `${fever.duration_days} day(s)` : null,
                  fever.max_temp_c != null ? `${fever.max_temp_c}°C` : null,
                ]
                  .filter(Boolean)
                  .join(" · ") || "Reported"
              : "Not reported"}
          </strong>
        </div>
        <div>
          <span className="cv-factor-label">Reports reviewed</span>
          <strong>{reports}</strong>
        </div>
      </div>
      {(factors.present_symptoms || symptoms.present_symptoms || []).length > 0 && (
        <p className="cv-factor-symptoms">
          Symptoms: {(symptoms.present_symptoms || []).join(", ")}
        </p>
      )}
    </section>
  );
}
