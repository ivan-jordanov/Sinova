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
import { browseDatasetFile } from "../../api/dataset";
import { usePreprocessingStore } from "../../store/preprocessingStore";
import { useViewerStore } from "../../store/viewerStore";

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
  const setBeamMask = useViewerStore((store) => store.setBeamMask);
  const beamMask = useViewerStore((store) => store.beamMask);

  const operation =
    state.operations.find((item) => item.id === state.selectedOperationId) ??
    state.operations[0];

  const params = operation.parameters;

  useEffect(() => {
    const isFov = operation.id === "fov-mask";
    if (isFov) {
      const cx = Number(params.center_x ?? 0);
      const cy = Number(params.center_y ?? 0);
      const radius = Number(params.radius ?? params.margin ?? 0.95);
      setBeamMask([true, { cx, cy, radius }]);
    } else {
      setBeamMask([false, { cx: 0, cy: 0, radius: 0 }]);
    }
  }, [operation.id, setBeamMask]);

  useEffect(() => {
    if (operation.id === "fov-mask" && beamMask[0] && beamMask[1]) {
      const { cx, cy, radius } = beamMask[1];
      if (radius > 0) {
        const roundedCx = Math.round(cx * 100) / 100;
        const roundedCy = Math.round(cy * 100) / 100;
        const roundedRadius = Math.round(radius * 100) / 100;

        if (
          roundedCx !== params.center_x ||
          roundedCy !== params.center_y ||
          roundedRadius !== (params.margin ?? params.radius)
        ) {
          state.updateParameter("fov-mask", "center_x", roundedCx);
          state.updateParameter("fov-mask", "center_y", roundedCy);
          state.updateParameter("fov-mask", "margin", roundedRadius);
          state.updateParameter("fov-mask", "radius", roundedRadius);
        }
      }
    }
  }, [beamMask, operation.id]);

  const [darkInput, setDarkInput] = useState<string>(String(params.dark ?? "Auto"));
  const [flatInput, setFlatInput] = useState<string>(String(params.flat ?? "Auto"));

  useEffect(() => {
    if (operation.id === "normalization") {
      setDarkInput(String(params.dark ?? "Auto"));
      setFlatInput(String(params.flat ?? "Auto"));
    }

  }, [operation.id, params.dark, params.flat, params.value]);

  const updateParam = (key: string, val: unknown, altKey?: string) => {
    state.updateParameter(operation.id, key, val as any);
    if (altKey) {
      state.updateParameter(operation.id, altKey, val as any);
    }

    if (operation.id === "fov-mask") {
      const currentCx = key === "center_x" ? Number(val) : Number(params.center_x ?? 0);
      const currentCy = key === "center_y" ? Number(val) : Number(params.center_y ?? 0);
      const currentRadius =
        key === "margin" || key === "radius"
          ? Number(val)
          : Number(params.radius ?? params.margin ?? 0.95);

      setBeamMask([true, { cx: currentCx, cy: currentCy, radius: currentRadius }]);
    }
  };

  const handleBrowseFile = async (paramKey: "dark" | "flat") => {
    try {
      const filePath = await browseDatasetFile();
      if (filePath) {
        if (paramKey === "dark") setDarkInput(filePath);
        if (paramKey === "flat") setFlatInput(filePath);
      }
    } catch {
      // Dialog cancelled
    }
  };

  const handleToggleOperation = () => {
    if (operation.id === "normalization") {
      state.updateParameter("normalization", "dark", darkInput);
      state.updateParameter("normalization", "flat", flatInput);
    }
    state.toggleOperation(operation.id);
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
          onChange={handleToggleOperation}
          aria-label={`Enable ${operation.name}`}
        />
      </Group>

      <Divider />

      {/* NORMALIZATION */}
      {operation.id === "normalization" && (
        <>
          <Stack gap={4}>
            <Text size="sm" fw={500}>
              Dark Reference
            </Text>
            <Group gap="xs">
              <TextInput
                style={{ flex: 1 }}
                placeholder="Auto or file path..."
                value={darkInput}
                onChange={(e) => setDarkInput(e.currentTarget.value)}
              />
              <Button
                variant="default"
                size="sm"
                onClick={() => handleBrowseFile("dark")}
              >
                Browse
              </Button>
            </Group>
          </Stack>

          <Stack gap={4}>
            <Text size="sm" fw={500}>
              Flat Reference
            </Text>
            <Group gap="xs">
              <TextInput
                style={{ flex: 1 }}
                placeholder="Auto or file path..."
                value={flatInput}
                onChange={(e) => setFlatInput(e.currentTarget.value)}
              />
              <Button
                variant="default"
                size="sm"
                onClick={() => handleBrowseFile("flat")}
              >
                Browse
              </Button>
            </Group>
          </Stack>

          <Switch
            label="Apply negative log"
            checked={Boolean(params.logarithm)}
            onChange={(e) => updateParam("logarithm", e.currentTarget.checked)}
            mt="xs"
          />
        </>
      )}

      {/* ATTENUATION CLIPPING */}
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
            data={["Manual", "Auto"]}
            value={String(params.mode ?? "Manual")}
            onChange={(next) => next && updateParam("mode", next)}
          />
        </>
      )}

      {/* FOV MASK */}
      {operation.id === "fov-mask" && (
        <>
          <DeferredNumberInput
            label="Radius / Margin"
            decimalScale={2}
            value={Number(params.radius ?? params.margin ?? 0.95)}
            onCommit={(val) => updateParam("margin", val, "radius")}
          />
          <Group grow>
            <DeferredNumberInput
              label="Center X"
              value={Number(params.center_x ?? 0)}
              onCommit={(val) => updateParam("center_x", val)}
            />
            <DeferredNumberInput
              label="Center Y"
              value={Number(params.center_y ?? 0)}
              onCommit={(val) => updateParam("center_y", val)}
            />
          </Group>
        </>
      )}

      {/* CROP & PAD BEAM */}
      {operation.id === "crop-pad-beam" && (
        <>
          <DeferredNumberInput
            label="Padding (px)"
            value={Number(params.pad ?? 128)}
            onCommit={(val) => updateParam("pad", val)}
          />
          <DeferredNumberInput
            label="Edge Average Window (px)"
            value={Number(params.navg ?? 8)}
            onCommit={(val) => updateParam("navg", val)}
          />
        </>
      )}

      {/* DENOISE */}
      {operation.id === "denoise" && (
        <>
          <Select
            label="Method"
            data={["median", "gaussian"]}
            value={String(params.method ?? "median")}
            onChange={(next) => next && updateParam("method", next)}
          />
          {params.method === "gaussian" ? (
            <DeferredNumberInput
              label="Sigma"
              decimalScale={2}
              value={Number(params.sigma ?? 1.0)}
              onCommit={(val) => updateParam("sigma", val)}
            />
          ) : (
            <DeferredNumberInput
              label="Kernel Size"
              value={Number(params.kernel_size ?? 3)}
              onCommit={(val) => updateParam("kernel_size", val)}
            />
          )}
        </>
      )}

      {/* CENTER OF ROTATION */}
      {operation.id === "cor_shift" && (
        <Stack gap="xs">
          <DeferredNumberInput
            label="Center of rotation value"
            decimalScale={1}
            value={Number(params.value ?? 0.0)}
            onCommit={(val) => updateParam("value", val)}
          />
          <Switch
            label="Estimate from projections"
            checked={Boolean(params.cor_estimation)}
            onChange={(e) => updateParam("cor_estimation", e.currentTarget.checked)}
            mt="xs"
          />
        </Stack>
      )}

      {/* FOURIER-WAVELET DESTRIPING */}
      {operation.id === "fourier-wavelet" && (
        <>
          <DeferredNumberInput
            label="Decomposition Level"
            value={Number(params.level ?? 5)}
            onCommit={(val) => updateParam("level", val)}
          />
          <DeferredNumberInput
            label="Damping Factor (Sigma / Parameter)"
            decimalScale={2}
            value={Number(params.sigma ?? params.parameter ?? 0.1)}
            onCommit={(val) => updateParam("parameter", val, "sigma")}
          />
        </>
      )}

      {/* VO'S SORTING DESTRIPING */}
      {operation.id === "vo-sorting" && (
        <>
          <DeferredNumberInput
            label="Filter Window Size"
            value={Number(params.window ?? 21)}
            onCommit={(val) => updateParam("window", val)}
          />
          <DeferredNumberInput
            label="Filtering Strength"
            decimalScale={2}
            value={Number(params.strength ?? 0.6)}
            onCommit={(val) => updateParam("strength", val)}
          />
        </>
      )}

      {/* NEURAL DESTRIPING */}
      {operation.id === "neural" && (
        <>
          <Select
            label="Neural Model"
            data={["Default", "DeepStriping-v1", "U-Net-Tomo"]}
            value={String(params.model ?? "Default")}
            onChange={(next) => next && updateParam("model", next)}
          />
          <DeferredNumberInput
            label="Model Strength"
            decimalScale={2}
            value={Number(params.strength ?? 0.5)}
            onCommit={(val) => updateParam("strength", val)}
          />
        </>
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