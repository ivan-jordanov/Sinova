import { useQuery } from "@tanstack/react-query";
import { getJobStatus } from "../api/preprocessing";
import type { JobStatus } from "../api/preprocessing";

export function useJobStatus(jobId: string | null) {
  return useQuery<JobStatus, Error>({
    queryKey: ["jobStatus", jobId],
    queryFn: async () => {
      if (!jobId) throw new Error("No job ID");
      return getJobStatus(jobId);
    },
    enabled: !!jobId,
    refetchInterval: 1000, // Poll every 1 second
    refetchIntervalInBackground: false,
  });
}
