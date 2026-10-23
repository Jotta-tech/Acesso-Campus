export default function EmptyState({ title = "Nenhuma ocorrência encontrada", message = "Tente alterar os filtros ou registre uma nova ocorrência." }) {
  return <div className="empty-state"><span className="empty-icon">○</span><h3>{title}</h3><p>{message}</p></div>;
}
