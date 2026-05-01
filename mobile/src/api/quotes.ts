import { apiFetch } from "./client";
import type { Quote } from "../types";

export async function getActiveQuote(sessionId: string): Promise<Quote | null> {
  const params = `session_id=${encodeURIComponent(sessionId)}`;
  return apiFetch<Quote | null>(`/quotes/active?${params}`);
}
