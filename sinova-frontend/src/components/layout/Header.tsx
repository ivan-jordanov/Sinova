import { useRef } from "react";
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
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Zustand metadata state
  const storeMetadata = useDatasetStore((state) => state.metadata);
  const setDataset = useDatasetStore((state) => state.setDataset);

  // React Query metadata (if backend is active)
  const { data: apiMetadata } = useQuery({
    queryKey: ["dataset", "metadata"],
    queryFn: getDatasetMetadata,
    enabled: false, // Prevents auto-fetching default mock data on mount
  });

  // Resolve active metadata or null
  const activeMetadata = storeMetadata ?? apiMetadata ?? null;

  const backendHealth = useBackendHealth();
  const { past, future, undo, redo } = usePreprocessingStore();
  const { setColorScheme } = useMantineColorScheme();
  const colorScheme = useComputedColorScheme("dark");
  const isDark = colorScheme === "dark";

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setDataset(file);
    }
  };

  const handleLoadFileClick = () => {
    fileInputRef.current?.click();
  }

  return (
    <Group h="100%" px="lg" justify="space-between" className="app-header">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
        accept=".dat,.dicom,.tif,.tiff,.mraw"
      />

      <Group gap="lg">
        <Text fw={700} size="lg" className="brand">
          SINOVA<span>•</span>
        </Text>

        <Group gap="xs">
          <Text size="sm" c="dimmed">
            Dataset:{" "}
            {activeMetadata?.name ? (
              <b>{activeMetadata.name}</b>
            ) : (
              <i>Nothing selected</i>
            )}
          </Text>

          <Button
            variant="light"
            size="compact-xs"
            onClick={handleLoadFileClick}
          >
            Load File
          </Button>
        </Group>

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
        <Button variant="default" size="xs" disabled={!activeMetadata}>
          Export
        </Button>
      </Group>
    </Group>
  );
}