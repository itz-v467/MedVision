export function StatCard({ label, value, icon, accent }) {
  return (
    <div className="stat-card" style={accent ? { borderTop: `3px solid ${accent}` } : {}}>
      <p style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span>{label}</span>
        {icon && <span style={{ fontSize: "1.2rem" }}>{icon}</span>}
      </p>
      <h3 style={accent ? { color: accent } : {}}>{value ?? 0}</h3>
    </div>
  );
}
