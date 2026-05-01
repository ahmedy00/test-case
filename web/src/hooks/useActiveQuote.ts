import { useCallback, useEffect, useRef, useState } from "react";
import { getActiveQuote } from "../api/quotes";
import type { Quote } from "../types";

const POLL_MS = 3000;

export type UseActiveQuote = {
  quote: Quote | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
};

export function useActiveQuote(sessionId: string | null): UseActiveQuote {
  const [quote, setQuote] = useState<Quote | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const cancelledRef = useRef<boolean>(false);

  const fetchOnce = useCallback(async (): Promise<void> => {
    if (sessionId === null) return;
    setLoading(true);
    try {
      const result = await getActiveQuote(sessionId);
      if (cancelledRef.current) return;
      setQuote(result ?? null);
      setError(null);
    } catch (err) {
      if (cancelledRef.current) return;
      setError(err instanceof Error ? err.message : "Failed to fetch quote");
    } finally {
      if (!cancelledRef.current) setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    cancelledRef.current = false;
    if (sessionId === null) {
      setQuote(null);
      setLoading(false);
      setError(null);
      return () => {
        cancelledRef.current = true;
      };
    }

    void fetchOnce();
    const id = window.setInterval(() => {
      void fetchOnce();
    }, POLL_MS);

    return () => {
      cancelledRef.current = true;
      window.clearInterval(id);
    };
  }, [sessionId, fetchOnce]);

  const refresh = useCallback(() => {
    void fetchOnce();
  }, [fetchOnce]);

  return { quote, loading, error, refresh };
}
