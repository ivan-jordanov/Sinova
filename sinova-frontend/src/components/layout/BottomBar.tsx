import { Button, Group, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useEffect, useRef, useState } from "react";
import { usePreprocessingStore } from "../../store/preprocessingStore";
import { ApplyStackDialog } from "../session/ApplyStackDialog";
import { useApplyPreprocessing } from "../../hooks/useApplyPreprocessing";
import { useJobStatus } from "../../hooks/useJobStatus";

export function BottomBar() {
  const [opened, setOpened] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const notifiedRef = useRef<string | null>(null);

  const { operations, session, past, future, undo, redo } = usePreprocessingStore();
  const apply = useApplyPreprocessing();
  const jobStatus = useJobStatus(jobId);

  const isJobRunning =
    jobStatus.data?.status === "queued" || jobStatus.data?.status === "running";

  useEffect(() => {
    if (!jobStatus.data || !jobId) return;

    const currentKey = `${jobId}-${jobStatus.data.status}`;
    if (notifiedRef.current === currentKey) return;

    const status = jobStatus.data.status;

    if (status === "completed" || status === "failed") {
      if (status === "completed") {
        notifications.show({
          title: "Processing Complete",
          message: "Processed stack saved to ./data/exports",
          color: "green",
          autoClose: 5000,
        });
      } else {
        notifications.show({
          title: "Processing Failed",
          message:
            jobStatus.data.error ||
            jobStatus.data.message ||
            "An unknown error occurred during preprocessing",
          color: "red",
          autoClose: 5000,
        });
      }

      notifiedRef.current = currentKey;

      // Automatically hide the status indicator after 5 seconds
      const timer = setTimeout(() => {
        setJobId(null);
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [jobStatus.data, jobId]);

  const handleOpenDialog = () => {
    apply.reset();
    setOpened(true);
  };

  const handleApply = () => {
    apply.mutate(
      { configuration: { operations } },
      {
        onSuccess: (response) => {
          setJobId(response.id);
          setOpened(false);
        },
        onError: (err) => {
          notifications.show({
            title: "Submission Error",
            message: err.message || "Failed to submit job to server",
            color: "red",
          });
        },
      },
    );
  };

  const getStatusColor = (status?: string) => {
    if (status === "failed") return "red";
    if (status === "completed") return "green";
    return "blue";
  };

  const message =
    jobStatus.data?.error ||
    jobStatus.data?.message ||
    apply.data?.message ||
    apply.error?.message;

  return (
    <>
      <Group className="bottom-bar" justify="space-between" px="lg">
        <Group gap="md">
          <span className="live-dot" />
          <Text size="sm">
            Preview mode{" "}
            <Text span c="dimmed">
              · changes apply to current slice only
            </Text>
          </Text>
          {session.dirty && (
            <Text size="xs" c="yellow">
              UNSAVED
            </Text>
          )}
          {jobStatus.data && (
            <Text size="xs" c={getStatusColor(jobStatus.data.status)}>
              Job: {jobStatus.data.status} ({jobStatus.data.progress}%)
            </Text>
          )}
        </Group>
        <Group gap="xs">
          <Button
            size="xs"
            variant="subtle"
            disabled={!past.length}
            onClick={undo}
          >
            Undo
          </Button>
          <Button
            size="xs"
            variant="subtle"
            disabled={!future.length}
            onClick={redo}
          >
            Redo
          </Button>
          <Button
            size="xs"
            onClick={handleOpenDialog}
            disabled={apply.isPending || isJobRunning}
          >
            Apply to entire stack ↗
          </Button>
        </Group>
      </Group>
      <ApplyStackDialog
        opened={opened}
        onClose={() => setOpened(false)}
        onApply={handleApply}
        isPending={apply.isPending}
        message={message}
      />
    </>
  );
}