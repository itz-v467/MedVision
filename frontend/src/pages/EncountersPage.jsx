import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { clinicalApi } from "../api/clinicalApi";
import { ErrorBanner } from "../components/ErrorBanner";
import { PatientSearchBar } from "../components/patients/PatientSearchBar";
import { Messages } from "../enums/messages";
import { AppRoutes } from "../enums/routes";
import { EncountersTable } from "../tables/EncountersTable";

export function EncountersPage() {
  const [encounters, setEncounters] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const filterQ = searchParams.get("q") || "";
  const navigate = useNavigate();

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await clinicalApi.encounters();
      setEncounters(data.encounters || []);
    } catch (err) {
      setError(err.message || Messages.LOAD_ERROR);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = useMemo(() => {
    if (!filterQ.trim()) return encounters;
    const q = filterQ.toLowerCase();
    return encounters.filter(
      (e) =>
        e.patient_name?.toLowerCase().includes(q) ||
        e.patient_external_id?.toLowerCase().includes(q)
    );
  }, [encounters, filterQ]);

  const handleSelectPatient = (patient) => {
    const match = encounters.find(
      (e) =>
        e.patient_external_id === patient.external_id ||
        e.patient_id === patient.patient_id
    );
    if (match) {
      navigate(`${AppRoutes.REVIEW}/${match.id}`);
    } else {
      setSearchParams({ q: patient.external_id });
    }
  };

  return (
    <div>
      <header className="mv-welcome-header" style={{ marginBottom: 24 }}>
        <h1>Reports</h1>
        <p>Search by patient name or ID, or browse all uploaded documents.</p>
      </header>

      <ErrorBanner message={error} onRetry={load} />

      <div className="cv-panel cv-panel-pad" style={{ marginBottom: 24 }}>
        <PatientSearchBar onSelectPatient={handleSelectPatient} />
      </div>

      {filterQ && (
        <div className="mv-filter-banner">
          Showing results for <strong>{filterQ}</strong>
          <button type="button" className="cv-btn cv-btn-ghost cv-btn-sm" onClick={() => setSearchParams({})}>
            Clear filter
          </button>
        </div>
      )}

      {loading ? (
        <div className="cv-skeleton" style={{ height: 320 }} />
      ) : (
        <div className="cv-panel cv-panel-pad">
          <EncountersTable encounters={filtered} onDeleted={load} />
        </div>
      )}
    </div>
  );
}
