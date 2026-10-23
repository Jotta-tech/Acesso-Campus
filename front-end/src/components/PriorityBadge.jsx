const labels = { baixa: "Baixa", media: "Média", alta: "Alta" };

export default function PriorityBadge({ priority }) {
  return <span className={`badge priority-${priority || "media"}`}>{labels[priority] || priority || "Média"}</span>;
}
