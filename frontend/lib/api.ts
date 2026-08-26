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

export async function getReport(jobId: string): Promise<Report> {
  const res = await fetch(`${API_URL}/reports/${jobId}`, { headers: headers() });
  if (!res.ok) throw new Error(`Failed to fetch report: ${res.status}`);
  return res.json();
}

export function reportPdfUrl(jobId: string): string {
  return `${API_URL}/reports/${jobId}/pdf`;
}
