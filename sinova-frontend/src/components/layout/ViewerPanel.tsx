import { Box, Group, Tabs, Text } from "@mantine/core";
import { useViewerStore } from "../../store/viewerStore";
import { ProjectionViewer } from "../viewer/ProjectionViewer";
import { SinogramViewer } from "../viewer/SinogramViewer";
import { ViewerToolbar } from "../viewer/ViewerToolbar";
import { GlobalAnalysis } from "../viewer/GlobalAnalysis";
import { SliceSelector } from "../session/SliceSelector";
import { usePreview } from "../../hooks/usePreview";
import { usePreprocessingStore } from "../../store/preprocessingStore";
import { useDatasetStore } from "../../store/datasetStore";

export function ViewerPanel() {
  const { context, setContext, mode, colormap } = useViewerStore();
  const operations = usePreprocessingStore((state) => state.operations);
  const selectedSlice = usePreprocessingStore((state) => state.session.selectedSlice);
  const metadata = useDatasetStore((state) => state.metadata);

  const preview = usePreview(
    {
      context,
      slice: selectedSlice,
      configuration: { operations },
      mode,
    },
    Boolean(metadata)
  );

  return (
    <Box className="panel viewer-panel">
      <Group justify="space-between" mb="md">
        <div>
          <Text className="eyebrow">DATA CONTEXT</Text>
          <Text fw={600}>Preview surface</Text>
        </div>
        <SliceSelector context={context} />
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
        {preview.isError && (
          <Text size="xs" c="red">
            Preview request failed: backend unavailable.
          </Text>
        )}
        {preview.data && (
          <Text size="xs" c="teal" mb="xs">
            {preview.data.message}
          </Text>
        )}

        <Box className="viewer-canvas">
          {context === "projection" ? (
            <ProjectionViewer
              data={preview.data}
              isLoading={preview.isLoading}
              colormap={colormap}
            />
          ) : (
            <SinogramViewer
              data={preview.data}
              isLoading={preview.isLoading}
              colormap={colormap}
            />
          )}
          <GlobalAnalysis data={preview.data} isLoading={preview.isLoading} />
        </Box>
      </Box>
    </Box>
  );
}