import { ClinicalCard } from "../ui/ClinicalCard";
import { LinePredictionsChart } from "../../charts/LinePredictionsChart";
import { BarVolumeChart } from "../../charts/BarVolumeChart";

function AnalyticsKpi({ value, label, hint }) {
  return (
    <div className="cv-analytics-kpi">
      <span className="cv-analytics-kpi-value">{value}</span>
      <span className="cv-analytics-kpi-label">{label}</span>
      {hint && <span className="cv-analytics-kpi-hint">{hint}</span>}
    </div>
  );
}

export function OperationsAnalytics({ charts, loading }) {
  const daily = charts?.daily_predictions || [];
  const weekly = charts?.weekly_analysis_volume || [];

  const weekTotal = weekly.reduce((sum, row) => sum + (row.volume || 0), 0);
  const latestDaily = daily.length ? daily[daily.length - 1].count : 0;
  const dailyAverage = daily.length
    ? Math.round(daily.reduce((sum, row) => sum + (row.count || 0), 0) / daily.length)
    : 0;

  return (
    <ClinicalCard
      title="Activity overview"
      action={
        <span className="cv-stat-inline">
          {loading ? "Loading…" : "Last 7–14 days"}
        </span>
      }
      className="cv-analytics-panel"
    >
      <p className="cv-analytics-lede">
        Quick snapshot of how many cases and AI analyses are moving through the clinic.
      </p>

      <div className="cv-analytics-kpis" role="list">
        <AnalyticsKpi
          value={loading ? "—" : weekTotal}
          label="Cases this week"
          hint="New uploads & intakes"
        />
        <AnalyticsKpi
          value={loading ? "—" : latestDaily}
          label="AI analyses today"
          hint="Completed predictions"
        />
        <AnalyticsKpi
          value={loading ? "—" : dailyAverage}
          label="Daily average"
          hint="Typical AI workload"
        />
      </div>

      <div className="cv-analytics-grid">
        <article className="cv-chart-panel">
          <header className="cv-chart-panel-head">
            <h3 className="cv-chart-panel-title">AI analyses per day</h3>
            <p className="cv-chart-panel-caption">
              Each point is one day — higher means more reports processed by AI.
            </p>
          </header>
          {loading ? (
            <div className="cv-skeleton cv-chart-canvas" />
          ) : (
            <LinePredictionsChart data={daily} loading={loading} />
          )}
        </article>

        <article className="cv-chart-panel">
          <header className="cv-chart-panel-head">
            <h3 className="cv-chart-panel-title">New cases by day</h3>
            <p className="cv-chart-panel-caption">
              Bars show how many patient cases were opened each day this week.
            </p>
          </header>
          {loading ? (
            <div className="cv-skeleton cv-chart-canvas" />
          ) : (
            <BarVolumeChart data={weekly} loading={loading} />
          )}
        </article>
      </div>
    </ClinicalCard>
  );
}
