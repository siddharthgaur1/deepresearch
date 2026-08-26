// Named websocket.ts to match the spec's file layout, but implemented over
// SSE (EventSource) since the backend streams via Server-Sent Events
// (backend/services/streaming.py) — one-directional server->client, no need
// for a full WebSocket round trip.

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface JobEvent {
  event: string;
  agent?: string;
  message: string;
  data?: Record<string, unknown>;
}

export function subscribeToJobEvents(jobId: string, onEvent: (event: JobEvent) => void): () => void {
  const source = new EventSource(`${API_URL}/jobs/${jobId}/events`);

  source.onmessage = (msg) => {
    try {
      onEvent(JSON.parse(msg.data) as JobEvent);
    } catch {
      // ignore malformed frames rather than tearing down the stream
    }
  };

  return () => source.close();
}
