import { useEffect, useState } from "react";

/**
 * Return a value that only changes after `delay` ms of quiet.
 * Used by the employee search box (300 ms debounce).
 */
export function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
