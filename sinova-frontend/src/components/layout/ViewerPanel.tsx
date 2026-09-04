import { Box, Group, Tabs, Text } from "@mantine/core";
import { useViewerStore } from "../../store/viewerStore";
import { ProjectionViewer } from "../viewer/ProjectionViewer";
import { SinogramViewer } from "../viewer/SinogramViewer";
import { ViewerToolbar } from "../viewer/ViewerToolbar";
import { LineProfile } from "../viewer/LineProfile";
import { SliceSelector } from "../session/SliceSelector";
export function ViewerPanel() {
  const { context, setContext } = useViewerStore();
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
        <Box className="viewer-canvas">
          {context === "projection" ? <ProjectionViewer /> : <SinogramViewer />}
          <LineProfile />
        </Box>
      </Box>
    </Box>
  );
}
