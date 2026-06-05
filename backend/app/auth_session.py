from __future__ import annotations

from inspect import isawaitable
from typing import Callable, Protocol

from app.auth import AuthenticatedPrincipal, verify_bearer_token
from app.domain import User


class MissingLocalUserHeader(ValueError):
    pass


class UserStore(Protocol):
    def sync_user(self, email: str, name: str | None = None, image: str | None = None) -> User:
        ...

    def get_user(self, user_id: str) -> User:
        ...


class AuthSession:
    def __init__(
        self,
        verify_token: Callable[[str | None], AuthenticatedPrincipal | None] = verify_bearer_token,
    ) -> None:
        self.verify_token = verify_token

    async def current_user(
        self,
        store: UserStore,
        authorization: str | None,
        local_user_id: str | None,
    ) -> User:
        principal = self.verify_token(authorization)
        if principal is not None:
            return await _resolve(
                store.sync_user(
                    email=principal.email,
                    name=principal.name,
                    image=principal.image,
                )
            )

        if not local_user_id:
            raise MissingLocalUserHeader("Missing user header for local MVP.")

        return await _resolve(store.get_user(local_user_id))


async def _resolve(value):
    if isawaitable(value):
        return await value
    return value
