"""Tests for the Occupant value object and the Seat entity (FR-27, FR-28)."""

from italian_card_games.engine.values import SeatIndex
from italian_card_games.lobby.nickname import Nickname
from italian_card_games.lobby.seat import Occupant, Seat


class TestOccupant:
    def test_fr27_a_human_occupant_has_a_nickname(self) -> None:
        occupant = Occupant.human(Nickname("Davide"))
        assert occupant.nickname == Nickname("Davide")
        assert not occupant.is_bot

    def test_fr28_a_bot_occupant_has_no_nickname(self) -> None:
        occupant = Occupant.bot()
        assert occupant.nickname is None
        assert occupant.is_bot

    def test_fr27_humans_with_the_same_nickname_are_equal(self) -> None:
        assert Occupant.human(Nickname("Davide")) == Occupant.human(Nickname("davide"))

    def test_fr27_a_human_and_a_bot_are_different(self) -> None:
        assert Occupant.human(Nickname("Davide")) != Occupant.bot()


class TestSeat:
    def test_fr27_a_new_seat_is_empty(self) -> None:
        seat = Seat(SeatIndex(2))
        assert seat.position == SeatIndex(2)
        assert seat.occupant is None
        assert seat.is_empty

    def test_fr27_a_seat_with_an_occupant_is_not_empty(self) -> None:
        seat = Seat(SeatIndex(0), Occupant.human(Nickname("Davide")))
        assert not seat.is_empty

    def test_fr27_the_occupant_can_be_replaced_and_cleared(self) -> None:
        seat = Seat(SeatIndex(1))
        seat.occupant = Occupant.bot()
        assert seat.occupant == Occupant.bot()
        seat.occupant = None
        assert seat.is_empty
