import unittest

from fastapi.testclient import TestClient

from app import main as main_module
from app.domain import RankKitStore


class ApiDemoFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        main_module.store = RankKitStore()
        self.client = TestClient(main_module.create_app())

    def test_demo_flow_through_http_routes(self) -> None:
        owner = self._sync_user("owner@example.com", "Owner")
        opponent = self._sync_user("opponent@example.com", "Opponent")

        league_response = self.client.post(
            "/v1/leagues",
            json={
                "owner_id": owner["id"],
                "name": "Friday Ladder",
                "slug": "friday-ladder-api",
                "is_public": True,
            },
        )
        self.assertEqual(league_response.status_code, 200)
        league = league_response.json()["data"]

        list_response = self.client.get(f"/v1/leagues?user_id={owner['id']}")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["data"][0]["id"], league["id"])

        invite_response = self.client.post(
            f"/v1/leagues/{league['id']}/invites",
            json={"admin_id": owner["id"]},
        )
        self.assertEqual(invite_response.status_code, 200)
        invite = invite_response.json()["data"]

        accept_response = self.client.post(
            f"/v1/invites/{invite['token']}/accept",
            json={"user_id": opponent["id"]},
        )
        self.assertEqual(accept_response.status_code, 200)

        match_response = self.client.post(
            f"/v1/leagues/{league['id']}/matches",
            json={
                "reported_by_id": owner["id"],
                "winner_id": owner["id"],
                "loser_id": opponent["id"],
            },
        )
        self.assertEqual(match_response.status_code, 200)
        match = match_response.json()["data"]
        self.assertEqual(match["status"], "PENDING")

        confirm_response = self.client.post(
            f"/v1/leagues/{league['id']}/matches/{match['id']}/confirm",
            json={"actor_id": opponent["id"]},
        )
        self.assertEqual(confirm_response.status_code, 200)
        self.assertEqual(confirm_response.json()["data"]["status"], "COMPLETED")

        leaderboard_response = self.client.get(f"/v1/leagues/{league['id']}/leaderboard")
        self.assertEqual(leaderboard_response.status_code, 200)
        standings = leaderboard_response.json()["data"]
        self.assertEqual(standings[0]["user_id"], owner["id"])
        self.assertEqual(standings[0]["rating"], 1016)
        self.assertEqual(standings[1]["rating"], 984)

        members_response = self.client.get(f"/v1/leagues/{league['id']}/members")
        self.assertEqual(members_response.status_code, 200)
        members = members_response.json()["data"]
        self.assertEqual(members[0]["email"], "owner@example.com")
        self.assertEqual(members[1]["email"], "opponent@example.com")

    def test_disputed_match_can_be_rejected_by_admin(self) -> None:
        owner = self._sync_user("owner@example.com", "Owner")
        opponent = self._sync_user("opponent@example.com", "Opponent")
        league = self.client.post(
            "/v1/leagues",
            json={
                "owner_id": owner["id"],
                "name": "Tuesday Ladder",
                "slug": "tuesday-ladder-api",
            },
        ).json()["data"]
        invite = self.client.post(
            f"/v1/leagues/{league['id']}/invites",
            json={"admin_id": owner["id"]},
        ).json()["data"]
        self.client.post(f"/v1/invites/{invite['token']}/accept", json={"user_id": opponent["id"]})
        match = self.client.post(
            f"/v1/leagues/{league['id']}/matches",
            json={
                "reported_by_id": owner["id"],
                "winner_id": owner["id"],
                "loser_id": opponent["id"],
            },
        ).json()["data"]

        dispute_response = self.client.post(
            f"/v1/leagues/{league['id']}/matches/{match['id']}/dispute",
            json={"actor_id": opponent["id"], "note": "Score was wrong"},
        )
        self.assertEqual(dispute_response.status_code, 200)
        self.assertEqual(dispute_response.json()["data"]["status"], "DISPUTED")

        reject_response = self.client.post(
            f"/v1/leagues/{league['id']}/matches/{match['id']}/reject",
            json={"actor_id": owner["id"]},
        )
        self.assertEqual(reject_response.status_code, 200)
        self.assertEqual(reject_response.json()["data"]["status"], "REJECTED")

        standings = self.client.get(f"/v1/leagues/{league['id']}/leaderboard").json()["data"]
        self.assertEqual(standings[0]["rating"], 1000)
        self.assertEqual(standings[1]["rating"], 1000)

    def _sync_user(self, email: str, name: str) -> dict:
        response = self.client.post("/v1/auth/sync", json={"email": email, "name": name})
        self.assertEqual(response.status_code, 200)
        return response.json()["data"]


if __name__ == "__main__":
    unittest.main()
