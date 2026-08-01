import json
import time
import urllib.request

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt

from config import settings

security = HTTPBearer()

_jwks_cache = {"data": None, "fetched_at": 0.0}
_JWKS_TTL_SECONDS = 3600


def _get_jwks() -> dict:
    now = time.time()
    if _jwks_cache["data"] is None or now - _jwks_cache["fetched_at"] > _JWKS_TTL_SECONDS:
        url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        with urllib.request.urlopen(url, timeout=10) as resp:
            _jwks_cache["data"] = json.loads(resp.read())
        _jwks_cache["fetched_at"] = now
    return _jwks_cache["data"]


def _get_public_key(kid: str):
    for candidate in _get_jwks().get("keys", []):
        if candidate.get("kid") == kid:
            return jwk.construct(candidate)
    raise JWTError(f"No JWK found for kid {kid}")


def _verify_token(token: str, alg: str) -> dict:
    if alg == "ES256":
        return jwt.decode(
            token,
            _get_public_key(jwt.get_unverified_header(token).get("kid")),
            algorithms=["ES256"],
            options={"verify_aud": False},
        )
    return jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=["HS256"],
        options={"verify_aud": False},
    )


def verify_supabase_token(token: str) -> dict:
    """Verify a Supabase JWT.

    Newer projects sign access tokens with ES256 (verified against the
    project JWKS); older ones use HS256 with the shared JWT secret.
    """
    try:
        return _verify_token(token, jwt.get_unverified_header(token).get("alg"))
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(exc)}",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    return verify_supabase_token(credentials.credentials)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    claims = verify_supabase_token(credentials.credentials)
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing sub claim.",
        )
    return sub
