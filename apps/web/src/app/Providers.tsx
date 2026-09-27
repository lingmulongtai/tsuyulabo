"use client";
import { useState, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ServiceWorker } from "@/components/shell/ServiceWorker";

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(() => new QueryClient({ defaultOptions: {
    queries: { staleTime: 15_000, refetchOnWindowFocus: true }, mutations: { retry: false },
  } }));
  return <QueryClientProvider client={client}><ServiceWorker />{children}</QueryClientProvider>;
}
