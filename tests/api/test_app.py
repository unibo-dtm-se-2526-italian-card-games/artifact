"""Tests for the app factory, the versioned routes and the OpenAPI document (FR-34)."""

from fastapi.testclient import TestClient


class TestGames:
    def test_fr34_games_lists_every_game_with_its_player_count(
        self, client: TestClient
    ) -> None:
        response = client.get("/api/v1/games")
        assert response.status_code == 200
        assert response.json() == [
            {"id": "briscola", "player_count": 2},
            {"id": "matazza", "player_count": 4},
        ]

    def test_fr34_routes_exist_only_under_the_versioned_prefix(
        self, client: TestClient
    ) -> None:
        assert client.get("/games").status_code == 404


class TestOpenApi:
    def test_fr34_the_openapi_document_is_published_under_the_version(
        self, client: TestClient
    ) -> None:
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        assert response.json()["openapi"].startswith("3.")

    def test_fr34_every_documented_path_is_versioned(self, client: TestClient) -> None:
        paths = client.get("/api/v1/openapi.json").json()["paths"]
        assert paths
        assert all(path.startswith("/api/v1/") for path in paths)

    def test_fr34_the_games_route_is_described(self, client: TestClient) -> None:
        paths = client.get("/api/v1/openapi.json").json()["paths"]
        assert "/api/v1/games" in paths

    def test_fr34_every_operation_has_a_description(self, client: TestClient) -> None:
        paths = client.get("/api/v1/openapi.json").json()["paths"]
        missing = [
            f"{method.upper()} {path}"
            for path, operations in paths.items()
            for method, operation in operations.items()
            if not operation.get("description")
        ]
        assert missing == []
