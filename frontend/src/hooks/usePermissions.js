import { useMemo } from "react";
import { Roles } from "../enums/roles";
import { useAuth } from "./useAuth";

export function usePermissions() {
  const { user } = useAuth();

  return useMemo(() => {
    const role = user?.role;
    return {
      isAdmin: role === Roles.ADMIN,
      canUpload: [
        Roles.ADMIN,
        Roles.RADIOLOGIST,
        Roles.PHYSICIAN,
        Roles.TECHNICIAN,
      ].includes(role),
      canViewAudit: role === Roles.ADMIN,
      canReview: [Roles.ADMIN, Roles.PHYSICIAN, Roles.RADIOLOGIST].includes(role),
    };
  }, [user]);
}
