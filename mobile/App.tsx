import React, { useCallback, useState } from "react";
import { Platform, Pressable, SafeAreaView, StatusBar, StyleSheet, Text, View } from "react-native";
import ChatScreen from "./src/screens/ChatScreen";
import QuoteScreen from "./src/screens/QuoteScreen";

type Tab = "chat" | "quote";

const App: React.FC = () => {
  const [tab, setTab] = useState<Tab>("chat");
  // Bumping `key` on the QuoteScreen makes it re-mount when a brand-new
  // session id is established by the chat stream — that re-runs the AsyncStorage
  // read so the quote starts polling without waiting for the user to refresh.
  const [quoteKey, setQuoteKey] = useState<number>(0);

  const handleSessionEstablished = useCallback((_sessionId: string) => {
    setQuoteKey((k) => k + 1);
  }, []);

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.appBar}>
        <Text style={styles.title}>B2B Sales Assistant</Text>
        <View style={styles.segment}>
          <SegmentButton
            label="Chat"
            active={tab === "chat"}
            onPress={() => setTab("chat")}
          />
          <SegmentButton
            label="Quote"
            active={tab === "quote"}
            onPress={() => setTab("quote")}
          />
        </View>
      </View>

      <View style={styles.body}>
        {tab === "chat" ? (
          <ChatScreen onSessionEstablished={handleSessionEstablished} />
        ) : (
          <QuoteScreen key={quoteKey} />
        )}
      </View>
    </SafeAreaView>
  );
};

const SegmentButton: React.FC<{
  label: string;
  active: boolean;
  onPress: () => void;
}> = ({ label, active, onPress }) => (
  <Pressable
    onPress={onPress}
    style={({ pressed }) => [
      styles.segmentButton,
      active && styles.segmentButtonActive,
      pressed && !active && styles.segmentButtonPressed,
    ]}
  >
    <Text
      style={[styles.segmentLabel, active && styles.segmentLabelActive]}
    >
      {label}
    </Text>
  </Pressable>
);

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: "#ffffff",
    // SafeAreaView on Android does not auto-pad the status bar.
    paddingTop: Platform.OS === "android" ? 24 : 0,
  },
  appBar: {
    paddingHorizontal: 12,
    paddingTop: 8,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#e5e7eb",
    gap: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111827",
  },
  segment: {
    flexDirection: "row",
    backgroundColor: "#f3f4f6",
    borderRadius: 8,
    padding: 2,
  },
  segmentButton: {
    flex: 1,
    paddingVertical: 8,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 6,
  },
  segmentButtonActive: {
    backgroundColor: "#ffffff",
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 1,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1,
  },
  segmentButtonPressed: {
    backgroundColor: "#e5e7eb",
  },
  segmentLabel: {
    fontSize: 14,
    color: "#6b7280",
    fontWeight: "500",
  },
  segmentLabelActive: {
    color: "#111827",
    fontWeight: "600",
  },
  body: {
    flex: 1,
  },
});

export default App;
