import { Box, Divider, Text } from "@mantine/core";
import { ActiveOperations } from "../operations/ActiveOperations";
import { OperationLibrary } from "../operations/OperationLibrary";
export function OperationsPanel() {
  return (
    <Box className="panel operations-panel">
      <Text className="eyebrow">TOOLBOX</Text>
      <Text fw={600} mb="md">
        Operations
      </Text>
      <OperationLibrary />
      <Divider my="lg" />
      <ActiveOperations />
    </Box>
  );
}
