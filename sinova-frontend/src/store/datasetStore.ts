import { create } from "zustand";
import type { DatasetMetadata } from "../types/dataset";
interface DatasetState {
  metadata: DatasetMetadata | null;
  selectedFile: File | null;
  // Declare the action on the state interface
  setDataset: (file: File) => void;
  clearDataset: () => void;
}

export const useDatasetStore = create<DatasetState>((set) => ({
  metadata: null,
  selectedFile: null,

  setDataset: (file: File) =>
    set({
      selectedFile: file,
      metadata: {
        name: file.name,
        // Stores path if running under Electron, or fallback name
        path: (file as File & { path?: string }).path || file.name,
      },
    }),

  clearDataset: () =>
    set({
      metadata: null,
      selectedFile: null,
    }),
}));