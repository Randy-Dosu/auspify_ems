import { useContext } from "react";
import { NotificationContext } from "../context/notification-context";

/** Access the global toast notifier. */
export function useNotification() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error("useNotification must be used inside NotificationProvider");
  }
  return context;
}
