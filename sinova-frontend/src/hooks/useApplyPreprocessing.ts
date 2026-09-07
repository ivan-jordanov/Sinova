import { useMutation } from "@tanstack/react-query";
import { applyToStack } from "../api/preprocessing";
import type { JobStatus } from "../api/preprocessing";

export function useApplyPreprocessing() {
  return useMutation<
    JobStatus,
    Error,
    { configuration: unknown },
    unknown
  >({
    mutationFn: (request) => applyToStack(request),
  });
}