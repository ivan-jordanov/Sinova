import { create } from "zustand";
import { initialOperations } from "../types/preprocessing";
import type {
  PreprocessingOperation,
  PreviewSession,
} from "../types/preprocessing";
interface PreprocessingState {
  operations: PreprocessingOperation[];
  selectedOperationId: string;
  session: PreviewSession;
  past: PreprocessingOperation[][];
  future: PreprocessingOperation[][];
  selectOperation: (id: string) => void;
  toggleOperation: (id: string) => void;
  updateParameter: (
    id: string,
    key: string,
    value: string | number | boolean,
  ) => void;
  undo: () => void;
  redo: () => void;
  selectSlice: (slice: number) => void;
  resetConfiguration: () => void;
  markClean: () => void;
}
const clone = (operations: PreprocessingOperation[]) =>
  operations.map((operation) => ({
    ...operation,
    parameters: { ...operation.parameters },
  }));

// History stores configuration snapshots only; image data never enters Zustand.
const matchesInitial = (operations: PreprocessingOperation[]) =>
  JSON.stringify(operations) === JSON.stringify(initialOperations);
export const usePreprocessingStore = create<PreprocessingState>((set) => {
  // Each committed edit creates one undo step and clears the redo branch.
  const commit = (
    operations: PreprocessingOperation[],
    state: PreprocessingState,
  ) => ({
    operations,
    past: [...state.past, clone(state.operations)],
    future: [],
    session: { ...state.session, dirty: !matchesInitial(operations) },
  });
  return {
    operations: clone(initialOperations),
    selectedOperationId: "normalization",
    session: {
      selectedSlice: 500,
      totalSlices: 2048,
      dirty: false,
      previewMode: true,
    },
    past: [],
    future: [],
    selectOperation: (selectedOperationId) => set({ selectedOperationId }),
    toggleOperation: (id) =>
      set((state) =>
        commit(
          state.operations.map((operation) =>
            operation.id === id
              ? { ...operation, enabled: !operation.enabled }
              : operation,
          ),
          state,
        ),
      ),
    updateParameter: (id, key, value) =>
      set((state) =>
        commit(
          state.operations.map((operation) =>
            operation.id === id
              ? {
                  ...operation,
                  parameters: { ...operation.parameters, [key]: value },
                }
              : operation,
          ),
          state,
        ),
      ),
    undo: () =>
      set((state) => {
        const previous = state.past.at(-1);
        return previous
          ? {
              operations: clone(previous),
              past: state.past.slice(0, -1),
              future: [clone(state.operations), ...state.future],
              session: { ...state.session, dirty: !matchesInitial(previous) },
            }
          : state;
      }),
    redo: () =>
      set((state) => {
        const next = state.future[0];
        return next
          ? {
              operations: clone(next),
              past: [...state.past, clone(state.operations)],
              future: state.future.slice(1),
              session: { ...state.session, dirty: !matchesInitial(next) },
            }
          : state;
      }),
    selectSlice: (selectedSlice) =>
      set((state) => ({
        session: {
          ...state.session,
          selectedSlice: Math.max(
            0,
            Math.min(selectedSlice, state.session.totalSlices - 1),
          ),
        },
      })),
    resetConfiguration: () =>
      set((state) => ({
        operations: clone(initialOperations),
        session: { ...state.session, dirty: false },
        past: [],
        future: [],
      })),
    markClean: () =>
      set((state) => ({
        session: { ...state.session, dirty: false },
        past: [],
        future: [],
      })),
  };
});
