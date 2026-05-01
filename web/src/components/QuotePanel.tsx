import React from "react";
import type { Quote } from "../types";

type QuotePanelProps = {
  sessionId: string | null;
  quote: Quote | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
};

const QuotePanel: React.FC<QuotePanelProps> = ({
  sessionId,
  quote,
  loading,
  error,
  onRefresh,
}) => {
  return (
    <aside className="quote-panel">
      <div className="quote-panel__header">
        <h2>Active Quote</h2>
        <button
          type="button"
          className="quote-panel__refresh"
          onClick={onRefresh}
          disabled={sessionId === null}
        >
          {loading ? "…" : "refresh"}
        </button>
      </div>

      {sessionId === null && (
        <p className="quote-panel__empty">
          No session yet — send your first message to start a quote.
        </p>
      )}

      {error !== null && sessionId !== null && (
        <p className="quote-panel__error">Failed to load quote: {error}</p>
      )}

      {sessionId !== null && quote === null && error === null && (
        <p className="quote-panel__empty">
          No items yet — ask the assistant to add something.
        </p>
      )}

      {quote !== null && (
        <>
          <div className="quote-panel__meta">
            <div>
              <span className="quote-panel__meta-label">Quote</span>
              <span className="quote-panel__meta-value">#{quote.id}</span>
            </div>
            <div>
              <span className="quote-panel__meta-label">Items</span>
              <span className="quote-panel__meta-value">{quote.item_count}</span>
            </div>
            <div>
              <span className="quote-panel__meta-label">Subtotal</span>
              <span className="quote-panel__meta-value">${quote.subtotal}</span>
            </div>
          </div>

          {quote.items.length === 0 ? (
            <p className="quote-panel__empty">
              No items yet — ask the assistant to add something.
            </p>
          ) : (
            <table className="quote-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Qty</th>
                  <th>Unit</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {quote.items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <div className="quote-table__name">{item.product_name}</div>
                      <div className="quote-table__sku">{item.product_sku}</div>
                    </td>
                    <td>{item.quantity}</td>
                    <td>${item.unit_price_snapshot}</td>
                    <td>${item.line_total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </aside>
  );
};

export default QuotePanel;
