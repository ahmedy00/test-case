import AsyncStorage from "@react-native-async-storage/async-storage";

const KEY = "b2b_sales_session_id";

export async function getStoredSessionId(): Promise<string | null> {
  return AsyncStorage.getItem(KEY);
}

export async function storeSessionId(id: string): Promise<void> {
  await AsyncStorage.setItem(KEY, id);
}

export async function resetSession(): Promise<void> {
  await AsyncStorage.removeItem(KEY);
}
