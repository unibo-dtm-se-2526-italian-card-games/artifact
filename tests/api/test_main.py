"""Tests for the composition root that wires the API to SQLite (FR-26, FR-31, FR-34)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from italian_card_games.api.main import DATABASE_URL_VARIABLE, build_app
from italian_card_games.persistence.sqlite import SqlMatchRepository
from tests.history.match_repository_contract import briscola


@pytest.fixture
def database_url(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path / 'api.db'}"


class TestBuildApp:
    def test_fr34_the_built_app_serves_the_games_of_the_catalog(
        self, database_url: str
    ) -> None:
        client = TestClient(build_app(database_url))
        games = client.get("/api/v1/games").json()
        assert [game["id"] for game in games] == ["briscola", "matazza"]

    def test_fr26_a_registered_player_survives_a_restart(
        self, database_url: str
    ) -> None:
        first = TestClient(build_app(database_url))
        assert (
            first.post("/api/v1/players", json={"nickname": "Anna"}).status_code == 201
        )

        second = TestClient(build_app(database_url))
        assert second.get("/api/v1/players/anna").json() == {"nickname": "Anna"}
        assert (
            second.post("/api/v1/players", json={"nickname": "ANNA"}).status_code == 409
        )

    def test_fr31_a_stored_match_appears_in_the_history_after_a_restart(
        self, database_url: str
    ) -> None:
        TestClient(build_app(database_url)).post(
            "/api/v1/players", json={"nickname": "anna"}
        )
        engine = create_engine(database_url)
        SqlMatchRepository(engine).save(briscola("m-1", 0))
        engine.dispose()

        client = TestClient(build_app(database_url))
        history = client.get("/api/v1/players/anna/matches").json()

        assert [match["id"] for match in history] == ["m-1"]

    def test_fr26_the_database_is_read_from_the_environment_by_default(
        self, database_url: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(DATABASE_URL_VARIABLE, database_url)
        TestClient(build_app()).post("/api/v1/players", json={"nickname": "anna"})

        client = TestClient(build_app(database_url))
        assert client.get("/api/v1/players/anna").status_code == 200

    def test_fr26_the_variable_has_a_documented_name(self) -> None:
        assert DATABASE_URL_VARIABLE == "ICG_DATABASE_URL"
