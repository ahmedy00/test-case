import React from 'react';
import ReactDOM from 'react-dom/client';

const App: React.FC = () => {
  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', padding: 24 }}>
      <h1>B2B Sales Assistant</h1>
      <p>Web client placeholder — Phase 0.</p>
    </main>
  );
};

const root = document.getElementById('root');
if (!root) {
  throw new Error('Root element #root not found');
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
