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
import { useMutation } from "@tanstack/react-query";
import { browseDatasetFile, loadDataset } from "../../api/dataset";
import { useDatasetStore } from "../../store/datasetStore";
import { usePreprocessingStore } from "../../store/preprocessingStore";
import { useBackendHealth } from "../../hooks/useBackendHealth";

export function Header() {
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

    // 1. Update dataset store metadata
    setMetadata(data);

    // 2. Set total slices and reset selected slice to initial index
    if (data.slices) {
      setTotalSlices(data.slices);
      selectSlice(0); // Ensures preview query has a valid slice value immediately
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

  const handleLoadFileClick = async () => {
    try {
      // 1. Open native OS file picker via FastAPI host process
      const fullPath = await browseDatasetFile();

      if (!fullPath) return;

      notifications.show({
        id: "loading-dataset",
        loading: true,
        title: "Loading Dataset",
        message: `Ingesting dataset...`,
        autoClose: false,
        withCloseButton: false,
      });

      // 2. Pass the exact full path to /ingestion/load
      loadMutation.mutate(fullPath, {
        onSettled: () => {
          notifications.hide("loading-dataset");
        },
      });
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