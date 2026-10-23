export default function Alert({ type = "success", children, onClose }) {
  if (!children) return null;
  return <div className={`alert alert-${type}`} role="status"><span>{children}</span>{onClose && <button className="alert-close" aria-label="Fechar aviso" onClick={onClose}>×</button>}</div>;
}
