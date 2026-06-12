import { useState } from "react";
import { BarVolumeChart } from "../charts/BarVolumeChart";
import { DoughnutAbnormalityChart } from "../charts/DoughnutAbnormalityChart";
import { LinePredictionsChart } from "../charts/LinePredictionsChart";
import { ScatterConfidenceChart } from "../charts/ScatterConfidenceChart";
import { ErrorBanner } from "../components/ErrorBanner";
import { StatCard } from "../components/StatCard";
import { useDashboardData } from "../hooks/useDashboardData";
import { AlertsTable } from "../tables/AlertsTable";
import { clinicalApi } from "../api/clinicalApi";

export function DashboardPage() {
  const { loading, error, dashboard, charts, alerts, aiPerformance, retry } =
    useDashboardData();
  const [acknowledgingId, setAcknowledgingId] = useState(null);

  const handleAcknowledge = async (alertId) => {
    setAcknowledgingId(alertId);
    try {
      await clinicalApi.acknowledgeAlert(alertId);
      await retry();
    } finally {
      setAcknowledgingId(null);
    }
  };

  return (
    <div>
      <header className="page-header">
        <h2>Enterprise Clinical Dashboard</h2>
        <p>Live AI operations, triage, and compliance monitoring</p>
      </header>

      <ErrorBanner message={error} onRetry={retry} />

      <section className="stats-grid">
        <StatCard label="Patients" value={dashboard?.patients} />
        <StatCard label="Encounters" value={dashboard?.encounters} />
        <StatCard label="Active Alerts" value={dashboard?.active_alerts} />
        <StatCard label="AI Analyses" value={dashboard?.ai_analyses} />
      </section>

      <section className="performance-strip">
        <StatCard
          label="Avg Confidence"
          value={aiPerformance?.avg_confidence?.toFixed(2)}
        />
        <StatCard
          label="Avg Latency (ms)"
          value={aiPerformance?.avg_latency_ms?.toFixed(0)}
        />
      </section>

      <section className="charts-grid">
        <article>
          <h3>Daily Predictions</h3>
          <LinePredictionsChart
            data={charts?.daily_predictions}
            loading={loading}
          />
        </article>
        <article>
          <h3>Weekly Analysis Volume</h3>
          <BarVolumeChart
            data={charts?.weekly_analysis_volume}
            loading={loading}
          />
        </article>
        <article>
          <h3>Abnormality Distribution</h3>
          <DoughnutAbnormalityChart
            data={charts?.abnormality_distribution}
            loading={loading}
          />
        </article>
        <article>
          <h3>Model Confidence Scatter</h3>
          <ScatterConfidenceChart
            data={charts?.model_confidence_scatter}
            loading={loading}
          />
        </article>
      </section>

      <section className="panel">
        <h3>Critical Alerts</h3>
        <AlertsTable
          alerts={alerts}
          onAcknowledge={handleAcknowledge}
          acknowledgingId={acknowledgingId}
        />
      </section>
    </div>
  );
}
