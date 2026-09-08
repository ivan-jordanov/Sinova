import type { PreviewRequest, PreviewResult } from "../types/preview";
import { apiClient } from "./client";
import type { PreviewParams } from "../types/preview";

export async function getProjectionPreview(
  params: PreviewParams
): Promise<PreviewResult> {
  return requestPreview("/preview/projection", {
    context: "projection",
    mode: params.mode ?? "original",
    slice: params.slice,
    configuration: params.configuration,
  });
}

export async function getSinogramPreview(
  params: PreviewParams
): Promise<PreviewResult> {
  return requestPreview("/preview/sinogram", {
    context: "sinogram",
    mode: params.mode ?? "original",
    slice: params.slice,
    configuration: params.configuration,
  });
}

export async function requestPreview(
  path: string,
  request: PreviewRequest
): Promise<PreviewResult> {
  const response = await apiClient.request<{
    context: "projection" | "sinogram";
    width: number;
    height: number;
    data_format: string;
    dtype: string;
    data: number[];
    min_value?: number;
    max_value?: number;
    request_id: string;
    message: string;
  }>(path, { method: "POST", body: JSON.stringify(request) });

  return {
    context: response.context,
    width: response.width,
    height: response.height,
    data: new Float32Array(response.data),
    minVal: response.min_value,
    maxVal: response.max_value,
    requestId: response.request_id,
    message: `${response.message} (${response.data_format}, ${response.dtype})`,
  };
}