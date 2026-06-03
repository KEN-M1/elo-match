import time
import unittest

import jwt
from fastapi.testclient import TestClient

from app import main as main_module
from app.config import settings
from app.domain import RankKitStore


class AuthTests(unittest.TestCase):
    def setUp(self) -> None:
        main_module.store = RankKitStore()
        self.client = TestClient(main_module.create_app())

    def test_me_syncs_user_from_valid_bearer_token(self) -> None:
        token = jwt.encode(
            {
                "sub": "owner@example.com",
                "email": "owner@example.com",
                "name": "Owner",
                "iat": int(time.time()),
                "exp": int(time.time()) + 3600,
            },
            settings.jwt_secret,
            algorithm="HS256",
        )

        response = self.client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["email"], "owner@example.com")
        self.assertEqual(response.json()["data"]["name"], "Owner")

    def test_me_rejects_invalid_bearer_token(self) -> None:
        response = self.client.get("/v1/auth/me", headers={"Authorization": "Bearer nope"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("Bearer token is invalid", response.text)


if __name__ == "__main__":
    unittest.main()
