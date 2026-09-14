export interface DatasetMetadata {
  name: string;
  detectorWidth?: number;
  detectorHeight?: number;
  projections?: number;
  slices?: number;
  format?: string;
  path?: string; // Optional path property to store the file path
  beamMask?: {
    cx: number; 
    cy: number; 
    radius: number;
  }
  COR?: number;
}
