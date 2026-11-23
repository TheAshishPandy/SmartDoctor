"""Idempotent synthetic SmartDoctor demo dataset for all five roles.
Run: python -m scripts.seed_demo_data
Local-only password: SMARTDOCTOR_DEMO_PASSWORD or SmartDoctor@2026!
"""
from datetime import datetime, timedelta, timezone
import os
from sqlalchemy import select
from argon2 import PasswordHasher
from app.db import SessionLocal
from app.models import (AuthUser, Organization, Membership, Patient, CareRelationship,
    ConsentGrant, WorkspaceEntry, WorkspaceMenuItem, AuditEvent)

PASSWORD = os.getenv("SMARTDOCTOR_DEMO_PASSWORD", "SmartDoctor@2026!")
HASHER = PasswordHasher()
NOW = datetime.now(timezone.utc)
ORGS = [("Northstar Family Clinic", "northstar", "clinical-light"),
        ("Harborview Specialty Center", "harborview", "ocean-blue")]
USERS = [
 ("platform.admin@smartdoctor.dev","Platform Super Admin","super_admin",None,None),
 ("admin@northstar.smartdoctor.dev","Olivia Carter","admin","northstar","admin"),
 ("doctor.sarah@northstar.smartdoctor.dev","Dr. Sarah Chen","doctor","northstar","clinician"),
 ("doctor.james@northstar.smartdoctor.dev","Dr. James Wilson","doctor","northstar","clinician"),
 ("reception@northstar.smartdoctor.dev","Mia Thompson","receptionist","northstar","receptionist"),
 ("patient.emma@smartdoctor.dev","Emma Johnson","patient","northstar",None),
 ("patient.noah@smartdoctor.dev","Noah Williams","patient","northstar",None),
 ("patient.amelia@smartdoctor.dev","Amelia Davis","patient","northstar",None),
 ("admin@harborview.smartdoctor.dev","Liam Anderson","admin","harborview","admin"),
 ("doctor.maya@harborview.smartdoctor.dev","Dr. Maya Patel","doctor","harborview","clinician"),
 ("reception@harborview.smartdoctor.dev","Ethan Brown","receptionist","harborview","receptionist"),
 ("patient.sophia@smartdoctor.dev","Sophia Martinez","patient","harborview",None),
]
MENUS = [
 ("dashboard","Dashboard","/portal","layout-dashboard",None,["admin","doctor","receptionist","patient"],1),
 ("clinic-management","Clinic Management","/portal/manage","building-2",None,["admin"],10),
 ("clinic-patients","Patients","/portal/manage/patients","users","clinic-management",["admin","receptionist"],11),
 ("clinic-team","Team & Roles","/portal/manage/team","user-cog","clinic-management",["admin"],12),
 ("clinic-assistant","Clinic Assistant","/portal/clinic-assistant","bot",None,["admin","doctor","receptionist"],20),
 ("clinical-records","Clinical Records","/records","file-heart",None,["doctor","patient"],30),
 ("ai-assistant","AI Health Assistant","/assistant","brain-circuit",None,["doctor","patient"],40),
 ("my-profile","My Profile","/profile","user-round",None,["admin","doctor","receptionist","patient"],90),
 ("settings","Settings","/settings","settings",None,["admin","doctor","receptionist","patient"],100),
]

def user_for(db, email, name, role):
    row = db.scalar(select(AuthUser).where(AuthUser.email == email))
    if row is None:
        row = AuthUser(email=email, password_hash=HASHER.hash(PASSWORD),
            display_name=name, role=role, is_verified=True, is_active=True)
        db.add(row)
        db.flush()
    else:
        row.display_name, row.role = name, role
        row.is_verified, row.is_active = True, True
        row.password_hash = HASHER.hash(PASSWORD)
    return row

def upsert_entry(db, org_id, patient_id, actor, kind, key, data, status="active"):
    rows = db.scalars(select(WorkspaceEntry).where(
        WorkspaceEntry.organization_id == org_id,
        WorkspaceEntry.resource_type == kind)).all()
    row = next((r for r in rows if r.data.get("demo_key") == key), None)
    if row is None:
        row = WorkspaceEntry(resource_type=kind, organization_id=org_id,
            patient_id=patient_id, data=data, status=status,
            created_by=actor, updated_by=actor)
        db.add(row)
    else:
        row.patient_id, row.data, row.status = patient_id, data, status
        row.updated_by, row.updated_at = actor, NOW
    return row

def main():
    with SessionLocal() as db:
        orgs = {}
        for name, key, theme in ORGS:
            org = db.scalar(select(Organization).where(Organization.name == name))
            if org is None:
                org = Organization(name=name, status="active")
                db.add(org)
                db.flush()
            org.status = "active"
            org.ui_theme = {"preset": theme}
            org.chatbot_config = org.chatbot_config or {
                "welcome": f"Welcome to {name}. I can help with appointments and clinic information."}
            orgs[key] = org

        users = {}
        for email, name, role, org_key, member_role in USERS:
            u = user_for(db, email, name, role)
            users[email] = u
            if org_key and member_role:
                org = orgs[org_key]
                m = db.scalar(select(Membership).where(
                    Membership.user_sub == str(u.id), Membership.organization_id == org.id,
                    Membership.role == member_role))
                if m is None:
                    db.add(Membership(user_sub=str(u.id), organization_id=org.id,
                        role=member_role, status="active",
                        specialties=["Family Medicine"] if role == "doctor" else [],
                        availability={"days":["Monday","Tuesday","Wednesday","Thursday","Friday"],
                            "start":"09:00","end":"17:00"} if role == "doctor" else {}))
                else:
                    m.status = "active"
        db.flush()

        patient_specs = [
          ("patient.emma@smartdoctor.dev","northstar","Emma Johnson","doctor.sarah@northstar.smartdoctor.dev"),
          ("patient.noah@smartdoctor.dev","northstar","Noah Williams","doctor.james@northstar.smartdoctor.dev"),
          ("patient.amelia@smartdoctor.dev","northstar","Amelia Davis","doctor.sarah@northstar.smartdoctor.dev"),
          ("patient.sophia@smartdoctor.dev","harborview","Sophia Martinez","doctor.maya@harborview.smartdoctor.dev"),
        ]
        patients = {}
        for email, org_key, label, doctor_email in patient_specs:
            u, org, doctor = users[email], orgs[org_key], users[doctor_email]
            p = db.scalar(select(Patient).where(
                Patient.owner_sub == str(u.id), Patient.organization_id == org.id))
            if p is None:
                p = Patient(owner_sub=str(u.id), organization_id=org.id, display_label=label)
                db.add(p)
                db.flush()
            else:
                p.display_label = label
            patients[email] = p
            rel = db.scalar(select(CareRelationship).where(
                CareRelationship.patient_id == p.id,
                CareRelationship.clinician_sub == str(doctor.id),
                CareRelationship.organization_id == org.id))
            if rel is None:
                db.add(CareRelationship(patient_id=p.id, clinician_sub=str(doctor.id),
                    organization_id=org.id, status="active"))
            else:
                rel.status = "active"
            grant = db.scalar(select(ConsentGrant).where(
                ConsentGrant.patient_id == p.id, ConsentGrant.grantee_sub == str(doctor.id),
                ConsentGrant.scope == "patient.read"))
            if grant is None:
                db.add(ConsentGrant(patient_id=p.id, grantee_sub=str(doctor.id),
                    scope="patient.read", status="active"))
            else:
                grant.status, grant.revoked_at = "active", None
        db.flush()

        menu_ids = {}
        for key, label, path, icon, parent, roles, order in MENUS:
            item = db.scalar(select(WorkspaceMenuItem).where(WorkspaceMenuItem.key == key))
            if item is None:
                item = WorkspaceMenuItem(key=key, label=label, path=path, icon=icon,
                    roles=roles, sort_order=order, is_active=True)
                db.add(item)
                db.flush()
            item.label, item.path, item.icon = label, path, icon
            item.roles, item.sort_order, item.is_active = roles, order, True
            item.parent_id = menu_ids.get(parent) if parent else None
            menu_ids[key] = item.id

        # Fictional records only; medication entries are examples, not treatment advice.
        for email, patient in patients.items():
            org = db.get(Organization, patient.organization_id)
            org_key = "northstar" if org.name.startswith("Northstar") else "harborview"
            admin_email = f"admin@{org_key}.smartdoctor.dev"
            doctor_email = next(x[3] for x in patient_specs if x[0] == email)
            actor, pid, label = str(users[doctor_email].id), patient.id, patient.display_label
            k = email.split("@")[0]
            records = [
             ("appointment","appt1",{"scheduled_at":(NOW+timedelta(days=2)).isoformat(),"reason":"Routine follow-up","status":"confirmed","provider":users[doctor_email].display_name,"location":"Consultation Room 2"},"confirmed"),
             ("appointment","appt2",{"scheduled_at":(NOW-timedelta(days=5)).isoformat(),"reason":"Annual wellness review","status":"completed","provider":users[doctor_email].display_name,"location":"Consultation Room 1"},"completed"),
             ("clinical_note","note1",{"title":"Initial consultation","body":"Synthetic demo note: patient reports generally good health. Review history and preventive care at the next visit.","author":users[doctor_email].display_name},"active"),
             ("encounter","encounter1",{"encounter_date":(NOW-timedelta(days=5)).date().isoformat(),"chief_complaint":"Routine wellness review","assessment":"Stable; preventive screening discussed.","plan":"Routine follow-up with treating clinician."},"completed"),
             ("diagnosis","diagnosis1",{"code":"Z00.00","description":"General adult medical examination without abnormal findings","clinical_status":"active"},"active"),
             ("vital","vital1",{"measured_at":(NOW-timedelta(days=5)).isoformat(),"blood_pressure":"118/76 mmHg","heart_rate":72,"temperature_c":36.8,"respiratory_rate":16,"oxygen_saturation":98,"weight_kg":68.4},"active"),
             ("allergy","allergy1",{"substance":"Pollen","reaction":"Seasonal sneezing","severity":"mild"},"active"),
             ("condition","condition1",{"name":"Seasonal allergic rhinitis","status":"active","onset_date":(NOW-timedelta(days=180)).date().isoformat()},"active"),
             ("prescription","rx1",{"medication_name":"Cetirizine (example record)","instructions":"Demo record only; follow clinician-approved directions.","prescribed_at":(NOW-timedelta(days=30)).date().isoformat(),"prescriber":users[doctor_email].display_name},"active"),
             ("medication","med1",{"medication_name":"Vitamin D (example record)","status":"active","frequency":"As documented by clinician","note":"Synthetic record, not a recommendation."},"active"),
             ("lab_order","lab1",{"test_name":"Complete blood count (CBC)","ordered_at":(NOW-timedelta(days=8)).date().isoformat(),"priority":"routine"},"active"),
             ("lab_result","result1",{"test_name":"Complete blood count (CBC)","result":"Within illustrative reference interval","resulted_at":(NOW-timedelta(days=6)).date().isoformat(),"unit":"See source report","flag":"normal"},"active"),
             ("care_plan","care1",{"title":"Preventive wellness plan","goals":["Review preventive screening schedule","Keep medication list updated","Attend scheduled follow-up"]},"active"),
             ("follow_up","follow1",{"title":"Review wellness visit","due_date":(NOW+timedelta(days=14)).date().isoformat(),"instructions":"Discuss questions with the treating clinician."},"active"),
             ("appointment_request","request1",{"preferred_date":(NOW+timedelta(days=10)).date().isoformat(),"reason":"Follow-up appointment request","preferred_time":"Morning"},"requested"),
             ("profile_note","profile1",{"full_name":label,"preferred_contact":"Email","note":"Synthetic patient profile for local UI testing."},"active"),
             ("patient_intake","intake1",{"full_name":label,"phone":"+1-202-555-0148","email":email,"visit_reason":"Routine wellness visit","source":"Online booking"},"active"),
             ("check_in","checkin1",{"arrival_time":(NOW-timedelta(hours=2)).isoformat(),"desk":"Front desk","status":"completed"},"completed"),
            ]
            for kind, key, data, status in records:
                data["demo_key"] = f"{k}-{key}"
                upsert_entry(db, patient.organization_id, pid, actor, kind, data["demo_key"], data, status)

        for org_key, org in orgs.items():
            actor = str(users[f"admin@{org_key}.smartdoctor.dev"].id)
            org_records = [
             ("department","department-primary",{"name":"Primary Care","description":"General and preventive care"}),
             ("department","department-lab",{"name":"Diagnostics","description":"Laboratory coordination and results"}),
             ("clinic_notice","notice-hours",{"title":"Clinic hours","message":"Monday to Friday, 9 AM to 5 PM. Contact reception for holiday hours.","priority":"normal"}),
             ("clinic_notice","notice-privacy",{"title":"Patient privacy reminder","message":"Verify identity and permissions before accessing or sharing patient records.","priority":"high"}),
            ]
            for kind, key, data in org_records:
                data["demo_key"] = f"{org_key}-{key}"
                upsert_entry(db, org.id, None, actor, kind, data["demo_key"], data)
        db.add(AuditEvent(actor_sub=str(users["platform.admin@smartdoctor.dev"].id),
            actor_role="super_admin", action="demo.seed", resource_type="demo_dataset",
            resource_id="smartdoctor-all-roles", outcome="allowed"))
        db.commit()
        print("SmartDoctor demo data seeded successfully.")
        print(f"Organizations: {len(orgs)} | Accounts: {len(users)} | Patient profiles: {len(patients)}")
        print(f"Menus: {len(MENUS)} | Demo password: {PASSWORD}")
        for email, name, role, org_key, _ in USERS:
            print(f"{role:12} {email:45} {name}")

if __name__ == "__main__":
    main()
