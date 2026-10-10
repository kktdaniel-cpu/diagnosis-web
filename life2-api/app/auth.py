from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient

from .config import get_settings


@dataclass(frozen=True)
class AuthSubject:
    sub: str


def _bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    return authorization[7:].strip()


def get_auth_subject(token: str = Depends(_bearer_token)) -> AuthSubject:
    settings = get_settings()
    if not settings.supabase_url:
        raise HTTPException(status_code=503, detail="AUTH_NOT_CONFIGURED")

    jwks_url = settings.supabase_url.rstrip("/") + "/auth/v1/.well-known/jwks.json"
    try:
        signing_key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token).key
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256", "ES256"],
            audience=settings.supabase_jwt_audience,
            options={"require": ["sub", "exp"]},
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED") from exc

    return AuthSubject(sub=str(payload["sub"]))
