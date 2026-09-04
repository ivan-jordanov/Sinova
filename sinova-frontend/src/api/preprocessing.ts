import type { PreviewRequest, PreviewResult } from "../types/preview";
import { getProjectionPreview, getSinogramPreview } from "./preview";
export async function previewProcessing(
  request: PreviewRequest,
): Promise<PreviewResult> {
  return request.context === "projection"
    ? getProjectionPreview(request)
    : getSinogramPreview(request);
}
export async function applyToStack(
  _request: PreviewRequest,
): Promise<{ jobId: string }> {
  return { jobId: "mock-job" };
}
