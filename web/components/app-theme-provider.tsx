"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useAuth } from "./auth-provider";

export type ThemePreset = "clinical-light" | "midnight-care" | "sage-wellness" | "ocean-blue" | "violet-glass" | "warm-sand";
export type ThemeOption = { id: ThemePreset; name: string; description: string; colors: { background: string; surface: string; primary: string; text: string; tint: string; border: string } };
type ThemeContextValue = { preset: ThemePreset; themes: ThemeOption[]; source: string; loading: boolean; setPreview: (preset: ThemePreset) => void; refresh: () => Promise<void> };
const ThemeContext = createContext<ThemeContextValue | null>(null);
const FALLBACK: ThemePreset = "clinical-light";

export function AppThemeProvider({ children }: { children: React.ReactNode }) {
  const { user, loading: authLoading } = useAuth();
  const [preset, setPreset] = useState<ThemePreset>(FALLBACK);
  const [themes, setThemes] = useState<ThemeOption[]>([]);
  const [source, setSource] = useState("global");
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState<ThemePreset | null>(null);

  const refresh = useCallback(async () => {
    if (!user) { setPreset(FALLBACK); setPreview(null); setLoading(false); return; }
    try {
      const response = await fetch("/api/backend/api/v1/themes/active", { cache: "no-store" });
      if (!response.ok) throw new Error("Theme settings unavailable");
      const data = await response.json();
      if (data.preset) setPreset(data.preset as ThemePreset);
      if (Array.isArray(data.themes)) setThemes(data.themes);
      setSource(data.source || "global");
    } catch { setPreset(FALLBACK); }
    finally { setLoading(false); }
  }, [user]);

  useEffect(() => { if (!authLoading) void refresh(); }, [authLoading, refresh]);
  const applied = preview || preset;
  useEffect(() => {
    document.documentElement.dataset.themePreset = applied;
    document.documentElement.dataset.themeSource = source;
    document.documentElement.style.colorScheme = applied === "midnight-care" ? "dark" : "light";
  }, [applied, source]);

  const value = useMemo(() => ({ preset: applied, themes, source, loading, setPreview: (next: ThemePreset) => setPreview(next), refresh }), [applied, themes, source, loading, refresh]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useAppTheme() {
  const value = useContext(ThemeContext);
  if (!value) throw new Error("useAppTheme must be used within AppThemeProvider");
  return value;
}
