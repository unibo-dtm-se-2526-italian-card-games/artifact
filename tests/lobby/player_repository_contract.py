"""Contract tests every PlayerRepository adapter must pass (FR-26).

Subclass PlayerRepositoryContract in a `test_*.py` file and override the
`repository` fixture with an empty repository of the adapter under test.
"""

import pytest

from italian_card_games.lobby.nickname import Nickname
from italian_card_games.lobby.player import RegisteredPlayer
from italian_card_games.lobby.ports import PlayerRepository


class PlayerRepositoryContract:
    @pytest.fixture
    def repository(self) -> PlayerRepository:
        raise NotImplementedError("override this fixture in the adapter's test class")

    def test_fr26_an_unknown_nickname_is_not_found(
        self, repository: PlayerRepository
    ) -> None:
        assert repository.get(Nickname("anna")) is None

    def test_fr26_an_added_player_can_be_read_back(
        self, repository: PlayerRepository
    ) -> None:
        player = RegisteredPlayer(Nickname("anna"))
        repository.add(player)
        assert repository.get(Nickname("anna")) == player

    def test_fr26_lookup_ignores_case_and_keeps_the_chosen_casing(
        self, repository: PlayerRepository
    ) -> None:
        repository.add(RegisteredPlayer(Nickname("DaVide")))
        found = repository.get(Nickname("DAVIDE"))
        assert found is not None
        assert found.nickname.value == "DaVide"

    def test_fr26_adding_a_taken_nickname_is_rejected(
        self, repository: PlayerRepository
    ) -> None:
        repository.add(RegisteredPlayer(Nickname("anna")))
        with pytest.raises(ValueError, match="anna"):
            repository.add(RegisteredPlayer(Nickname("anna")))

    def test_fr26_a_nickname_differing_only_in_case_is_taken(
        self, repository: PlayerRepository
    ) -> None:
        repository.add(RegisteredPlayer(Nickname("Anna")))
        with pytest.raises(ValueError, match="ANNA"):
            repository.add(RegisteredPlayer(Nickname("ANNA")))

    def test_fr26_a_rejected_add_leaves_the_first_player_unchanged(
        self, repository: PlayerRepository
    ) -> None:
        repository.add(RegisteredPlayer(Nickname("Anna")))
        with pytest.raises(ValueError):
            repository.add(RegisteredPlayer(Nickname("ANNA")))
        found = repository.get(Nickname("anna"))
        assert found is not None
        assert found.nickname.value == "Anna"

    def test_fr26_different_nicknames_are_stored_side_by_side(
        self, repository: PlayerRepository
    ) -> None:
        repository.add(RegisteredPlayer(Nickname("anna")))
        repository.add(RegisteredPlayer(Nickname("bruno")))
        assert repository.get(Nickname("anna")) is not None
        assert repository.get(Nickname("bruno")) is not None
