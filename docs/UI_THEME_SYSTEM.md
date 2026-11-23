# SmartDoctor Global UI Theme System

**Status:** Design specification  
**Reference:** [Murmura demo](https://demo.codeandchill.store/murmura/) and [Code and Chill catalogue](https://codeandchill.store/)  
**Prepared:** 2026-11-21

## 1. Reference review and crawl notes

The public Code and Chill catalogue was discoverable and indexed. It describes Murmura as a social-media manager for publishing to eight networks. The broader catalogue advertises dashboard templates and animated UI components, including frosted-glass dashboards, collapsible/dock sidebars, interactive navigation, animated buttons and toggles, OTP fields, sliders, upload/download feedback, chat controls, and animated cards.

**Crawl limitation:** the exact demo URL could not be fetched by the browsing layer during this review (cache-miss response). This document therefore separates catalogue-level observations from the proposed SmartDoctor adaptation. It does not claim to have inspected hidden pages, authenticated states, exact CSS values, or the demo's full DOM.

**Adaptation principle:** reproduce interaction quality and design patterns using original SmartDoctor components. Do not copy proprietary source code, artwork, or assets.

## 2. Design principles

- Premium clinical SaaS: calm, clear, trustworthy, modern.
- Information hierarchy first: patient identity, appointment status, alerts, and next action must be scannable.
- Consistent shell: sidebar, top bar, page header, breadcrumbs, content grid, notifications, responsive mobile navigation.
- Layered surfaces: subtle elevation, restrained translucency, soft borders, and low-noise backgrounds. Glass effects must never reduce readability.
- Purposeful motion: state feedback, navigation continuity, progress, and discoverabilityΓÇönot decoration that delays clinical work.
- Accessibility: WCAG AA contrast, keyboard focus, reduced-motion support, semantic controls, and no color-only status indicators.

## 3. Theme presets

All presets share semantic tokens and component contracts. Themes change token values and optional surface treatment; they never change business logic, permissions, or data.

| Preset | Intent | Canvas | Surface | Primary | Text | Tint |
|---|---|---|---|---|---|---|
| Clinical Light | Clean default | #F5F8FC | #FFFFFF | #176B87 | #172B4D | #E8F3F7 |
| Midnight Care | Dark premium | #0D1422 | #151F31 | #55C7BE | #EAF1FA | #22344C |
| Sage Wellness | Warm natural | #F2F6F0 | #FFFFFF | #477B62 | #20382B | #E3EFE5 |
| Ocean Blue | Professional | #EEF4FB | #FFFFFF | #376ED5 | #1D3154 | #E2ECFC |
| Violet Glass | Expressive glass | #F3F1FA | #FFFFFF | #7657D6 | #292342 | #EAE5FA |
| Warm Sand | Soft neutral | #F7F3ED | #FFFEFC | #B66B42 | #3A3029 | #F1E6D9 |

Additional global controls: light/dark/system mode; compact/comfortable density; border-radius scale; expanded/collapsed sidebar; motion intensity (full/reduced/off).

## 4. Super Admin Theme Studio

Create a platform-level **Appearance & Themes** workspace available only to Super Admin.

- **Theme gallery:** preset cards, previews, names, descriptions, light/dark support, active status.
- **Theme editor:** semantic color tokens, typography, radii, shadows, spacing, density, sidebar style, chart palette, icon treatment, motion profile.
- **Live preview:** Super Admin, Organization Admin, Doctor, Receptionist, Patient, and Chatbot surfaces without mutating real user data.
- **Component playground:** buttons, icon buttons, badges, tabs, inputs, selects, date pickers, tables, dialogs, toasts, charts, empty states, skeletons, chat bubbles, appointment cards.
- **Publishing:** draft, preview, publish, schedule, rollback, duplicate, archive, version history.
- **Scope:** global default; organization override; optional user preference only when allowed by platform policy.
- **Governance:** lock required brand/accessibility tokens, restrict organization overrides, force safe fallback theme.
- **Audit:** actor, old/new values, scope, timestamp, publication version.

## 5. Theme inheritance and precedence

Resolve tokens in this order (highest precedence first):

1. Platform safety/accessibility constraints (not overridable).
2. Explicit user accessibility preference, such as reduced motion or high contrast.
3. Organization theme override, if Super Admin permits it.
4. Platform-wide published theme.
5. Application fallback tokens.

Store theme definitions as versioned JSON token documents and assignments separately. Never execute arbitrary CSS or JavaScript from the database. Validate every theme against a strict schema and allow only approved values.

## 6. Component and icon library

| Family | Building blocks |
|---|---|
| Navigation | Collapsible sidebar, active-route indicator, command/search launcher, top nav, breadcrumbs, mobile bottom bar |
| Actions | Primary/secondary/quiet/danger buttons, icon buttons, split buttons, loading/progress buttons, confirmation actions |
| Forms | Text/email/password, OTP, textarea, combobox, multi-select, date/time, file upload, validation, password strength |
| Data display | Stat cards, trend charts, tables, patient/doctor cards, appointment timeline, status chips, activity feed |
| Overlays | Dialog, drawer, popover, tooltip, command palette, notification tray, contextual action menu |
| Clinical | Patient identity banner, vitals panel, allergy alert, medication list, encounter summary, prescription status, lab result panel |
| Chatbot | Floating launcher, chat panel, message composer, suggested prompts, typing state, booking progress, confirmation |
| Feedback | Toast, inline alert, empty state, skeleton, upload progress, success/error state, offline banner |

Use one consistent outline icon family (Lucide-style stroke icons) with a small set of filled status glyphs. Maintain a central semantic icon registry: calendar, users, stethoscope, prescription, flask, shield, bot, settings, etc. Avoid mixing icon weights or emoji in core clinical navigation.

## 7. Motion specification

| Area | Behavior |
|---|---|
| Micro-interactions | 120ΓÇô180 ms for hover, press, focus, toggle, tooltip, active navigation |
| Panel transitions | 180ΓÇô260 ms for drawers, sidebar collapse, tab switch, popovers, modal entrance |
| Data transitions | 250ΓÇô450 ms for chart updates and counters; respect reduced motion |
| Loading | Skeleton shimmer or subtle pulse; prefer explicit progress when available |
| Success feedback | Short confirmation; reserve celebration for non-clinical completion |
| Drag/resize | Visible handles on hover/focus, snap-to-grid, placeholder outline, keyboard alternatives, save/reset |
| Reduced motion | Disable parallax, large transforms, looping decoration, and animated chart interpolation |

## 8. Role-aware workspaces

- **Super Admin:** platform overview, organizations, Theme Studio, global component settings, audit and publishing.
- **Organization Admin:** organization dashboard, staff, clinic settings, appointments, allowed organization theme preview.
- **Doctor:** schedule, assigned patients, encounters, notes, diagnoses, prescriptions, labs, care plans.
- **Receptionist:** check-in, appointment queue, patient registration workflow, doctor availability and scheduling.
- **Patient:** appointments, assigned doctor, records shared with consent, prescriptions, results, chatbot.
- **Chatbot:** organization-branded chat, authenticated patient context, specialty-aware doctor search, availability and booking.

## 9. Technical implementation blueprint

1. **Frontend tokens:** CSS custom properties generated from a validated theme object; semantic tokens only (background, surface, text, muted, border, primary, accent, success, warning, danger, focus).
2. **Theme provider:** resolve theme before rendering the authenticated shell to avoid a flash of the wrong theme.
3. **Persistence:** platform theme definitions and assignments stored in the backend; cache by organization and version; invalidate on publish.
4. **API boundaries:** Super Admin-only create/update/publish/rollback endpoints; organization admins can only preview/select from the allowed catalogue.
5. **Tenant isolation:** assignments keyed by organization ID; one tenant cannot update another tenant's branding.
6. **No unsafe CSS injection:** schema-validated tokens and approved component variants only.
7. **Widget layouts:** per-role defaults plus user-specific layout preferences; drag/resize state persisted separately from theme tokens.
8. **Tests:** token schema validation, precedence, tenant isolation, permission denial, rollback, reduced motion, contrast, responsive behavior.

## 10. Theme Studio navigation

- Super Admin ΓåÆ Appearance & Themes
- Theme Gallery ΓåÆ presets and saved custom themes
- Theme Editor ΓåÆ colors, typography, surfaces, radii, shadows, density
- Component Studio ΓåÆ buttons, inputs, cards, tables, charts, chat, clinical components
- Motion Studio ΓåÆ transitions, interaction states, reduced-motion profile
- Organization Branding ΓåÆ assign theme, lock tokens, allow overrides
- Preview & Publish ΓåÆ role previews, draft review, publish and rollback
- Theme Audit ΓåÆ version history and change log

## 11. Delivery phases and acceptance criteria

1. **Foundation:** semantic token schema, theme provider, six presets, light/dark/system, global shell.
2. **Super Admin:** gallery/editor, live role previews, organization assignment, publish/rollback, audit history.
3. **Component system:** icon registry, reusable controls, chart palette, clinical components, chat UI, responsive states.
4. **Motion and widgets:** motion tokens, reduced-motion behavior, draggable/resizable widgets, layout persistence.
5. **QA:** tenant isolation, role permissions, accessibility/contrast, responsive checks, visual regression.

**Definition of done:** Super Admin can publish a theme globally or assign an approved theme to one organization; every role uses consistent tokens/components; no tenant can affect another; theme switching does not alter clinical data, permissions, or workflows; reduced motion and contrast remain accessible.

## References

- [Code and Chill catalogue](https://codeandchill.store/)
- [Murmura demo supplied for review](https://demo.codeandchill.store/murmura/)

## Implementation snapshot from the local feature work


## What is implemented

- Six validated presets: Clinical Light, Midnight Care, Sage Wellness, Ocean Blue, Violet Glass, and Warm Sand.
- A global theme provider resolves the signed-in user's effective theme from the backend and applies CSS design tokens to the document root.
- Super Admin Theme Studio provides instant preview, global publishing, and organization-specific assignment or inheritance.
- Global theme configuration is stored in `platform_settings`; organization overrides are stored in `organizations.ui_theme`.
- Theme updates are audited. Only Super Admin can publish the global theme or assign tenant overrides. Organization Admins cannot alter platform or tenant theme assignments.
- Reusable Framer Motion primitives are available in `web/components/ui/motion.tsx`.
- Global CSS tokens, responsive Theme Studio styling, focus-visible treatment, and `prefers-reduced-motion` support are included.

## Theme presets

| Preset | Canvas | Surface | Primary | Text |
|---|---|---|---|---|
| Clinical Light | `#F5F8FC` | `#FFFFFF` | `#176B87` | `#172B4D` |
| Midnight Care | `#0D1422` | `#151F31` | `#55C7BE` | `#EAF1FA` |
| Sage Wellness | `#F2F6F0` | `#FFFFFF` | `#477B62` | `#20382B` |
| Ocean Blue | `#EEF4FB` | `#FFFFFF` | `#376ED5` | `#1D3154` |
| Violet Glass | `#F3F1FA` | `#FFFFFF` | `#7657D6` | `#292342` |
| Warm Sand | `#F7F3ED` | `#FFFEFC` | `#B66B42` | `#3A3029` |

## API

- `GET /api/v1/themes/active` resolves the signed-in user's effective theme.
- `GET /api/v1/themes/catalog` returns the supported theme catalog.
- `GET /api/v1/super-admin/theme` reads the platform default.
- `PATCH /api/v1/super-admin/theme` publishes a platform default.
- `GET /api/v1/super-admin/organizations/{organization_id}/theme` reads a tenant assignment.
- `PATCH /api/v1/super-admin/organizations/{organization_id}/theme` assigns a preset or `inherit`.

All write operations require Super Admin authorization and are recorded in the audit log. Preset IDs are allow-listed; arbitrary CSS, JavaScript, and token injection are not accepted.

## Persistence and migration

Alembic revision `0005_theme_studio` adds `organizations.ui_theme` and creates `platform_settings`. The global row is lazily initialized to `clinical-light`. An organization with no preset inherits the platform default.

## Frontend usage

`AppThemeProvider` is mounted inside `AuthProvider` in `web/components/providers.tsx`. Use `useAppTheme()` to read the active preset, inspect the catalog, preview a preset, or refresh the persisted theme. The provider writes `data-theme-preset` to the root element; all application surfaces should use semantic CSS variables rather than hard-coded palette values.

`ThemeStudio` is mounted on `/portal/super-admin`. Theme preview is client-side and does not persist until the Super Admin chooses Publish globally or Save assignment.

## Safety and accessibility

Theme assignment is presentation-only. It does not change roles, membership checks, organization isolation, patient relationships, consent grants, or clinical workflows. Controls expose keyboard focus states. Animations are reduced when the operating system requests reduced motion. Continue to check text contrast for any future token changes.
