"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { use } from "react";
import { cancelJob, getJobStatus } from "@/lib/api";
import AgentFeed from "@/components/AgentFeed";
import ProgressBar from "@/components/ProgressBar";

export default function JobPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();

  const { data: job } = useQuery({
    queryKey: ["job", id],
    queryFn: () => getJobStatus(id),
    refetchInterval: (query) => (query.state.data?.status === "done" ? false : 2000),
  });

  if (job?.status === "done") {
    router.replace(`/reports/${id}`);
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">{job?.query ?? "Loading…"}</h1>
        <p className="text-sm text-neutral-500 mt-1">Job {id}</p>
      </div>

      {job && <ProgressBar status={job.status} />}

      {job && job.status !== "done" && job.status !== "failed" && job.status !== "cancelled" && (
        <button
          onClick={() => cancelJob(id)}
          className="self-start text-sm rounded-md border border-red-800 text-red-400 px-3 py-1.5 hover:bg-red-950"
        >
          Cancel
        </button>
      )}

      {job?.error && <p className="text-sm text-red-400">{job.error}</p>}

      <AgentFeed jobId={id} />

      {job && (
        <p className="text-xs text-neutral-500">
          {job.total_tokens.toLocaleString()} tokens · ${job.total_cost_usd.toFixed(4)}
        </p>
      )}
    </div>
  );
}
