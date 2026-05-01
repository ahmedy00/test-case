import React from "react";
import QuotePanel from "../components/QuotePanel";
import { useActiveQuote } from "../hooks/useActiveQuote";

type QuotePageProps = {
  sessionId: string | null;
};

const QuotePage: React.FC<QuotePageProps> = ({ sessionId }) => {
  const quote = useActiveQuote(sessionId);

  return (
    <div className="quote-page">
      <header className="quote-page__header">
        <h1>Quote Detail</h1>
        <div className="quote-page__session">
          <span>session_id:</span>
          <code>{sessionId ?? "—"}</code>
        </div>
      </header>
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

export default QuotePage;
