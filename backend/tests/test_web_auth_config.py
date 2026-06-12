import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class WebAuthConfigTests(unittest.TestCase):
    def test_web_auth_secret_is_guarded_for_production(self) -> None:
        secret_module = (REPO_ROOT / "apps" / "web" / "src" / "auth-secret.ts").read_text(encoding="utf-8")

        for expected in [
            "export function requireNextAuthSecret",
            "process.env.NEXTAUTH_SECRET",
            "process.env.NODE_ENV === \"production\"",
            "NEXTAUTH_SECRET must be set in production",
            "dev-nextauth-secret-change-me",
        ]:
            self.assertIn(expected, secret_module)

    def test_web_auth_and_middleware_use_secret_guard(self) -> None:
        auth = (REPO_ROOT / "apps" / "web" / "src" / "auth.ts").read_text(encoding="utf-8")
        middleware = (REPO_ROOT / "apps" / "web" / "middleware.ts").read_text(encoding="utf-8")

        self.assertIn("requireNextAuthSecret", auth)
        self.assertIn("requireNextAuthSecret", middleware)
        self.assertNotIn("process.env.NEXTAUTH_SECRET ?? \"dev-nextauth-secret-change-me\"", auth)
        self.assertNotIn("secret: process.env.NEXTAUTH_SECRET", middleware)


if __name__ == "__main__":
    unittest.main()
