export function StatCard({ label, value }) {
  return (
    <div className="stat-card">
      <p>{label}</p>
      <h3>{value ?? 0}</h3>
    </div>
  );
}
