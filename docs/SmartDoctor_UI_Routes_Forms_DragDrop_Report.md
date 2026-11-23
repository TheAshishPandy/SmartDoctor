# SmartDoctor â€” UI, Routes, Forms & Dashboard Customization Report

**Project:** `C:\Ashish\SmartDoctor`
**Date:** 22 November 2026
**Environment:** Local Docker development application
**Data policy:** New route examples use synthetic demo data only.

## 1. Implementation delivered

Ten independent Next.js App Router pages have been added under `/portal/*`. Each has its own browser URL, shared workspace shell, sidebar navigation, page heading and responsive layout. The existing role dashboard, authentication and management routes remain in place.

## 2. Independent page URLs

| URL | Page |
|---|---|
| `/portal` | Role-based dashboard |
| `/portal/patients` | Patient directory and validated demo registration form |
| `/portal/appointments` | Appointment schedule and validated demo booking form |
| `/portal/records` | Clinical record review workspace |
| `/portal/reports` | Report filters, preview and CSV export |
| `/portal/observability` | Service-health and telemetry status view |
| `/portal/team` | Team and role overview |
| `/portal/audit` | Audit activity view |
| `/portal/knowledge` | Knowledge document selection and ingestion entry point |
| `/portal/assistant` | Assistant entry point |
| `/portal/settings` | Workspace preferences |
| `/portal/manage` | Existing dynamic role-based resource manager |
| `/portal/manage/team` | Existing clinic membership administration |
| `/portal/clinic-assistant` | Existing patient clinic assistant |

## 3. Drag, drop and resize

- Dashboard metric cards, hero, quick-action cards, menu cards and recent-appointment card use the editable widget wrapper.
- Customize layout mode allows drag-to-reorder and width/height controls for supported dashboard widgets.
- Chart cards support drag-to-reorder and width/height controls.
- Replace and remove actions remain available on chart cards. Replace opens the right-side chart library.
- Chart selections and dashboard layouts persist in browser local storage, scoped by dashboard role.
- Chart series are still sample values; live analytics queries are not connected yet.

## 4. Form validation audit

| Form / workflow | Validation checked in code |
|---|---|
| Patient registration page | Required name/email/DOB; trimmed name length; email format; DOB must be in the past; optional phone format |
| Appointment booking page | Required patient, clinician, date, time and reason; date/time must be future; reason minimum length |
| Reports page | Report type and period restricted to predefined options; CSV export generated from current demo data |
| Assistant page | Question minimum length; client-only entry point, not wired to medical backend |
| Document selection | PDF/DOCX/TXT/MD allowlist and 10 MB size cap |
| Authentication | Required email/password; trimmed registration name; password minimum 12 characters; OTP exactly six digits |
| Clinic assistant | Message/specialty/reason length limits; specialty minimum; future appointment date/time and reason checks |
| Dynamic workspace CRUD | Required fields, email format, non-negative numeric values, patient ID requirement, date range consistency |
| Menu builder | Key pattern, label length, safe internal route allowlist, allowed role values, non-negative integer sort order |
| Super-admin organization/team forms | Existing required/minimum-length constraints reviewed; API behavior not exercised |
| Clinic membership forms | Existing required and minimum-length controls reviewed; API behavior not exercised |
| Knowledge chat/upload | Empty prompt blocked by send state; accepted document extensions reviewed; backend remains authoritative |

**Important:** This is a code-level validation review. Browser-driven negative/positive interaction tests were not run because Playwright is not installed in the project. Server-side validation remains mandatory and was not replaced by client checks.

## 5. Verification results

- `npm run build`: passed; Next.js generated the independent routes listed above.
- `npx tsc --noEmit`: passed after the page and form-validation changes.
- `npm run lint`: passed after the page and form-validation changes.
- Local HTTP smoke check: all eleven tested URLs returned HTTP 200 â€” `/portal` and all ten new `/portal/*` module pages.
- Docker web service was restarted and its generated Next.js cache cleared before the HTTP smoke check.

## 6. Reporting and observability limitations

The Reports page can export CSV, but current rows are derived from local synthetic preview values. Connect authorized, tenant-scoped analytics endpoints before treating the output as a production report.

The Observability page marks FastAPI, PostgreSQL, MongoDB, Qdrant, Redis and worker/queue status as **Not probed** until real health checks and telemetry are integrated. The page does not invent health metrics.

## 7. Data, security and clinical safety

- New patient and appointment forms currently update only local page state; they do not create backend records.
- Use synthetic data only in this development preview.
- Client-side validation does not replace API-side validation, authorization, organization membership, patient relationship, consent or audit checks.
- Dashboard role preview is not an authorization boundary.
- The new Assistant page is a navigation entry point; use the existing connected Knowledge Hub for actual RAG queries.

## 8. Remaining work

1. Add browser-driven positive and negative tests for every form, including login, registration, OTP, password reset, dynamic CRUD, menu builder, clinic assistant, organization and team administration.
2. Connect Patients and Appointments pages to authenticated FastAPI endpoints and replace local demo state.
3. Connect report filters and CSV export to tenant-scoped analytics APIs with authorization checks.
4. Add live service health checks, queue depth, latency, error-rate and tracing metrics.
5. Connect chart series to authorized analytics data and verify role-specific visibility.
6. Add keyboard-accessible alternatives to drag/drop and verify mobile resizing behavior.
7. Run end-to-end regression tests for auth, document ingestion, RAG, CRUD and clinic workflows.

## 9. Deployment status

Changes are applied in the local repository and the local Docker web service. No public deployment or production release is claimed.
