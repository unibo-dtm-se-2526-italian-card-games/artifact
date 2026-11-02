"""The SQLite PlayerRepository against the repository contract (FR-26)."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine

from italian_card_games.history.records import MatchId
from italian_card_games.lobby.nickname import Nickname
from italian_card_games.lobby.player import RegisteredPlayer
from italian_card_games.lobby.ports import PlayerRepository
from italian_card_games.persistence.sqlite import (
    SqlMatchRepository,
    SqlPlayerRepository,
)
from tests.history.match_repository_contract import briscola
from tests.lobby.player_repository_contract import PlayerRepositoryContract


@pytest.fixture
def file_url(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path / 'players.db'}"


class TestSqlPlayerRepository(PlayerRepositoryContract):
    @pytest.fixture
    def repository(self) -> PlayerRepository:
        return SqlPlayerRepository(create_engine("sqlite://"))


class TestSurvivingARestart:
    """Each engine is disposed before the next opens, as on a real restart."""

    def test_fr26_a_registered_player_survives_a_restart(self, file_url: str) -> None:
        before = create_engine(file_url)
        SqlPlayerRepository(before).add(RegisteredPlayer(Nickname("DaVide")))
        before.dispose()

        after = create_engine(file_url)
        try:
            found = SqlPlayerRepository(after).get(Nickname("davide"))
            assert found is not None
            assert found.nickname.value == "DaVide"
        finally:
            after.dispose()

    def test_fr26_a_nickname_stays_taken_after_a_restart(self, file_url: str) -> None:
        before = create_engine(file_url)
        SqlPlayerRepository(before).add(RegisteredPlayer(Nickname("Anna")))
        before.dispose()

        after = create_engine(file_url)
        try:
            with pytest.raises(ValueError, match="ANNA"):
                SqlPlayerRepository(after).add(RegisteredPlayer(Nickname("ANNA")))
        finally:
            after.dispose()


class TestSharingADatabaseWithMatches:
    def test_fr26_players_and_matches_live_on_one_engine(self) -> None:
        engine = create_engine("sqlite://")
        players = SqlPlayerRepository(engine)
        matches = SqlMatchRepository(engine)

        players.add(RegisteredPlayer(Nickname("anna")))
        matches.save(briscola("m-1", 0))

        assert players.get(Nickname("anna")) is not None
        assert matches.get(MatchId("m-1")) is not None
