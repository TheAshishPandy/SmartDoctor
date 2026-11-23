"use client";
import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";
import { AuthProvider } from "./auth-provider";
import { AppThemeProvider } from "./app-theme-provider";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
      <AuthProvider>
        <AppThemeProvider>
          {children}
          <Toaster position="top-right" richColors closeButton />
        </AppThemeProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
