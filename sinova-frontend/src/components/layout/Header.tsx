import {
  ActionIcon,
  Badge,
  Button,
  Group,
  Text,
  useComputedColorScheme,
  useMantineColorScheme,
} from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { getDatasetMetadata } from "../../api/dataset";
import { useDatasetStore } from "../../store/datasetStore";
import { usePreprocessingStore } from "../../store/preprocessingStore";
import { useBackendHealth } from "../../hooks/useBackendHealth";
export function Header() {
  const fallbackDataset = useDatasetStore((state) => state.metadata);
  // React Query caches this request and exposes loading/error states when the API
  // becomes real. The Zustand value keeps the shell useful while the mock loads.
  const { data: dataset = fallbackDataset } = useQuery({
    queryKey: ["dataset", "metadata"],
    queryFn: getDatasetMetadata,
  });
  const backendHealth = useBackendHealth();
  // This is local configuration history, so it does not belong in React Query.
  const { past, future, undo, redo } = usePreprocessingStore();
  const { setColorScheme } = useMantineColorScheme();
  const colorScheme = useComputedColorScheme("dark");
  const isDark = colorScheme === "dark";
  return (
    <Group h="100%" px="lg" justify="space-between" className="app-header">
      <Group gap="lg">
        <Text fw={700} size="lg" className="brand">
          SINOVA<span>•</span>
        </Text>
        <Text size="sm" c="dimmed">
          Dataset <b>{dataset.name}</b>
        </Text>
        <Badge color={backendHealth.isSuccess ? "teal" : "yellow"} variant="light">
          API · {backendHealth.isSuccess ? "READY" : "OFFLINE"}
        </Badge>
      </Group>
      <Group gap="xs">
        <ActionIcon
          variant="subtle"
          disabled={!past.length}
          onClick={undo}
          aria-label="Undo"
        >
          ↶
        </ActionIcon>
        <ActionIcon
          variant="subtle"
          disabled={!future.length}
          onClick={redo}
          aria-label="Redo"
        >
          ↷
        </ActionIcon>
        <ActionIcon
          variant="subtle"
          onClick={() => setColorScheme(isDark ? "light" : "dark")}
          aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
        >
          {isDark ? "☼" : "☾"}
        </ActionIcon>
        <Button variant="default" size="xs" disabled>
          Export
        </Button>
      </Group>
    </Group>
  );
}
