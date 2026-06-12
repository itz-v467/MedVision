import { useCallback, useEffect, useState } from "react";
import { statsApi } from "../api/statsApi";
import { Messages } from "../enums/messages";

export function useDashboardData() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dashboard, setDashboard] = useState(null);
  const [charts, setCharts] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [aiPerformance, setAiPerformance] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [dashboardData, chartData, alertData, performanceData] =
        await Promise.all([
          statsApi.dashboard(),
          statsApi.charts(),
          statsApi.alerts(),
          statsApi.aiPerformance(),
        ]);
      setDashboard(dashboardData);
      setCharts(chartData);
      setAlerts(alertData.alerts || []);
      setAiPerformance(performanceData);
    } catch (err) {
      setError(err.message || Messages.LOAD_ERROR);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { loading, error, dashboard, charts, alerts, aiPerformance, retry: load };
}
