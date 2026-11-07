"""Tests for the Lobby aggregate (FR-27, FR-28)."""

import pytest

from italian_card_games.engine.values import SeatIndex
from italian_card_games.lobby.join_code import JoinCode
from italian_card_games.lobby.lobby import (
    AlreadyJoinedError,
    Lobby,
    LobbyError,
    LobbyFullError,
    LobbyStartedError,
    NotCreatorError,
    NotInLobbyError,
)
from italian_card_games.lobby.nickname import Nickname
from italian_card_games.lobby.seat import Occupant

CODE = JoinCode("ABC234")
ANNA = Nickname("Anna")
BRUNO = Nickname("Bruno")
CARLA = Nickname("Carla")
DARIO = Nickname("Dario")
ELENA = Nickname("Elena")


def make_lobby(player_count: int = 4) -> Lobby:
    return Lobby(CODE, "matazza", player_count, ANNA)


class TestCreation:
    def test_fr27_a_new_lobby_has_its_code_and_game(self) -> None:
        lobby = make_lobby()
        assert lobby.code == CODE
        assert lobby.game_id == "matazza"

    def test_fr27_a_new_lobby_has_one_seat_per_player(self) -> None:
        assert len(make_lobby(4).seats) == 4
        assert len(make_lobby(2).seats) == 2

    def test_fr27_the_creator_takes_seat_zero(self) -> None:
        lobby = make_lobby()
        assert lobby.seats[0].occupant == Occupant.human(ANNA)
        assert all(seat.is_empty for seat in lobby.seats[1:])
        assert lobby.creator == ANNA

    def test_fr27_seat_positions_run_from_zero(self) -> None:
        positions = [seat.position for seat in make_lobby().seats]
        assert positions == [SeatIndex(i) for i in range(4)]

    def test_fr27_a_new_lobby_has_not_started(self) -> None:
        assert not make_lobby().is_started

    def test_fr27_a_lobby_needs_at_least_two_seats(self) -> None:
        with pytest.raises(ValueError, match="2"):
            Lobby(CODE, "briscola", 1, ANNA)


class TestJoin:
    def test_fr27_a_player_takes_the_lowest_empty_seat(self) -> None:
        lobby = make_lobby()
        assert lobby.join(BRUNO) == SeatIndex(1)
        assert lobby.join(CARLA) == SeatIndex(2)
        assert lobby.seats[2].occupant == Occupant.human(CARLA)

    def test_fr27_joining_twice_is_rejected_ignoring_case(self) -> None:
        lobby = make_lobby()
        lobby.join(BRUNO)
        with pytest.raises(AlreadyJoinedError):
            lobby.join(Nickname("bruno"))

    def test_fr27_the_creator_cannot_join_again(self) -> None:
        with pytest.raises(AlreadyJoinedError):
            make_lobby().join(ANNA)

    def test_fr27_a_full_lobby_rejects_joins(self) -> None:
        lobby = make_lobby(2)
        lobby.join(BRUNO)
        with pytest.raises(LobbyFullError):
            lobby.join(CARLA)

    def test_fr27_a_started_lobby_rejects_joins(self) -> None:
        lobby = make_lobby(4)
        lobby.start(ANNA)
        with pytest.raises(LobbyStartedError):
            lobby.join(BRUNO)

    def test_fr27_all_lobby_errors_are_value_errors(self) -> None:
        assert issubclass(LobbyError, ValueError)
        for error in (
            AlreadyJoinedError,
            LobbyFullError,
            LobbyStartedError,
            NotCreatorError,
            NotInLobbyError,
        ):
            assert issubclass(error, LobbyError)


class TestLeave:
    def test_fr27_leaving_frees_the_seat(self) -> None:
        lobby = make_lobby()
        lobby.join(BRUNO)
        lobby.leave(BRUNO)
        assert lobby.seats[1].is_empty

    def test_fr27_a_freed_seat_is_taken_by_the_next_join(self) -> None:
        lobby = make_lobby()
        lobby.join(BRUNO)
        lobby.join(CARLA)
        lobby.leave(BRUNO)
        assert lobby.join(DARIO) == SeatIndex(1)

    def test_fr27_leaving_ignores_letter_case(self) -> None:
        lobby = make_lobby()
        lobby.join(BRUNO)
        lobby.leave(Nickname("BRUNO"))
        assert lobby.seats[1].is_empty

    def test_fr27_someone_not_in_the_lobby_cannot_leave(self) -> None:
        with pytest.raises(NotInLobbyError):
            make_lobby().leave(BRUNO)

    def test_fr27_a_started_lobby_rejects_leaving(self) -> None:
        lobby = make_lobby()
        lobby.start(ANNA)
        with pytest.raises(LobbyStartedError):
            lobby.leave(ANNA)

    def test_fr27_when_the_creator_leaves_the_next_human_by_seat_takes_over(
        self,
    ) -> None:
        lobby = make_lobby()
        lobby.join(BRUNO)
        lobby.join(CARLA)
        lobby.leave(ANNA)
        assert lobby.creator == BRUNO

    def test_fr27_a_lobby_with_no_humans_is_empty(self) -> None:
        lobby = make_lobby()
        assert not lobby.is_empty
        lobby.leave(ANNA)
        assert lobby.is_empty

    def test_fr27_an_empty_lobby_has_no_creator(self) -> None:
        lobby = make_lobby()
        lobby.leave(ANNA)
        assert lobby.creator is None


class TestFillWithBots:
    def test_fr28_every_empty_seat_gets_a_bot(self) -> None:
        lobby = make_lobby()
        lobby.join(BRUNO)
        lobby.fill_with_bots()
        assert lobby.seats[0].occupant == Occupant.human(ANNA)
        assert lobby.seats[1].occupant == Occupant.human(BRUNO)
        assert lobby.seats[2].occupant == Occupant.bot()
        assert lobby.seats[3].occupant == Occupant.bot()

    def test_fr28_a_lobby_filled_with_bots_is_full(self) -> None:
        lobby = make_lobby()
        lobby.fill_with_bots()
        with pytest.raises(LobbyFullError):
            lobby.join(BRUNO)

    def test_fr28_a_started_lobby_rejects_filling(self) -> None:
        lobby = make_lobby()
        lobby.start(ANNA)
        with pytest.raises(LobbyStartedError):
            lobby.fill_with_bots()


class TestStart:
    def test_fr28_one_human_starts_a_full_four_player_match(self) -> None:
        lobby = make_lobby(4)
        occupants = lobby.start(ANNA)
        assert occupants == (
            Occupant.human(ANNA),
            Occupant.bot(),
            Occupant.bot(),
            Occupant.bot(),
        )

    def test_fr28_the_occupants_come_in_seat_order(self) -> None:
        lobby = make_lobby(4)
        lobby.join(BRUNO)
        lobby.join(CARLA)
        occupants = lobby.start(ANNA)
        assert occupants == (
            Occupant.human(ANNA),
            Occupant.human(BRUNO),
            Occupant.human(CARLA),
            Occupant.bot(),
        )

    def test_fr28_a_two_player_game_needs_one_bot_for_one_human(self) -> None:
        occupants = make_lobby(2).start(ANNA)
        assert occupants == (Occupant.human(ANNA), Occupant.bot())

    def test_fr28_starting_marks_the_lobby_as_started(self) -> None:
        lobby = make_lobby()
        lobby.start(ANNA)
        assert lobby.is_started

    def test_fr28_only_the_creator_can_start(self) -> None:
        lobby = make_lobby()
        lobby.join(BRUNO)
        with pytest.raises(NotCreatorError):
            lobby.start(BRUNO)
        assert not lobby.is_started

    def test_fr28_someone_outside_the_lobby_cannot_start(self) -> None:
        with pytest.raises(NotCreatorError):
            make_lobby().start(ELENA)

    def test_fr28_the_creator_check_ignores_letter_case(self) -> None:
        assert len(make_lobby().start(Nickname("anna"))) == 4

    def test_fr28_a_lobby_starts_only_once(self) -> None:
        lobby = make_lobby()
        lobby.start(ANNA)
        with pytest.raises(LobbyStartedError):
            lobby.start(ANNA)

    def test_fr28_the_new_creator_can_start_after_the_first_one_left(self) -> None:
        lobby = make_lobby()
        lobby.join(BRUNO)
        lobby.leave(ANNA)
        occupants = lobby.start(BRUNO)
        assert occupants[1] == Occupant.human(BRUNO)
        assert occupants[0] == Occupant.bot()
