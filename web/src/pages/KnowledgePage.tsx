import React, { useEffect, useState } from "react";
import { createKnowledge, listKnowledge } from "../api/knowledge";
import type { KnowledgeCreateInput, KnowledgeEntry } from "../types";

const EMPTY_FORM: KnowledgeCreateInput = {
  title: "",
  content: "",
  category: "",
};

const KnowledgePage: React.FC = () => {
  const [items, setItems] = useState<KnowledgeEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [listError, setListError] = useState<string | null>(null);
  const [form, setForm] = useState<KnowledgeCreateInput>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitOk, setSubmitOk] = useState<string | null>(null);

  const refresh = async (): Promise<void> => {
    setLoading(true);
    try {
      const data = await listKnowledge();
      setItems(data);
      setListError(null);
    } catch (err) {
      setListError(err instanceof Error ? err.message : "Failed to load knowledge");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const update = (key: keyof KnowledgeCreateInput) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void => {
      setForm((prev) => ({ ...prev, [key]: e.target.value }));
    };

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setSubmitting(true);
    setSubmitError(null);
    setSubmitOk(null);
    try {
      const created = await createKnowledge(form);
      setSubmitOk(`Created “${created.title}” (#${created.id}).`);
      setForm(EMPTY_FORM);
      await refresh();
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to create entry");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="data-page">
      <header className="data-page__header">
        <h1>Knowledge</h1>
        <button type="button" onClick={() => void refresh()} disabled={loading}>
          {loading ? "Loading…" : "Refresh"}
        </button>
      </header>

      {listError !== null && <p className="data-page__error">{listError}</p>}

      <table className="data-table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Category</th>
            <th>Content</th>
          </tr>
        </thead>
        <tbody>
          {items.map((k) => (
            <tr key={k.id}>
              <td>{k.title}</td>
              <td>{k.category}</td>
              <td className="data-table__excerpt">{k.content}</td>
            </tr>
          ))}
          {items.length === 0 && !loading && (
            <tr>
              <td colSpan={3} className="data-table__empty">No entries.</td>
            </tr>
          )}
        </tbody>
      </table>

      <section className="data-page__form-section">
        <h2>Add Knowledge Entry</h2>
        <form className="data-form" onSubmit={onSubmit}>
          <label>
            <span>Title</span>
            <input
              type="text"
              required
              value={form.title}
              onChange={update("title")}
            />
          </label>
          <label>
            <span>Category</span>
            <input
              type="text"
              required
              value={form.category}
              onChange={update("category")}
            />
          </label>
          <label className="data-form__full">
            <span>Content</span>
            <textarea
              required
              rows={6}
              value={form.content}
              onChange={update("content")}
            />
          </label>
          <div className="data-form__footer">
            <button type="submit" disabled={submitting}>
              {submitting ? "Creating…" : "Create"}
            </button>
            {submitOk !== null && <span className="data-form__ok">{submitOk}</span>}
            {submitError !== null && (
              <span className="data-form__err">{submitError}</span>
            )}
          </div>
        </form>
      </section>
    </div>
  );
};

export default KnowledgePage;
