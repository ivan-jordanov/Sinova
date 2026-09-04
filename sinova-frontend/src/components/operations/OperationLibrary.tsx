import { Button, Stack, Text } from "@mantine/core";
import { usePreprocessingStore } from "../../store/preprocessingStore";
import type { OperationCategory } from "../../types/preprocessing";
const groups: { id: OperationCategory; label: string }[] = [
  { id: "intensity", label: "Intensity" },
  { id: "spatial", label: "Spatial" },
  { id: "geometry", label: "Geometry" },
  { id: "destriping", label: "Destriping" },
];
export function OperationLibrary() {
  const operations = usePreprocessingStore((state) => state.operations);
  const selected = usePreprocessingStore((state) => state.selectedOperationId);
  const select = usePreprocessingStore((state) => state.selectOperation);
  return (
    <Stack gap="sm">
      {groups.map((group) => (
        <div key={group.id}>
          <Text className="eyebrow" mb={4}>
            {group.label}
          </Text>
          <Stack gap={2}>
            {operations
              .filter((operation) => operation.category === group.id)
              .map((operation) => (
                <Button
                  key={operation.id}
                  variant={selected === operation.id ? "light" : "subtle"}
                  color={selected === operation.id ? "cyan" : "gray"}
                  justify="space-between"
                  size="xs"
                  onClick={() => select(operation.id)}
                >
                  {operation.shortName}
                  {operation.enabled && (
                    <Text span c="teal">
                      ●
                    </Text>
                  )}
                </Button>
              ))}
          </Stack>
        </div>
      ))}
    </Stack>
  );
}
