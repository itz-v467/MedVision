import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { clinicalApi } from "../api/clinicalApi";
import { ErrorBanner } from "../components/ErrorBanner";
import { PageTemplate } from "../components/layout/PageTemplate";
import { ClinicalCard } from "../components/ui/ClinicalCard";
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
  const filterStatus = searchParams.get("status") || "";
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
    let rows = encounters;
    if (filterStatus === "pending") {
      rows = rows.filter(
        (e) => e.status === "REVIEW_REQUIRED" || e.status === "PROCESSING"
      );
    }
    if (!filterQ.trim()) return rows;
    const q = filterQ.toLowerCase();
    return rows.filter(
      (e) =>
        e.patient_name?.toLowerCase().includes(q) ||
        e.patient_external_id?.toLowerCase().includes(q)
    );
  }, [encounters, filterQ, filterStatus]);

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
    <PageTemplate
      title="Reports"
      subtitle="Search by patient name or ID, or browse all uploaded documents."
    >
      <ErrorBanner message={error} onRetry={load} />

      <ClinicalCard>
        <PatientSearchBar onSelectPatient={handleSelectPatient} />
      </ClinicalCard>

      {filterStatus === "pending" && (
        <div className="mv-filter-banner">
          Showing <strong>pending review</strong> only
          <button type="button" className="cv-btn cv-btn-ghost cv-btn-sm" onClick={() => setSearchParams({})}>
            Clear filter
          </button>
        </div>
      )}

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
        <ClinicalCard>
          <EncountersTable encounters={filtered} onDeleted={load} />
        </ClinicalCard>
      )}
    </PageTemplate>
  );
}
