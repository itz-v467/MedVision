import { useState } from "react";
import { Link } from "react-router-dom";
import { clinicalApi } from "../api/clinicalApi";
import { AppRoutes } from "../enums/routes";
import { plainStatus, UI_LABELS } from "../utils/plainLanguage";

export function EncountersTable({ encounters, onDeleted }) {
  const [deletingId, setDeletingId] = useState(null);
  const [error, setError] = useState("");

  if (!encounters?.length) {
    return <p className="empty-state">No patient reports in the queue yet.</p>;
  }

  const handleDelete = async (encounter) => {
    if (!window.confirm(UI_LABELS.deleteConfirm)) return;
    setDeletingId(encounter.id);
    setError("");
    try {
      await clinicalApi.deleteEncounter(encounter.id);
      onDeleted?.();
    } catch (err) {
      setError(err.message || "Could not remove this record.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="cv-encounters-wrap">
      {error && <div className="error-banner">{error}</div>}
      <div className="cv-encounters-table-scroll">
        <table className="cv-encounters-table">
          <thead>
            <tr>
              <th>Patient</th>
              <th>Patient ID</th>
              <th>Status</th>
              <th>Uploaded</th>
              <th className="cv-encounters-th-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            {encounters.map((encounter) => (
              <tr key={encounter.id}>
                <td className="cv-encounters-patient">{encounter.patient_name || "Unknown"}</td>
                <td className="cv-encounters-id">{encounter.patient_external_id || "—"}</td>
                <td>
                  <span className="cv-encounters-status">{plainStatus(encounter.status)}</span>
                </td>
                <td className="cv-encounters-date">
                  {new Date(encounter.created_at).toLocaleString()}
                </td>
                <td>
                  <div className="cv-table-actions">
                    <Link
                      to={`${AppRoutes.REVIEW}/${encounter.id}`}
                      className="cv-btn cv-btn-sm cv-btn-table-primary"
                    >
                      Open
                    </Link>
                    <button
                      type="button"
                      className="cv-btn cv-btn-sm cv-btn-table-danger"
                      onClick={() => handleDelete(encounter)}
                      disabled={deletingId === encounter.id}
                    >
                      {deletingId === encounter.id ? "Removing…" : "Remove"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
