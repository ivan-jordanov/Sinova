import {
  ActionIcon,
  Badge,
  Button,
  Group,
  SegmentedControl,
  Select,
  Stack,
  Text,
  Tooltip,
} from "@mantine/core";
import { useViewerStore } from "../../store/viewerStore";
import { useDatasetStore } from "../../store/datasetStore";

export function ViewerToolbar() {
  const { mode, setMode, colormap, setColormap, resetZoom } = useViewerStore();
  const { metadata } = useDatasetStore();

  console.log(metadata);

  const tooltipLabel = (
  <Stack gap={4} p={2}>
    <Text fw={700} size="xs">
      {metadata?.name}
    </Text>
    {metadata?.path && (
      <Text size="xs" c="dimmed" style={{ wordBreak: 'break-all' }}>
        {metadata.path}
      </Text>
    )}
    <Group gap={6} mt={2}>
      {metadata?.detectorWidth && metadata?.detectorHeight && (
        <Badge size="xs" variant="light">
          {metadata.detectorWidth}×{metadata.detectorHeight}
        </Badge>
      )}
      {metadata?.projections && (
        <Badge size="xs" variant="light">
          {metadata.projections} proj
        </Badge>
      )}
      {metadata?.slices && (
        <Badge size="xs" variant="light">
          {metadata.slices} slices
        </Badge>
      )}
      {metadata?.format && (
        <Badge size="xs" variant="outline">
          {metadata.format.toUpperCase()}
        </Badge>
      )}
    </Group>
    {metadata?.beamMask && (
      <Text size="xs" c="dimmed" mt={2}>
        Beam Mask: r={metadata.beamMask.radius.toFixed(2)} at ({metadata.beamMask.cx.toFixed(2)}, {metadata.beamMask.cy.toFixed(2)})
      </Text>
    )}
  </Stack>
);

  return (
    <Group justify="space-between" my="md">
      <Group gap="xs">
        <Text size="xs" c="dimmed">
          VIEW
        </Text>
        <SegmentedControl
          size="xs"
          value={mode}
          onChange={(value) => setMode(value as "current" | "original")}
          data={[
            { label: "Current", value: "current" },
            { label: "Original", value: "original" },
          ]}
        />
        <Tooltip
          label={tooltipLabel}
          multiline
          w={280}
          withArrow
          position="bottom-start"
        >
          <ActionIcon
            variant="subtle"
            color="gray"
            size="xs"
            aria-label="Dataset details"
          >
            <Text size="xs" fw={700} style={{ lineHeight: 1 }}>
              🛈
            </Text>
          </ActionIcon>
        </Tooltip>
        <Group gap="xs"></Group>
      </Group>
      <Group gap="xs">
        <Select
          size="xs"
          w={110}
          value={colormap}
          onChange={(val) => val && setColormap(val)}
          data={[
            { label: "gray", value: "Greys" },
            { label: "viridis", value: "Viridis" },
            { label: "magma", value: "Magma" },
          ]}
          aria-label="Colormap"
        />
        <Button size="xs" variant="subtle" onClick={resetZoom}>
          Reset preview
        </Button>
      </Group>
    </Group>
  );
}
