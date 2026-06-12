import { useCallback, useEffect, useState } from "react";
import { clinicalApi } from "../api/clinicalApi";
import { ErrorBanner } from "../components/ErrorBanner";
import { Messages } from "../enums/messages";
import { EncountersTable } from "../tables/EncountersTable";

export function EncountersPage() {
  const [encounters, setEncounters] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

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

  return (
    <div>
      <header className="page-header">
        <h2>Encounter Triage Queue</h2>
      </header>
      <ErrorBanner message={error} onRetry={load} />
      {loading ? <div className="chart-skeleton" /> : <EncountersTable encounters={encounters} />}
    </div>
  );
}
