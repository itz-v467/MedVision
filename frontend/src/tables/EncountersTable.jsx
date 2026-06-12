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
    <div>
      {error && <div className="error-banner">{error}</div>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Patient</th>
            <th>Patient ID</th>
            <th>Status</th>
            <th>Uploaded</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {encounters.map((encounter) => (
            <tr key={encounter.id}>
              <td>{encounter.patient_name || "Unknown"}</td>
              <td>{encounter.patient_external_id || "—"}</td>
              <td>{plainStatus(encounter.status)}</td>
              <td>{new Date(encounter.created_at).toLocaleString()}</td>
              <td className="table-actions">
                <Link to={`${AppRoutes.REVIEW}/${encounter.id}`}>Open report</Link>
                <button
                  type="button"
                  className="btn-delete"
                  onClick={() => handleDelete(encounter)}
                  disabled={deletingId === encounter.id}
                >
                  {deletingId === encounter.id ? "Removing…" : UI_LABELS.deleteRecord}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
