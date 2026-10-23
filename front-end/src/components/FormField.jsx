export default function FormField({ label, error, children, hint }) {
  return <div className="form-field"><label>{label}</label>{children}{hint && <small>{hint}</small>}{error && <small className="field-error">{error}</small>}</div>;
}
