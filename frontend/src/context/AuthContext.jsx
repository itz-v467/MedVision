import { createContext, useCallback, useEffect, useMemo, useState } from "react";
import { authApi } from "../api/authApi";
import {
  clearSession,
  getStoredUser,
  hasActiveSession,
  onSessionExpired,
  saveSession,
} from "../services/authSession";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    if (!hasActiveSession()) {
      clearSession();
      return null;
    }
    return getStoredUser();
  });

  useEffect(() => {
    onSessionExpired(() => setUser(null));
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await authApi.login(email, password);
    saveSession({
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      user: data.user,
    });
    setUser(data.user);
    return data;
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      /* still clear local session */
    } finally {
      clearSession();
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({
      user,
      login,
      logout,
      isAuthenticated: Boolean(user && hasActiveSession()),
    }),
    [user, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
