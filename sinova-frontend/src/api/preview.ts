import type { PreviewRequest, PreviewResult } from "../types/preview";
import { apiClient } from "./client";
import type { PreviewParams } from "../types/preview";
import type { PreprocessingOperation } from "../types/preprocessing";

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
    operations?: PreprocessingOperation[];
  }>(path, { method: "POST", body: JSON.stringify(request) });

  // Due to me trying to fix a bug to implement a feature which caused too many server-state and client-state mismatches, we now have to normalize the operations returned by the backend to ensure that they have the correct property names. This is a temporary fix until the backend is updated to return the correct property names.
  // However, we dont need to return operations necessarily so rewrite the frontend and backend in the future to fix this
  const rawOps = response.operations ?? request.configuration.operations;
  const normalizedOps = rawOps?.map((op: any) => ({
    ...op,
    shortName: op.shortName ?? op.short_name,
  }));

  return {
    context: response.context,
    width: response.width,
    height: response.height,
    data: new Float32Array(response.data),
    minVal: response.min_value,
    maxVal: response.max_value,
    requestId: response.request_id,
    message: `${response.message} (${response.data_format}, ${response.dtype})`,
    operations: normalizedOps,
  };
}