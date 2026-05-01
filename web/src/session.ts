const KEY = "b2b_sales_session_id";

export function getStoredSessionId(): string | null {
  return localStorage.getItem(KEY);
}

export function storeSessionId(id: string): void {
  localStorage.setItem(KEY, id);
}

export function resetSession(): void {
  localStorage.removeItem(KEY);
}
