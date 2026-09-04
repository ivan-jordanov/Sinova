import { ColorSchemeScript, MantineProvider } from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { theme } from "../theme/theme";
import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";

// QueryClient owns cached server data, request status, retries, and refetching.
// It is intentionally separate from Zustand, which owns local workspace state.
const queryClient = new QueryClient();
export function Providers({ children }: { children: ReactNode }) {
  return (
    // QueryClientProvider makes useQuery/useMutation available to descendants.
    <QueryClientProvider client={queryClient}>
      {/* MantineProvider supplies theme, color scheme, and component defaults. */}
      <ColorSchemeScript defaultColorScheme="dark" />
      <MantineProvider theme={theme} defaultColorScheme="dark">
        <Notifications position="bottom-right" />
        {children}
      </MantineProvider>
    </QueryClientProvider>
  );
}
