import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class LocalDemoFlowTests(unittest.TestCase):
    def test_demo_page_delegates_to_local_demo_flow_module(self) -> None:
        demo_flow = REPO_ROOT / "apps" / "web" / "src" / "lib" / "local-demo-flow.ts"
        demo_client = REPO_ROOT / "apps" / "web" / "src" / "app" / "demo" / "demo-client.tsx"

        self.assertTrue(demo_flow.exists())
        self.assertIn("export async function runLocalDemo", demo_flow.read_text(encoding="utf-8"))

        client_source = demo_client.read_text(encoding="utf-8")
        self.assertIn("runLocalDemo", client_source)
        self.assertNotIn("api.auth.sync", client_source)
        self.assertNotIn("api.matches.confirm", client_source)


if __name__ == "__main__":
    unittest.main()
