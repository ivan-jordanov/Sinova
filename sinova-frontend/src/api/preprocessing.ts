import { apiClient } from "./client";

export interface JobStatus {
  id: string;
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  progress: number;
  message: string;
  current_operation: string | null;
  error: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export async function applyToStack(request: {
  configuration: unknown;
}): Promise<JobStatus> {
  return apiClient.request<JobStatus>("/preprocessing/apply", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  return apiClient.request<JobStatus>(`/preprocessing/status/${jobId}`);
}

export async function cancelJob(jobId: string): Promise<JobStatus> {
  return apiClient.request<JobStatus>(`/preprocessing/cancel/${jobId}`, {
    method: "POST",
  });
}

export async function getAvailableOperations() {
  return apiClient.request<unknown[]>("/preprocessing/operations");
}

export function getProcessingStatus() {
  return apiClient.request<{ status: string; job_id: string | null; message: string }>("/preprocessing/status");
}

// New: resolve an operation's broad-scope parameters (e.g. COR estimation)
// into concrete values. Call once, then store the result back into that
// operation's parameters in your preprocessing store -- preview/apply
// don't need to know anything changed.
export async function resolveOperation(request: {
  short_name: string;
  parameters: Record<string, unknown>;
  context: "projection" | "sinogram";
}): Promise<{ parameters: Record<string, unknown> }> {
  return apiClient.request<{ parameters: Record<string, unknown> }>(
    "/preprocessing/resolve",
    { method: "POST", body: JSON.stringify(request) }
  );
}
