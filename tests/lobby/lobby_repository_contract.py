"""Contract tests every LobbyRepository adapter must pass (FR-27).

Subclass LobbyRepositoryContract in a `test_*.py` file and override the
`repository` fixture with an empty repository of the adapter under test.
"""

import pytest

from italian_card_games.lobby.join_code import JoinCode
from italian_card_games.lobby.lobby import Lobby
from italian_card_games.lobby.nickname import Nickname
from italian_card_games.lobby.ports import LobbyRepository


def make_lobby(code: str = "ABC234") -> Lobby:
    return Lobby(JoinCode(code), "matazza", 4, Nickname("Anna"))


class LobbyRepositoryContract:
    @pytest.fixture
    def repository(self) -> LobbyRepository:
        raise NotImplementedError("override this fixture in the adapter's test class")

    def test_fr27_an_unknown_code_is_not_found(
        self, repository: LobbyRepository
    ) -> None:
        assert repository.get(JoinCode("ABC234")) is None

    def test_fr27_an_added_lobby_can_be_read_back(
        self, repository: LobbyRepository
    ) -> None:
        lobby = make_lobby()
        repository.add(lobby)
        assert repository.get(JoinCode("ABC234")) is lobby

    def test_fr27_a_change_to_a_stored_lobby_is_seen_on_the_next_read(
        self, repository: LobbyRepository
    ) -> None:
        lobby = make_lobby()
        repository.add(lobby)
        lobby.join(Nickname("Bruno"))
        stored = repository.get(JoinCode("ABC234"))
        assert stored is not None
        assert stored.seats[1].occupant is not None

    def test_fr27_adding_a_code_already_in_use_is_rejected(
        self, repository: LobbyRepository
    ) -> None:
        repository.add(make_lobby("ABC234"))
        with pytest.raises(ValueError, match="ABC234"):
            repository.add(make_lobby("ABC234"))

    def test_fr27_a_rejected_add_leaves_the_first_lobby_in_place(
        self, repository: LobbyRepository
    ) -> None:
        first = make_lobby("ABC234")
        repository.add(first)
        with pytest.raises(ValueError):
            repository.add(make_lobby("ABC234"))
        assert repository.get(JoinCode("ABC234")) is first

    def test_fr27_lobbies_with_different_codes_are_stored_side_by_side(
        self, repository: LobbyRepository
    ) -> None:
        repository.add(make_lobby("ABC234"))
        repository.add(make_lobby("XYZ789"))
        assert repository.get(JoinCode("ABC234")) is not None
        assert repository.get(JoinCode("XYZ789")) is not None

    def test_fr27_a_removed_lobby_is_no_longer_found(
        self, repository: LobbyRepository
    ) -> None:
        repository.add(make_lobby())
        repository.remove(JoinCode("ABC234"))
        assert repository.get(JoinCode("ABC234")) is None

    def test_fr27_removing_an_unknown_code_does_nothing(
        self, repository: LobbyRepository
    ) -> None:
        repository.remove(JoinCode("ABC234"))
        assert repository.get(JoinCode("ABC234")) is None

    def test_fr27_a_removed_code_can_be_used_again(
        self, repository: LobbyRepository
    ) -> None:
        repository.add(make_lobby())
        repository.remove(JoinCode("ABC234"))
        repository.add(make_lobby())
        assert repository.get(JoinCode("ABC234")) is not None
