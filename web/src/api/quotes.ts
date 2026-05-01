import { apiFetch } from "./client";
import type { Quote } from "../types";

export async function getActiveQuote(sessionId: string): Promise<Quote | null> {
  const params = new URLSearchParams({ session_id: sessionId });
  return apiFetch<Quote | null>(`/quotes/active?${params.toString()}`);
}
