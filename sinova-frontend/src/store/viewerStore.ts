import { create } from "zustand";
import type { DataContext, ViewerDataMode } from "../types/preprocessing";
interface ViewerState {
  context: DataContext;
  mode: ViewerDataMode;
  zoom: number;
  contrast: [number, number];
  crosshair: boolean;
  setContext: (context: DataContext) => void;
  setMode: (mode: ViewerDataMode) => void;
  resetZoom: () => void;
}
// Zustand is used for synchronous UI state such as context, zoom, and contrast.
// Components subscribe only to this store; server requests stay in React Query.
export const useViewerStore = create<ViewerState>((set) => ({
  context: "sinogram",
  mode: "current",
  zoom: 1,
  contrast: [0, 1],
  crosshair: true,
  setContext: (context) => set({ context }),
  setMode: (mode) => set({ mode }),
  resetZoom: () => set({ zoom: 1 }),
}));
