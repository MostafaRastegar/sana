import { useEffect, useRef } from "react";

export function useAutoRefresh(callback: () => void, intervalMs: number | null) {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (intervalMs === null || intervalMs <= 0) return;
    const id = setInterval(() => savedCallback.current(), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
}