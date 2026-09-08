import { create } from "zustand";
import type { DatasetMetadata } from "../types/dataset";

interface DatasetState {
  metadata: DatasetMetadata | null;
  selectedFile: File | null;
  setMetadata: (metadata: DatasetMetadata | null) => void;
  setDataset: (file: File) => void;
  clearDataset: () => void;
}

export const useDatasetStore = create<DatasetState>((set) => ({
  metadata: null,
  selectedFile: null,

  setMetadata: (metadata) => set({ metadata }),

  setDataset: (file) =>
    set({
      selectedFile: file,
      metadata: {
        name: file.name,
        detectorWidth: 0,
        detectorHeight: 0,
        projections: 0,
        slices: 0,
        format: file.name.split(".").pop() || "",
      },
    }),

  clearDataset: () =>
    set({
      metadata: null,
      selectedFile: null,
    }),
}));