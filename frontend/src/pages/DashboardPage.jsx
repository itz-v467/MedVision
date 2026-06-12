import { useCallback, useEffect, useState } from "react";
import { useDashboardData } from "../hooks/useDashboardData";
import { clinicalApi } from "../api/clinicalApi";
import { ErrorBanner } from "../components/ErrorBanner";
import { ClinicalWorkspace } from "../components/workspace/ClinicalWorkspace";
import { usePermissions } from "../hooks/usePermissions";
import { BarVolumeChart } from "../charts/BarVolumeChart";
import { LinePredictionsChart } from "../charts/LinePredictionsChart";

export function DashboardPage() {
  const { loading, error, authExpired, dashboard, charts, alerts, retry } = useDashboardData();
  const { canUpload } = usePermissions();
  const [encounters, setEncounters] = useState([]);
  const [encountersLoading, setEncountersLoading] = useState(true);
  const [encountersError, setEncountersError] = useState("");
  const [encountersAuthExpired, setEncountersAuthExpired] = useState(false);
  const [acknowledgingId, setAcknowledgingId] = useState(null);

  const loadEncounters = useCallback(async () => {
    setEncountersLoading(true);
    setEncountersError("");
    setEncountersAuthExpired(false);
    try {
      const data = await clinicalApi.encounters();
      setEncounters(data.encounters || []);
    } catch (err) {
      setEncounters([]);
      if (err?.authExpired || err?.status === 401) {
        setEncountersAuthExpired(true);
        setEncountersError(err.message);
      }
    } finally {
      setEncountersLoading(false);
    }
  }, []);

  useEffect(() => {
    loadEncounters();
  }, [loadEncounters]);

  const handleAcknowledge = async (alertId) => {
    setAcknowledgingId(alertId);
    try {
      await clinicalApi.acknowledgeAlert(alertId);
      await retry();
    } finally {
      setAcknowledgingId(null);
    }
  };

  const handleRetryAll = () => {
    retry();
    loadEncounters();
  };

  const pageLoading = loading || encountersLoading;
  const showError = error || encountersError;
  const isAuthError = authExpired || encountersAuthExpired;

  return (
    <div>
      <ErrorBanner
        message={showError}
        onRetry={isAuthError ? undefined : handleRetryAll}
        authExpired={isAuthError}
      />

      <ClinicalWorkspace
        loading={pageLoading}
        encounters={encounters}
        alerts={alerts}
        pendingReviews={dashboard?.pending_reviews ?? 0}
        onAcknowledge={handleAcknowledge}
        acknowledgingId={acknowledgingId}
        canUpload={canUpload}
      />

      <details className="cv-analytics-fold cv-panel cv-panel-pad" style={{ marginTop: "var(--cv-space-4)" }}>
        <summary>Operations analytics</summary>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "var(--cv-space-3)", marginTop: "var(--cv-space-3)" }}>
          <div>
            <h4 style={{ margin: "0 0 8px", fontSize: "var(--cv-text-sm)", color: "var(--cv-slate-500)" }}>Daily predictions</h4>
            {pageLoading ? (
              <div className="cv-skeleton" style={{ height: 180 }} />
            ) : (
              <LinePredictionsChart data={charts?.daily_predictions} loading={pageLoading} />
            )}
          </div>
          <div>
            <h4 style={{ margin: "0 0 8px", fontSize: "var(--cv-text-sm)", color: "var(--cv-slate-500)" }}>Weekly volume</h4>
            {pageLoading ? (
              <div className="cv-skeleton" style={{ height: 180 }} />
            ) : (
              <BarVolumeChart data={charts?.weekly_analysis_volume} loading={pageLoading} />
            )}
          </div>
        </div>
      </details>
    </div>
  );
}
