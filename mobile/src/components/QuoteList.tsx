import React from "react";
import { StyleSheet, Text, View } from "react-native";
import type { Quote } from "../types";

type QuoteListProps = {
  quote: Quote | null;
};

const QuoteList: React.FC<QuoteListProps> = ({ quote }) => {
  if (quote === null || quote.items.length === 0) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyText}>
          No items yet — head to Chat and ask the assistant to add something.
        </Text>
      </View>
    );
  }

  return (
    <View>
      <View style={styles.headerRow}>
        <Text style={[styles.headerCell, styles.cellName]}>Product</Text>
        <Text style={[styles.headerCell, styles.cellQty]}>Qty</Text>
        <Text style={[styles.headerCell, styles.cellPrice]}>Unit</Text>
        <Text style={[styles.headerCell, styles.cellTotal]}>Total</Text>
      </View>
      {quote.items.map((item) => (
        <View key={item.id} style={styles.row}>
          <View style={styles.cellName}>
            <Text style={styles.name}>{item.product_name}</Text>
            <Text style={styles.sku}>{item.product_sku}</Text>
          </View>
          <Text style={[styles.cell, styles.cellQty]}>{item.quantity}</Text>
          <Text style={[styles.cell, styles.cellPrice]}>${item.unit_price_snapshot}</Text>
          <Text style={[styles.cell, styles.cellTotal]}>${item.line_total}</Text>
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  empty: {
    padding: 24,
    alignItems: "center",
  },
  emptyText: {
    color: "#6b7280",
    textAlign: "center",
    fontSize: 14,
  },
  headerRow: {
    flexDirection: "row",
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#e5e7eb",
    backgroundColor: "#f9fafb",
  },
  headerCell: {
    fontSize: 11,
    fontWeight: "600",
    color: "#6b7280",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  row: {
    flexDirection: "row",
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#f3f4f6",
    alignItems: "center",
  },
  cell: {
    color: "#111827",
    fontSize: 14,
    fontVariant: ["tabular-nums"],
  },
  cellName: {
    flex: 3,
  },
  cellQty: {
    flex: 1,
    textAlign: "right",
  },
  cellPrice: {
    flex: 1.4,
    textAlign: "right",
  },
  cellTotal: {
    flex: 1.4,
    textAlign: "right",
    fontWeight: "600",
  },
  name: {
    fontSize: 14,
    color: "#111827",
    fontWeight: "500",
  },
  sku: {
    fontSize: 11,
    color: "#6b7280",
    marginTop: 2,
  },
});

export default QuoteList;
