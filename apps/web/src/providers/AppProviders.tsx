"use client";

import { ToastProvider } from "@/components/ui/Toast";
import { ThemeProvider } from "@/providers/ThemeProvider";
import React from "react";

export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <ToastProvider>{children}</ToastProvider>
    </ThemeProvider>
  );
}
