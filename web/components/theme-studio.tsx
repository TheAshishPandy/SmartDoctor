"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, Building2, Check, CheckCircle2, Cloud, Palette, RefreshCw, Save, Sparkles, WandSparkles } from "lucide-react";
import { toast } from "sonner";
import { useAppTheme, type ThemeOption, type ThemePreset } from "./app-theme-provider";
import { AnimatedButton, AnimatedCard, AnimatedReveal, StatusBadge } from "./ui/motion";

type Organization = { id: string; name: string; status: string; staff_count: number };
const API = "/api/backend/api/v1/";

export function ThemeStudio() {
  const { preset, themes: providerThemes, setPreview, refresh } = useAppTheme();
  const [themes, setThemes] = useState<ThemeOption[]>(providerThemes);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selected, setSelected] = useState<ThemePreset>(preset);
  const [previewPreset, setPreviewPreset] = useState<ThemePreset>(preset);
  const [organizationId, setOrganizationId] = useState("");
  const [organizationPreset, setOrganizationPreset] = useState("inherit");
  const [globalPreset, setGlobalPreset] = useState<ThemePreset>(preset);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const request = useCallback(async (path: string, init?: RequestInit) => {
    const response = await fetch(API + path, { ...init, cache: "no-store", headers: { ...(init?.body ? { "content-type": "application/json" } : {}), ...init?.headers } });
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.detail || "Theme request failed");
    return data;
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [global, orgs] = await Promise.all([request("super-admin/theme"), request("super-admin/organizations")]);
      setThemes(global.themes || providerThemes);
      setGlobalPreset(global.preset);
      setSelected(global.preset);
      setPreview(global.preset);
      setPreviewPreset(global.preset);
      setOrganizations(orgs);
    } catch (error) { toast.error(error instanceof Error ? error.message : "Unable to load Theme Studio"); }
    finally { setLoading(false); }
  }, [providerThemes, request, setPreview]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => { if (organizationId) void request(`super-admin/organizations/${organizationId}/theme`).then(data => { setOrganizationPreset(data.preset); setPreview(data.effective_preset as ThemePreset); setPreviewPreset(data.effective_preset as ThemePreset); }).catch(error => toast.error(error instanceof Error ? error.message : "Unable to load clinic theme")); }, [organizationId, request, setPreview]);

  const activeTheme = useMemo(() => themes.find(theme => theme.id === previewPreset), [themes, previewPreset]);
  const choose = (id: ThemePreset) => { setSelected(id); setPreview(id); setPreviewPreset(id); };

  const saveGlobal = async () => {
    setSaving(true);
    try { await request("super-admin/theme", { method: "PATCH", body: JSON.stringify({ preset: selected }) }); setGlobalPreset(selected); await refresh(); toast.success("Platform theme published to all inheriting organizations."); }
    catch (error) { toast.error(error instanceof Error ? error.message : "Unable to publish theme"); }
    finally { setSaving(false); }
  };

  const saveOrganization = async () => {
    if (!organizationId) { toast.error("Choose an organization first."); return; }
    setSaving(true);
    try { const data = await request(`super-admin/organizations/${organizationId}/theme`, { method: "PATCH", body: JSON.stringify({ preset: organizationPreset }) }); await refresh(); setPreview(data.effective_preset as ThemePreset); setPreviewPreset(data.effective_preset as ThemePreset); toast.success("Organization theme assignment saved."); }
    catch (error) { toast.error(error instanceof Error ? error.message : "Unable to save organization theme"); }
    finally { setSaving(false); }
  };

  return <section className="theme-studio" aria-labelledby="theme-studio-title">
    <div className="theme-studio-header"><div><p className="theme-kicker"><Sparkles size={14}/> PLATFORM DESIGN SYSTEM</p><h2 id="theme-studio-title">Theme Studio</h2><p>Control the visual experience across SmartDoctor and every clinic workspace.</p></div><div className="theme-header-actions"><StatusBadge tone="success">Live preview</StatusBadge><AnimatedButton className="theme-quiet-button" onClick={() => void load()}><RefreshCw size={15}/> Refresh</AnimatedButton></div></div>
    <div className="theme-studio-grid">
      <div className="theme-library-panel"><div className="theme-section-title"><div><h3><Palette size={17}/> Theme library</h3><p>Choose a preset to preview it instantly.</p></div><span className="theme-count">{themes.length} presets</span></div>
        {loading ? <div className="theme-loading"><span className="theme-spinner"/> Loading design system…</div> : <div className="theme-preset-grid">{themes.map((theme, index) => <AnimatedCard key={theme.id} className={`theme-preset-card ${selected === theme.id ? "selected" : ""}`}><button type="button" className="theme-preset-select" onClick={() => choose(theme.id)} aria-pressed={selected === theme.id}><div className="theme-swatch" style={{ background: theme.colors.background, borderColor: theme.colors.border }}><div className="theme-swatch-sidebar" style={{ background: theme.colors.surface }}><i style={{ background: theme.colors.primary }}/><i/><i/></div><div className="theme-swatch-content"><b style={{ background: theme.colors.text }}/><span style={{ background: theme.colors.border }}/><span style={{ background: theme.colors.tint }}/><em style={{ background: theme.colors.primary }}/></div><span className="theme-swatch-check" style={{ background: theme.colors.primary }}>{selected === theme.id ? <Check size={13}/> : index + 1}</span></div><div className="theme-preset-meta"><span><b>{theme.name}</b><small>{theme.description}</small></span>{selected === theme.id && <CheckCircle2 size={17} className="theme-selected-icon"/>}</div></button></AnimatedCard>)}</div>}
        <div className="theme-publish-row"><div><b>Platform default</b><small>Currently published: {themes.find(t => t.id === globalPreset)?.name || globalPreset}</small></div><AnimatedButton className="theme-primary-button" onClick={() => void saveGlobal()} disabled={saving || loading}><Save size={15}/>{saving ? "Saving…" : "Publish globally"}</AnimatedButton></div>
      </div>
      <div className="theme-preview-column"><AnimatedReveal className="theme-preview-card"><div className="theme-preview-top"><div><span className="theme-preview-label"><WandSparkles size={13}/> LIVE CANVAS</span><h3>{activeTheme?.name || "Theme preview"}</h3><p>{activeTheme?.description || "Preview your selected design tokens."}</p></div><span className="preview-live-dot"/></div><div className="theme-mini-dashboard" style={{ background: activeTheme?.colors.background, color: activeTheme?.colors.text }}><div className="mini-topbar" style={{ background: activeTheme?.colors.surface, borderColor: activeTheme?.colors.border }}><span className="mini-logo" style={{ background: activeTheme?.colors.primary }}>✚</span><b>SmartDoctor</b><i/><span>•••</span></div><div className="mini-body"><small>CLINIC OVERVIEW</small><h4>Good morning, Doctor</h4><div className="mini-stat-row"><div style={{ background: activeTheme?.colors.surface, borderColor: activeTheme?.colors.border }}><span>Appointments</span><b>24</b><em style={{ color: activeTheme?.colors.primary }}>+12.5%</em></div><div style={{ background: activeTheme?.colors.surface, borderColor: activeTheme?.colors.border }}><span>Patients</span><b>1,284</b><em style={{ color: activeTheme?.colors.primary }}>Active</em></div></div><div className="mini-chart" style={{ background: activeTheme?.colors.surface, borderColor: activeTheme?.colors.border }}><span>Weekly activity</span><div>{[35, 58, 42, 78, 54, 88, 66].map((height, i) => <i key={i} style={{ height: `${height}%`, background: activeTheme?.colors.primary, opacity: .35 + i * .09 }}/>)}</div></div><button type="button" style={{ background: activeTheme?.colors.primary }}>View schedule <Activity size={12}/></button></div></div><div className="theme-token-row">{activeTheme && Object.entries(activeTheme.colors).map(([name, color]) => <span key={name} title={`${name}: ${color}`}><i style={{ background: color }}/><small>{name}</small></span>)}</div></AnimatedReveal>
        <div className="theme-org-panel"><div className="theme-section-title"><div><h3><Building2 size={17}/> Organization themes</h3><p>Assign a clinic-specific preset or inherit the platform default.</p></div></div><label className="theme-field-label" htmlFor="theme-organization">Organization</label><select id="theme-organization" value={organizationId} onChange={event => setOrganizationId(event.target.value)}><option value="">Select an organization…</option>{organizations.map(org => <option key={org.id} value={org.id}>{org.name}</option>)}</select><label className="theme-field-label" htmlFor="theme-org-preset">Theme assignment</label><select id="theme-org-preset" value={organizationPreset} onChange={event => setOrganizationPreset(event.target.value)} disabled={!organizationId}><option value="inherit">Inherit platform default</option>{themes.map(theme => <option key={theme.id} value={theme.id}>{theme.name}</option>)}</select><div className="theme-org-footer"><span><Cloud size={14}/> Saved per organization</span><AnimatedButton className="theme-primary-button" onClick={() => void saveOrganization()} disabled={!organizationId || saving}><Save size={15}/> Save assignment</AnimatedButton></div></div>
      </div>
    </div>
    <div className="theme-studio-note"><CheckCircle2 size={16}/><span>Theme settings only affect presentation. Clinical permissions, patient consent, organization boundaries and workflows remain unchanged.</span></div>
  </section>;
}
