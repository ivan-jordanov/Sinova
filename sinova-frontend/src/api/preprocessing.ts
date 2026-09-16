import { apiClient } from "./client";
import type { JobStatus } from "../types/preprocessing";

export async function applyToStack(request: {
  configuration: unknown;
}): Promise<JobStatus> {
  console.log("applyToStack request:", request);
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