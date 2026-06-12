import { HttpClient } from "./httpClient";

export class StatsService {
  static getDashboard() {
    return HttpClient.request("/api/stats/dashboard");
  }

  static getCharts() {
    return HttpClient.request("/api/stats/charts");
  }

  static getAlerts() {
    return HttpClient.request("/api/stats/alerts");
  }

  static getPatients() {
    return HttpClient.request("/api/stats/patients");
  }

  static getAiPerformance() {
    return HttpClient.request("/api/stats/ai-performance");
  }
}
