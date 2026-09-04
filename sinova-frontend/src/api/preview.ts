import type { PreviewRequest, PreviewResult } from "../types/preview";

// The mock keeps the ArrayBuffer boundary used by the future FastAPI endpoint.
export async function getProjectionPreview(
  _request: PreviewRequest,
): Promise<PreviewResult> {
  return {
    context: "projection",
    width: 2,
    height: 2,
    data: new Float32Array([0, 0, 0, 0]).buffer,
    requestId: "mock",
  };
}
export async function getSinogramPreview(
  _request: PreviewRequest,
): Promise<PreviewResult> {
  return {
    context: "sinogram",
    width: 2,
    height: 2,
    data: new Float32Array([0, 0, 0, 0]).buffer,
    requestId: "mock",
  };
}
