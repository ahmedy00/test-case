import React from "react";
import type { Sources } from "../types";

type SourceListProps = {
  sources: Sources;
};

function summarize(record: Record<string, unknown>): string {
  if (typeof record.name === "string") return record.name;
  if (typeof record.title === "string") return record.title;
  if (typeof record.sku === "string") return record.sku;
  return `#${String(record.id ?? "?")}`;
}

const SourceList: React.FC<SourceListProps> = ({ sources }) => {
  const hasAny =
    sources.products.length > 0 || sources.knowledge.length > 0;
  if (!hasAny) return null;

  return (
    <div className="sources">
      <div className="sources__header">
        <span>retrieval: {sources.methodUsed}</span>
      </div>
      {sources.products.length > 0 && (
        <div className="sources__group">
          <div className="sources__group-title">Products</div>
          <ul>
            {sources.products.map((p) => (
              <li key={`p-${p.id}`}>
                <span className="sources__name">
                  {summarize(p as unknown as Record<string, unknown>)}
                </span>
                <span className="sources__score">
                  {Number(p.score ?? 0).toFixed(3)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {sources.knowledge.length > 0 && (
        <div className="sources__group">
          <div className="sources__group-title">Knowledge</div>
          <ul>
            {sources.knowledge.map((k) => (
              <li key={`k-${k.id}`}>
                <span className="sources__name">
                  {summarize(k as unknown as Record<string, unknown>)}
                </span>
                <span className="sources__score">
                  {Number(k.score ?? 0).toFixed(3)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default SourceList;
