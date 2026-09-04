import { Button, Group, Text } from "@mantine/core";
import { useState } from "react";
import { usePreprocessingStore } from "../../store/preprocessingStore";
import { ApplyStackDialog } from "../session/ApplyStackDialog";
export function BottomBar() {
  const [opened, setOpened] = useState(false);
  const { session, past, future, undo, redo } = usePreprocessingStore();
  return (
    <>
      <Group className="bottom-bar" justify="space-between" px="lg">
        <Group gap="md">
          <span className="live-dot" />
          <Text size="sm">
            Preview mode{" "}
            <Text span c="dimmed">
              · changes apply to current slice only
            </Text>
          </Text>
          {session.dirty && (
            <Text size="xs" c="yellow">
              UNSAVED
            </Text>
          )}
        </Group>
        <Group gap="xs">
          <Button
            size="xs"
            variant="subtle"
            disabled={!past.length}
            onClick={undo}
          >
            Undo
          </Button>
          <Button
            size="xs"
            variant="subtle"
            disabled={!future.length}
            onClick={redo}
          >
            Redo
          </Button>
          <Button size="xs" onClick={() => setOpened(true)}>
            Apply to entire stack ↗
          </Button>
        </Group>
      </Group>
      <ApplyStackDialog opened={opened} onClose={() => setOpened(false)} />
    </>
  );
}
