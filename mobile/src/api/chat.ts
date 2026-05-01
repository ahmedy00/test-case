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

export type StreamHandle = { abort: () => void };

export type StreamOptions = {
  sessionId: string | null;
  message: string;
  onEvent: (event: SseEvent) => void;
  onDone: () => void;
  onError: (message: string) => void;
};

type RawEvent = { event: string; data: string };

// React Native does not expose response.body as a ReadableStream consistently
// across iOS, Android and the Expo web target. XHR + onreadystatechange (LOADING)
// reliably exposes incremental responseText on every platform Expo supports.
export function streamChat(opts: StreamOptions): StreamHandle {
  const xhr = new XMLHttpRequest();
  let processedLength = 0;
  let buffer = "";
  let aborted = false;

  const flush = (final: boolean): void => {
    const newText = xhr.responseText.slice(processedLength);
    if (newText.length > 0) {
      processedLength = xhr.responseText.length;
      buffer += newText;
    }

    let sepIndex = buffer.indexOf("\n\n");
    while (sepIndex !== -1) {
      const block = buffer.slice(0, sepIndex);
      buffer = buffer.slice(sepIndex + 2);
      const raw = parseEventBlock(block);
      if (raw !== null) {
        const mapped = mapEvent(raw);
        if (mapped !== null) opts.onEvent(mapped);
      }
      sepIndex = buffer.indexOf("\n\n");
    }

    if (final) {
      const tail = buffer.trim();
      if (tail.length > 0) {
        const raw = parseEventBlock(tail);
        if (raw !== null) {
          const mapped = mapEvent(raw);
          if (mapped !== null) opts.onEvent(mapped);
        }
      }
      buffer = "";
    }
  };

  xhr.open("POST", `${API_BASE_URL}/chat/stream`);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Accept", "text/event-stream");

  xhr.onreadystatechange = (): void => {
    if (aborted) return;
    if (
      xhr.readyState === XMLHttpRequest.LOADING ||
      xhr.readyState === XMLHttpRequest.DONE
    ) {
      flush(xhr.readyState === XMLHttpRequest.DONE);
    }
    if (xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status >= 200 && xhr.status < 300) {
        opts.onDone();
      } else {
        opts.onError(`HTTP ${xhr.status}`);
      }
    }
  };

  xhr.onerror = (): void => {
    if (aborted) return;
    opts.onError("Network error");
  };

  xhr.send(
    JSON.stringify({
      session_id: opts.sessionId,
      message: opts.message,
    }),
  );

  return {
    abort: (): void => {
      aborted = true;
      try {
        xhr.abort();
      } catch {
        // ignore
      }
    },
  };
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
