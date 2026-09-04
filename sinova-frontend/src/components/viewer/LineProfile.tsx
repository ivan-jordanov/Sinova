import { Box, Group, Text } from "@mantine/core";
export function LineProfile() {
  return (
    <Box className="line-profile">
      <Group justify="space-between">
        <Text className="eyebrow">LINE PROFILE</Text>
        <Text size="xs" c="dimmed">
          RAW / CURRENT / RESIDUAL
        </Text>
      </Group>
      <Box className="profile-line" />
    </Box>
  );
}
