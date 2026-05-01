# Mobile (Expo)

React Native client for the B2B Sales Assistant. Two screens — Chat and Quote — share an anonymous session UUID with the web client via the backend so the same active draft quote shows up on both surfaces.

## Quick start

```bash
cd mobile
cp .env.example .env          # tweak EXPO_PUBLIC_API_BASE_URL if needed
npm install
npx expo start
```

Then choose a target:

- Press `w` — opens the web target at `http://localhost:8081`.
- Press `i` — iOS Simulator (macOS only).
- Press `a` — Android Emulator.
- Scan the QR code with Expo Go on a physical phone (same Wi-Fi).

## `EXPO_PUBLIC_API_BASE_URL` matrix

The backend listens on `http://localhost:8000` from the host machine. Mobile clients see "localhost" differently depending on where they run:

| Target              | Value                            |
|---------------------|----------------------------------|
| Web (`w`)           | `http://localhost:8000`          |
| iOS Simulator       | `http://localhost:8000`          |
| Android Emulator    | `http://10.0.2.2:8000`           |
| Physical device     | `http://<your-LAN-IP>:8000`      |

Find your LAN IP with `ipconfig` (Windows) or `ifconfig` / `ip addr` (mac/linux). Expo CLI also prints the dev-server URL above the QR code — your machine's IP appears there.

After editing `.env`, restart the Expo dev server (the env var is embedded at bundle build time, not read at runtime).

## CORS

The backend's `BACKEND_CORS_ORIGINS` already includes `http://localhost:8081` (Expo Metro web target) and `http://localhost:19006` (legacy Expo web). For physical-device requests, React Native's `XMLHttpRequest` does not send an `Origin` header, and FastAPI's CORS middleware allows missing-origin requests through, so no extra CORS config is needed.

## Architecture notes

- **SSE on RN**: Uses `XMLHttpRequest` with `onreadystatechange` / `LOADING` to consume the chat stream incrementally. RN's `fetch` does not expose `response.body` as a `ReadableStream` reliably across iOS, Android and the web target. The library `react-native-sse` is GET-only, so it doesn't fit our POST endpoint without a backend change.
- **Storage**: `@react-native-async-storage/async-storage` for the session UUID. Same key (`b2b_sales_session_id`) as the web client so cross-surface sync works when both surfaces are pointed at the same session.
- **Polling**: Quote screen polls `/quotes/active` every 3s, matching the web behavior.
- **No navigation library**: Two screens with a `useState`-driven segmented control is enough.

## Cross-surface sync demo

1. Boot backend + web: `docker compose up -d db backend web`.
2. Start Expo: `cd mobile && npx expo start`, then `w` for the web target.
3. In the Expo web target, send any chat message — this establishes a session and the value gets stored in `AsyncStorage` under `b2b_sales_session_id`.
4. Read the session id (Quote screen header shows a truncated form; full id is in `localStorage.b2b_sales_session_id` since the web target uses localStorage as the AsyncStorage backing store).
5. Open `http://localhost:5173` in another tab. In devtools console run `localStorage.setItem("b2b_sales_session_id", "<paste-id>")` and reload.
6. Add an item from either surface; the other reflects it within ~3 seconds.
