import {
  ActionIcon,
  Button,
  Group,
  Modal,
  NumberInput,
  Text,
} from "@mantine/core";
import { useState } from "react";
import { usePreprocessingStore } from "../../store/preprocessingStore";
export function SliceSelector() {
  const { session, selectSlice, resetConfiguration } = usePreprocessingStore();
  const [pendingSlice, setPendingSlice] = useState<number | null>(null);
  const goToSlice = (slice: number) =>
    session.dirty ? setPendingSlice(slice) : selectSlice(slice);
  const confirm = () => {
    resetConfiguration();
    if (pendingSlice !== null) selectSlice(pendingSlice);
    setPendingSlice(null);
  };
  return (
    <>
      <Group gap={5}>
        <Text size="xs" c="dimmed">
          SLICE
        </Text>
        <NumberInput
          hideControls
          size="xs"
          w={72}
          value={session.selectedSlice}
          min={0}
          max={session.totalSlices - 1}
          onChange={(next) => goToSlice(Number(next) || 0)}
        />
        <Text size="xs" c="dimmed">
          / {session.totalSlices}
        </Text>
        <ActionIcon
          size="sm"
          variant="subtle"
          onClick={() => goToSlice(Math.max(0, session.selectedSlice - 1))}
          aria-label="Previous slice"
        >
          ‹
        </ActionIcon>
        <ActionIcon
          size="sm"
          variant="subtle"
          onClick={() =>
            goToSlice(
              Math.min(session.totalSlices - 1, session.selectedSlice + 1),
            )
          }
          aria-label="Next slice"
        >
          ›
        </ActionIcon>
      </Group>
      <Modal
        opened={pendingSlice !== null}
        onClose={() => setPendingSlice(null)}
        title="Unsaved changes"
      >
        <Text size="sm" c="dimmed">
          Changing the slice will discard the current preprocessing
          configuration.
        </Text>
        <Group justify="flex-end" mt="lg">
          <Button variant="default" onClick={() => setPendingSlice(null)}>
            Cancel
          </Button>
          <Button color="red" onClick={confirm}>
            Discard &amp; go
          </Button>
        </Group>
      </Modal>
    </>
  );
}
