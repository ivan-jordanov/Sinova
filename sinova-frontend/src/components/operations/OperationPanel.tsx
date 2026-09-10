import {
  Accordion,
  Button,
  Divider,
  Group,
  NumberInput,
  type NumberInputProps,
  Select,
  Stack,
  Switch,
  Text,
  TextInput,
} from "@mantine/core";
import { useEffect, useState } from "react";
import { usePreprocessingStore } from "../../store/preprocessingStore";

interface DeferredInputProps extends Omit<NumberInputProps, "value" | "onChange"> {
  value: number;
  onCommit: (val: number) => void;
}

function DeferredNumberInput({ value, onCommit, ...props }: DeferredInputProps) {
  const [localVal, setLocalVal] = useState<number | string>(value);

  useEffect(() => {
    setLocalVal(value);
  }, [value]);

  const commit = (targetVal: number | string = localVal) => {
    const num = typeof targetVal === "number" ? targetVal : parseFloat(String(targetVal));
    const valid = Number.isNaN(num) ? 0 : Math.max(0, num);
    setLocalVal(valid);
    onCommit(valid);
  };

  return (
    <NumberInput
      min={0}
      allowNegative={false}
      {...props}
      value={localVal}
      onChange={setLocalVal}
      onKeyDown={(e) => e.key === "Enter" && commit()}
      onBlur={() => commit()}
    />
  );
}

export function OperationPanel() {
  const state = usePreprocessingStore();
  const operation =
    state.operations.find((item) => item.id === state.selectedOperationId) ??
    state.operations[0];

  const params = operation.parameters;

  const updateParam = (key: string, val: unknown, altKey?: string) => {
    state.updateParameter(operation.id, key, val as any);
    if (altKey) {
      state.updateParameter(operation.id, altKey, val as any);
    }
  };

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
            value={String(params.dark ?? "Auto")}
            onChange={(next) => next && updateParam("dark", next)}
          />
          <DeferredNumberInput
            label="Flat reference"
            value={Number(params.vmax ?? params.flat ?? 0)}
            onCommit={(val) => updateParam("flat", val, "vmax")}
          />
          <Switch
            label="Apply negative log"
            checked={Boolean(params.logarithm)}
            onChange={(e) => updateParam("logarithm", e.currentTarget.checked)}
          />
        </>
      )}

      {operation.id === "attenuation" && (
        <>
          <DeferredNumberInput
            label="Threshold"
            decimalScale={2}
            value={Number(params.max_value ?? params.threshold ?? 1.0)}
            onCommit={(val) => updateParam("threshold", val, "max_value")}
          />
          <Select
            label="Mode"
            data={["Manual", "Automatic suggestion"]}
            value={String(params.mode ?? "Manual")}
            onChange={(next) => next && updateParam("mode", next)}
          />
        </>
      )}

      {operation.id === "fov-mask" && (
        <>
          <Select
            label="Boundary"
            data={["Auto", "Manual"]}
            value={String(params.boundary ?? "Auto")}
            onChange={(next) => next && updateParam("boundary", next)}
          />
          <DeferredNumberInput
            label="Margin (px)"
            value={Number(params.radius ?? params.margin ?? 0.95)}
            onCommit={(val) => updateParam("margin", val, "radius")}
          />
          <Button variant="default" size="xs">
            Auto detect boundary
          </Button>
        </>
      )}

      {operation.id === "cor" && (
        <>
          <DeferredNumberInput
            label="Center of rotation"
            decimalScale={1}
            value={Number(params.offset ?? params.value ?? 0.0)}
            onCommit={(val) => updateParam("value", val, "offset")}
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
                Additional controls will be connected to the FastAPI preview contract.
              </Text>
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      )}
    </Stack>
  );
}