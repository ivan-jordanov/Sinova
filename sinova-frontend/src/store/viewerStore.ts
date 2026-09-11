import { create } from "zustand";
import type { DataContext, ViewerDataMode } from "../types/preprocessing";

interface ViewerState {
  context: DataContext;
  mode: ViewerDataMode;
  colormap: string;
  zoom: number;
  resetCounter: number;
  contrast: [number, number];
  crosshair: boolean;
  setContext: (context: DataContext) => void;
  setMode: (mode: ViewerDataMode) => void;
  setColormap: (colormap: string) => void;
  resetZoom: () => void;
}

// Zustand is used for synchronous UI state such as context, zoom, and contrast.
// Components subscribe only to this store; server requests stay in React Query.
export const useViewerStore = create<ViewerState>((set) => ({
  context: "sinogram",
  mode: "current",
  colormap: "Greys",
  zoom: 1,
  resetCounter: 0,
  contrast: [0, 1],
  crosshair: true,
  setContext: (context) => set({ context }),
  setMode: (mode) => set({ mode }),
  setColormap: (colormap) => set({ colormap }),
  resetZoom: () =>
    set((state) => ({
      zoom: 1,
      resetCounter: state.resetCounter + 1,
    })),
}));