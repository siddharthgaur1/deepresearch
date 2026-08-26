"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { submitJob } from "@/lib/api";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const { job_id } = await submitJob(query.trim());
      router.push(`/jobs/${job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit job");
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold">DeepResearch</h1>
        <p className="text-neutral-400 mt-2">
          Ask a research question. A team of agents will plan, search, verify, and write a cited report.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. What are the tradeoffs between RAG and fine-tuning for domain-specific chatbots?"
          rows={4}
          className="w-full rounded-lg border border-neutral-700 bg-neutral-900 p-3 text-sm focus:outline-none focus:border-neutral-500"
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={submitting || !query.trim()}
          className="self-start rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {submitting ? "Submitting…" : "Start Research"}
        </button>
      </form>
    </div>
  );
}
