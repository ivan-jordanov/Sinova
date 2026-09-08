import {
  ActionIcon,
  Button,
  Group,
  Modal,
  NumberInput,
  Text,
} from "@mantine/core";
import { useEffect, useState } from "react";
import { usePreprocessingStore } from "../../store/preprocessingStore";

export function SliceSelector() {
  const { session, selectSlice, resetConfiguration } = usePreprocessingStore();
  const [pendingSlice, setPendingSlice] = useState<number | null>(null);
  const [localSlice, setLocalSlice] = useState<number | string>(session.selectedSlice);

  // Synchronize local input state when active store slice updates
  useEffect(() => {
    setLocalSlice(session.selectedSlice);
  }, [session.selectedSlice]);

  const goToSlice = (targetSlice: number) => {
    const maxSlice = Math.max(0, session.totalSlices - 1);
    const clampedSlice = Math.max(0, Math.min(targetSlice, maxSlice));

    if (clampedSlice === session.selectedSlice) {
      setLocalSlice(session.selectedSlice);
      return;
    }

    if (session.dirty) {
      setPendingSlice(clampedSlice);
    } else {
      selectSlice(clampedSlice);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      const parsed = typeof localSlice === "number" ? localSlice : parseInt(localSlice, 10);
      goToSlice(isNaN(parsed) ? 0 : parsed);
    }
  };

  const confirm = () => {
    resetConfiguration();
    if (pendingSlice !== null) selectSlice(pendingSlice);
    setPendingSlice(null);
  };

  const cancel = () => {
    setPendingSlice(null);
    setLocalSlice(session.selectedSlice);
  };

  const maxSlice = Math.max(0, session.totalSlices - 1);

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
          value={localSlice}
          min={0}
          max={maxSlice}
          onChange={(val) => setLocalSlice(val)}
          onKeyDown={handleKeyDown}
        />
        <Text size="xs" c="dimmed">
          / {session.totalSlices}
        </Text>
        <ActionIcon
          size="sm"
          variant="subtle"
          onClick={() => goToSlice(session.selectedSlice - 1)}
          aria-label="Previous slice"
          disabled={session.selectedSlice <= 0}
        >
          ‹
        </ActionIcon>
        <ActionIcon
          size="sm"
          variant="subtle"
          onClick={() => goToSlice(session.selectedSlice + 1)}
          aria-label="Next slice"
          disabled={session.selectedSlice >= maxSlice}
        >
          ›
        </ActionIcon>
      </Group>

      <Modal
        opened={pendingSlice !== null}
        onClose={cancel}
        title="Unsaved changes"
      >
        <Text size="sm" c="dimmed">
          Changing the slice will discard the current preprocessing configuration.
        </Text>
        <Group justify="flex-end" mt="lg">
          <Button variant="default" onClick={cancel}>
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