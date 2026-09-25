import {
  Accordion,
  ActionIcon,
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
  Tooltip,
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

function FieldLabel({ label, tooltip }: { label: string; tooltip: string }) {
  return (
    <Group gap={4} align="center" mb={2}>
      <Text size="sm" fw={500}>
        {label}
      </Text>
      <Tooltip label={tooltip} multiline w={240} withArrow position="right">
        <ActionIcon variant="subtle" color="gray" size="xs" aria-label={label}>
          🛈
        </ActionIcon>
      </Tooltip>
    </Group>
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
            <FieldLabel
              label="Dark Reference"
              tooltip="Path to dark field image or 'Auto' to automatically find and average dark frames."
            />
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
            <FieldLabel
              label="Flat Reference"
              tooltip="Path to flat field image or 'Auto' to automatically find and average flat frames."
            />
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
          <div>
            <FieldLabel
              label="Threshold"
              tooltip="Upper bound intensity clipping value to eliminate extreme beam hardening or unattenuated ray spikes."
            />
            <DeferredNumberInput
              decimalScale={2}
              value={Number(params.max_value ?? params.threshold ?? 1.0)}
              onCommit={(val) => updateParam("threshold", val, "max_value")}
            />
          </div>
          <div>
            <FieldLabel
              label="Mode"
              tooltip="'Manual' uses the specified threshold value; 'Auto' estimates threshold from intensity percentiles."
            />
            <Select
              data={["Manual", "Auto"]}
              value={String(params.mode ?? "Manual")}
              onChange={(next) => next && updateParam("mode", next)}
            />
          </div>
        </>
      )}

      {/* FOV MASK */}
      {operation.id === "fov-mask" && (
        <>
          <div>
            <FieldLabel
              label="Radius / Margin"
              tooltip="Normalized field-of-view radius (e.g. 0.95 = 95% of beam area)."
            />
            <DeferredNumberInput
              decimalScale={2}
              value={Number(params.radius ?? params.margin ?? 0.95)}
              onCommit={(val) => updateParam("margin", val, "radius")}
            />
          </div>
          <Group grow align="flex-start">
            <div>
              <FieldLabel
                label="Center X"
                tooltip="Horizontal offset of the circular beam mask center."
              />
              <DeferredNumberInput
                value={Number(params.center_x ?? 0)}
                onCommit={(val) => updateParam("center_x", val)}
              />
            </div>
            <div>
              <FieldLabel
                label="Center Y"
                tooltip="Vertical offset of the circular beam mask center."
              />
              <DeferredNumberInput
                value={Number(params.center_y ?? 0)}
                onCommit={(val) => updateParam("center_y", val)}
              />
            </div>
          </Group>
        </>
      )}

      {/* CROP & PAD BEAM */}
      {operation.id === "crop-pad-beam" && (
        <>
          <div>
            <FieldLabel
              label="Padding (px)"
              tooltip="Number of pixels padded at the sinogram boundaries to prevent circular FBP reconstruction artifacts."
            />
            <DeferredNumberInput
              value={Number(params.pad ?? 128)}
              onCommit={(val) => updateParam("pad", val)}
            />
          </div>
          <div>
            <FieldLabel
              label="Edge Average Window (px)"
              tooltip="Number of outer boundary pixels averaged to create smooth padding transitions."
            />
            <DeferredNumberInput
              value={Number(params.navg ?? 8)}
              onCommit={(val) => updateParam("navg", val)}
            />
          </div>
        </>
      )}

      {/* MUTATE PROJECTIONS */}
      {operation.id === "mutate" && (
        <Stack gap="xs">
          <div>
            <FieldLabel
              label="New Projection Count"
              tooltip="Target angular resampling count for angular downsampling or interpolation."
            />
            <DeferredNumberInput
              decimalScale={1}
              value={Number(params.new_count ?? 0.0)}
              onCommit={(val) => updateParam("new_count", val)}
            />
          </div>
          <Switch
            label="Estimate from sinogram"
            checked={Boolean(params.auto)}
            onChange={(e) => updateParam("auto", e.currentTarget.checked)}
            mt="xs"
          />
        </Stack>
      )}

      {/* DENOISE */}
      {operation.id === "denoise" && (
        <>
          <div>
            <FieldLabel
              label="Method"
              tooltip="Spatial filter type: Median (preserves sharp edges) or Gaussian (smooths high-frequency noise)."
            />
            <Select
              data={["median", "gaussian"]}
              value={String(params.method ?? "median")}
              onChange={(next) => next && updateParam("method", next)}
            />
          </div>
          {params.method === "gaussian" ? (
            <div>
              <FieldLabel
                label="Sigma"
                tooltip="Standard deviation for Gaussian kernel smoothing."
              />
              <DeferredNumberInput
                decimalScale={2}
                value={Number(params.sigma ?? 1.0)}
                onCommit={(val) => updateParam("sigma", val)}
              />
            </div>
          ) : (
            <div>
              <FieldLabel
                label="Kernel Size"
                tooltip="Median filter window width in pixels (must be an odd integer, e.g., 3, 5)."
              />
              <DeferredNumberInput
                value={Number(params.kernel_size ?? 3)}
                onCommit={(val) => updateParam("kernel_size", val)}
              />
            </div>
          )}
        </>
      )}

      {/* CENTER OF ROTATION */}
      {operation.id === "cor_shift" && (
        <Stack gap="xs">
          <div>
            <FieldLabel
              label="Center of rotation value"
              tooltip="Rotation axis location on the detector in pixels. Incorrect values cause tuning fork / double edge artifacts."
            />
            <DeferredNumberInput
              decimalScale={1}
              value={Number(params.value ?? 0.0)}
              onCommit={(val) => updateParam("value", val)}
            />
          </div>
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
          <div>
            <FieldLabel
              label="Decomposition Level"
              tooltip="Wavelet transform decomposition depth. Higher levels isolate broader ring artifacts."
            />
            <DeferredNumberInput
              value={Number(params.level ?? 5)}
              onCommit={(val) => updateParam("level", val)}
            />
          </div>
          <div>
            <FieldLabel
              label="Damping Factor (Sigma / Parameter)"
              tooltip="Gaussian damping factor in Fourier space. Higher values remove stronger stripes but risk blurring."
            />
            <DeferredNumberInput
              decimalScale={2}
              value={Number(params.sigma ?? params.parameter ?? 0.1)}
              onCommit={(val) => updateParam("parameter", val, "sigma")}
            />
          </div>
        </>
      )}

      {/* VO'S SORTING DESTRIPING */}
      {operation.id === "vo-sorting" && (
        <>
          <div>
            <FieldLabel
              label="Filter Window Size"
              tooltip="Moving average window width for Vo's sorting destriping algorithm."
            />
            <DeferredNumberInput
              value={Number(params.window ?? 21)}
              onCommit={(val) => updateParam("window", val)}
            />
          </div>
          <div>
            <FieldLabel
              label="Filtering Strength"
              tooltip="Relative response filtering strength for detecting ring artifacts."
            />
            <DeferredNumberInput
              decimalScale={2}
              value={Number(params.strength ?? 0.6)}
              onCommit={(val) => updateParam("strength", val)}
            />
          </div>
        </>
      )}

      {/* NEURAL DESTRIPING */}
      {operation.id === "neural" && (
        <>
          <div>
            <FieldLabel
              label="Neural Model"
              tooltip="Pretrained deep learning model architecture for ring artifact removal."
            />
            <Select
              data={["Default", "DeepStriping-v1", "U-Net-Tomo"]}
              value={String(params.model ?? "Default")}
              onChange={(next) => next && updateParam("model", next)}
            />
          </div>
          <div>
            <FieldLabel
              label="Model Strength"
              tooltip="Blending weight between original and deep learning corrected sinograms."
            />
            <DeferredNumberInput
              decimalScale={2}
              value={Number(params.strength ?? 0.5)}
              onCommit={(val) => updateParam("strength", val)}
            />
          </div>
        </>
      )}

      {/* UNSUPERVISED INR DESTRIPING (Shi et al., 2024) */}
      {(operation.id === "ring_filter_inr" || operation.id === "ring-filter-inr") && (
        <>
          <div>
            <FieldLabel
              label="Iterations"
              tooltip="Total optimization steps. Use ~1000 for fast previewing or 3000-5000 for final reconstruction."
            />
            <DeferredNumberInput
              value={Number(params.iterations ?? 1500)}
              step={100}
              min={100}
              max={10000}
              onCommit={(val) => updateParam("iterations", val)}
            />
          </div>

          <div>
            <FieldLabel
              label="Learning Rate (lr)"
              tooltip="Optimizer step size for coordinate feature grids (default: 1e-4)."
            />
            <DeferredNumberInput
              decimalScale={6}
              step={0.00005}
              value={Number(params.lr ?? 0.0001)}
              onCommit={(val) => updateParam("lr", val)}
            />
          </div>

          <div>
            <FieldLabel
              label="Residual Factor (kappa)"
              tooltip="Controls high-frequency detail re-injection (0.0 = low noise, 0.5 = balanced, 1.0 = maximum edge sharpness)."
            />
            <DeferredNumberInput
              decimalScale={2}
              step={0.05}
              max={1.0}
              value={Number(params.kappa ?? 0.5)}
              onCommit={(val) => updateParam("kappa", val)}
            />
          </div>

          <div>
            <FieldLabel
              label="Stripe Mode"
              tooltip="'matrix' fits a 2D spatially varying artifact matrix (recommended for real micro-CT). 'column' enforces strict 1D detector column offsets."
            />
            <Select
              data={[
                { value: "matrix", label: "Matrix (2D spatially varying)" },
                { value: "column", label: "Column (1D detector constant)" },
              ]}
              value={String(params.stripe_mode ?? "matrix")}
              onChange={(next) => next && updateParam("stripe_mode", next)}
            />
          </div>

          <div>
            <FieldLabel
              label="Defect Threshold"
              tooltip="Angular difference threshold for detecting and masking dead or non-responsive detector columns (default: 1e-6)."
            />
            <DeferredNumberInput
              decimalScale={8}
              step={1e-7}
              value={Number(params.defect_threshold ?? 0.000001)}
              onCommit={(val) => updateParam("defect_threshold", val)}
            />
          </div>
        </>
      )}
    </Stack>
  );
}