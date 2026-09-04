import { useQuery } from "@tanstack/react-query";
import { getBackendHealth } from "../api/dataset";

export function useBackendHealth() {
  return useQuery({
    queryKey: ["backend", "health"],
    queryFn: getBackendHealth,
    retry: false,
    refetchInterval: 10_000,
  });
}