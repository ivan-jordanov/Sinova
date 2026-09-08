import { useQuery } from "@tanstack/react-query";
import { getProjectionPreview, getSinogramPreview } from "../api/preview";
import type { DataContext } from "../types/preprocessing";
import type { PreviewParams } from "../types/preview";

type UsePreviewParams = PreviewParams & { context: DataContext };

export function usePreview(request: UsePreviewParams, enabled: boolean = true) {
  return useQuery({
    queryKey: ["preview", request.context, request.slice, request.configuration, request.mode],
    queryFn: () =>
      request.context === "projection"
        ? getProjectionPreview(request)
        : getSinogramPreview(request),
    enabled,
    retry: false,
  });
}