"use client";

import { useEffect, useRef, useCallback, useState } from "react";

interface UsePollingOptions {
  interval?: number;
  enabled?: boolean;
}

export function usePolling(
  fetchFn: () => Promise<void>,
  { interval = 30_000, enabled = true }: UsePollingOptions = {}
) {
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fetchRef = useRef(fetchFn);
  fetchRef.current = fetchFn;

  const refresh = useCallback(async () => {
    await fetchRef.current();
    setLastUpdated(new Date());
  }, []);

  useEffect(() => {
    if (!enabled) return;

    function startPolling() {
      timerRef.current = setInterval(() => {
        if (document.visibilityState === "visible") {
          refresh();
        }
      }, interval);
    }

    function handleVisibility() {
      if (document.visibilityState === "visible") {
        refresh();
      }
    }

    startPolling();
    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [interval, enabled, refresh]);

  return { lastUpdated, refresh };
}
