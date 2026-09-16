import { useQuery } from "@tanstack/react-query";
import { getJobStatus } from "../api/preprocessing";
import type { JobStatus } from "../types/preprocessing";

export function useJobStatus(jobId: string | null) {
  return useQuery<JobStatus, Error>({
    queryKey: ["jobStatus", jobId],
    queryFn: async () => {
      if (!jobId) throw new Error("No job ID provided");
      return getJobStatus(jobId);
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed" || status === "cancelled") {
        return false;
      }
      return 1000;
    },
    refetchIntervalInBackground: false,
  });
}