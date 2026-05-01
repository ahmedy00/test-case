import { apiFetch } from "./client";
import type { Product, ProductCreateInput } from "../types";

export async function listProducts(): Promise<Product[]> {
  return apiFetch<Product[]>("/products");
}

export async function createProduct(input: ProductCreateInput): Promise<Product> {
  return apiFetch<Product>("/products", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
