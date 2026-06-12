import { useCallback, useEffect, useState } from "react";
import { statsApi } from "../api/statsApi";
import { Messages } from "../enums/messages";

export function useDashboardData() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [authExpired, setAuthExpired] = useState(false);
  const [dashboard, setDashboard] = useState(null);
  const [charts, setCharts] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [aiPerformance, setAiPerformance] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    setAuthExpired(false);

    try {
      const results = await Promise.allSettled([
        statsApi.dashboard(),
        statsApi.charts(),
        statsApi.alerts(),
        statsApi.aiPerformance(),
      ]);

      const names = ["dashboard", "charts", "alerts", "aiPerformance"];
      let authFailure = null;
      let otherFailure = null;

      results.forEach((result, index) => {
        if (result.status === "fulfilled") {
          const data = result.value;
          if (index === 0) setDashboard(data);
          if (index === 1) setCharts(data);
          if (index === 2) setAlerts(data?.alerts || []);
          if (index === 3) setAiPerformance(data);
          return;
        }

        const err = result.reason;
        if (err?.authExpired || err?.status === 401) {
          authFailure = err;
        } else if (!otherFailure) {
          otherFailure = err;
        }
        console.warn(`Dashboard stats: ${names[index]} failed`, err?.message);
      });

      if (authFailure) {
        setAuthExpired(true);
        setError(authFailure.message || Messages.LOAD_ERROR);
      } else if (otherFailure) {
        setError(
          "Some analytics could not be loaded. Your clinical queue is still available below."
        );
      }
    } catch (err) {
      if (err?.authExpired || err?.status === 401) {
        setAuthExpired(true);
      }
      setError(err.message || Messages.LOAD_ERROR);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return {
    loading,
    error,
    authExpired,
    dashboard,
    charts,
    alerts,
    aiPerformance,
    retry: load,
  };
}
