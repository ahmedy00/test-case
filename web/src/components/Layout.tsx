import React from "react";
import { resetSession } from "../session";

export type ViewName = "chat" | "quote" | "products" | "knowledge";

type LayoutProps = {
  current: ViewName;
  onNavigate: (view: ViewName) => void;
  sessionId: string | null;
  children: React.ReactNode;
};

const NAV_ITEMS: Array<{ key: ViewName; label: string }> = [
  { key: "chat", label: "Chat" },
  { key: "quote", label: "Quote" },
  { key: "products", label: "Products" },
  { key: "knowledge", label: "Knowledge" },
];

const Layout: React.FC<LayoutProps> = ({
  current,
  onNavigate,
  sessionId,
  children,
}) => {
  const truncated =
    sessionId === null ? "no session" : `${sessionId.slice(0, 8)}…`;

  const handleCopy = async (): Promise<void> => {
    if (sessionId === null) return;
    try {
      await navigator.clipboard.writeText(sessionId);
    } catch {
      window.prompt("Copy session id", sessionId);
    }
  };

  const handleReset = (): void => {
    if (!window.confirm("Reset the local session? You'll start a new draft quote.")) {
      return;
    }
    resetSession();
    window.location.reload();
  };

  return (
    <div className="layout">
      <header className="topbar">
        <div className="brand">B2B Sales Assistant</div>
        <nav className="nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              type="button"
              className={`nav-link${current === item.key ? " nav-link--active" : ""}`}
              onClick={() => onNavigate(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div className="session-badge">
          <span className="session-badge__label">session</span>
          <code className="session-badge__id" title={sessionId ?? "no session"}>
            {truncated}
          </code>
          <button
            type="button"
            className="session-badge__btn"
            onClick={handleCopy}
            disabled={sessionId === null}
            title="Copy full session id"
          >
            copy
          </button>
          <button
            type="button"
            className="session-badge__btn"
            onClick={handleReset}
            title="Reset local session"
          >
            reset
          </button>
        </div>
      </header>
      <main className="content">{children}</main>
    </div>
  );
};

export default Layout;
