import { useCallback, useEffect, useRef, useState } from "react";
import { getActiveQuote } from "../api/quotes";
import { getStoredSessionId } from "../session";
import type { Quote } from "../types";

const POLL_MS = 3000;

export type UseActiveQuote = {
  sessionId: string | null;
  sessionLoaded: boolean;
  quote: Quote | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
  reloadSession: () => Promise<void>;
};

export function useActiveQuote(): UseActiveQuote {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionLoaded, setSessionLoaded] = useState<boolean>(false);
  const [quote, setQuote] = useState<Quote | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const cancelledRef = useRef<boolean>(false);

  const reloadSession = useCallback(async (): Promise<void> => {
    const id = await getStoredSessionId();
    if (cancelledRef.current) return;
    setSessionId(id);
    setSessionLoaded(true);
  }, []);

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
    void reloadSession();
    return () => {
      cancelledRef.current = true;
    };
  }, [reloadSession]);

  useEffect(() => {
    if (!sessionLoaded) return;
    if (sessionId === null) {
      setQuote(null);
      setLoading(false);
      setError(null);
      return;
    }

    void fetchOnce();
    const id = setInterval(() => {
      void fetchOnce();
    }, POLL_MS);

    return () => {
      clearInterval(id);
    };
  }, [sessionId, sessionLoaded, fetchOnce]);

  const refresh = useCallback(() => {
    void fetchOnce();
  }, [fetchOnce]);

  return {
    sessionId,
    sessionLoaded,
    quote,
    loading,
    error,
    refresh,
    reloadSession,
  };
}
