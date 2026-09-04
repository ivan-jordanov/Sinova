import type { DatasetMetadata } from "../types/dataset";
import { apiClient } from "./client";
import { mockDataset } from "./mockData";

interface BackendDatasetMetadata {
  name: string;
  detector_width: number;
  detector_height: number;
  projections: number;
  slices: number;
  format: string;
}

export async function getDatasetMetadata(): Promise<DatasetMetadata> {
  try {
    const data = await apiClient.request<BackendDatasetMetadata>("/ingestion/metadata");
    return {
      name: data.name,
      detectorWidth: data.detector_width,
      detectorHeight: data.detector_height,
      projections: data.projections,
      slices: data.slices,
      format: data.format,
    };
  } catch {
    return mockDataset;
  }
}

export interface BackendHealth { status: string; service: string }
export function getBackendHealth() {
  return apiClient.request<BackendHealth>("/health");
}
