from __future__ import annotations

from inspect import isawaitable
from typing import Callable, TypeVar

from fastapi import HTTPException

from app.auth_session import MissingLocalUserHeader
from app.domain import RankKitError


T = TypeVar("T")


class RoutePolicy:
    """HTTP response shape and error mapping shared by RankKit routes."""

    async def data_response(self, callback: Callable[[], T]) -> dict[str, T]:
        try:
            return {"data": await _resolve(callback())}
        except RankKitError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def auth_response(self, callback: Callable[[], T]) -> dict[str, T]:
        try:
            return {"data": await _resolve(callback())}
        except MissingLocalUserHeader as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except RankKitError as exc:
            if str(exc) == "User was not found.":
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            raise HTTPException(status_code=400, detail=str(exc)) from exc


async def _resolve(value: T) -> T:
    if isawaitable(value):
        return await value
    return value
