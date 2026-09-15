import { create } from "zustand";
import type { DatasetMetadata } from "../types/dataset";

interface DatasetState {
  metadata: DatasetMetadata | null;
  selectedFile: File | null;
  setMetadata: (metadata: DatasetMetadata | null) => void;
  updateMetadata: (partial: Partial<DatasetMetadata>) => void;
  setBeamMask: (mask: { cx: number; cy: number; radius: number } | undefined) => void;
  setCOR: (COR: number | undefined) => void;
  setDataset: (file: File) => void;
  clearDataset: () => void;
}

export const useDatasetStore = create<DatasetState>((set) => ({
  metadata: null,
  selectedFile: null,

  setMetadata: (metadata) => set({ metadata }),

  updateMetadata: (partial) =>
    set((state) => ({
      metadata: state.metadata ? { ...state.metadata, ...partial } : null,
    })),

  setBeamMask: (beamMask) =>
    set((state) => ({
      metadata: state.metadata ? { ...state.metadata, beamMask } : null,
    })),
  
  setCOR: (COR) =>
  set((state) => ({
    metadata: state.metadata ? { ...state.metadata, COR } : null,
  })),

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