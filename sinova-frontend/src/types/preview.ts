import type { DataContext, PreprocessingConfig } from "./preprocessing";
export interface PreviewRequest {
  context: DataContext;
  slice: number;
  configuration: PreprocessingConfig;
  mode: "current" | "original";
}
export interface PreviewResult {
  context: DataContext;
  width: number;
  height: number;
  data: ArrayBuffer;
  requestId: string;
  message: string;
}
