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
  const { session, selectSlice, resetConfiguration, setTotalSlices } =
    usePreprocessingStore();
  const metadata = useDatasetStore((state) => state.metadata);

  const isProjection = context === "projection";
  const label = isProjection ? "PROJECTION" : "ROW";

  const totalItems = isProjection
    ? (metadata?.projections ?? 1)
    : (metadata?.detectorHeight ?? 1);

  const maxSlice = Math.max(0, totalItems - 1);
  const currentSlice = Number(session.selectedSlice) || 0;

  const [pendingSlice, setPendingSlice] = useState<number | null>(null);
  const [localSlice, setLocalSlice] = useState<number | string>(currentSlice);

  useEffect(() => {
    setLocalSlice(currentSlice);
  }, [currentSlice]);

  // Keep the store's totalSlices in sync with whichever context we're
  // viewing, and reset to the middle slice whenever context/metadata changes.
  useEffect(() => {
    if (totalItems > 0) {
      setTotalSlices(totalItems);
    }
  }, [context, totalItems, setTotalSlices]);

  const goToSlice = (targetSlice: number) => {
    const clampedSlice = Math.max(0, Math.min(targetSlice, maxSlice));

    if (clampedSlice === currentSlice) {
      setLocalSlice(currentSlice);
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
      event.preventDefault();
      const parsed = parseInt(event.currentTarget.value, 10);
      goToSlice(Number.isNaN(parsed) ? 0 : parsed);
    }
  };

  const confirm = () => {
    resetConfiguration();
    if (pendingSlice !== null) selectSlice(pendingSlice);
    setPendingSlice(null);
  };

  const cancel = () => {
    setPendingSlice(null);
    setLocalSlice(currentSlice);
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
          value={typeof localSlice === "number" ? localSlice + 1 : localSlice}
          min={1}
          max={totalItems}
          onChange={(val) => setLocalSlice(typeof val === "number" ? val - 1 : val)}
          onKeyDown={handleKeyDown}
        />
        <Text size="xs" c="dimmed">
          / {totalItems}
        </Text>
        <ActionIcon
          size="sm"
          variant="subtle"
          onClick={() => goToSlice(currentSlice - 1)}
          aria-label={`Previous ${label.toLowerCase()}`}
          disabled={currentSlice <= 0}
        >
          ‹
        </ActionIcon>
        <ActionIcon
          size="sm"
          variant="subtle"
          onClick={() => goToSlice(currentSlice + 1)}
          aria-label={`Next ${label.toLowerCase()}`}
          disabled={currentSlice >= maxSlice}
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