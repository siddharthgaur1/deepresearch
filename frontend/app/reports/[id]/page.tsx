"use client";

import { useQuery } from "@tanstack/react-query";
import { use } from "react";
import { getReport } from "@/lib/api";
import ReportViewer from "@/components/ReportViewer";

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  const { data: report, isLoading, error } = useQuery({
    queryKey: ["report", id],
    queryFn: () => getReport(id),
    retry: 3,
  });

  if (isLoading) return <p className="text-neutral-500">Loading report…</p>;
  if (error) return <p className="text-red-400">Report not ready yet — the job may still be running.</p>;
  if (!report) return null;

  return <ReportViewer report={report} />;
}
