"""The in-memory MatchRepository against the repository contract (FR-31 to FR-33)."""

import pytest

from italian_card_games.history.ports import MatchRepository
from italian_card_games.persistence.in_memory import InMemoryMatchRepository
from tests.history.match_repository_contract import MatchRepositoryContract


class TestInMemoryMatchRepository(MatchRepositoryContract):
    @pytest.fixture
    def repository(self) -> MatchRepository:
        return InMemoryMatchRepository()
