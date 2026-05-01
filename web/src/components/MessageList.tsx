import React, { useEffect, useRef } from "react";
import type { ChatMessage, Sources } from "../types";
import SourceList from "./SourceList";

type MessageListProps = {
  messages: ChatMessage[];
  streamingText: string;
  streamingSources: Sources | null;
  isStreaming: boolean;
  error: string | null;
};

const MessageList: React.FC<MessageListProps> = ({
  messages,
  streamingText,
  streamingSources,
  isStreaming,
  error,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (el === null) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, streamingText, isStreaming, error]);

  return (
    <div className="messages" ref={containerRef}>
      {messages.length === 0 && !isStreaming && (
        <div className="messages__empty">
          Try: <em>"What laptops do you offer?"</em> or{" "}
          <em>"Add 2 ThinkBooks to my quote."</em>
        </div>
      )}

      {messages.map((m, i) => (
        <div key={i} className={`message message--${m.role}`}>
          <div className="message__role">{m.role}</div>
          <div className="message__body">{m.content || <em>(empty)</em>}</div>
          {m.sources && <SourceList sources={m.sources} />}
          {m.actions && m.actions.length > 0 && (
            <ul className="message__actions">
              {m.actions.map((a, j) => (
                <li
                  key={j}
                  className={`message__action message__action--${a.status}`}
                >
                  <span className="message__action-tool">{a.tool}</span>
                  <span className="message__action-msg">{a.message}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}

      {isStreaming && (
        <div className="message message--assistant message--streaming">
          <div className="message__role">assistant</div>
          <div className="message__body">
            {streamingText}
            <span className="message__cursor">▍</span>
          </div>
          {streamingSources && <SourceList sources={streamingSources} />}
        </div>
      )}

      {error !== null && (
        <div className="message message--error">
          <div className="message__role">error</div>
          <div className="message__body">{error}</div>
        </div>
      )}
    </div>
  );
};

export default MessageList;
