import { StatsService } from "../services/statsService";

export const statsApi = {
  dashboard: StatsService.getDashboard,
  charts: StatsService.getCharts,
  alerts: StatsService.getAlerts,
  patients: StatsService.getPatients,
  aiPerformance: StatsService.getAiPerformance,
};
