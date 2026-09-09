import {
  ActionIcon,
  Badge,
  Button,
  Group,
  Text,
  useComputedColorScheme,
  useMantineColorScheme,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { browseDatasetFile, loadDataset, unloadDataset } from "../../api/dataset";
import { useDatasetStore } from "../../store/datasetStore";
import { usePreprocessingStore } from "../../store/preprocessingStore";
import { useBackendHealth } from "../../hooks/useBackendHealth";

export function Header() {
  const queryClient = useQueryClient();
  const activeMetadata = useDatasetStore((state) => state.metadata);
  const setMetadata = useDatasetStore((state) => state.setMetadata);

  const selectSlice = usePreprocessingStore((state) => state.selectSlice);
  const setTotalSlices = usePreprocessingStore((state) => state.setTotalSlices);
  const { past, future, undo, redo } = usePreprocessingStore();

  const backendHealth = useBackendHealth();
  const { setColorScheme } = useMantineColorScheme();
  const colorScheme = useComputedColorScheme("dark");
  const isDark = colorScheme === "dark";

  // Mutation for POST /load
  const loadMutation = useMutation({
    mutationFn: (filePath: string) => loadDataset(filePath),
    onMutate: () => {
      notifications.show({
        id: "loading-dataset",
        loading: true,
        title: "Loading Dataset",
        message: "Ingesting dataset...",
        autoClose: false,
        withCloseButton: false,
      });
    },
    onSuccess: (data) => {
      notifications.update({
        id: "loading-dataset",
        color: "green",
        title: "Dataset Loaded",
        message: `Successfully loaded ${data.name}`,
        loading: false,
        autoClose: 4000,
        withCloseButton: true,
      });

      setMetadata(data);

      if (data.slices) {
        setTotalSlices(data.slices);
        selectSlice(0);
      }
    },
    onError: (error: Error) => {
      notifications.update({
        id: "loading-dataset",
        color: "red",
        title: "Failed to Load Dataset",
        message: error.message || "An error occurred while loading the dataset.",
        loading: false,
        autoClose: 5000,
        withCloseButton: true,
      });
    },
  });

  // Mutation for POST /unload
  const unloadMutation = useMutation({
    mutationFn: unloadDataset,
    onSuccess: () => {
      // 1. Clear dataset metadata from store
      setMetadata(null);

      // 2. Reset slice count in preprocessing store
      setTotalSlices(0);
      selectSlice(0);

      // 3. Purge cached preview queries so viewers reset immediately
      queryClient.removeQueries({ queryKey: ["preview"] });

      notifications.show({
        id: "clear-dataset",
        color: "gray",
        title: "Dataset Deselected",
        message: "Active dataset cleared from session.",
        autoClose: 3000,
      });
    },
    onError: (error: Error) => {
      notifications.show({
        id: "clear-dataset-error",
        color: "red",
        title: "Failed to Unload Dataset",
        message: error.message || "An error occurred while clearing the dataset.",
        autoClose: 5000,
      });
    },
  });

  const handleLoadFileClick = async () => {
    try {
      const fullPath = await browseDatasetFile();
      if (!fullPath) return;

      loadMutation.mutate(fullPath);
    } catch (error) {
      // User closed or cancelled file dialog
    }
  };

  return (
    <Group h="100%" px="lg" justify="space-between" className="app-header">
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
            loading={loadMutation.isPending}
            onClick={handleLoadFileClick}
          >
            Load File
          </Button>

          {activeMetadata && (
            <Button
              variant="subtle"
              color="red"
              size="compact-xs"
              loading={unloadMutation.isPending}
              onClick={() => unloadMutation.mutate()}
            >
              Deselect
            </Button>
          )}
        </Group>

        <Badge color={backendHealth.isSuccess ? "teal" : "yellow"} variant="light">
          API · {backendHealth.isSuccess ? "READY" : "OFFLINE"}
        </Badge>

        <Badge color={"yellow"} variant="light">
          CUDA · {"OFFLINE"}
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