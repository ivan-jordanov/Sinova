import { AppShell, Box, Group, Splitter, Text } from "@mantine/core";
import { useEffect, useState } from "react";
import type { SplitterPaneSize } from "@mantine/hooks";
import { Header } from "./Header";
import { OperationsPanel } from "./OperationsPanel";
import { ViewerPanel } from "./ViewerPanel";
import { InspectorPanel } from "./InspectorPanel";
import { BottomBar } from "./BottomBar";
import { usePreview } from "../../hooks/usePreview";
import { useViewerStore } from "../../store/viewerStore";
import { usePreprocessingStore } from "../../store/preprocessingStore";
import { useDatasetStore } from "../../store/datasetStore";
import "./layout.css";

export function MainLayout() {
  const [sizes, setSizes] = useState<SplitterPaneSize[]>(["22%", "56%", "22%"]);

  /* Atomic store selectors matching your Zustand implementation */
  const context = useViewerStore((state) => state.context);
  const mode = useViewerStore((state) => state.mode);
  
  const operations = usePreprocessingStore((state) => state.operations);
  const selectedSlice = usePreprocessingStore((state) => state.session.selectedSlice);
  const setCOR = useDatasetStore((state) => state.setCOR);
  
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
    if (!preview.data) return;

    const responseCorOp = preview.data.operations?.find(
      (op) => op.id === "cor_shift" || op.shortName === "cor_shift"
    );

    if (!responseCorOp?.parameters) return;

    console.log("Setting COR from preview response:", responseCorOp.parameters.value);
    setCOR(Number(responseCorOp.parameters.value));
  }, [preview.data, setCOR]);

  return (
    <AppShell padding={0} className="app-shell">
      <AppShell.Header>
        <Header />
      </AppShell.Header>
      <AppShell.Main>
        <Box className="workspace">
          <Splitter
            className="workspace-splitter"
            sizes={sizes}
            onSizeChange={setSizes}
            lineSize={1}
            handleColor="cyan"
          >
            <Splitter.Pane defaultSize="22%" min="180px" max="25%">
              <OperationsPanel />
            </Splitter.Pane>
            <Splitter.Pane defaultSize="56%" min="520px">
              <ViewerPanel
                data={preview.data}
                isLoading={preview.isLoading}
                isError={preview.isError}
                error={preview.error}
                dataUpdatedAt={preview.dataUpdatedAt}
              />
            </Splitter.Pane>
            <Splitter.Pane defaultSize="22%" min="250px" max="25%">
              <InspectorPanel />
            </Splitter.Pane>
          </Splitter>
        </Box>
        <BottomBar />
      </AppShell.Main>
      <Group className="status-line" justify="space-between">
        <Text size="xs" c="dimmed">
          SINOVA / PREPROCESSING WORKSPACE
        </Text>
        <Text size="xs" c="dimmed" className="mono">
          LOCAL MOCK PROVIDER · READY
        </Text>
      </Group>
    </AppShell>
  );
}