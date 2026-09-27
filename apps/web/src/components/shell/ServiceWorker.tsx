"use client";
import { useEffect } from "react";
import { registerServiceWorker } from "@/lib/push-browser";

export function ServiceWorker() {
  useEffect(() => {
    if (window.isSecureContext && "serviceWorker" in navigator) {
      void registerServiceWorker().catch(() => { /* Retry on the next visit or notification action. */ });
    }
  }, []);
  return null;
}
