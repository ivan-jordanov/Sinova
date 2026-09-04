import type { DatasetMetadata } from "../types/dataset";
import { mockDataset } from "./mockData";
export async function getDatasetMetadata(): Promise<DatasetMetadata> {
  return mockDataset;
}
