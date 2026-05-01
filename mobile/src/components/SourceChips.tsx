import React from "react";
import { StyleSheet, Text, View } from "react-native";
import type { Source, Sources } from "../types";

type SourceChipsProps = {
  sources: Sources;
};

function summarize(record: Record<string, unknown>): string {
  if (typeof record.name === "string") return record.name;
  if (typeof record.title === "string") return record.title;
  if (typeof record.sku === "string") return record.sku;
  return `#${String(record.id ?? "?")}`;
}

const Chip: React.FC<{ label: string; score: number; tone: "product" | "knowledge" }> = ({
  label,
  score,
  tone,
}) => (
  <View style={[styles.chip, tone === "product" ? styles.chipProduct : styles.chipKnowledge]}>
    <Text style={styles.chipLabel} numberOfLines={1}>
      {label}
    </Text>
    <Text style={styles.chipScore}>{score.toFixed(2)}</Text>
  </View>
);

const SourceChips: React.FC<SourceChipsProps> = ({ sources }) => {
  const hasAny = sources.products.length > 0 || sources.knowledge.length > 0;
  if (!hasAny) return null;

  return (
    <View style={styles.container}>
      <Text style={styles.method}>retrieval: {sources.methodUsed}</Text>
      <View style={styles.row}>
        {sources.products.map((p: Source) => (
          <Chip
            key={`p-${p.id}`}
            label={summarize(p as unknown as Record<string, unknown>)}
            score={Number(p.score ?? 0)}
            tone="product"
          />
        ))}
        {sources.knowledge.map((k: Source) => (
          <Chip
            key={`k-${k.id}`}
            label={summarize(k as unknown as Record<string, unknown>)}
            score={Number(k.score ?? 0)}
            tone="knowledge"
          />
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginTop: 6,
  },
  method: {
    fontSize: 11,
    color: "#6b7280",
    marginBottom: 4,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  row: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
  },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    maxWidth: "100%",
  },
  chipProduct: {
    backgroundColor: "#eef2ff",
    borderColor: "#c7d2fe",
  },
  chipKnowledge: {
    backgroundColor: "#ecfdf5",
    borderColor: "#a7f3d0",
  },
  chipLabel: {
    fontSize: 12,
    color: "#1f2937",
    marginRight: 6,
    maxWidth: 180,
  },
  chipScore: {
    fontSize: 11,
    color: "#6b7280",
    fontVariant: ["tabular-nums"],
  },
});

export default SourceChips;
