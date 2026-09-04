import { AppShell, Box, Group, Splitter, Text } from "@mantine/core";
import { useState } from "react";
import type { SplitterPaneSize } from "@mantine/hooks";
import { Header } from "./Header";
import { OperationsPanel } from "./OperationsPanel";
import { ViewerPanel } from "./ViewerPanel";
import { InspectorPanel } from "./InspectorPanel";
import { BottomBar } from "./BottomBar";
import "./layout.css";

export function MainLayout() {
  const [sizes, setSizes] = useState<SplitterPaneSize[]>(["22%", "56%", "22%"]);
  // Keep pane changes stable while the user works in this session.
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
              <ViewerPanel />
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
