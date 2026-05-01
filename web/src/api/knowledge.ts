import { apiFetch } from "./client";
import type { KnowledgeEntry, KnowledgeCreateInput } from "../types";

export async function listKnowledge(): Promise<KnowledgeEntry[]> {
  return apiFetch<KnowledgeEntry[]>("/knowledge");
}

export async function createKnowledge(
  input: KnowledgeCreateInput,
): Promise<KnowledgeEntry> {
  return apiFetch<KnowledgeEntry>("/knowledge", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
