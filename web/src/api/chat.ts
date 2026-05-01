import { API_BASE_URL } from "./client";
import type { Action, RetrievalMethod, Source } from "../types";

export type SseEvent =
  | { type: "session"; sessionId: string }
  | {
      type: "sources";
      products: Source[];
      knowledge: Source[];
      methodUsed: RetrievalMethod;
    }
  | { type: "chunk"; delta: string }
  | ({ type: "action" } & Action)
  | { type: "done"; messageId: number }
  | { type: "error"; code: string; message: string };

type RawEvent = { event: string; data: string };

export async function* streamChat(opts: {
  sessionId: string | null;
  message: string;
  signal?: AbortSignal;
}): AsyncGenerator<SseEvent> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({
      session_id: opts.sessionId,
      message: opts.message,
    }),
    signal: opts.signal,
  });

  if (!response.ok || response.body === null) {
    const text = await safeText(response);
    yield {
      type: "error",
      code: `HTTP_${response.status}`,
      message: text || `Chat request failed with status ${response.status}`,
    };
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let sepIndex: number;
      while ((sepIndex = buffer.indexOf("\n\n")) !== -1) {
        const block = buffer.slice(0, sepIndex);
        buffer = buffer.slice(sepIndex + 2);
        const raw = parseEventBlock(block);
        if (raw === null) continue;
        const mapped = mapEvent(raw);
        if (mapped !== null) yield mapped;
      }
    }

    const tail = buffer.trim();
    if (tail.length > 0) {
      const raw = parseEventBlock(tail);
      if (raw !== null) {
        const mapped = mapEvent(raw);
        if (mapped !== null) yield mapped;
      }
    }
  } finally {
    reader.releaseLock();
  }
}

function parseEventBlock(block: string): RawEvent | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of block.split("\n")) {
    if (line.length === 0 || line.startsWith(":")) continue;
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).replace(/^ /, ""));
    }
  }
  if (dataLines.length === 0) return null;
  return { event, data: dataLines.join("\n") };
}

function mapEvent(raw: RawEvent): SseEvent | null {
  let payload: unknown;
  try {
    payload = JSON.parse(raw.data);
  } catch {
    return null;
  }
  if (payload === null || typeof payload !== "object") return null;
  const obj = payload as Record<string, unknown>;

  switch (raw.event) {
    case "session":
      return { type: "session", sessionId: String(obj.session_id) };
    case "sources":
      return {
        type: "sources",
        products: (obj.products as Source[]) ?? [],
        knowledge: (obj.knowledge as Source[]) ?? [],
        methodUsed: (obj.method_used as RetrievalMethod) ?? "fts",
      };
    case "chunk":
      return { type: "chunk", delta: String(obj.delta ?? "") };
    case "action":
      return {
        type: "action",
        tool: String(obj.tool ?? ""),
        args: obj.args ?? {},
        result: obj.result ?? {},
        status: (obj.status as "success" | "error") ?? "error",
        message: String(obj.message ?? ""),
      };
    case "done":
      return { type: "done", messageId: Number(obj.message_id ?? 0) };
    case "error":
      return {
        type: "error",
        code: String(obj.code ?? "unknown"),
        message: String(obj.message ?? ""),
      };
    default:
      return null;
  }
}

async function safeText(response: Response): Promise<string> {
  try {
    return await response.text();
  } catch {
    return "";
  }
}
