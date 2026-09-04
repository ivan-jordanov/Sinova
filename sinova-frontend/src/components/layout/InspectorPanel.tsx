import { Box, Text } from "@mantine/core";
import { OperationPanel } from "../operations/OperationPanel";
export function InspectorPanel() {
  return (
    <Box className="panel inspector-panel">
      <Text className="eyebrow">INSPECTOR</Text>
      <Text fw={600} mb="md">
        Operation settings
      </Text>
      <OperationPanel />
    </Box>
  );
}
