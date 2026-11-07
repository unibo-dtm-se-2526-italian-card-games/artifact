"""The in-memory LobbyRepository against the repository contract (FR-27)."""

import pytest

from italian_card_games.lobby.ports import LobbyRepository
from italian_card_games.persistence.in_memory import InMemoryLobbyRepository
from tests.lobby.lobby_repository_contract import LobbyRepositoryContract


class TestInMemoryLobbyRepository(LobbyRepositoryContract):
    @pytest.fixture
    def repository(self) -> LobbyRepository:
        return InMemoryLobbyRepository()
