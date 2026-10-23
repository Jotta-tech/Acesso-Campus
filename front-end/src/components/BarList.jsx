export default function BarList({ title, items = [], labels = {} }) {
  const max = Math.max(1, ...items.map((item) => Number(item.value) || 0));
  return <section className="panel bar-panel"><h3>{title}</h3><div className="bar-list">{items.map((item) => <div className="bar-row" key={item.key}><div className="bar-label"><span>{labels[item.key] || item.key}</span><strong>{item.value}</strong></div><div className="bar-track"><div className="bar-fill" style={{ width: `${((Number(item.value) || 0) / max) * 100}%` }} /></div></div>)}</div></section>;
}
