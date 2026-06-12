import { useCallback, useEffect, useState } from "react";
import { HttpClient } from "../services/httpClient";
import { ErrorBanner } from "../components/ErrorBanner";

export function AuditPage() {
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const data = await HttpClient.request("/api/audit/logs");
      setLogs(data.logs || []);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div>
      <header className="page-header">
        <h2>Audit Logs</h2>
      </header>
      <ErrorBanner message={error} onRetry={load} />
      <table className="data-table">
        <thead>
          <tr>
            <th>Action</th>
            <th>Resource</th>
            <th>User</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id}>
              <td>{log.action}</td>
              <td>{log.resource_type}</td>
              <td>{log.user_id || "system"}</td>
              <td>{new Date(log.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
