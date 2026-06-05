from __future__ import annotations

from dataclasses import dataclass

from app.auth_session import AuthSession
from app.config import Settings, settings
from app.domain import RankKitStore
from app.route_policy import RoutePolicy


@dataclass(frozen=True)
class RankKitRuntime:
    store: object
    auth_session: AuthSession
    route_policy: RoutePolicy


def create_runtime(app_settings: Settings = settings) -> RankKitRuntime:
    return RankKitRuntime(
        store=RankKitStore(app_settings.local_data_path),
        auth_session=AuthSession(),
        route_policy=RoutePolicy(),
    )
