import { Box, Group, Tabs, Text } from "@mantine/core";
import { useViewerStore } from "../../store/viewerStore";
import { ProjectionViewer } from "../viewer/ProjectionViewer";
import { SinogramViewer } from "../viewer/SinogramViewer";
import { ViewerToolbar } from "../viewer/ViewerToolbar";
import { LineProfile } from "../viewer/LineProfile";
import { SliceSelector } from "../session/SliceSelector";
import { usePreview } from "../../hooks/usePreview";
import { usePreprocessingStore } from "../../store/preprocessingStore";
export function ViewerPanel() {
  const { context, setContext } = useViewerStore();
  const { operations, session } = usePreprocessingStore();
  const preview = usePreview({
    context,
    slice: session.selectedSlice,
    configuration: { operations },
    mode: "current",
  });
  return (
    <Box className="panel viewer-panel">
      <Group justify="space-between" mb="md">
        <div>
          <Text className="eyebrow">DATA CONTEXT</Text>
          <Text fw={600}>Preview surface</Text>
        </div>
        <SliceSelector />
      </Group>
      <Tabs
        value={context}
        onChange={(value) =>
          setContext((value as "projection" | "sinogram") ?? "sinogram")
        }
        variant="default"
      >
        <Tabs.List>
          <Tabs.Tab value="projection">Projection</Tabs.Tab>
          <Tabs.Tab value="sinogram">Sinogram</Tabs.Tab>
        </Tabs.List>
      </Tabs>
      <ViewerToolbar />
      <Box className="viewer-scroll">
        {preview.isError && <Text size="xs" c="red">Preview request failed: backend unavailable.</Text>}
        {preview.data && <Text size="xs" c="teal" mb="xs">{preview.data.message}</Text>}
        <Box className="viewer-canvas">
          {context === "projection" ? <ProjectionViewer /> : <SinogramViewer />}
          <LineProfile />
        </Box>
      </Box>
    </Box>
  );
}
