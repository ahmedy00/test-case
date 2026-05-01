import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import ActionToast from "../components/ActionToast";
import ChatBubble from "../components/ChatBubble";
import { useSseChat } from "../hooks/useSseChat";
import type { ChatMessage } from "../types";

type ChatScreenProps = {
  onSessionEstablished: (sessionId: string) => void;
};

type RenderItem = ChatMessage & { _key: string };

const ChatScreen: React.FC<ChatScreenProps> = ({ onSessionEstablished }) => {
  const [draft, setDraft] = useState<string>("");
  const listRef = useRef<FlatList<RenderItem>>(null);

  const chat = useSseChat({ onSessionEstablished });
  const isStreaming = chat.state.status === "streaming";

  const data: RenderItem[] = chat.state.messages.map((m, i) => ({
    ...m,
    _key: `m-${i}`,
  }));
  if (isStreaming) {
    data.push({
      _key: "streaming",
      role: "assistant",
      content: chat.state.currentAssistantText,
      sources: chat.state.currentSources ?? undefined,
    });
  }

  useEffect(() => {
    if (data.length > 0) {
      requestAnimationFrame(() => {
        listRef.current?.scrollToEnd({ animated: true });
      });
    }
  }, [data.length, chat.state.currentAssistantText]);

  const onSend = useCallback(async (): Promise<void> => {
    const text = draft.trim();
    if (text.length === 0 || isStreaming) return;
    setDraft("");
    await chat.send(text);
  }, [draft, chat, isStreaming]);

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ActionToast
        action={chat.state.latestAction}
        onDismiss={chat.clearLatestAction}
      />

      {data.length === 0 && !isStreaming && (
        <View style={styles.empty}>
          <Text style={styles.emptyTitle}>Start chatting</Text>
          <Text style={styles.emptyHint}>
            Try: "What laptops do you offer?" or "Add 2 ThinkBooks to my quote."
          </Text>
        </View>
      )}

      <FlatList
        ref={listRef}
        style={styles.list}
        contentContainerStyle={styles.listContent}
        data={data}
        keyExtractor={(item) => item._key}
        renderItem={({ item }) => (
          <ChatBubble message={item} streaming={item._key === "streaming"} />
        )}
        onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: false })}
      />

      {chat.state.error !== null && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{chat.state.error}</Text>
        </View>
      )}

      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          placeholder="Ask about products, policies, or pricing…"
          placeholderTextColor="#9ca3af"
          value={draft}
          onChangeText={setDraft}
          editable={!isStreaming}
          multiline
          onSubmitEditing={() => {
            void onSend();
          }}
          returnKeyType="send"
          blurOnSubmit
        />
        <Pressable
          onPress={() => {
            void onSend();
          }}
          disabled={isStreaming || draft.trim().length === 0}
          style={({ pressed }) => [
            styles.sendButton,
            (isStreaming || draft.trim().length === 0) && styles.sendButtonDisabled,
            pressed && styles.sendButtonPressed,
          ]}
        >
          {isStreaming ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.sendButtonText}>Send</Text>
          )}
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  empty: {
    padding: 24,
    alignItems: "center",
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 4,
  },
  emptyHint: {
    fontSize: 13,
    color: "#6b7280",
    textAlign: "center",
  },
  list: {
    flex: 1,
  },
  listContent: {
    paddingVertical: 8,
  },
  errorBox: {
    backgroundColor: "#fef2f2",
    borderTopWidth: 1,
    borderTopColor: "#fecaca",
    padding: 10,
  },
  errorText: {
    color: "#991b1b",
    fontSize: 13,
  },
  inputBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    padding: 8,
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: "#e5e7eb",
    backgroundColor: "#ffffff",
  },
  input: {
    flex: 1,
    minHeight: 40,
    maxHeight: 120,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 8,
    fontSize: 15,
    color: "#111827",
    backgroundColor: "#f9fafb",
  },
  sendButton: {
    backgroundColor: "#2563eb",
    paddingHorizontal: 16,
    height: 40,
    minWidth: 64,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  sendButtonDisabled: {
    backgroundColor: "#9ca3af",
  },
  sendButtonPressed: {
    backgroundColor: "#1d4ed8",
  },
  sendButtonText: {
    color: "#ffffff",
    fontWeight: "600",
    fontSize: 14,
  },
});

export default ChatScreen;
