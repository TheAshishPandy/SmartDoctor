"""OIDC JWT verification and an explicitly opt-in local demo identity."""
from dataclasses import dataclass
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


@lru_cache
def _jwks_client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_keys=True)


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Principal:
    settings = get_settings()
    if credentials is None:
        if settings.app_env == "development" and settings.dev_auth_enabled:
            return Principal("demo-patient", frozenset({"patient"}), DEMO_ORGANIZATION_ID)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Bearer authentication required")
    if not all((settings.oidc_issuer, settings.oidc_audience, settings.oidc_jwks_url)):
        raise HTTPException(status_code=503, detail="Identity provider is not configured")
    try:
        key = _jwks_client(settings.oidc_jwks_url).get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials, key.key, algorithms=["RS256"],
            issuer=settings.oidc_issuer, audience=settings.oidc_audience,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid access token") from exc
    subject = claims.get("sub")
    raw_roles = claims.get("roles", [])
    organization_id = claims.get("organization_id")
    if not isinstance(subject, str) or not subject or not isinstance(raw_roles, list):
        raise HTTPException(status_code=401, detail="Invalid access token claims")
    if organization_id is not None and not isinstance(organization_id, str):
        raise HTTPException(status_code=401, detail="Invalid access token claims")
    return Principal(subject, frozenset(r for r in raw_roles if isinstance(r, str)), organization_id)
