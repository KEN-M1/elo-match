import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.auth_session import AuthSession
from app.config import Settings
from app.domain import RankKitStore, User
from app.main import create_app
from app.route_policy import RoutePolicy
from app.runtime import RankKitRuntime, create_runtime


REPO_ROOT = Path(__file__).resolve().parents[2]


class RuntimeTests(unittest.TestCase):
    def test_create_runtime_uses_configured_local_snapshot_store(self) -> None:
        with TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "rankkit.json"
            runtime = create_runtime(
                Settings(
                    local_data_path=str(data_path),
                    database_url="postgresql+asyncpg://rankkit:rankkit@localhost:5432/rankkit",
                )
            )

            self.assertIsInstance(runtime.store, RankKitStore)
            user = runtime.store.sync_user("runtime@example.com", "Runtime")

            hydrated = RankKitStore(data_path)
            self.assertEqual(hydrated.get_user(user.id).email, "runtime@example.com")

    def test_create_app_uses_injected_runtime_store(self) -> None:
        class ProbeStore:
            def __init__(self) -> None:
                self.synced_email: str | None = None

            def sync_user(self, email: str, name: str | None = None, image: str | None = None) -> User:
                self.synced_email = email
                return User(id="probe-user", email=email, name=name, image=image)

        probe_store = ProbeStore()
        runtime = RankKitRuntime(
            store=probe_store,
            auth_session=AuthSession(),
            route_policy=RoutePolicy(),
        )
        client = TestClient(create_app(runtime))

        response = client.post("/v1/auth/sync", json={"email": "probe@example.com", "name": "Probe"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["id"], "probe-user")
        self.assertEqual(probe_store.synced_email, "probe@example.com")

    def test_main_module_does_not_hardwire_local_snapshot_store(self) -> None:
        main_source = (REPO_ROOT / "backend" / "app" / "main.py").read_text(encoding="utf-8")

        self.assertIn("def create_app(runtime: RankKitRuntime | None = None)", main_source)
        self.assertIn("runtime = runtime or create_runtime()", main_source)
        self.assertNotIn("store = RankKitStore", main_source)


if __name__ == "__main__":
    unittest.main()
