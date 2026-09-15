import { Box, Group, Tabs, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useEffect, useRef } from "react";
import { useViewerStore } from "../../store/viewerStore";
import { ProjectionViewer } from "../viewer/ProjectionViewer";
import { SinogramViewer } from "../viewer/SinogramViewer";
import { ViewerToolbar } from "../viewer/ViewerToolbar";
import { GlobalAnalysis } from "../viewer/GlobalAnalysis";
import { SliceSelector } from "../session/SliceSelector";
import type { PreviewResult } from "../../types/preview";

interface ViewerPanelProps {
  data?: PreviewResult;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  dataUpdatedAt: number;
}

export function ViewerPanel({
  data,
  isLoading,
  isError,
  error,
  dataUpdatedAt,
}: ViewerPanelProps) {
  const { context, setContext, colormap } = useViewerStore();
  const maxFetchTimeRef = useRef<number>(0);

  useEffect(() => {
    if (!isError) return;

    const err = error as any;
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
  }, [isError, error]);

  useEffect(() => {
    if (data?.message && dataUpdatedAt && dataUpdatedAt > maxFetchTimeRef.current) {
      maxFetchTimeRef.current = dataUpdatedAt;
      notifications.show({
        title: "Preview",
        message: data.message,
        color: "teal",
      });
    }
  }, [data, dataUpdatedAt]);

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
              data={data}
              isLoading={isLoading}
              colormap={colormap}
            />
          ) : (
            <SinogramViewer
              data={data}
              isLoading={isLoading}
              colormap={colormap}
            />
          )}
          <GlobalAnalysis data={data} isLoading={isLoading} />
        </Box>
      </Box>
    </Box>
  );
}