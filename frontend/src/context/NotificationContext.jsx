import { useCallback, useMemo, useState } from "react";
import NotificationStack from "../components/Notification";
import { NotificationContext } from "./notification-context";

/**
 * Provides a global `notify(message, type)` function and renders the toast
 * stack. Used by every screen for success/error feedback.
 */
export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = useState([]);

  const dismiss = useCallback((id) => {
    setNotifications((current) => current.filter((item) => item.id !== id));
  }, []);

  const notify = useCallback(
    (message, type = "success") => {
      const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
      setNotifications((current) => [...current, { id, message, type }]);
      window.setTimeout(() => dismiss(id), 4500);
    },
    [dismiss],
  );

  const value = useMemo(() => ({ notify }), [notify]);

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <NotificationStack
        notifications={notifications}
        onDismiss={dismiss}
      />
    </NotificationContext.Provider>
  );
}
