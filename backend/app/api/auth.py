"""Email/password authentication with verified-email OTP and rotating refresh tokens."""
import asyncio
import hashlib
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from uuid import UUID
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from typing import Literal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db import get_db
from app.models import AuthUser, EmailOTP, RefreshSession
from app.security import Principal, get_current_principal

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
password_hasher = PasswordHasher()
REFRESH_COOKIE = "smartdoctor_refresh"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=2, max_length=160)


class EmailRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(EmailRequest):
    code: str = Field(pattern=r"^\d{6}$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ResetPasswordRequest(VerifyOTPRequest):
    new_password: str = Field(min_length=12, max_length=128)


class RoleUpdateRequest(BaseModel):
    role: Literal["patient", "doctor", "admin", "receptionist"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _require_secret() -> str:
    secret = get_settings().auth_jwt_secret
    if not secret or len(secret) < 32:
        raise HTTPException(status_code=503, detail="Authentication signing secret is not configured")
    return secret


def _access_token(user: AuthUser) -> str:
    cfg = get_settings()
    now = _now()
    return jwt.encode({"sub": str(user.id), "email": user.email, "name": user.display_name,
        "roles": [user.role], "iat": now, "exp": now + timedelta(minutes=cfg.auth_access_minutes),
        "jti": secrets.token_urlsafe(12), "typ": "access"}, _require_secret(), algorithm="HS256")


def _deliver_email(to_email: str, subject: str, body: str) -> None:
    cfg = get_settings()
    if not all((cfg.smtp_host, cfg.smtp_from_email)):
        raise RuntimeError("SMTP is not configured")
    message = EmailMessage()
    message["From"] = cfg.smtp_from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=10) as smtp:
        if cfg.smtp_use_tls:
            smtp.starttls()
        if cfg.smtp_username:
            smtp.login(cfg.smtp_username, cfg.smtp_password)
        smtp.send_message(message)


async def _send_otp(email: str, code: str, purpose: str) -> bool:
    cfg = get_settings()
    if cfg.app_env == "development" and cfg.auth_dev_otp_enabled and not cfg.smtp_host:
        return True
    if cfg.app_env == "production" and not all((cfg.smtp_host, cfg.smtp_from_email)):
        raise HTTPException(status_code=503, detail="Email delivery is not configured")
    try:
        await asyncio.to_thread(_deliver_email, email, f"SmartDoctor {purpose.replace('_', ' ')} code",
            f"Your SmartDoctor verification code is {code}. It expires in {cfg.auth_otp_minutes} minutes. If you did not request this, ignore this email.")
        return False
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Unable to send verification email") from exc


def _create_otp(db: Session, email: str, purpose: str, code: str) -> None:
    now = _now()
    for previous in db.scalars(select(EmailOTP).where(EmailOTP.email == email, EmailOTP.purpose == purpose, EmailOTP.consumed_at.is_(None))).all():
        previous.consumed_at = now
    cfg = get_settings()
    db.add(EmailOTP(email=email, purpose=purpose, code_hash=password_hasher.hash(code),
        expires_at=now + timedelta(minutes=cfg.auth_otp_minutes)))
    db.commit()


def _verify_otp(db: Session, email: str, purpose: str, code: str) -> EmailOTP:
    cfg = get_settings()
    challenge = db.scalar(select(EmailOTP).where(EmailOTP.email == email, EmailOTP.purpose == purpose,
        EmailOTP.consumed_at.is_(None)).order_by(EmailOTP.created_at.desc()))
    if challenge is None or _aware(challenge.expires_at) <= _now() or challenge.attempts >= cfg.auth_otp_max_attempts:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    challenge.attempts += 1
    try:
        password_hasher.verify(challenge.code_hash, code)
    except (VerifyMismatchError, VerificationError):
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    challenge.consumed_at = _now()
    db.commit()
    return challenge


def _set_refresh_cookie(response: Response, raw: str) -> None:
    cfg = get_settings()
    response.set_cookie(REFRESH_COOKIE, raw, httponly=True, secure=cfg.app_env == "production",
        samesite="lax", max_age=cfg.auth_refresh_days * 86400, path="/api/v1/auth")


def _issue_refresh(db: Session, user: AuthUser, response: Response) -> None:
    cfg = get_settings()
    raw = secrets.token_urlsafe(48)
    db.add(RefreshSession(user_id=user.id, token_hash=_hash(raw),
        expires_at=_now() + timedelta(days=cfg.auth_refresh_days)))
    db.commit()
    _set_refresh_cookie(response, raw)


def _user_payload(user: AuthUser) -> dict:
    return {"id": str(user.id), "email": user.email, "display_name": user.display_name, "role": user.role, "is_verified": user.is_verified}


@router.post("/register", status_code=202)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    email = payload.email.lower()
    if db.scalar(select(AuthUser).where(AuthUser.email == email)):
        return {"message": "If this address can be registered, a verification code will be sent."}
    cfg = get_settings()
    super_admins = {item.strip().lower() for item in cfg.auth_super_admin_emails.split(",") if item.strip()}
    bootstrap_admins = {item.strip().lower() for item in cfg.auth_admin_emails.split(",") if item.strip()}
    initial_role = "super_admin" if email in super_admins else ("admin" if email in bootstrap_admins else "patient")
    user = AuthUser(email=email, password_hash=password_hasher.hash(payload.password),
        display_name=payload.display_name.strip(), role=initial_role, is_verified=False)
    db.add(user)
    db.commit()
    code = f"{secrets.randbelow(1_000_000):06d}"
    _create_otp(db, email, "verify_email", code)
    dev_mode = await _send_otp(email, code, "verify_email")
    result = {"message": "If this address can be registered, a verification code will be sent."}
    if dev_mode:
        result["development_otp"] = code
    return result


@router.post("/verify-email")
def verify_email(payload: VerifyOTPRequest, db: Session = Depends(get_db)) -> dict:
    email = payload.email.lower()
    user = db.scalar(select(AuthUser).where(AuthUser.email == email))
    if user is None or user.is_verified:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    _verify_otp(db, email, "verify_email", payload.code)
    user.is_verified = True
    db.commit()
    return {"message": "Email verified successfully"}


@router.post("/resend-otp", status_code=202)
async def resend_otp(payload: EmailRequest, db: Session = Depends(get_db)) -> dict:
    email = payload.email.lower()
    user = db.scalar(select(AuthUser).where(AuthUser.email == email))
    if user is None or user.is_verified:
        return {"message": "If verification is pending, a new code will be sent."}
    cfg = get_settings()
    recent = db.scalar(select(EmailOTP).where(EmailOTP.email == email, EmailOTP.purpose == "verify_email").order_by(EmailOTP.created_at.desc()))
    if recent and (_now() - _aware(recent.created_at)).total_seconds() < cfg.auth_otp_resend_seconds:
        raise HTTPException(status_code=429, detail="Please wait before requesting another code")
    code = f"{secrets.randbelow(1_000_000):06d}"
    _create_otp(db, email, "verify_email", code)
    dev_mode = await _send_otp(email, code, "verify_email")
    result = {"message": "If verification is pending, a new code will be sent."}
    if dev_mode:
        result["development_otp"] = code
    return result


@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(AuthUser).where(AuthUser.email == payload.email.lower()))
    try:
        valid = user is not None and password_hasher.verify(user.password_hash, payload.password)
    except (VerifyMismatchError, VerificationError):
        valid = False
    if not valid or user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before signing in")
    cfg = get_settings()
    super_admins = {item.strip().lower() for item in cfg.auth_super_admin_emails.split(",") if item.strip()}
    bootstrap_admins = {item.strip().lower() for item in cfg.auth_admin_emails.split(",") if item.strip()}
    if user.email in super_admins:
        user.role = "super_admin"
    elif user.role == "super_admin":
        user.role = "admin" if user.email in bootstrap_admins else "patient"
    db.commit()
    _issue_refresh(db, user, response)
    return {"access_token": _access_token(user), "token_type": "bearer", "expires_in": get_settings().auth_access_minutes * 60, "user": _user_payload(user)}


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    raw = request.cookies.get(REFRESH_COOKIE)
    if not raw:
        raise HTTPException(status_code=401, detail="Refresh session required")
    session = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == _hash(raw)))
    if session is None or session.revoked_at is not None or _aware(session.expires_at) <= _now():
        response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
        raise HTTPException(status_code=401, detail="Refresh session expired")
    user = db.get(AuthUser, session.user_id)
    if user is None or not user.is_active or not user.is_verified:
        session.revoked_at = _now()
        db.commit()
        raise HTTPException(status_code=401, detail="Authentication required")
    session.revoked_at = _now()
    db.commit()
    _issue_refresh(db, user, response)
    return {"access_token": _access_token(user), "token_type": "bearer", "expires_in": get_settings().auth_access_minutes * 60, "user": _user_payload(user)}


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> Response:
    raw = request.cookies.get(REFRESH_COOKIE)
    if raw:
        session = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == _hash(raw)))
        if session and session.revoked_at is None:
            session.revoked_at = _now()
            db.commit()
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    response.status_code = 204
    return response


@router.post("/forgot-password", status_code=202)
async def forgot_password(payload: EmailRequest, db: Session = Depends(get_db)) -> dict:
    email = payload.email.lower()
    user = db.scalar(select(AuthUser).where(AuthUser.email == email, AuthUser.is_verified.is_(True)))
    if user is not None:
        cfg = get_settings()
        recent = db.scalar(select(EmailOTP).where(EmailOTP.email == email, EmailOTP.purpose == "reset_password").order_by(EmailOTP.created_at.desc()))
        if recent and (_now() - _aware(recent.created_at)).total_seconds() < cfg.auth_otp_resend_seconds:
            return {"message": "If an account exists, a password reset code will be sent."}
        code = f"{secrets.randbelow(1_000_000):06d}"
        _create_otp(db, email, "reset_password", code)
        dev_mode = await _send_otp(email, code, "reset_password")
        if dev_mode:
            return {"message": "If an account exists, a password reset code will be sent.", "development_otp": code}
    return {"message": "If an account exists, a password reset code will be sent."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict:
    email = payload.email.lower()
    user = db.scalar(select(AuthUser).where(AuthUser.email == email, AuthUser.is_verified.is_(True)))
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    _verify_otp(db, email, "reset_password", payload.code)
    user.password_hash = password_hasher.hash(payload.new_password)
    for session in db.scalars(select(RefreshSession).where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None))).all():
        session.revoked_at = _now()
    db.commit()
    return {"message": "Password reset successfully"}


@router.patch("/users/{user_id}/role")
def update_user_role(user_id: UUID, payload: RoleUpdateRequest,
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    if "super_admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="Platform Super Admin access required")
    user = db.get(AuthUser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    previous_role = user.role
    user.role = payload.role
    from app.models import AuditEvent
    db.add(AuditEvent(actor_sub=principal.subject, actor_role="super_admin", action="auth.role.change",
        resource_type="auth_user", resource_id=str(user.id), outcome="allowed"))
    db.commit()
    return {"user_id": str(user.id), "previous_role": previous_role, "role": user.role}


@router.get("/me")
def me(principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    try:
        user_id = UUID(principal.subject)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")
    user = db.get(AuthUser, user_id)
    if user is None or not user.is_active or not user.is_verified:
        raise HTTPException(status_code=401, detail="Authentication required")
    return _user_payload(user)


@router.get("/users")
def list_users(principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> list[dict]:
    if "super_admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="Platform Super Admin access required")
    users = db.scalars(select(AuthUser).order_by(AuthUser.created_at.desc()).limit(500)).all()
    return [{"id": str(user.id), "email": user.email, "display_name": user.display_name,
        "role": user.role, "is_verified": user.is_verified, "is_active": user.is_active}
        for user in users]
