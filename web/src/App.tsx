import React, { useCallback, useEffect, useState } from "react";
import Layout from "./components/Layout";
import type { ViewName } from "./components/Layout";
import ChatPage from "./pages/ChatPage";
import QuotePage from "./pages/QuotePage";
import ProductsPage from "./pages/ProductsPage";
import KnowledgePage from "./pages/KnowledgePage";
import { getStoredSessionId } from "./session";

const App: React.FC = () => {
  const [view, setView] = useState<ViewName>("chat");
  const [sessionId, setSessionId] = useState<string | null>(() =>
    getStoredSessionId(),
  );

  const refreshSessionId = useCallback(() => {
    setSessionId(getStoredSessionId());
  }, []);

  useEffect(() => {
    const onStorage = (e: StorageEvent): void => {
      if (e.key === "b2b_sales_session_id") refreshSessionId();
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [refreshSessionId]);

  return (
    <Layout current={view} onNavigate={setView} sessionId={sessionId}>
      {view === "chat" && (
        <ChatPage sessionId={sessionId} onSessionChange={refreshSessionId} />
      )}
      {view === "quote" && <QuotePage sessionId={sessionId} />}
      {view === "products" && <ProductsPage />}
      {view === "knowledge" && <KnowledgePage />}
    </Layout>
  );
};

export default App;
