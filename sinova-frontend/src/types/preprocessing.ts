export type OperationCategory =
  | "intensity"
  | "spatial"
  | "geometry"
  | "destriping";
export type OperationScope = "slice" | "stack" | "dataset";
export type DataContext = "projection" | "sinogram";
export type ViewerDataMode = "current" | "original";
export interface PreprocessingOperation {
  id: string;
  name: string;
  shortName: string;
  category: OperationCategory;
  description: string;
  enabled: boolean;
  scope: OperationScope;
  parameters: Record<string, string | number | boolean>;
}
export interface PreviewSession {
  selectedSlice: number;
  totalSlices: number;
  dirty: boolean;
  previewMode: boolean;
}
export interface PreprocessingConfig {
  operations: PreprocessingOperation[];
}
export const initialOperations: PreprocessingOperation[] = [
  {
    id: "normalization",
    name: "Normalization",
    shortName: "normalize", // Changed from "Normalization" to match backend short_name
    category: "intensity",
    description: "Correct detector response using dark and flat references.",
    enabled: false,
    scope: "slice",
    parameters: { dark: "Auto", flat: 0, logarithm: true },
  },
  {
    id: "attenuation",
    name: "Attenuation Clipping",
    shortName: "clip_attenuation",
    category: "intensity",
    description: "Limit high attenuation values before downstream processing.",
    enabled: false,
    scope: "slice",
    parameters: { threshold: 4.5, mode: "Manual" },
  },
  {
    id: "fov-mask",
    name: "FOV / Beam Mask",
    shortName: "fov_mask",
    category: "spatial",
    description: "Define the useful detector field of view.",
    enabled: false,
    scope: "dataset",
    parameters: { boundary: "Auto", margin: 5, taper: "Gaussian" },
  },
  {
    id: "edge-taper",
    name: "Edge Taper",
    shortName: "edge_enhance",
    category: "spatial",
    description: "Soften detector edges to reduce boundary artifacts.",
    enabled: false,
    scope: "slice",
    parameters: { width: 12, window: "Cosine" },
  },
  {
    id: "cor",
    name: "Center of Rotation",
    shortName: "cor",
    category: "geometry",
    description: "Set the detector center used by geometry-aware operations.",
    enabled: false,
    scope: "dataset",
    parameters: { value: 1024.5 },
  },
  {
    id: "fourier-wavelet",
    name: "Fourier-Wavelet",
    shortName: "ring_filter",
    category: "destriping",
    description: "Preview a frequency and wavelet-based destriping configuration.",
    enabled: false,
    scope: "slice",
    parameters: { level: 5, sigma: 2 },
  },
  {
    id: "vo-sorting",
    name: "Vo's Sorting",
    shortName: "ring_filter",
    category: "destriping",
    description: "Configure the Vo sorting destriping method.",
    enabled: false,
    scope: "slice",
    parameters: { window: 21, strength: 0.6 },
  },
  {
    id: "neural",
    name: "Neural Destriping",
    shortName: "denoise",
    category: "destriping",
    description: "Placeholder for a future neural destriping model.",
    enabled: false,
    scope: "slice",
    parameters: { model: "Default", strength: 0.5 },
  },
];