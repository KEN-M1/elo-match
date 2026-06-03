from __future__ import annotations

from dataclasses import dataclass

import jwt

from app.config import settings
from app.domain import RankKitError


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    subject: str
    email: str
    name: str | None = None
    image: str | None = None


def verify_bearer_token(authorization: str | None) -> AuthenticatedPrincipal | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise RankKitError("Authorization header must be a Bearer token.")

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise RankKitError("Bearer token is invalid.") from exc

    email = payload.get("email")
    subject = payload.get("sub")
    if not isinstance(email, str) or not isinstance(subject, str):
        raise RankKitError("Bearer token is missing required user claims.")

    return AuthenticatedPrincipal(
        subject=subject,
        email=email,
        name=payload.get("name") if isinstance(payload.get("name"), str) else None,
        image=payload.get("image") if isinstance(payload.get("image"), str) else None,
    )
