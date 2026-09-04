import { Button, Group, Modal, Text } from "@mantine/core";
interface Props {
  opened: boolean;
  onClose: () => void;
  onApply: () => void;
  isPending: boolean;
  message?: string;
}
export function ApplyStackDialog({ opened, onClose, onApply, isPending, message }: Props) {
  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Apply preprocessing to entire stack?"
    >
      <Text size="sm" c="dimmed">
        The current configuration will be applied to the complete dataset. This
        operation may take a significant amount of time.
      </Text>
      <Group justify="flex-end" mt="xl">
        <Button variant="default" onClick={onClose}>
          Cancel
        </Button>
        <Button onClick={onApply} loading={isPending}>Apply to entire stack</Button>
      </Group>
      {message && <Text size="xs" c="teal" mt="md">{message}</Text>}
    </Modal>
  );
}
