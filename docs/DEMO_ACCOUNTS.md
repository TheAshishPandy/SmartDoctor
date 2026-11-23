# SmartDoctor local demo accounts

These accounts and records are synthetic and are intended only for local development and UI/role testing. Do not use this password or dataset in production.

**Shared local demo password:** `SmartDoctor@2026!`

| Role | Email | Organization |
|---|---|---|
| Super Admin | `platform.admin@smartdoctor.dev` | Platform |
| Organization Admin | `admin@northstar.smartdoctor.dev` | Northstar Family Clinic |
| Doctor | `doctor.sarah@northstar.smartdoctor.dev` | Northstar Family Clinic |
| Doctor | `doctor.james@northstar.smartdoctor.dev` | Northstar Family Clinic |
| Receptionist | `reception@northstar.smartdoctor.dev` | Northstar Family Clinic |
| Patient | `patient.emma@smartdoctor.dev` | Northstar Family Clinic |
| Patient | `patient.noah@smartdoctor.dev` | Northstar Family Clinic |
| Patient | `patient.amelia@smartdoctor.dev` | Northstar Family Clinic |
| Organization Admin | `admin@harborview.smartdoctor.dev` | Harborview Specialty Center |
| Doctor | `doctor.maya@harborview.smartdoctor.dev` | Harborview Specialty Center |
| Receptionist | `reception@harborview.smartdoctor.dev` | Harborview Specialty Center |
| Patient | `patient.sophia@smartdoctor.dev` | Harborview Specialty Center |

## Seeded demo content

- Two organizations with different UI theme presets.
- Verified, active role accounts and active staff memberships.
- Four clinic patient profiles, assigned clinician relationships, and explicit patient-read consent grants.
- Role-filtered dashboard menus and nested clinic management navigation.
- Appointments, appointment requests, intake, check-in, clinical notes, encounters, diagnoses, vitals, allergies, conditions, medication examples, lab orders/results, care plans, follow-ups, departments, and clinic notices.
- Audit event marking the demo seed operation.

All patient and clinical content is fabricated. Medication rows are illustrative records, not prescriptions or treatment advice.

## Re-seed

From the repository root:

```powershell
docker compose exec -T api python -m scripts.seed_demo_data
```

The script is idempotent for seeded users, memberships, patients, menu keys, and records identified by `demo_key`. It re-enables seeded accounts and resets their password to the configured demo password each time it runs. Set `SMARTDOCTOR_DEMO_PASSWORD` inside the API container environment to override the local default.
