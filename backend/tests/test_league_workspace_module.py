import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class LeagueWorkspaceModuleTests(unittest.TestCase):
    def test_league_view_uses_display_ready_workspace_interface(self) -> None:
        workspace = (
            REPO_ROOT
            / "apps"
            / "web"
            / "src"
            / "app"
            / "leagues"
            / "[id]"
            / "league-workspace.ts"
        )
        client = (
            REPO_ROOT
            / "apps"
            / "web"
            / "src"
            / "app"
            / "leagues"
            / "[id]"
            / "league-client.tsx"
        )

        self.assertTrue(workspace.exists())
        workspace_source = workspace.read_text(encoding="utf-8")
        client_source = client.read_text(encoding="utf-8")

        for expected in [
            "memberRows",
            "matchForm",
            "pendingMatchCards",
            "recentMatchCards",
            "ratingHistoryRows",
        ]:
            self.assertIn(expected, workspace_source)
            self.assertIn(f"workspace.{expected}", client_source)

        for leaked_implementation in [
            "workspace.labelFor",
            "workspace.setWinnerId",
            "workspace.setLoserId",
            "workspace.setNewMemberEmail",
            "workspace.confirmMatch(",
            "workspace.confirmMatchAsAdmin",
            "workspace.disputeMatch(",
            "workspace.rejectMatch(",
        ]:
            self.assertNotIn(leaked_implementation, client_source)


if __name__ == "__main__":
    unittest.main()
