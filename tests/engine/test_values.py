"""Tests for the value objects shared by the games and the AI strategies (FR-04, FR-06)."""

from dataclasses import FrozenInstanceError

import pytest

from italian_card_games.engine.cards import Card, Rank, Suit
from italian_card_games.engine.values import Move, Outcome, PlayerView, SeatIndex

EIGHT_OF_SPADES = Card(Suit.SPADE, Rank(8))
ACE_OF_COINS = Card(Suit.DENARI, Rank(1))


class TestSeatIndex:
    @pytest.mark.parametrize("value", [0, 1, 3])
    def test_accepts_non_negative_numbers(self, value):
        assert SeatIndex(value).value == value

    @pytest.mark.parametrize("value", [-1, -10])
    def test_rejects_negative_numbers(self, value):
        with pytest.raises(ValueError):
            SeatIndex(value)

    def test_is_equal_by_value(self):
        assert SeatIndex(2) == SeatIndex(2)
        assert SeatIndex(2) != SeatIndex(3)
        assert hash(SeatIndex(2)) == hash(SeatIndex(2))


class TestMove:
    def test_holds_the_seat_and_the_card_played(self):
        move = Move(SeatIndex(1), EIGHT_OF_SPADES)
        assert move.seat == SeatIndex(1)
        assert move.card == EIGHT_OF_SPADES

    def test_is_equal_by_value(self):
        move = Move(SeatIndex(1), EIGHT_OF_SPADES)
        assert move == Move(SeatIndex(1), EIGHT_OF_SPADES)
        assert move != Move(SeatIndex(2), EIGHT_OF_SPADES)
        assert move != Move(SeatIndex(1), ACE_OF_COINS)

    def test_is_immutable(self):
        move = Move(SeatIndex(1), EIGHT_OF_SPADES)
        with pytest.raises(FrozenInstanceError):
            move.card = ACE_OF_COINS  # type: ignore[misc]


class TestOutcome:
    def test_is_either_win_or_loss(self):
        assert {outcome.name for outcome in Outcome} == {"WIN", "LOSS"}


class TestPlayerView:
    def test_holds_the_own_hand_and_the_moves_on_the_table(self):
        on_table = (Move(SeatIndex(0), ACE_OF_COINS),)
        view = PlayerView(SeatIndex(1), (EIGHT_OF_SPADES,), on_table)
        assert view.seat == SeatIndex(1)
        assert view.hand == (EIGHT_OF_SPADES,)
        assert view.trick == on_table

    def test_the_table_can_be_empty_when_the_seat_leads(self):
        view = PlayerView(SeatIndex(0), (EIGHT_OF_SPADES,), ())
        assert view.trick == ()

    def test_fr20_has_no_trump_suit_unless_the_game_names_one(self):
        view = PlayerView(SeatIndex(0), (EIGHT_OF_SPADES,), ())
        assert view.trump is None

    def test_fr20_holds_the_trump_suit_of_the_round(self):
        view = PlayerView(SeatIndex(0), (EIGHT_OF_SPADES,), (), Suit.DENARI)
        assert view.trump == Suit.DENARI

    def test_rejects_duplicate_cards_in_the_hand(self):
        with pytest.raises(ValueError):
            PlayerView(SeatIndex(0), (EIGHT_OF_SPADES, EIGHT_OF_SPADES), ())

    def test_is_immutable(self):
        view = PlayerView(SeatIndex(0), (EIGHT_OF_SPADES,), ())
        with pytest.raises(FrozenInstanceError):
            view.hand = ()  # type: ignore[misc]
