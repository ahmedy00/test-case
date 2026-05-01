import { useCallback, useEffect, useReducer, useRef } from "react";
import { streamChat } from "../api/chat";
import type { SseEvent, StreamHandle } from "../api/chat";
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

type ReducerEvent =
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

function reducer(state: ChatState, event: ReducerEvent): ChatState {
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
  onSessionEstablished?: (sessionId: string) => void;
}): UseSseChat {
  const [state, dispatch] = useReducer(reducer, initialState);
  const inflightRef = useRef<StreamHandle | null>(null);
  const onAction = opts?.onAction;
  const onSessionEstablished = opts?.onSessionEstablished;

  useEffect(() => {
    return () => {
      inflightRef.current?.abort();
      inflightRef.current = null;
    };
  }, []);

  const clearLatestAction = useCallback(() => {
    dispatch({ kind: "clear-latest-action" });
  }, []);

  const send = useCallback(
    async (message: string): Promise<void> => {
      inflightRef.current?.abort();
      inflightRef.current = null;

      dispatch({ kind: "send", userMessage: message });

      const sessionId = await getStoredSessionId();

      const handle = streamChat({
        sessionId,
        message,
        onEvent: (evt: SseEvent) => {
          switch (evt.type) {
            case "session":
              // Fire-and-forget: subsequent events do not depend on the
              // AsyncStorage write being flushed, and we want to surface the
              // id to listeners immediately so the quote screen can poll.
              void storeSessionId(evt.sessionId);
              onSessionEstablished?.(evt.sessionId);
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
        },
        onDone: () => {
          dispatch({ kind: "finalize" });
          if (inflightRef.current === handle) inflightRef.current = null;
        },
        onError: (msg: string) => {
          dispatch({ kind: "error", message: msg });
          if (inflightRef.current === handle) inflightRef.current = null;
        },
      });

      inflightRef.current = handle;
    },
    [onAction, onSessionEstablished],
  );

  return { state, send, clearLatestAction };
}
