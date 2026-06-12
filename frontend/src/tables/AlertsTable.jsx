import { AlertTypes } from "../enums/alertTypes";

export function AlertsTable({ alerts, onAcknowledge, acknowledgingId }) {
  if (!alerts?.length) {
    return <p className="empty-state">No active alerts.</p>;
  }
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Title</th>
          <th>Priority</th>
          <th>Message</th>
          <th>Created</th>
          {onAcknowledge ? <th>Action</th> : null}
        </tr>
      </thead>
      <tbody>
        {alerts.map((alert) => (
          <tr
            key={alert.id}
            className={
              alert.priority === AlertTypes.CRITICAL ? "row-critical" : ""
            }
          >
            <td>{alert.title}</td>
            <td>{alert.priority}</td>
            <td>{alert.message}</td>
            <td>{new Date(alert.created_at).toLocaleString()}</td>
            {onAcknowledge ? (
              <td>
                {alert.is_acknowledged ? (
                  "Acknowledged"
                ) : (
                  <button
                    type="button"
                    onClick={() => onAcknowledge(alert.id)}
                    disabled={acknowledgingId === alert.id}
                  >
                    {acknowledgingId === alert.id ? "Saving..." : "Acknowledge"}
                  </button>
                )}
              </td>
            ) : null}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
