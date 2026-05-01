import React, { useEffect, useState } from "react";
import { createProduct, listProducts } from "../api/products";
import type { Product, ProductCreateInput } from "../types";

const EMPTY_FORM: ProductCreateInput = {
  sku: "",
  name: "",
  description: "",
  category: "",
  price: "",
  currency: "USD",
  stock: 0,
};

const ProductsPage: React.FC = () => {
  const [items, setItems] = useState<Product[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [listError, setListError] = useState<string | null>(null);
  const [form, setForm] = useState<ProductCreateInput>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitOk, setSubmitOk] = useState<string | null>(null);

  const refresh = async (): Promise<void> => {
    setLoading(true);
    try {
      const data = await listProducts();
      setItems(data);
      setListError(null);
    } catch (err) {
      setListError(err instanceof Error ? err.message : "Failed to load products");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const update = (key: keyof ProductCreateInput) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void => {
      const value = e.target.value;
      setForm((prev) => ({
        ...prev,
        [key]: key === "stock" ? Number(value) : value,
      }));
    };

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setSubmitting(true);
    setSubmitError(null);
    setSubmitOk(null);
    try {
      const payload: ProductCreateInput = {
        ...form,
        currency: form.currency?.trim() || "USD",
        stock: Number(form.stock ?? 0),
      };
      const created = await createProduct(payload);
      setSubmitOk(`Created ${created.sku} (#${created.id}).`);
      setForm(EMPTY_FORM);
      await refresh();
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to create product");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="data-page">
      <header className="data-page__header">
        <h1>Products</h1>
        <button type="button" onClick={() => void refresh()} disabled={loading}>
          {loading ? "Loading…" : "Refresh"}
        </button>
      </header>

      {listError !== null && <p className="data-page__error">{listError}</p>}

      <table className="data-table">
        <thead>
          <tr>
            <th>SKU</th>
            <th>Name</th>
            <th>Category</th>
            <th>Price</th>
            <th>Stock</th>
          </tr>
        </thead>
        <tbody>
          {items.map((p) => (
            <tr key={p.id}>
              <td><code>{p.sku}</code></td>
              <td>{p.name}</td>
              <td>{p.category}</td>
              <td>${p.price} {p.currency}</td>
              <td>{p.stock}</td>
            </tr>
          ))}
          {items.length === 0 && !loading && (
            <tr>
              <td colSpan={5} className="data-table__empty">No products.</td>
            </tr>
          )}
        </tbody>
      </table>

      <section className="data-page__form-section">
        <h2>Add Product</h2>
        <form className="data-form" onSubmit={onSubmit}>
          <label>
            <span>SKU</span>
            <input
              type="text"
              required
              value={form.sku}
              onChange={update("sku")}
            />
          </label>
          <label>
            <span>Name</span>
            <input
              type="text"
              required
              value={form.name}
              onChange={update("name")}
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
          <label>
            <span>Price (USD)</span>
            <input
              type="text"
              inputMode="decimal"
              required
              value={form.price}
              onChange={update("price")}
            />
          </label>
          <label>
            <span>Stock</span>
            <input
              type="number"
              min={0}
              required
              value={form.stock ?? 0}
              onChange={update("stock")}
            />
          </label>
          <label className="data-form__full">
            <span>Description</span>
            <textarea
              required
              rows={3}
              value={form.description}
              onChange={update("description")}
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

export default ProductsPage;
