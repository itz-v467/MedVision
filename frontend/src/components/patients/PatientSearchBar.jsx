import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { clinicalApi } from "../../api/clinicalApi";
import { AppRoutes } from "../../enums/routes";

/**
 * Vector + keyword patient search. Selecting a row links an existing patient to intake.
 */
export function PatientSearchBar({
  onSelectPatient,
  placeholder = "Type patient name or MV number…",
  showHeading = true,
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const runSearch = useCallback(async () => {
    const q = query.trim();
    if (q.length < 2) {
      setError("Enter at least 2 characters to search.");
      setResults([]);
      return;
    }
    setLoading(true);
    setError("");
    setSearched(true);
    try {
      const data = await clinicalApi.searchPatients(q);
      setResults(data.patients || []);
    } catch (err) {
      setError(err.message || "Search failed.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [query]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      runSearch();
    }
  };

  return (
    <div className="cv-patient-search">
      {showHeading && (
        <div className="cv-patient-search-head">
          <h3>Find a patient</h3>
          <p>Search by name or patient number (e.g. MV-20260612-0001)</p>
        </div>
      )}

      <div className="cv-patient-search-row">
        <input
          type="search"
          className="cv-patient-search-input"
          placeholder={placeholder}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          aria-label="Search patients"
        />
        <button
          type="button"
          className="cv-btn cv-btn-primary"
          onClick={runSearch}
          disabled={loading}
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </div>

      {error && <p className="cv-patient-search-error">{error}</p>}

      {searched && !loading && results.length === 0 && !error && (
        <p className="cv-patient-search-empty">No matching patients. A new number will be assigned at registration.</p>
      )}

      {results.length > 0 && (
        <ul className="cv-patient-search-results" role="listbox">
          {results.map((patient) => (
            <li key={patient.patient_id}>
              <button
                type="button"
                className="cv-patient-search-hit"
                role="option"
                onClick={() => onSelectPatient?.(patient)}
              >
                <span className="cv-patient-search-hit-id">{patient.external_id}</span>
                <span className="cv-patient-search-hit-name">{patient.full_name}</span>
                <span className="cv-patient-search-hit-meta">
                  {[patient.gender, patient.age && `Age ${patient.age}`].filter(Boolean).join(" · ")}
                  {patient.match_type === "vector" && patient.similarity >= 0.75 && (
                    <span className="cv-patient-search-badge">AI match</span>
                  )}
                  {patient.match_type === "keyword" && (
                    <span className="cv-patient-search-badge is-keyword">Name match</span>
                  )}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** Compact search for patient reports page — navigates to latest encounter if possible */
export function PatientSearchNavigate({ encounters = [] }) {
  const navigate = useNavigate();

  const handleSelect = (patient) => {
    const match = encounters.find(
      (e) => e.patient_external_id === patient.external_id || e.patient_id === patient.patient_id
    );
    if (match) {
      navigate(`${AppRoutes.REVIEW}/${match.id}`);
    }
  };

  return (
    <div className="cv-panel cv-panel-pad" style={{ marginBottom: "var(--cv-space-3)" }}>
      <PatientSearchBar
        onSelectPatient={handleSelect}
        showHeading={false}
        placeholder="Search patient by name or MV number…"
      />
      <p className="cv-patient-search-hint">
        Select a result to open their most recent report, or browse the table below.
      </p>
    </div>
  );
}

export function PatientIdBadge({ patientId, isExisting, previewId }) {
  const display = patientId || previewId || "Assigning…";
  return (
    <div className={`cv-patient-id-badge${isExisting ? " is-existing" : ""}`}>
      <span className="cv-patient-id-label">
        {isExisting ? "Patient number" : "New patient number"}
      </span>
      <strong className="cv-patient-id-value">{display}</strong>
      {!isExisting && (
        <span className="cv-patient-id-note">Auto-generated MedVision ID (MV-YYYYMMDD-####)</span>
      )}
    </div>
  );
}
