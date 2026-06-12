import { AuthService } from "../services/authService";

export const authApi = {
  login: AuthService.login,
  register: AuthService.register,
  logout: AuthService.logout,
  refresh: AuthService.refresh,
};
