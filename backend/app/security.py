"""OIDC JWT verification and normalized application principal."""
from dataclasses import dataclass
from functools import lru_cache
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from app.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)

@dataclass(frozen=True)
class Principal:
    subject: str
    roles: frozenset[str]
    organization_id: str | None = None

@lru_cache
def _jwks_client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_keys=True)

async def get_current_principal(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    settings = get_settings()
    if not all((settings.oidc_issuer, settings.oidc_audience, settings.oidc_jwks_url)):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Identity provider is not configured")
    try:
        key = _jwks_client(settings.oidc_jwks_url).get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials, key.key, algorithms=["RS256"],
            issuer=settings.oidc_issuer, audience=settings.oidc_audience,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from exc
    subject = claims.get("sub")
    raw_roles = claims.get("roles", [])
    if not isinstance(subject, str) or not subject or not isinstance(raw_roles, list):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token claims")
    roles = frozenset(role for role in raw_roles if isinstance(role, str))
    organization_id = claims.get("organization_id")
    if organization_id is not None and not isinstance(organization_id, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token claims")
    return Principal(subject=subject, roles=roles, organization_id=organization_id)
