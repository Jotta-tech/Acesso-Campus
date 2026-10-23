export default function StatCard({ label, value, hint, icon }) {
  return <article className="stat-card"><div className="stat-card-top"><span>{label}</span><span className="stat-icon" aria-hidden="true">{icon}</span></div><strong className="stat-value">{value ?? "—"}</strong><p>{hint}</p></article>;
}
