import type { PreviewRequest, PreviewResult } from "../types/preview";
import { apiClient } from "./client";
import { getProjectionPreview, getSinogramPreview } from "./preview";
export async function previewProcessing(
  request: PreviewRequest,
): Promise<PreviewResult> {
  return request.context === "projection"
    ? getProjectionPreview(request)
    : getSinogramPreview(request);
}
export async function applyToStack(
  request: PreviewRequest,
): Promise<{ jobId: string; status: string; message: string }> {
  const response = await apiClient.request<{ job_id: string; status: string; message: string }>(
    "/preprocessing/apply",
    { method: "POST", body: JSON.stringify({ configuration: request.configuration }) },
  );
  return { jobId: response.job_id, status: response.status, message: response.message };
}

export function getProcessingStatus() {
  return apiClient.request<{ status: string; job_id: string | null; message: string }>("/preprocessing/status");
}
