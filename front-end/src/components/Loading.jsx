export default function Loading({ message = "Carregando informações..." }) {
  return <div className="loading-state"><span className="spinner" aria-hidden="true" />{message}</div>;
}
