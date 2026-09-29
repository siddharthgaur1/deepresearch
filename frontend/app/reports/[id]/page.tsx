"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { getReport } from "@/lib/api";
import ReportViewer from "@/components/ReportViewer";

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();

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
