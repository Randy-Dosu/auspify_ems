/** Small accessible loading spinner. */
export default function Spinner({ label = "Loading" }) {
  return (
    <span className="spinner" role="status" aria-label={label}>
      <span className="sr-only">{label}</span>
    </span>
  );
}
