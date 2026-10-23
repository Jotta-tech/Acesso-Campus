const labels = {
  pendente: "Pendente",
  em_andamento: "Em andamento",
  resolvida: "Resolvida",
};

export default function StatusBadge({ status }) {
  return <span className={`badge status-${status || "pendente"}`}>{labels[status] || status || "Pendente"}</span>;
}
