"""The in-memory PlayerRepository against the repository contract (FR-26)."""

import pytest

from italian_card_games.lobby.ports import PlayerRepository
from italian_card_games.persistence.in_memory import InMemoryPlayerRepository
from tests.lobby.player_repository_contract import PlayerRepositoryContract


class TestInMemoryPlayerRepository(PlayerRepositoryContract):
    @pytest.fixture
    def repository(self) -> PlayerRepository:
        return InMemoryPlayerRepository()
