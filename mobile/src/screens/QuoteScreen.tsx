import React, { useCallback, useState } from "react";
import {
  Alert,
  Platform,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import QuoteList from "../components/QuoteList";
import { useActiveQuote } from "../hooks/useActiveQuote";
import { resetSession } from "../session";

const QuoteScreen: React.FC = () => {
  const quote = useActiveQuote();
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const onRefresh = useCallback(async (): Promise<void> => {
    setRefreshing(true);
    await quote.reloadSession();
    quote.refresh();
    // Allow the spinner to be visible briefly while the request flies.
    setTimeout(() => setRefreshing(false), 400);
  }, [quote]);

  const onReset = useCallback((): void => {
    const doReset = async (): Promise<void> => {
      await resetSession();
      await quote.reloadSession();
    };

    if (Platform.OS === "web") {
      // Alert.alert with buttons is a no-op on web; use confirm() instead.
      const confirmed =
        typeof window !== "undefined" && typeof window.confirm === "function"
          ? window.confirm("Reset the current session? This clears the local session id.")
          : true;
      if (confirmed) void doReset();
      return;
    }

    Alert.alert(
      "Reset session",
      "Clear the local session id? Your draft quote will be replaced on next message.",
      [
        { text: "Cancel", style: "cancel" },
        { text: "Reset", style: "destructive", onPress: () => void doReset() },
      ],
    );
  }, [quote]);

  const truncatedSession =
    quote.sessionId === null
      ? "—"
      : `${quote.sessionId.slice(0, 8)}…${quote.sessionId.slice(-4)}`;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.headerLabel}>session</Text>
          <Text style={styles.headerValue}>{truncatedSession}</Text>
        </View>
        <Pressable
          onPress={onReset}
          disabled={quote.sessionId === null}
          style={({ pressed }) => [
            styles.resetButton,
            quote.sessionId === null && styles.resetButtonDisabled,
            pressed && styles.resetButtonPressed,
          ]}
        >
          <Text style={styles.resetButtonText}>Reset session</Text>
        </Pressable>
      </View>

      {!quote.sessionLoaded && (
        <View style={styles.notice}>
          <Text style={styles.noticeText}>Loading session…</Text>
        </View>
      )}

      {quote.sessionLoaded && quote.sessionId === null && (
        <View style={styles.notice}>
          <Text style={styles.noticeText}>
            No session yet — send your first chat message to start a quote.
          </Text>
        </View>
      )}

      {quote.error !== null && quote.sessionId !== null && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>Failed to load quote: {quote.error}</Text>
        </View>
      )}

      {quote.sessionId !== null && (
        <>
          <View style={styles.summary}>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryLabel}>Quote</Text>
              <Text style={styles.summaryValue}>
                {quote.quote === null ? "—" : `#${quote.quote.id}`}
              </Text>
            </View>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryLabel}>Items</Text>
              <Text style={styles.summaryValue}>
                {quote.quote?.item_count ?? 0}
              </Text>
            </View>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryLabel}>Subtotal</Text>
              <Text style={styles.summaryValue}>
                ${quote.quote?.subtotal ?? "0.00"}
              </Text>
            </View>
          </View>

          <View style={styles.list}>
            <QuoteList quote={quote.quote} />
          </View>
        </>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  content: {
    paddingBottom: 32,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#e5e7eb",
  },
  headerLeft: {
    flex: 1,
  },
  headerLabel: {
    fontSize: 11,
    color: "#6b7280",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  headerValue: {
    fontSize: 14,
    color: "#111827",
    fontFamily: Platform.select({ ios: "Menlo", android: "monospace", default: "monospace" }),
    marginTop: 2,
  },
  resetButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d1d5db",
    backgroundColor: "#ffffff",
  },
  resetButtonDisabled: {
    opacity: 0.5,
  },
  resetButtonPressed: {
    backgroundColor: "#f3f4f6",
  },
  resetButtonText: {
    color: "#374151",
    fontSize: 13,
    fontWeight: "500",
  },
  notice: {
    padding: 24,
    alignItems: "center",
  },
  noticeText: {
    color: "#6b7280",
    textAlign: "center",
    fontSize: 14,
  },
  errorBox: {
    margin: 12,
    padding: 12,
    backgroundColor: "#fef2f2",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#fecaca",
  },
  errorText: {
    color: "#991b1b",
    fontSize: 13,
  },
  summary: {
    flexDirection: "row",
    padding: 12,
    gap: 12,
  },
  summaryItem: {
    flex: 1,
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    backgroundColor: "#f9fafb",
  },
  summaryLabel: {
    fontSize: 10,
    color: "#6b7280",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  summaryValue: {
    fontSize: 16,
    color: "#111827",
    fontWeight: "600",
    marginTop: 2,
  },
  list: {
    marginTop: 4,
    borderTopWidth: 1,
    borderTopColor: "#e5e7eb",
  },
});

export default QuoteScreen;
