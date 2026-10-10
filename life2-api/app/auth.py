from __future__ import annotations

import httpx
from fastapi import Header, HTTPException
from . import config

async def get_current_subject(authorization: str = Header(default="")) -> str:
    if not config.SUPABASE_URL or not config.SUPABASE_ANON_KEY:
        raise HTTPException(status_code=503, detail="auth not configured")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")

    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="missing bearer token")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{config.SUPABASE_URL}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": config.SUPABASE_ANON_KEY,
                },
            )
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="auth service unavailable")

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="invalid bearer token")

    payload = response.json()
    subject = payload.get("id")
    if not subject:
        raise HTTPException(status_code=401, detail="invalid auth response")
    return str(subject)
