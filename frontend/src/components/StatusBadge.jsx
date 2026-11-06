import { statusLabel } from "../utils";

/** Colored status pill used in tables and detail pages. */
export default function StatusBadge({ status }) {
  const label = statusLabel(status);
  return <span className={`status-badge status-${status}`}>{label}</span>;
}
