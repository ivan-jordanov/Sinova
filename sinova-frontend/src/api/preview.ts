import type { PreviewRequest, PreviewResult } from "../types/preview";
import { apiClient } from "./client";

// The mock keeps the ArrayBuffer boundary used by the future FastAPI endpoint.
export async function getProjectionPreview(
  request: PreviewRequest,
): Promise<PreviewResult> {
  return requestPreview("/preview/projection", request);
}
export async function getSinogramPreview(
  request: PreviewRequest,
): Promise<PreviewResult> {
  return requestPreview("/preview/sinogram", request);
}

async function requestPreview(path: string, request: PreviewRequest): Promise<PreviewResult> {
  const response = await apiClient.request<{
    context: "projection" | "sinogram";
    width: number;
    height: number;
    data_format: string;
    dtype: string;
    data: number[];
    request_id: string;
    message: string;
  }>(path, { method: "POST", body: JSON.stringify(request) });
  return {
    context: response.context,
    width: response.width,
    height: response.height,
    data: new Float32Array(response.data).buffer,
    requestId: response.request_id,
    message: `${response.message} (${response.data_format}, ${response.dtype})`,
  };
}
