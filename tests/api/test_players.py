"""Tests for registering and selecting a player through the API (FR-26, FR-34)."""

import pytest
from fastapi.testclient import TestClient


def register(client: TestClient, nickname: str) -> int:
    return client.post("/api/v1/players", json={"nickname": nickname}).status_code


class TestRegisterPlayer:
    def test_fr26_a_new_nickname_is_created(self, client: TestClient) -> None:
        response = client.post("/api/v1/players", json={"nickname": "Anna"})
        assert response.status_code == 201
        assert response.json() == {"nickname": "Anna"}

    def test_fr26_the_nickname_is_trimmed(self, client: TestClient) -> None:
        response = client.post("/api/v1/players", json={"nickname": "  anna  "})
        assert response.status_code == 201
        assert response.json() == {"nickname": "anna"}

    def test_fr26_a_taken_nickname_is_a_conflict_with_an_explicit_error(
        self, client: TestClient
    ) -> None:
        register(client, "anna")
        response = client.post("/api/v1/players", json={"nickname": "anna"})
        assert response.status_code == 409
        assert "anna" in response.json()["detail"]

    def test_fr26_a_nickname_differing_only_in_case_is_a_conflict(
        self, client: TestClient
    ) -> None:
        register(client, "Anna")
        assert register(client, "ANNA") == 409

    def test_fr26_a_conflict_keeps_the_first_casing(self, client: TestClient) -> None:
        register(client, "Anna")
        register(client, "ANNA")
        assert client.get("/api/v1/players/anna").json() == {"nickname": "Anna"}

    @pytest.mark.parametrize("nickname", ["", "ab", "x" * 21, "anna rossi", "anna!"])
    def test_fr26_an_invalid_nickname_is_unprocessable(
        self, client: TestClient, nickname: str
    ) -> None:
        assert register(client, nickname) == 422

    def test_fr26_a_missing_nickname_is_unprocessable(self, client: TestClient) -> None:
        assert client.post("/api/v1/players", json={}).status_code == 422


class TestSelectPlayer:
    def test_fr26_a_registered_player_is_found(self, client: TestClient) -> None:
        register(client, "anna")
        response = client.get("/api/v1/players/anna")
        assert response.status_code == 200
        assert response.json() == {"nickname": "anna"}

    def test_fr26_the_lookup_ignores_case_and_returns_the_chosen_casing(
        self, client: TestClient
    ) -> None:
        register(client, "DaVide")
        response = client.get("/api/v1/players/DAVIDE")
        assert response.status_code == 200
        assert response.json() == {"nickname": "DaVide"}

    def test_fr26_an_unregistered_nickname_is_not_found(
        self, client: TestClient
    ) -> None:
        response = client.get("/api/v1/players/anna")
        assert response.status_code == 404
        assert "anna" in response.json()["detail"]

    def test_fr26_an_invalid_nickname_is_unprocessable(
        self, client: TestClient
    ) -> None:
        assert client.get("/api/v1/players/ab").status_code == 422


class TestPlayersAreDocumented:
    def test_fr34_both_player_routes_are_in_the_openapi_document(
        self, client: TestClient
    ) -> None:
        paths = client.get("/api/v1/openapi.json").json()["paths"]
        assert "post" in paths["/api/v1/players"]
        assert "get" in paths["/api/v1/players/{nickname}"]
