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
