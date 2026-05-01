import React, { useEffect } from "react";
import type { Action } from "../types";

type ActionToastProps = {
  action: Action | null;
  onDismiss: () => void;
};

const AUTO_DISMISS_MS = 4000;

const ActionToast: React.FC<ActionToastProps> = ({ action, onDismiss }) => {
  useEffect(() => {
    if (action === null) return;
    const id = window.setTimeout(onDismiss, AUTO_DISMISS_MS);
    return () => window.clearTimeout(id);
  }, [action, onDismiss]);

  if (action === null) return null;

  const className = `action-toast action-toast--${action.status}`;
  return (
    <div className={className} role="status" aria-live="polite">
      <span className="action-toast__tool">{action.tool}</span>
      <span className="action-toast__message">{action.message}</span>
      <button
        type="button"
        className="action-toast__dismiss"
        onClick={onDismiss}
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  );
};

export default ActionToast;
