import { HttpClient } from "./httpClient";

export class ClinicalService {
  static upload(formData) {
    return HttpClient.request("/api/clinical/upload", {
      method: "POST",
      body: formData,
    });
  }

  static listEncounters() {
    return HttpClient.request("/api/clinical/encounters");
  }

  static getEncounter(encounterId) {
    return HttpClient.request(`/api/clinical/encounters/${encounterId}`);
  }

  static finalizeSummary(summaryId) {
    return HttpClient.request(`/api/clinical/summaries/${summaryId}/finalize`, {
      method: "POST",
    });
  }

  static acknowledgeAlert(alertId) {
    return HttpClient.request(`/api/clinical/alerts/${alertId}/acknowledge`, {
      method: "POST",
    });
  }
}
