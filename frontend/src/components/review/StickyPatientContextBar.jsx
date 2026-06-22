import { Link } from "react-router-dom";
import { AppRoutes } from "../../enums/routes";
import { StatusBadge } from "../ui/StatusBadge";

export function StickyPatientContextBar({
  patient,
  initials,
  caseBadge,
  risk,
  updated,
}) {
  return (
    <header className="cv-sticky-patient-bar">
      <div className="cv-sticky-patient-main">
        <div className="cv-sticky-patient-avatar" aria-hidden="true">{initials}</div>
        <div>
          <h1 className="cv-sticky-patient-name">{patient?.full_name || "Unknown patient"}</h1>
          <div className="cv-sticky-patient-meta">
            <span className="cv-mono">ID {patient?.external_id || "—"}</span>
            {patient?.date_of_birth && <span>Age {patient.date_of_birth}</span>}
            {patient?.gender && <span>{patient.gender}</span>}
            {caseBadge && <span className="cv-sticky-patient-type">{caseBadge}</span>}
            <span>Updated {updated}</span>
          </div>
        </div>
      </div>
      <div className="cv-sticky-patient-actions">
        <StatusBadge tone={risk || "low"} label={`${risk || "low"} priority`} />
        <Link to={AppRoutes.ENCOUNTERS} className="cv-btn cv-btn-ghost cv-btn-sm">
          ← Reports
        </Link>
      </div>
    </header>
  );
}
