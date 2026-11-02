"""Tests for a player's match history and statistics through the API (FR-32, FR-33)."""

from datetime import datetime

from fastapi.testclient import TestClient

from italian_card_games.engine.values import Outcome
from italian_card_games.persistence.in_memory import InMemoryMatchRepository
from tests.history.match_repository_contract import START, briscola, matazza


def register(client: TestClient, nickname: str) -> None:
    client.post("/api/v1/players", json={"nickname": nickname})


class TestHistory:
    def test_fr32_a_player_without_matches_has_an_empty_history(
        self, client: TestClient
    ) -> None:
        register(client, "anna")
        response = client.get("/api/v1/players/anna/matches")
        assert response.status_code == 200
        assert response.json() == []

    def test_fr32_a_match_lists_its_participants_and_exact_round_scores(
        self, client: TestClient, matches: InMemoryMatchRepository
    ) -> None:
        register(client, "anna")
        matches.save(matazza("m-1", 0))

        [match] = client.get("/api/v1/players/anna/matches").json()

        assert match["id"] == "m-1"
        assert match["game_type"] == "matazza"
        assert datetime.fromisoformat(match["finished_at"]) == START
        assert match["participants"][2] == {
            "seat": 2,
            "name": "anna",
            "is_bot": False,
            "outcome": "win",
        }
        assert [p["is_bot"] for p in match["participants"]] == [True, True, False, True]
        assert match["rounds"] == [
            {"scores": ["4", "10/3", "2", "4/3"]},
            {"scores": ["1/3", "5", "3", "7/3"]},
        ]

    def test_fr32_matches_come_oldest_first(
        self, client: TestClient, matches: InMemoryMatchRepository
    ) -> None:
        register(client, "anna")
        matches.save(briscola("m-2", 10))
        matches.save(matazza("m-1", 0))

        history = client.get("/api/v1/players/anna/matches").json()

        assert [match["id"] for match in history] == ["m-1", "m-2"]

    def test_fr32_only_the_matches_of_that_player_are_listed(
        self, client: TestClient, matches: InMemoryMatchRepository
    ) -> None:
        register(client, "anna")
        matches.save(briscola("m-1", 0))
        matches.save(briscola("m-2", 5, name="bruno"))

        history = client.get("/api/v1/players/anna/matches").json()

        assert [match["id"] for match in history] == ["m-1"]

    def test_fr32_the_lookup_ignores_case(
        self, client: TestClient, matches: InMemoryMatchRepository
    ) -> None:
        register(client, "Anna")
        matches.save(briscola("m-1", 0, name="Anna"))

        response = client.get("/api/v1/players/ANNA/matches")

        assert [match["id"] for match in response.json()] == ["m-1"]

    def test_fr32_an_unregistered_player_is_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/players/anna/matches")
        assert response.status_code == 404
        assert "anna" in response.json()["detail"]

    def test_fr32_an_invalid_nickname_is_unprocessable(self, client: TestClient) -> None:
        assert client.get("/api/v1/players/ab/matches").status_code == 422


class TestStatistics:
    def test_fr33_a_player_without_matches_has_no_statistics(
        self, client: TestClient
    ) -> None:
        register(client, "anna")
        response = client.get("/api/v1/players/anna/stats")
        assert response.status_code == 200
        assert response.json() == {}

    def test_fr33_statistics_count_results_per_game_type(
        self, client: TestClient, matches: InMemoryMatchRepository
    ) -> None:
        register(client, "anna")
        matches.save(matazza("m-1", 0))
        matches.save(briscola("m-2", 10))
        matches.save(briscola("m-3", 20, anna=Outcome.DRAW))
        matches.save(briscola("m-4", 30, anna=Outcome.LOSS))

        response = client.get("/api/v1/players/anna/stats")

        assert response.status_code == 200
        assert response.json() == {
            "briscola": {"played": 3, "wins": 1, "losses": 1, "draws": 1},
            "matazza": {"played": 1, "wins": 1, "losses": 0, "draws": 0},
        }

    def test_fr33_statistics_ignore_other_players_and_case(
        self, client: TestClient, matches: InMemoryMatchRepository
    ) -> None:
        register(client, "Anna")
        matches.save(briscola("m-1", 0, name="Anna"))
        matches.save(briscola("m-2", 5, name="bruno"))

        response = client.get("/api/v1/players/ANNA/stats")

        assert response.json() == {
            "briscola": {"played": 1, "wins": 1, "losses": 0, "draws": 0}
        }

    def test_fr33_an_unregistered_player_is_not_found(self, client: TestClient) -> None:
        assert client.get("/api/v1/players/anna/stats").status_code == 404

    def test_fr33_an_invalid_nickname_is_unprocessable(self, client: TestClient) -> None:
        assert client.get("/api/v1/players/ab/stats").status_code == 422


class TestHistoryIsDocumented:
    def test_fr34_the_history_and_statistics_routes_are_in_the_openapi_document(
        self, client: TestClient
    ) -> None:
        paths = client.get("/api/v1/openapi.json").json()["paths"]
        assert "get" in paths["/api/v1/players/{nickname}/matches"]
        assert "get" in paths["/api/v1/players/{nickname}/stats"]
