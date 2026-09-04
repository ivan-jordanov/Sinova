import { create } from "zustand";
import type { DatasetMetadata } from "../types/dataset";
import { mockDataset } from "../api/mockData";
interface DatasetState {
  metadata: DatasetMetadata;
  loading: boolean;
  available: boolean;
}
export const useDatasetStore = create<DatasetState>(() => ({
  metadata: mockDataset,
  loading: false,
  available: true,
}));
