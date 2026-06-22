import { useCallback, useEffect, useState } from "react";
import { useDashboardData } from "../hooks/useDashboardData";
import { clinicalApi } from "../api/clinicalApi";
import { ErrorBanner } from "../components/ErrorBanner";
import { PageTemplate } from "../components/layout/PageTemplate";
import { ClinicalWorkspace } from "../components/workspace/ClinicalWorkspace";
import { usePermissions } from "../hooks/usePermissions";

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
    <PageTemplate title="Workspace" subtitle="Pending reviews, alerts, and recent patient reports.">
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
        charts={charts}
        chartsLoading={loading}
        onAcknowledge={handleAcknowledge}
        acknowledgingId={acknowledgingId}
        canUpload={canUpload}
      />
    </PageTemplate>
  );
}
