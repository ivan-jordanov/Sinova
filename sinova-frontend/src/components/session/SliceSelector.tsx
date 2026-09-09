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
import { useDatasetStore } from "../../store/datasetStore";

interface SliceSelectorProps {
  context?: "projection" | "sinogram";
}

export function SliceSelector({ context = "projection" }: SliceSelectorProps) {
  const { session, selectSlice, resetConfiguration } = usePreprocessingStore();
  const metadata = useDatasetStore((state) => state.metadata);

  // Resolve active display label and bounds based on viewing mode
  const isProjection = context === "projection";
  
  const label = isProjection ? "PROJECTION" : "ROW";
  
  const totalItems = isProjection
    ? (metadata?.projections ?? session.totalSlices)
    : (metadata?.detectorHeight ?? session.totalSlices);

  const [pendingSlice, setPendingSlice] = useState<number | null>(null);
  const [localSlice, setLocalSlice] = useState<number | string>(session.selectedSlice);

  useEffect(() => {
    setLocalSlice(session.selectedSlice);
  }, [session.selectedSlice]);

  const maxSlice = Math.max(0, totalItems - 1);

  const goToSlice = (targetSlice: number) => {
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

  return (
    <>
      <Group gap={5}>
        <Text size="xs" c="dimmed">
          {label}
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
          / {totalItems}
        </Text>
        <ActionIcon
          size="sm"
          variant="subtle"
          onClick={() => goToSlice(session.selectedSlice - 1)}
          aria-label={`Previous ${label.toLowerCase()}`}
          disabled={session.selectedSlice <= 0}
        >
          ‹
        </ActionIcon>
        <ActionIcon
          size="sm"
          variant="subtle"
          onClick={() => goToSlice(session.selectedSlice + 1)}
          aria-label={`Next ${label.toLowerCase()}`}
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
          Changing the target index will discard the current preprocessing configuration.
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