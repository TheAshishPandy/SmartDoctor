"""Platform-controlled visual themes and tenant theme assignments."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import AuditEvent, Membership, Organization, Patient, PlatformSetting
from app.security import Principal, get_current_principal

router = APIRouter(prefix="/api/v1", tags=["themes"])

THEMES = {
    "clinical-light": {"name": "Clinical Light", "description": "Calm, clear clinical workspace", "colors": {"background": "#F5F8FC", "surface": "#FFFFFF", "primary": "#176B87", "text": "#172B4D", "tint": "#E8F3F7", "border": "#DCE6EE"}},
    "midnight-care": {"name": "Midnight Care", "description": "Focused dark workspace", "colors": {"background": "#0D1422", "surface": "#151F31", "primary": "#55C7BE", "text": "#EAF1FA", "tint": "#22344C", "border": "#2B3B52"}},
    "sage-wellness": {"name": "Sage Wellness", "description": "Natural and reassuring", "colors": {"background": "#F2F6F0", "surface": "#FFFFFF", "primary": "#477B62", "text": "#20382B", "tint": "#E3EFE5", "border": "#DCE7DD"}},
    "ocean-blue": {"name": "Ocean Blue", "description": "Confident, modern blue", "colors": {"background": "#EEF4FB", "surface": "#FFFFFF", "primary": "#376ED5", "text": "#1D3154", "tint": "#E2ECFC", "border": "#D8E3F3"}},
    "violet-glass": {"name": "Violet Glass", "description": "Creative, refined interface", "colors": {"background": "#F3F1FA", "surface": "#FFFFFF", "primary": "#7657D6", "text": "#292342", "tint": "#EAE5FA", "border": "#E1DCF0"}},
    "warm-sand": {"name": "Warm Sand", "description": "Warm, welcoming surfaces", "colors": {"background": "#F7F3ED", "surface": "#FFFEFC", "primary": "#B66B42", "text": "#3A3029", "tint": "#F1E6D9", "border": "#E8DED2"}},
}
DEFAULT_THEME = "clinical-light"

class ThemeAssignment(BaseModel):
    preset: str = Field(min_length=3, max_length=40)


def _super_admin(principal: Principal) -> None:
    if "super_admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="Platform Super Admin access required")


def _setting(db: Session) -> PlatformSetting:
    row = db.scalar(select(PlatformSetting).where(PlatformSetting.key == "global_theme"))
    if row is None:
        row = PlatformSetting(key="global_theme", value={"preset": DEFAULT_THEME})
        db.add(row)
        db.flush()
    return row


def _audit(db: Session, principal: Principal, action: str, resource_id: str) -> None:
    db.add(AuditEvent(actor_sub=principal.subject, actor_role=",".join(sorted(principal.roles)),
        action=action, resource_type="theme", resource_id=resource_id, outcome="allowed"))


@router.get("/themes/catalog")
def theme_catalog(principal: Principal = Depends(get_current_principal)) -> dict:
    return {"themes": [{"id": key, **value} for key, value in THEMES.items()]}


@router.get("/themes/active")
def active_theme(principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    global_preset = (_setting(db).value or {}).get("preset", DEFAULT_THEME)
    organization = None
    if "super_admin" not in principal.roles:
        membership = db.scalar(select(Membership).where(Membership.user_sub == principal.subject,
            Membership.status == "active").order_by(Membership.created_at.desc()))
        if membership is not None:
            organization = db.get(Organization, membership.organization_id)
        else:
            patient = db.scalar(select(Patient).where(Patient.owner_sub == principal.subject,
                Patient.organization_id.is_not(None)).order_by(Patient.created_at.desc()))
            if patient is not None:
                organization = db.get(Organization, patient.organization_id)
    assigned = (organization.ui_theme or {}).get("preset") if organization else None
    preset = assigned if assigned in THEMES else global_preset
    return {"preset": preset if preset in THEMES else DEFAULT_THEME,
        "source": "organization" if assigned in THEMES else "global",
        "organization_id": str(organization.id) if organization else None,
        "themes": [{"id": key, **value} for key, value in THEMES.items()]}


@router.get("/super-admin/theme")
def get_global_theme(principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    _super_admin(principal)
    preset = (_setting(db).value or {}).get("preset", DEFAULT_THEME)
    return {"preset": preset if preset in THEMES else DEFAULT_THEME, "themes": [{"id": key, **value} for key, value in THEMES.items()]}


@router.patch("/super-admin/theme")
def set_global_theme(payload: ThemeAssignment, principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> dict:
    _super_admin(principal)
    if payload.preset not in THEMES:
        raise HTTPException(status_code=422, detail="Choose one of the six supported themes")
    row = _setting(db)
    row.value = {"preset": payload.preset}
    _audit(db, principal, "theme.global.update", "global")
    db.commit()
    return {"preset": payload.preset, "source": "global"}


@router.get("/super-admin/organizations/{organization_id}/theme")
def get_organization_theme(organization_id: UUID, principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> dict:
    _super_admin(principal)
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    global_preset = (_setting(db).value or {}).get("preset", DEFAULT_THEME)
    assigned = (organization.ui_theme or {}).get("preset")
    return {"organization_id": str(organization.id), "preset": assigned or "inherit",
        "effective_preset": assigned or global_preset, "source": "organization" if assigned else "global"}


@router.patch("/super-admin/organizations/{organization_id}/theme")
def set_organization_theme(organization_id: UUID, payload: ThemeAssignment,
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    _super_admin(principal)
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if payload.preset != "inherit" and payload.preset not in THEMES:
        raise HTTPException(status_code=422, detail="Choose a supported theme or inherit the platform theme")
    organization.ui_theme = {} if payload.preset == "inherit" else {"preset": payload.preset}
    _audit(db, principal, "theme.organization.update", str(organization.id))
    db.commit()
    global_preset = (_setting(db).value or {}).get("preset", DEFAULT_THEME)
    return {"organization_id": str(organization.id), "preset": payload.preset,
        "effective_preset": global_preset if payload.preset == "inherit" else payload.preset}
