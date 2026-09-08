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

