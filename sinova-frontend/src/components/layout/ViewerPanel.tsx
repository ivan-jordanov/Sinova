import { Box, Group, Tabs, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useEffect } from "react";
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

  useEffect(() => {
    if (!preview.isError) return;

    const err = preview.error as any;
    let errorMessage =
      err?.body?.detail ?? err?.detail ?? err?.response?.data?.detail;

    if (!errorMessage && typeof err?.message === "string") {
      try {
        const parsed = JSON.parse(err.message.replace(/^ApiError:\s*/, ""));
        errorMessage = parsed?.detail ?? err.message;
      } catch {
        errorMessage = err.message;
      }
    }

    notifications.show({
      title: "Preview Error",
      message: String(errorMessage || "Preview request failed: backend unavailable."),
      color: "red",
    });
  }, [preview.isError, preview.error]);

  useEffect(() => {
    if (preview.data?.message) {
      notifications.show({
        title: "Preview",
        message: preview.data.message,
        color: "teal",
      });
    }
  }, [preview.data?.message]);

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