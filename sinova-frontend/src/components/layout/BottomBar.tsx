import { Button, Group, Text } from "@mantine/core";
import { useState } from "react";
import { usePreprocessingStore } from "../../store/preprocessingStore";
import { ApplyStackDialog } from "../session/ApplyStackDialog";
import { useApplyPreprocessing } from "../../hooks/useApplyPreprocessing";
import { useJobStatus } from "../../hooks/useJobStatus";

export function BottomBar() {
  const [opened, setOpened] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const { operations, session, past, future, undo, redo } = usePreprocessingStore();
  const apply = useApplyPreprocessing();
  const jobStatus = useJobStatus(jobId);

  const handleApply = () => {
    apply.mutate(
      { configuration: { operations } },
      {
        onSuccess: (response) => {
          setJobId(response.id);
          setOpened(false);
        },
      },
    );
  };

  const message = jobStatus.data?.message || apply.data?.message || apply.error?.message;

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
            <Text size="xs" c="blue">
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
          <Button size="xs" onClick={() => setOpened(true)} disabled={!!jobId}>
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
