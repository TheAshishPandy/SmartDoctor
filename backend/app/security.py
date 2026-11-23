"""Access-token verification and the shared Principal abstraction."""
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from app.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)
DEMO_ORGANIZATION_ID = "00000000-0000-0000-0000-000000000001"


@dataclass(frozen=True)
class Principal:
    subject: str
    roles: frozenset[str]
    organization_id: str | None = None
    is_demo: bool = False
    display_name: str | None = None


@lru_cache
def _jwks_client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_keys=True)


async def get_current_principal(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> Principal:
    settings = get_settings()
    if credentials is None:
        if settings.app_env == "development" and settings.dev_auth_enabled:
            return Principal("demo-patient", frozenset({"patient"}), DEMO_ORGANIZATION_ID, is_demo=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Bearer authentication required")
    token = credentials.credentials
    if settings.auth_jwt_secret:
        try:
            claims = jwt.decode(token, settings.auth_jwt_secret, algorithms=["HS256"], options={"require": ["exp", "iat", "sub"]})
            if claims.get("typ") != "access":
                raise jwt.InvalidTokenError("Wrong token type")
            raw_roles = claims.get("roles", [])
            if isinstance(raw_roles, str):
                raw_roles = [raw_roles]
            if not isinstance(raw_roles, list):
                raise jwt.InvalidTokenError("Invalid roles")
            roles = set(role for role in raw_roles if isinstance(role, str))
            if "doctor" in roles:
                roles.add("clinician")
            return Principal(str(claims["sub"]), frozenset(roles), claims.get("organization_id"), display_name=claims.get("name"))
        except jwt.InvalidTokenError:
            pass
    if not all((settings.oidc_issuer, settings.oidc_audience, settings.oidc_jwks_url)):
        raise HTTPException(status_code=401, detail="Invalid access token")
    try:
        key = _jwks_client(settings.oidc_jwks_url).get_signing_key_from_jwt(token)
        claims = jwt.decode(token, key.key, algorithms=["RS256"], issuer=settings.oidc_issuer,
            audience=settings.oidc_audience, options={"require": ["exp", "iat", "sub", "iss", "aud"]})
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid access token") from exc
    subject = claims.get("sub")
    raw_roles = claims.get(settings.oidc_roles_claim, []) or []
    organization_id = claims.get(settings.oidc_organization_claim)
    display_name = claims.get("name")
    if isinstance(raw_roles, str):
        raw_roles = [raw_roles]
    if not isinstance(subject, str) or not subject or not isinstance(raw_roles, list):
        raise HTTPException(status_code=401, detail="Invalid access token claims")
    roles = {role for role in raw_roles if isinstance(role, str) and role}
    if not roles:
        roles = {"patient"}
    if "doctor" in roles:
        roles.add("clinician")
    return Principal(subject, frozenset(roles), organization_id, display_name=display_name if isinstance(display_name, str) else None)
