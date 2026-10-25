"""Tests for the Briscola trick rules: strength, trump and trick winner (FR-20)."""

from itertools import combinations

import pytest

from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.cards import Card, Rank, Suit
from italian_card_games.engine.values import Move, PlayerView, SeatIndex

# FR-20: strongest first.
STRENGTH_ORDER = [1, 3, 10, 9, 8, 7, 6, 5, 4, 2]
TRUMP = Suit.DENARI


def card(suit: Suit, rank: int) -> Card:
    return Card(suit, Rank(rank))


def move(seat: int, suit: Suit, rank: int) -> Move:
    return Move(SeatIndex(seat), card(suit, rank))


class TestPlayers:
    def test_fr20_declares_two_players(self) -> None:
        assert BriscolaRules().player_count() == 2


class TestLegalMoves:
    def test_fr20_a_seat_leading_can_play_any_card_in_hand(self) -> None:
        hand = (card(Suit.COPPE, 4), card(Suit.SPADE, 1), card(TRUMP, 7))
        view = PlayerView(SeatIndex(0), hand, (), TRUMP)
        assert BriscolaRules().legal_moves(view) == tuple(
            Move(SeatIndex(0), c) for c in hand
        )

    def test_fr20_a_seat_answering_does_not_have_to_follow_the_led_suit(self) -> None:
        hand = (card(Suit.COPPE, 4), card(Suit.SPADE, 1))
        on_table = (move(0, Suit.COPPE, 10),)
        view = PlayerView(SeatIndex(1), hand, on_table, TRUMP)
        assert BriscolaRules().legal_moves(view) == tuple(
            Move(SeatIndex(1), c) for c in hand
        )

    def test_fr20_an_empty_hand_has_no_legal_moves(self) -> None:
        view = PlayerView(SeatIndex(0), (), (), TRUMP)
        assert BriscolaRules().legal_moves(view) == ()


class TestTrickWinnerStrength:
    @pytest.mark.parametrize(
        ("stronger", "weaker"),
        list(combinations(STRENGTH_ORDER, 2)),
    )
    def test_fr20_stronger_rank_beats_weaker_rank_in_the_led_suit(
        self, stronger: int, weaker: int
    ) -> None:
        for stronger_first in (True, False):
            first, second = (stronger, weaker) if stronger_first else (weaker, stronger)
            trick = (move(0, Suit.COPPE, first), move(1, Suit.COPPE, second))
            winner = BriscolaRules().trick_winner(trick, TRUMP)
            assert winner == SeatIndex(0 if stronger_first else 1)

    def test_fr20_ace_is_the_strongest_and_two_the_weakest(self) -> None:
        ace_over_three = (move(0, Suit.SPADE, 3), move(1, Suit.SPADE, 1))
        assert BriscolaRules().trick_winner(ace_over_three, TRUMP) == SeatIndex(1)
        four_over_two = (move(0, Suit.SPADE, 2), move(1, Suit.SPADE, 4))
        assert BriscolaRules().trick_winner(four_over_two, TRUMP) == SeatIndex(1)


class TestTrickWinnerTrump:
    def test_fr20_an_off_suit_non_trump_card_never_wins(self) -> None:
        trick = (move(0, Suit.COPPE, 2), move(1, Suit.SPADE, 1))
        assert BriscolaRules().trick_winner(trick, TRUMP) == SeatIndex(0)

    def test_fr20_a_trump_beats_a_stronger_card_of_the_led_suit(self) -> None:
        trick = (move(0, Suit.COPPE, 1), move(1, TRUMP, 2))
        assert BriscolaRules().trick_winner(trick, TRUMP) == SeatIndex(1)

    def test_fr20_a_led_trump_beats_an_off_suit_card(self) -> None:
        trick = (move(0, TRUMP, 2), move(1, Suit.COPPE, 1))
        assert BriscolaRules().trick_winner(trick, TRUMP) == SeatIndex(0)

    def test_fr20_the_higher_of_two_trumps_wins(self) -> None:
        trick = (move(0, TRUMP, 3), move(1, TRUMP, 1))
        assert BriscolaRules().trick_winner(trick, TRUMP) == SeatIndex(1)

    def test_fr20_the_winner_is_reported_by_seat_not_by_play_order(self) -> None:
        trick = (move(1, Suit.BASTONI, 5), move(0, Suit.BASTONI, 6))
        assert BriscolaRules().trick_winner(trick, TRUMP) == SeatIndex(0)


class TestInvalidTrick:
    @pytest.mark.parametrize("played", [0, 1, 3])
    def test_rejects_a_trick_without_two_moves(self, played: int) -> None:
        seats = (0, 1, 0)[:played]
        trick = tuple(move(seat, Suit.COPPE, 4 + seat) for seat in seats)
        with pytest.raises(ValueError):
            BriscolaRules().trick_winner(trick, TRUMP)

    def test_rejects_a_trick_where_a_seat_plays_twice(self) -> None:
        trick = (move(0, Suit.COPPE, 4), move(0, Suit.COPPE, 5))
        with pytest.raises(ValueError):
            BriscolaRules().trick_winner(trick, TRUMP)

    def test_rejects_a_trick_without_a_trump_suit(self) -> None:
        trick = (move(0, Suit.COPPE, 4), move(1, Suit.COPPE, 5))
        with pytest.raises(ValueError):
            BriscolaRules().trick_winner(trick)
