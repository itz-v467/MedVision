import { HttpClient } from "./httpClient";

export class AuthService {
  static login(email, password) {
    return HttpClient.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  static register(payload) {
    return HttpClient.request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  static logout() {
    return HttpClient.request("/auth/logout", { method: "POST" });
  }

  static refresh(refreshToken) {
    return HttpClient.request("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }
}
