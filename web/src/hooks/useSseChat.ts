import { useCallback, useReducer, useRef } from "react";
import { streamChat } from "../api/chat";
import type { SseEvent } from "../api/chat";
import { getStoredSessionId, storeSessionId } from "../session";
import type { Action, ChatMessage, Sources } from "../types";

export type ChatStatus = "idle" | "streaming" | "done" | "error";

export type ChatState = {
  status: ChatStatus;
  currentAssistantText: string;
  currentSources: Sources | null;
  pendingActions: Action[];
  messages: ChatMessage[];
  error: string | null;
  latestAction: Action | null;
};

type Event =
  | { kind: "send"; userMessage: string }
  | { kind: "sources"; sources: Sources }
  | { kind: "chunk"; delta: string }
  | { kind: "action"; action: Action }
  | { kind: "clear-latest-action" }
  | { kind: "finalize" }
  | { kind: "error"; message: string };

const initialState: ChatState = {
  status: "idle",
  currentAssistantText: "",
  currentSources: null,
  pendingActions: [],
  messages: [],
  error: null,
  latestAction: null,
};

function reducer(state: ChatState, event: Event): ChatState {
  switch (event.kind) {
    case "send":
      return {
        ...state,
        status: "streaming",
        currentAssistantText: "",
        currentSources: null,
        pendingActions: [],
        error: null,
        latestAction: null,
        messages: [
          ...state.messages,
          { role: "user", content: event.userMessage },
        ],
      };
    case "sources":
      return { ...state, currentSources: event.sources };
    case "chunk":
      return {
        ...state,
        currentAssistantText: state.currentAssistantText + event.delta,
      };
    case "action":
      return {
        ...state,
        pendingActions: [...state.pendingActions, event.action],
        latestAction: event.action,
      };
    case "clear-latest-action":
      return { ...state, latestAction: null };
    case "finalize": {
      if (state.status !== "streaming") return state;
      const hasText = state.currentAssistantText.length > 0;
      const hasActions = state.pendingActions.length > 0;
      if (!hasText && !hasActions) {
        return { ...state, status: "done" };
      }
      const finalized: ChatMessage = {
        role: "assistant",
        content: state.currentAssistantText,
        sources: state.currentSources ?? undefined,
        actions: hasActions ? state.pendingActions : undefined,
      };
      return {
        ...state,
        status: "done",
        messages: [...state.messages, finalized],
        currentAssistantText: "",
        currentSources: null,
        pendingActions: [],
      };
    }
    case "error":
      return { ...state, status: "error", error: event.message };
    default:
      return state;
  }
}

export type UseSseChat = {
  state: ChatState;
  send: (message: string) => Promise<void>;
  clearLatestAction: () => void;
};

export function useSseChat(opts?: {
  onAction?: (action: Action) => void;
}): UseSseChat {
  const [state, dispatch] = useReducer(reducer, initialState);
  const inflight = useRef<AbortController | null>(null);
  const onAction = opts?.onAction;

  const clearLatestAction = useCallback(() => {
    dispatch({ kind: "clear-latest-action" });
  }, []);

  const send = useCallback(
    async (message: string) => {
      if (inflight.current !== null) {
        inflight.current.abort();
      }
      const controller = new AbortController();
      inflight.current = controller;

      dispatch({ kind: "send", userMessage: message });

      try {
        const sessionId = getStoredSessionId();
        for await (const evt of streamChat({
          sessionId,
          message,
          signal: controller.signal,
        })) {
          handle(evt);
        }
        dispatch({ kind: "finalize" });
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Unknown streaming error";
        dispatch({ kind: "error", message: msg });
      } finally {
        if (inflight.current === controller) {
          inflight.current = null;
        }
      }

      function handle(evt: SseEvent): void {
        switch (evt.type) {
          case "session":
            storeSessionId(evt.sessionId);
            break;
          case "sources":
            dispatch({
              kind: "sources",
              sources: {
                products: evt.products,
                knowledge: evt.knowledge,
                methodUsed: evt.methodUsed,
              },
            });
            break;
          case "chunk":
            dispatch({ kind: "chunk", delta: evt.delta });
            break;
          case "action": {
            const action: Action = {
              tool: evt.tool,
              args: evt.args,
              result: evt.result,
              status: evt.status,
              message: evt.message,
            };
            dispatch({ kind: "action", action });
            onAction?.(action);
            break;
          }
          case "done":
            dispatch({ kind: "finalize" });
            break;
          case "error":
            dispatch({
              kind: "error",
              message: `${evt.code}: ${evt.message}`,
            });
            break;
        }
      }
    },
    [onAction],
  );

  return { state, send, clearLatestAction };
}
