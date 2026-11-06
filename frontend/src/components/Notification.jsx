import { createPortal } from "react-dom";
import { classNames } from "../utils";

const ICONS = {
  success: "✓",
  error: "!",
  info: "i",
};

/**
 * Toast stack. Rendered in a portal so it is not clipped by page layout.
 */
export default function NotificationStack({ notifications, onDismiss }) {
  if (typeof document === "undefined") return null;

  return createPortal(
    <div className="toast-stack" aria-live="polite" aria-atomic="false">
      {notifications.map((item) => (
        <div
          key={item.id}
          className={classNames("toast", `toast-${item.type}`)}
          role="status"
        >
          <span className="toast-icon" aria-hidden="true">
            {ICONS[item.type] ?? "i"}
          </span>
          <p className="toast-message">{item.message}</p>
          <button
            type="button"
            className="toast-close"
            onClick={() => onDismiss(item.id)}
            aria-label="Dismiss notification"
          >
            ×
          </button>
        </div>
      ))}
    </div>,
    document.body,
  );
}
