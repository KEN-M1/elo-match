from __future__ import annotations

from typing import Callable, TypeVar

from fastapi import HTTPException

from app.auth_session import MissingLocalUserHeader
from app.domain import RankKitError


T = TypeVar("T")


class RoutePolicy:
    """HTTP response shape and error mapping shared by RankKit routes."""

    def data_response(self, callback: Callable[[], T]) -> dict[str, T]:
        try:
            return {"data": callback()}
        except RankKitError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    def auth_response(self, callback: Callable[[], T]) -> dict[str, T]:
        try:
            return {"data": callback()}
        except MissingLocalUserHeader as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except RankKitError as exc:
            if str(exc) == "User was not found.":
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            raise HTTPException(status_code=400, detail=str(exc)) from exc
