import unittest
from pathlib import Path

from fastapi import HTTPException

from app.auth_session import MissingLocalUserHeader
from app.domain import RankKitError


REPO_ROOT = Path(__file__).resolve().parents[2]


class RoutePolicyTests(unittest.TestCase):
    def test_route_module_delegates_response_and_error_mapping_to_policy(self) -> None:
        policy_path = REPO_ROOT / "backend" / "app" / "route_policy.py"
        main_path = REPO_ROOT / "backend" / "app" / "main.py"

        self.assertTrue(policy_path.exists())
        policy_source = policy_path.read_text(encoding="utf-8")
        main_source = main_path.read_text(encoding="utf-8")

        self.assertIn("class RoutePolicy", policy_source)
        self.assertIn("def data_response", policy_source)
        self.assertIn("def auth_response", policy_source)
        self.assertIn("route_policy = RoutePolicy()", main_source)
        self.assertIn("route_policy.data_response", main_source)
        self.assertIn("route_policy.auth_response", main_source)
        self.assertNotIn("def _response", main_source)
        self.assertNotIn("def _auth_response", main_source)

    def test_route_policy_maps_auth_and_domain_errors(self) -> None:
        from app.route_policy import RoutePolicy

        policy = RoutePolicy()

        self.assertEqual(policy.data_response(lambda: "ok"), {"data": "ok"})

        with self.assertRaises(HTTPException) as missing_header:
            policy.auth_response(lambda: (_ for _ in ()).throw(MissingLocalUserHeader("Missing user header for local MVP.")))
        self.assertEqual(missing_header.exception.status_code, 401)

        with self.assertRaises(HTTPException) as missing_user:
            policy.auth_response(lambda: (_ for _ in ()).throw(RankKitError("User was not found.")))
        self.assertEqual(missing_user.exception.status_code, 404)

        with self.assertRaises(HTTPException) as domain_error:
            policy.data_response(lambda: (_ for _ in ()).throw(RankKitError("League was not found.")))
        self.assertEqual(domain_error.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
