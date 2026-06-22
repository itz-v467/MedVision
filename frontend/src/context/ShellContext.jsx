import { createContext, useCallback, useContext, useMemo, useState } from "react";

const STORAGE_KEY = "medvision-sidebar-expanded";

const ShellContext = createContext(null);

export function ShellProvider({ children }) {
  const [sidebarExpanded, setSidebarExpanded] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === "true";
    } catch {
      return false;
    }
  });

  const toggleSidebar = useCallback(() => {
    setSidebarExpanded((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(STORAGE_KEY, String(next));
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  const expandSidebar = useCallback(() => {
    setSidebarExpanded(true);
    try {
      localStorage.setItem(STORAGE_KEY, "true");
    } catch {
      /* ignore */
    }
  }, []);

  const collapseSidebar = useCallback(() => {
    setSidebarExpanded(false);
    try {
      localStorage.setItem(STORAGE_KEY, "false");
    } catch {
      /* ignore */
    }
  }, []);

  const value = useMemo(
    () => ({ sidebarExpanded, toggleSidebar, expandSidebar, collapseSidebar }),
    [sidebarExpanded, toggleSidebar, expandSidebar, collapseSidebar]
  );

  return <ShellContext.Provider value={value}>{children}</ShellContext.Provider>;
}

export function useShell() {
  const ctx = useContext(ShellContext);
  if (!ctx) {
    throw new Error("useShell must be used within ShellProvider");
  }
  return ctx;
}
