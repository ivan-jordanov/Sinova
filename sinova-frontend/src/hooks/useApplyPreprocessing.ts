import { useMutation } from "@tanstack/react-query";
import { applyToStack } from "../api/preprocessing";
import type { JobStatus, PreprocessingConfig } from "../types/preprocessing";

export function useApplyPreprocessing() {
  return useMutation<
    JobStatus,
    Error,
    { configuration: PreprocessingConfig }
  >({
    mutationFn: (request) => applyToStack(request),
  });
}