import { Providers } from "./providers";
import { MainLayout } from "../components/layout/MainLayout";
export function App() {
  return (
    <Providers>
      <MainLayout />
    </Providers>
  );
}
