const API_BASE = "";

export class HttpClient {
  static async request(path, options = {}) {
    const token = localStorage.getItem("access_token");
    const headers = {
      ...(options.headers || {}),
    };
    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });
    const payload = await response.json();
    if (!response.ok) {
      const error = new Error(payload.message || "Request failed");
      error.code = payload.error_code;
      throw error;
    }
    return payload.data;
  }

  static async requestBlob(path, options = {}) {
    const token = localStorage.getItem("access_token");
    const headers = { ...(options.headers || {}) };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });
    if (!response.ok) {
      throw new Error("Failed to load resource.");
    }
    return response.blob();
  }
}
