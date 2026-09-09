import { Button, Group, SegmentedControl, Select, Text } from "@mantine/core";
import { useViewerStore } from "../../store/viewerStore";

export function ViewerToolbar() {
  const { mode, setMode, colormap, setColormap, resetZoom } = useViewerStore();

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
          Reset zoom
        </Button>
      </Group>
    </Group>
  );
}