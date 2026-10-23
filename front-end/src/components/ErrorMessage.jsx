export default function ErrorMessage({ message, onRetry }) {
  if (!message) return null;
  return <div className="error-message" role="alert"><div><strong>Não foi possível carregar os dados.</strong><p>{message}</p></div>{onRetry && <button className="button button-secondary" onClick={onRetry}>Tentar novamente</button>}</div>;
}
