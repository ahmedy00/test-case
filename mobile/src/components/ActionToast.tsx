import React, { useEffect } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import type { Action } from "../types";

type ActionToastProps = {
  action: Action | null;
  onDismiss: () => void;
};

const AUTO_DISMISS_MS = 4000;

const ActionToast: React.FC<ActionToastProps> = ({ action, onDismiss }) => {
  useEffect(() => {
    if (action === null) return;
    const id = setTimeout(onDismiss, AUTO_DISMISS_MS);
    return () => clearTimeout(id);
  }, [action, onDismiss]);

  if (action === null) return null;

  return (
    <View
      style={[
        styles.container,
        action.status === "success" ? styles.success : styles.error,
      ]}
      accessibilityLiveRegion="polite"
    >
      <Text style={styles.tool}>{action.tool}</Text>
      <Text style={styles.message} numberOfLines={2}>
        {action.message}
      </Text>
      <Pressable
        onPress={onDismiss}
        accessibilityLabel="Dismiss action notification"
        style={({ pressed }) => [styles.dismiss, pressed && styles.dismissPressed]}
      >
        <Text style={styles.dismissText}>×</Text>
      </Pressable>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    margin: 12,
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
  },
  success: {
    backgroundColor: "#ecfdf5",
    borderColor: "#a7f3d0",
  },
  error: {
    backgroundColor: "#fef2f2",
    borderColor: "#fecaca",
  },
  tool: {
    fontSize: 12,
    fontWeight: "700",
    color: "#1f2937",
  },
  message: {
    fontSize: 13,
    color: "#1f2937",
    flex: 1,
  },
  dismiss: {
    width: 24,
    height: 24,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 12,
  },
  dismissPressed: {
    backgroundColor: "rgba(0,0,0,0.06)",
  },
  dismissText: {
    fontSize: 18,
    color: "#6b7280",
    lineHeight: 18,
  },
});

export default ActionToast;
