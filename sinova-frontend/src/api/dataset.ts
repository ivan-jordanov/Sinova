import type { DatasetMetadata } from "../types/dataset";
import { apiClient } from "./client";
import type { BackendDatasetMetadata } from "../types/datasetBackend.ts";

// Helper mapper to transform snake_case backend response to camelCase frontend model
function mapMetadata(data: BackendDatasetMetadata): DatasetMetadata {
  return {
    name: data.name,
    detectorWidth: data.detector_width,
    detectorHeight: data.detector_height,
    projections: data.projections,
    slices: data.slices,
    format: data.format,
  };
}

export async function browseDatasetFile(): Promise<string> {
  const response = await apiClient.request<{ path: string }>("/ingestion/browse", {
    method: "POST",
  });
  return response.path;
}

/**
 * Loads a dataset from a given file path.
 * Calls POST /load with { path: filePath } and returns the dataset metadata.
 */
// Triggers native Tkinter file picker on the local host machine
// Submits the full path string to the existing backend ingestion route
export async function loadDataset(filePath: string): Promise<DatasetMetadata> {
  const data = await apiClient.request<BackendDatasetMetadata>("/ingestion/load", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ path: filePath }),
  });

  return mapMetadata(data);
}

/**
 * Retrieves metadata for the currently active/loaded dataset.
 * Calls GET /ingestion/metadata.
 */
export async function getDatasetMetadata(): Promise<DatasetMetadata> {
  const data = await apiClient.request<BackendDatasetMetadata>("/ingestion/metadata");
  return mapMetadata(data);
}

export interface BackendHealth {
  status: string;
  service: string;
}

export function getBackendHealth() {
  return apiClient.request<BackendHealth>("/health");
}