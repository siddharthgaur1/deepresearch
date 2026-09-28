const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "dev-key";

function headers() {
  return { "Content-Type": "application/json", "x-api-key": API_KEY };
}

export interface JobStatus {
  job_id: string;
  query: string;
  status: string;
  error: string | null;
  total_cost_usd: number;
  total_tokens: number;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  id: number;
  url: string;
  title: string;
  verified: boolean;
}

export interface Report {
  id: string;
  job_id: string;
  markdown: string;
  citations: Citation[];
  sections: Record<string, string>;
  created_at: string;
}

export async function submitJob(query: string): Promise<{ job_id: string; status: string }> {
  const res = await fetch(`${API_URL}/jobs`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`Failed to submit job: ${res.status}`);
  return res.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${API_URL}/jobs/${jobId}`, { headers: headers() });
  if (!res.ok) throw new Error(`Failed to fetch job: ${res.status}`);
  return res.json();
}

export async function cancelJob(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${API_URL}/jobs/${jobId}/cancel`, { method: "POST", headers: headers() });
  if (!res.ok) throw new Error(`Failed to cancel job: ${res.status}`);
  return res.json();
}

export async function getStreamToken(jobId: string): Promise<string> {
  const res = await fetch(`${API_URL}/jobs/${jobId}/stream-token`, { method: "POST", headers: headers() });
  if (!res.ok) throw new Error(`Failed to fetch stream token: ${res.status}`);
  return (await res.json()).token;
}

export async function getReport(jobId: string): Promise<Report> {
  const res = await fetch(`${API_URL}/reports/${jobId}`, { headers: headers() });
  if (!res.ok) throw new Error(`Failed to fetch report: ${res.status}`);
  return res.json();
}

// A plain <a href> to /pdf can't send the x-api-key header, so fetch it and
// hand the browser the bytes instead.
export async function getReportPdf(jobId: string): Promise<Blob> {
  const res = await fetch(`${API_URL}/reports/${jobId}/pdf`, { headers: headers() });
  if (!res.ok) throw new Error(`Failed to fetch PDF: ${res.status}`);
  return res.blob();
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url)); // after the click's download has started
}
