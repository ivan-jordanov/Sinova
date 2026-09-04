import { Badge, Stack, Text } from "@mantine/core";
import { usePreprocessingStore } from "../../store/preprocessingStore";
export function ActiveOperations() {
  const operations = usePreprocessingStore((state) => state.operations);
  const select = usePreprocessingStore((state) => state.selectOperation);
  return (
    <div>
      <Text className="eyebrow" mb="sm">
        Active
      </Text>
      <Stack gap="xs">
        {operations
          .filter((operation) => operation.enabled)
          .map((operation) => (
            <Badge
              key={operation.id}
              variant="light"
              color="teal"
              size="sm"
              fullWidth
              onClick={() => select(operation.id)}
              style={{ cursor: "pointer", justifyContent: "flex-start" }}
            >
              ✓ {operation.shortName}
            </Badge>
          ))}
      </Stack>
    </div>
  );
}
