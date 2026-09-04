import {
  Accordion,
  Button,
  Divider,
  Group,
  NumberInput,
  Select,
  Stack,
  Switch,
  Text,
  TextInput,
} from "@mantine/core";
import { usePreprocessingStore } from "../../store/preprocessingStore";
export function OperationPanel() {
  const state = usePreprocessingStore();
  const operation =
    state.operations.find((item) => item.id === state.selectedOperationId) ??
    state.operations[0];
  const value = (key: string) => operation.parameters[key];
  return (
    <Stack gap="md">
      <Group justify="space-between" align="flex-start">
        <div>
          <Text fw={600}>{operation.name}</Text>
          <Text size="xs" c="dimmed" mt={4}>
            {operation.description}
          </Text>
        </div>
        <Switch
          checked={operation.enabled}
          onChange={() => state.toggleOperation(operation.id)}
          aria-label={`Enable ${operation.name}`}
        />
      </Group>
      <Divider />
      {operation.id === "normalization" && (
        <>
          <Select
            label="Dark reference"
            data={["Auto", "Manual"]}
            value={String(value("dark"))}
            onChange={(next) =>
              next && state.updateParameter(operation.id, "dark", next)
            }
          />
          <NumberInput
            label="Flat reference"
            value={Number(value("flat"))}
            onChange={(next) =>
              state.updateParameter(operation.id, "flat", Number(next) || 0)
            }
          />
          <Switch
            label="Apply negative log"
            checked={Boolean(value("logarithm"))}
            onChange={(event) =>
              state.updateParameter(
                operation.id,
                "logarithm",
                event.currentTarget.checked,
              )
            }
          />
        </>
      )}
      {operation.id === "attenuation" && (
        <>
          <NumberInput
            label="Threshold"
            decimalScale={2}
            value={Number(value("threshold"))}
            onChange={(next) =>
              state.updateParameter(
                operation.id,
                "threshold",
                Number(next) || 0,
              )
            }
          />
          <Select
            label="Mode"
            data={["Manual", "Automatic suggestion"]}
            value={String(value("mode"))}
            onChange={(next) =>
              next && state.updateParameter(operation.id, "mode", next)
            }
          />
        </>
      )}
      {operation.id === "fov-mask" && (
        <>
          <Select
            label="Boundary"
            data={["Auto", "Manual"]}
            value={String(value("boundary"))}
            onChange={(next) =>
              next && state.updateParameter(operation.id, "boundary", next)
            }
          />
          <NumberInput
            label="Margin (px)"
            value={Number(value("margin"))}
            onChange={(next) =>
              state.updateParameter(operation.id, "margin", Number(next) || 0)
            }
          />
          <Button variant="default" size="xs">
            Auto detect boundary
          </Button>
        </>
      )}
      {operation.id === "cor" && (
        <>
          <NumberInput
            label="Center of rotation"
            decimalScale={1}
            value={Number(value("value"))}
            onChange={(next) =>
              state.updateParameter(operation.id, "value", Number(next) || 0)
            }
          />
          <Button variant="default" size="xs">
            Estimate from projections
          </Button>
        </>
      )}
      {["edge-taper", "fourier-wavelet", "vo-sorting", "neural"].includes(
        operation.id,
      ) && (
        <TextInput
          label="Configuration status"
          value="Placeholder configuration"
          readOnly
        />
      )}
      {operation.id !== "cor" && (
        <Accordion variant="contained">
          <Accordion.Item value="advanced">
            <Accordion.Control>Advanced</Accordion.Control>
            <Accordion.Panel>
              <Text size="xs" c="dimmed">
                Additional controls will be connected to the FastAPI preview
                contract.
              </Text>
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      )}
    </Stack>
  );
}
