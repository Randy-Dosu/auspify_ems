import { createContext } from "react";

/** Shared context object (kept in a .js file so the provider file only exports a component). */
export const NotificationContext = createContext(null);
