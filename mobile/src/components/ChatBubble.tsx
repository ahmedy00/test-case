import React from "react";
import { StyleSheet, Text, View } from "react-native";
import type { ChatMessage } from "../types";
import SourceChips from "./SourceChips";

type ChatBubbleProps = {
  message: ChatMessage;
  streaming?: boolean;
};

const ChatBubble: React.FC<ChatBubbleProps> = ({ message, streaming = false }) => {
  const isUser = message.role === "user";
  return (
    <View
      style={[
        styles.row,
        isUser ? styles.rowUser : styles.rowAssistant,
      ]}
    >
      <View
        style={[
          styles.bubble,
          isUser ? styles.bubbleUser : styles.bubbleAssistant,
        ]}
      >
        <Text style={styles.role}>{message.role}</Text>
        <Text style={isUser ? styles.bodyUser : styles.bodyAssistant}>
          {message.content.length > 0 ? message.content : streaming ? "…" : "(empty)"}
          {streaming && <Text style={styles.cursor}> ▍</Text>}
        </Text>
        {message.sources && <SourceChips sources={message.sources} />}
        {message.actions && message.actions.length > 0 && (
          <View style={styles.actions}>
            {message.actions.map((a, i) => (
              <View
                key={i}
                style={[
                  styles.action,
                  a.status === "success" ? styles.actionSuccess : styles.actionError,
                ]}
              >
                <Text style={styles.actionTool}>{a.tool}</Text>
                <Text style={styles.actionMsg}>{a.message}</Text>
              </View>
            ))}
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  row: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    flexDirection: "row",
  },
  rowUser: {
    justifyContent: "flex-end",
  },
  rowAssistant: {
    justifyContent: "flex-start",
  },
  bubble: {
    maxWidth: "85%",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderWidth: 1,
  },
  bubbleUser: {
    backgroundColor: "#2563eb",
    borderColor: "#1d4ed8",
  },
  bubbleAssistant: {
    backgroundColor: "#f9fafb",
    borderColor: "#e5e7eb",
  },
  role: {
    fontSize: 10,
    textTransform: "uppercase",
    letterSpacing: 0.6,
    marginBottom: 2,
    color: "#6b7280",
  },
  bodyUser: {
    color: "#ffffff",
    fontSize: 15,
    lineHeight: 21,
  },
  bodyAssistant: {
    color: "#111827",
    fontSize: 15,
    lineHeight: 21,
  },
  cursor: {
    color: "#9ca3af",
  },
  actions: {
    marginTop: 8,
    gap: 4,
  },
  action: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
  },
  actionSuccess: {
    backgroundColor: "#ecfdf5",
    borderColor: "#a7f3d0",
  },
  actionError: {
    backgroundColor: "#fef2f2",
    borderColor: "#fecaca",
  },
  actionTool: {
    fontSize: 11,
    fontWeight: "600",
    color: "#374151",
  },
  actionMsg: {
    fontSize: 12,
    color: "#374151",
    flexShrink: 1,
  },
});

export default ChatBubble;
