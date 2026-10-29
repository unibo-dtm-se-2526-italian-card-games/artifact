"""The SQLite MatchRepository against the repository contract (FR-31 to FR-33)."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine

from italian_card_games.history.ports import MatchRepository
from italian_card_games.history.records import MatchId
from italian_card_games.persistence.sqlite import SqlMatchRepository
from tests.history.match_repository_contract import (
    MatchRepositoryContract,
    briscola,
    matazza,
)


@pytest.fixture
def file_url(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path / 'matches.db'}"


class TestSqlMatchRepository(MatchRepositoryContract):
    @pytest.fixture
    def repository(self) -> MatchRepository:
        return SqlMatchRepository(create_engine("sqlite://"))


class TestSurvivingARestart:
    """Each engine is disposed before the next opens, as on a real restart."""

    def test_fr31_a_saved_match_survives_a_restart(self, file_url: str) -> None:
        record = matazza("m-1", 0)
        before = create_engine(file_url)
        SqlMatchRepository(before).save(record)
        before.dispose()

        after = create_engine(file_url)
        try:
            assert SqlMatchRepository(after).get(MatchId("m-1")) == record
        finally:
            after.dispose()

    def test_fr32_history_survives_a_restart_in_order(self, file_url: str) -> None:
        first, later = matazza("a", 0), briscola("b", 10)
        before = create_engine(file_url)
        repository = SqlMatchRepository(before)
        repository.save(later)
        repository.save(first)
        before.dispose()

        after = create_engine(file_url)
        try:
            assert SqlMatchRepository(after).history_of("anna") == [first, later]
        finally:
            after.dispose()
