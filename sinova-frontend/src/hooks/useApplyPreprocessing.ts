import { useMutation } from "@tanstack/react-query";
import { applyToStack } from "../api/preprocessing";
import type { PreviewRequest } from "../types/preview";

export function useApplyPreprocessing() {
  return useMutation({
    mutationFn: (request: PreviewRequest) => applyToStack(request),
  });
}