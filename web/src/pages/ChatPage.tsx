import React, { useCallback, useState } from "react";
import MessageList from "../components/MessageList";
import QuotePanel from "../components/QuotePanel";
import ActionToast from "../components/ActionToast";
import { useSseChat } from "../hooks/useSseChat";
import { useActiveQuote } from "../hooks/useActiveQuote";

type ChatPageProps = {
  sessionId: string | null;
  onSessionChange: () => void;
};

const ChatPage: React.FC<ChatPageProps> = ({ sessionId, onSessionChange }) => {
  const [draft, setDraft] = useState<string>("");
  const quote = useActiveQuote(sessionId);

  const handleAction = useCallback(() => {
    quote.refresh();
    onSessionChange();
  }, [quote, onSessionChange]);

  const chat = useSseChat({ onAction: handleAction });

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    const text = draft.trim();
    if (text.length === 0 || chat.state.status === "streaming") return;
    setDraft("");
    await chat.send(text);
    onSessionChange();
  };

  const isStreaming = chat.state.status === "streaming";

  return (
    <div className="chat-page">
      <ActionToast
        action={chat.state.latestAction}
        onDismiss={chat.clearLatestAction}
      />
      <div className="chat-page__main">
        <MessageList
          messages={chat.state.messages}
          streamingText={chat.state.currentAssistantText}
          streamingSources={chat.state.currentSources}
          isStreaming={isStreaming}
          error={chat.state.error}
        />
        <form className="chat-input" onSubmit={onSubmit}>
          <textarea
            className="chat-input__textarea"
            placeholder="Ask about products, policies, or pricing…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                e.currentTarget.form?.requestSubmit();
              }
            }}
            disabled={isStreaming}
            rows={2}
          />
          <button
            type="submit"
            className="chat-input__send"
            disabled={isStreaming || draft.trim().length === 0}
          >
            {isStreaming ? "…" : "Send"}
          </button>
        </form>
      </div>
      <QuotePanel
        sessionId={sessionId}
        quote={quote.quote}
        loading={quote.loading}
        error={quote.error}
        onRefresh={quote.refresh}
      />
    </div>
  );
};

export default ChatPage;
