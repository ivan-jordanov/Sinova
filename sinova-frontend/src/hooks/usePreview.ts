import { useQuery } from "@tanstack/react-query";
import { getProjectionPreview, getSinogramPreview } from "../api/preview";
import type { PreviewRequest } from "../types/preview";

export function usePreview(request: PreviewRequest) {
  return useQuery({
    queryKey: ["preview", request],
    queryFn: () =>
      request.context === "projection"
        ? getProjectionPreview(request)
        : getSinogramPreview(request),
    retry: false,
  });
}