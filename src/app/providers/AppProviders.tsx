import {
  QueryClient,
  QueryClientProvider,
  QueryCache,
  MutationCache,
} from "@tanstack/react-query";
import { ReactNode, useState } from "react";
import { BrowserRouter } from "react-router-dom";
import { AuthSessionProvider } from "@/features/auth/session/AuthSessionProvider";

type AppProvidersProps = {
  children: ReactNode;
};

export function AppProviders({ children }: AppProvidersProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        queryCache: new QueryCache(),
        mutationCache: new MutationCache(),
        defaultOptions: {
          queries: {
            retry: 1,
            refetchOnWindowFocus: false,
            staleTime: 30_000,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthSessionProvider>
        <BrowserRouter>{children}</BrowserRouter>
      </AuthSessionProvider>
    </QueryClientProvider>
  );
}
