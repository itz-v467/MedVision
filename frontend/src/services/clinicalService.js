import { HttpClient } from "./httpClient";

export class ClinicalService {
  static upload(formData) {
    return HttpClient.request("/api/clinical/upload", {
      method: "POST",
      body: formData,
    });
  }

  static uploadCase(formData) {
    return HttpClient.request("/api/clinical/cases", {
      method: "POST",
      body: formData,
    });
  }

  static uploadSingleLegacy(file, fileType, baseFormData) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("file_type", fileType);
    for (const [key, value] of baseFormData.entries()) {
      if (key !== "files" && key !== "file_types") {
        formData.append(key, value);
      }
    }
    return ClinicalService.upload(formData);
  }

  static listEncounters() {
    return HttpClient.request("/api/clinical/encounters");
  }

  static getEncounter(encounterId) {
    return HttpClient.request(`/api/clinical/encounters/${encounterId}`);
  }

  static reanalyzeImaging(encounterId) {
    return HttpClient.request(`/api/clinical/encounters/${encounterId}/imaging/reanalyze`, {
      method: "POST",
    });
  }

  static regenerateSynthesis(encounterId) {
    return HttpClient.request(`/api/clinical/encounters/${encounterId}/synthesis/regenerate`, {
      method: "POST",
    });
  }

  static getCarePlan(encounterId) {
    return HttpClient.request(`/api/clinical/encounters/${encounterId}/care-plan`);
  }

  static approveCarePlan(encounterId) {
    return HttpClient.request(`/api/clinical/encounters/${encounterId}/care-plan/approve`, {
      method: "POST",
    });
  }

  static requestConsult(encounterId, payload = {}) {
    return HttpClient.request(`/api/clinical/encounters/${encounterId}/consult/request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  static getConsultConfig() {
    return HttpClient.request("/api/clinical/consult/config");
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

  static deleteEncounter(encounterId) {
    return HttpClient.request(`/api/clinical/encounters/${encounterId}`, {
      method: "DELETE",
    });
  }

  static searchPatients(query, limit = 10) {
    const params = new URLSearchParams({ q: query, limit: String(limit) });
    return HttpClient.request(`/api/clinical/patients/search?${params}`);
  }

  static previewPatientId() {
    return HttpClient.request("/api/clinical/patients/preview-id");
  }

  static triageConverse(payload) {
    return HttpClient.request("/api/clinical/triage/converse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  static triageRoadmap() {
    return HttpClient.request("/api/clinical/triage/roadmap");
  }

  static triageGetSession(encounterId) {
    return HttpClient.request(`/api/clinical/encounters/${encounterId}/triage/session`);
  }

  static triageAddMessage(encounterId, message) {
    return HttpClient.request(`/api/clinical/encounters/${encounterId}/triage/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
  }

  static triageFinalize(encounterId, physicianNote) {
    return HttpClient.request(`/api/clinical/encounters/${encounterId}/triage/finalize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ physician_note: physicianNote }),
    });
  }
}
