import { Providers } from "./providers";
import { MainLayout } from "../components/layout/MainLayout";
import { useHydrateDataset } from "../hooks/useHydrateDataset";

function AppContent() {
  // Checks backend for active dataset on app load/reload and syncs Zustand store
  useHydrateDataset();

  return <MainLayout />;
}

export function App() {
  return (
    <Providers>
      <AppContent />
    </Providers>
  );
}