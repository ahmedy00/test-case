export type Source = {
  id: number;
  score: number;
  [key: string]: unknown;
};

export type RetrievalMethod = "vector" | "fts" | "mixed";

export type Sources = {
  products: Source[];
  knowledge: Source[];
  methodUsed: RetrievalMethod;
};

export type Action = {
  tool: string;
  args: unknown;
  result: unknown;
  status: "success" | "error";
  message: string;
};

export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  role: ChatRole;
  content: string;
  sources?: Sources;
  actions?: Action[];
};

export type QuoteItem = {
  id: number;
  product_id: number;
  product_sku: string;
  product_name: string;
  quantity: number;
  unit_price_snapshot: string;
  line_total: string;
};

export type Quote = {
  id: number;
  session_id: string;
  status: string;
  items: QuoteItem[];
  subtotal: string;
  item_count: number;
  created_at: string;
  updated_at: string;
};
