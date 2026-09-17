import { useMutation, useQueryClient } from "@tanstack/react-query";
import { cancelJob } from "../api/preprocessing";
import type { JobStatus } from "../types/preprocessing";

export function useCancelJob() {
  const queryClient = useQueryClient();

  return useMutation<JobStatus, Error, string>({
    mutationFn: (jobId: string) => cancelJob(jobId),
    onSuccess: (data, jobId) => {
      // Instantly update the cached jobStatus so polling stops and UI reflects cancellation
      queryClient.setQueryData(["jobStatus", jobId], data);
      
      // Invalidate query to trigger a background refetch if needed
      queryClient.invalidateQueries({ queryKey: ["jobStatus", jobId] });
    },
  });
}