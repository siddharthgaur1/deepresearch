"use client";

import { useEffect, useState } from "react";
import { subscribeToJobEvents, type JobEvent } from "@/lib/websocket";

export default function AgentFeed({ jobId }: { jobId: string }) {
  const [events, setEvents] = useState<JobEvent[]>([]);

  useEffect(() => {
    return subscribeToJobEvents(jobId, (event) => {
      setEvents((prev) => [...prev, event].slice(-100));
    });
  }, [jobId]);

  return (
    <div className="flex flex-col gap-1 rounded-lg border border-neutral-800 p-4 max-h-96 overflow-y-auto">
      <h3 className="font-semibold text-sm text-neutral-400 mb-2">Agent Activity</h3>
      {events.length === 0 && <p className="text-neutral-500 text-sm">Waiting for updates…</p>}
      {events.map((e, i) => (
        <div key={i} className="text-sm flex gap-2">
          <span className="text-neutral-500">{e.agent ?? e.event}</span>
          <span>{e.message}</span>
        </div>
      ))}
    </div>
  );
}
