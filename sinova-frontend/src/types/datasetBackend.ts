export interface BackendDatasetMetadata {
  name: string;
  detector_width: number;
  detector_height: number;
  projections: number;
  slices: number;
  format: string;
}

export interface LoadDatasetResponse {
  loaded: boolean;
  metadata: BackendDatasetMetadata;
}