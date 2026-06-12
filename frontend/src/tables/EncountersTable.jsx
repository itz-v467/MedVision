import { Link } from "react-router-dom";
import { AppRoutes } from "../enums/routes";

export function EncountersTable({ encounters }) {
  if (!encounters?.length) {
    return <p className="empty-state">No encounters in queue.</p>;
  }
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Encounter ID</th>
          <th>Status</th>
          <th>Chief Complaint</th>
          <th>Created</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {encounters.map((encounter) => (
          <tr key={encounter.id}>
            <td>{encounter.id}</td>
            <td>{encounter.status}</td>
            <td>{encounter.chief_complaint || "—"}</td>
            <td>{new Date(encounter.created_at).toLocaleString()}</td>
            <td>
              <Link to={`${AppRoutes.REVIEW}/${encounter.id}`}>Review</Link>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
