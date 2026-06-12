import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  notifySessionExpired,
  saveSession,
} from "./authSession";

const API_BASE = "";

let refreshInFlight = null;

async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return false;
  }

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!response.ok) {
          return false;
        }

        const payload = await response.json();
        const data = payload.data || payload;
        if (!data?.access_token) {
          return false;
        }

        saveSession({
          access_token: data.access_token,
          refresh_token: data.refresh_token || refreshToken,
          user: data.user,
        });
        return true;
      } catch {
        return false;
      } finally {
        refreshInFlight = null;
      }
    })();
  }

  return refreshInFlight;
}

function buildAuthError(message) {
  const error = new Error(message);
  error.status = 401;
  error.authExpired = true;
  return error;
}

export class HttpClient {
  static async request(path, options = {}, allowRetry = true) {
    const token = getAccessToken();
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

    let payload = {};
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      try {
        payload = await response.json();
      } catch {
        payload = {};
      }
    }

    if (response.status === 401 && allowRetry && !path.startsWith("/auth/")) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        return this.request(path, options, false);
      }
      notifySessionExpired();
      throw buildAuthError("Your session has expired. Please sign in again.");
    }

    if (!response.ok) {
      let message = payload.message || `Request failed (${response.status})`;
      if (response.status === 405) {
        message = "This action is not available — please restart the backend (docker compose up --build).";
      } else if (response.status === 403) {
        message = payload.message || "You do not have permission for this action.";
      } else if (response.status === 404) {
        message = payload.message || "Record not found.";
      }
      const error = new Error(message);
      error.code = payload.error_code;
      error.status = response.status;
      if (response.status === 401) {
        error.authExpired = true;
      }
      throw error;
    }

    return payload.data;
  }

  static async requestBlob(path, options = {}, allowRetry = true) {
    const token = getAccessToken();
    const headers = { ...(options.headers || {}) };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (response.status === 401 && allowRetry && !path.startsWith("/auth/")) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        return this.requestBlob(path, options, false);
      }
      notifySessionExpired();
      throw buildAuthError("Your session has expired. Please sign in again.");
    }

    if (!response.ok) {
      throw new Error("Failed to load resource.");
    }
    return response.blob();
  }
}
