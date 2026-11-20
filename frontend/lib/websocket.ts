// Named websocket.ts to match the spec's file layout, but implemented over
// SSE (EventSource) since the backend streams via Server-Sent Events
// (backend/services/streaming.py) — one-directional server->client, no need
// for a full WebSocket round trip.

import { getStreamToken } from "./api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface JobEvent {
  event: string;
  agent?: string;
  message: string;
  data?: Record<string, unknown>;
}

export function subscribeToJobEvents(jobId: string, onEvent: (event: JobEvent) => void): () => void {
  let source: EventSource | null = null;
  let closed = false;

  // EventSource can't send the x-api-key header, so trade it for a
  // short-lived job-scoped token first. The token is only checked when the
  // stream opens, so on a dropped connection we fetch a fresh one instead of
  // letting EventSource retry with an expired token.
  const connect = async () => {
    let token: string;
    try {
      token = await getStreamToken(jobId);
    } catch {
      return; // the job page's status polling still tracks progress
    }
    if (closed) return;
    source = new EventSource(`${API_URL}/jobs/${jobId}/events?token=${encodeURIComponent(token)}`);
    source.onmessage = (msg) => {
      try {
        onEvent(JSON.parse(msg.data) as JobEvent);
      } catch {
        // ignore malformed frames rather than tearing down the stream
      }
    };
    source.onerror = () => {
      source?.close();
      if (!closed) setTimeout(connect, 2000);
    };
  };

  connect();

  return () => {
    closed = true;
    source?.close();
  };
}
