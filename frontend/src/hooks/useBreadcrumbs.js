import { useMemo } from "react";
import { useLocation, useParams } from "react-router-dom";
import { AppRoutes } from "../enums/routes";

export function useBreadcrumbs() {
  const { pathname } = useLocation();
  const { encounterId } = useParams();

  return useMemo(() => {
    const crumbs = [{ label: "Workspace", to: AppRoutes.DASHBOARD }];

    if (pathname.startsWith(AppRoutes.UPLOAD)) {
      crumbs.push({ label: "New case" });
    } else if (pathname.startsWith(AppRoutes.ENCOUNTERS)) {
      crumbs.push({ label: "Reports" });
    } else if (pathname.startsWith("/review")) {
      crumbs.push({ label: "Reports", to: AppRoutes.ENCOUNTERS });
      crumbs.push({ label: encounterId ? `Case ${encounterId.slice(0, 8)}…` : "Review" });
    }

    return crumbs;
  }, [pathname, encounterId]);
}
