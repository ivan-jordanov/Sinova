import type { DataContext, PreprocessingConfig } from "./preprocessing";

export interface PreviewRequest {
  context: DataContext;
  slice: number;
  configuration: PreprocessingConfig;
  mode: "current" | "original";
}

export type PreviewParams = {
  slice: number;
  configuration: PreprocessingConfig;
  mode?: "current" | "original";
};

export interface PreviewResult {
  context: DataContext;
  width: number;
  height: number;
  data: Float32Array;
  minVal?: number;
  maxVal?: number;
  requestId: string;
  message: string;
}

export interface SinogramViewerProps {
  data?: PreviewResult;
  isLoading: boolean;
  colormap?: string;
}

export interface ProjectionViewerProps {
  data?: PreviewResult;
  isLoading: boolean;
  colormap?: string;
}

export interface ImageStats {
  min: number;
  max: number;
  mean: number;
  stdDev: number;
  snr: number;
}

export interface LineProfileProps {
  data?: PreviewResult;
  isLoading?: boolean;
}