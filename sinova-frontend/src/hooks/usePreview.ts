import { useQuery } from "@tanstack/react-query";
import { getProjectionPreview, getSinogramPreview } from "../api/preview";
import type { DataContext } from "../types/preprocessing";
import type { PreviewParams } from "../types/preview";

type UsePreviewParams = PreviewParams & { context: DataContext };

export function usePreview(request: UsePreviewParams, enabled: boolean = true) {
  const isOriginal = request.mode === "original";

  // Isolate active enabled operations so disabled ops don't bust the cache
  const activeOperations = isOriginal
    ? null
    : request.configuration?.operations
        ?.filter((op) => op.enabled)
        .map((op) => ({
          shortName: op.shortName,
          parameters: op.parameters,
        }));

  return useQuery({
    queryKey: [
      "preview",
      request.context,
      request.slice,
      request.mode,
      activeOperations,
    ],

    queryFn: () =>
      request.context === "projection"
        ? getProjectionPreview(request)
        : getSinogramPreview(request),

    enabled,

    // Caching configuration
    staleTime: Infinity,           // Keep fetched slices fresh indefinitely in memory
    gcTime: 1000 * 60 * 15,        // Retain unmounted slices for 15 minutes before garbage collection
    refetchOnWindowFocus: false,  // Prevent automatic re-fetching on tab switch
    retry: false,
  });
}