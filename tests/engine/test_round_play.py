"""Tests for playing a card in a round: validation and trick resolution (FR-05, FR-10)."""

from copy import deepcopy

import pytest

from italian_card_games.engine.cards import Card, Rank, Suit
from italian_card_games.engine.match import IllegalMoveError, Round
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.values import Move, SeatIndex


def card(suit: Suit, rank: int) -> Card:
    return Card(suit, Rank(rank))


def move(seat: int, suit: Suit, rank: int) -> Move:
    return Move(SeatIndex(seat), card(suit, rank))


def make_round(*hands: tuple[Card, ...], leader: int = 0) -> Round:
    """A round with hand-picked hands, nothing played and nothing won yet."""
    return Round(
        hands=hands,
        dealer=SeatIndex((leader - 1) % len(hands)),
        leader=SeatIndex(leader),
        trick=(),
        won=((),) * len(hands),
    )


def one_card_each(leader: int = 0) -> Round:
    """Seat 0 to 3 hold 1, 3, 2 and 4 of denari, so seat 1 wins a trick led by 0."""
    return make_round(
        (card(Suit.DENARI, 1), card(Suit.COPPE, 5)),
        (card(Suit.DENARI, 3),),
        (card(Suit.DENARI, 2),),
        (card(Suit.DENARI, 4),),
        leader=leader,
    )


class TestPlayCard:
    def test_fr05_a_played_card_leaves_the_hand_and_joins_the_trick(self) -> None:
        round_ = one_card_each()
        played = move(0, Suit.DENARI, 1)
        round_.play(played, MatazzaRules())
        assert round_.hands[0] == (card(Suit.COPPE, 5),)
        assert round_.trick == (played,)

    def test_fr05_the_turn_passes_to_the_next_seat(self) -> None:
        round_ = one_card_each()
        assert round_.current_seat == SeatIndex(0)
        round_.play(move(0, Suit.DENARI, 1), MatazzaRules())
        assert round_.current_seat == SeatIndex(1)

    def test_fr05_the_turn_wraps_around_the_table(self) -> None:
        round_ = one_card_each(leader=3)
        assert round_.current_seat == SeatIndex(3)
        round_.play(move(3, Suit.DENARI, 4), MatazzaRules())
        assert round_.current_seat == SeatIndex(0)


class TestRejectedMoves:
    def test_fr05_a_seat_playing_out_of_turn_is_rejected(self) -> None:
        round_ = one_card_each()
        before = deepcopy(round_)
        with pytest.raises(IllegalMoveError):
            round_.play(move(1, Suit.DENARI, 3), MatazzaRules())
        assert round_ == before

    def test_fr05_a_card_not_in_the_hand_is_rejected(self) -> None:
        round_ = one_card_each()
        before = deepcopy(round_)
        with pytest.raises(IllegalMoveError):
            round_.play(move(0, Suit.BASTONI, 7), MatazzaRules())
        assert round_ == before

    def test_fr09_not_following_the_led_suit_is_rejected(self) -> None:
        round_ = make_round(
            (card(Suit.DENARI, 1),),
            (card(Suit.DENARI, 3), card(Suit.COPPE, 9)),
            (card(Suit.DENARI, 2),),
            (card(Suit.DENARI, 4),),
        )
        round_.play(move(0, Suit.DENARI, 1), MatazzaRules())
        before = deepcopy(round_)
        with pytest.raises(IllegalMoveError):
            round_.play(move(1, Suit.COPPE, 9), MatazzaRules())
        assert round_ == before

    def test_fr09_a_seat_without_the_led_suit_may_discard_any_card(self) -> None:
        round_ = make_round(
            (card(Suit.DENARI, 1),),
            (card(Suit.COPPE, 9),),
            (card(Suit.DENARI, 2),),
            (card(Suit.DENARI, 4),),
        )
        round_.play(move(0, Suit.DENARI, 1), MatazzaRules())
        round_.play(move(1, Suit.COPPE, 9), MatazzaRules())
        assert round_.current_seat == SeatIndex(2)


class TestTrickResolution:
    def play_trick(self, round_: Round) -> None:
        rules = MatazzaRules()
        round_.play(move(0, Suit.DENARI, 1), rules)
        round_.play(move(1, Suit.DENARI, 3), rules)
        round_.play(move(2, Suit.DENARI, 2), rules)
        round_.play(move(3, Suit.DENARI, 4), rules)

    def test_fr10_the_winner_collects_the_four_cards(self) -> None:
        round_ = one_card_each()
        self.play_trick(round_)
        assert set(round_.won[1]) == {
            card(Suit.DENARI, 1),
            card(Suit.DENARI, 3),
            card(Suit.DENARI, 2),
            card(Suit.DENARI, 4),
        }
        assert round_.won[0] == round_.won[2] == round_.won[3] == ()

    def test_fr10_the_winner_leads_the_next_trick_and_the_trick_is_cleared(
        self,
    ) -> None:
        round_ = one_card_each()
        self.play_trick(round_)
        assert round_.trick == ()
        assert round_.leader == SeatIndex(1)
        assert round_.current_seat == SeatIndex(1)

    def test_fr10_an_off_suit_card_never_wins_the_trick(self) -> None:
        rules = MatazzaRules()
        round_ = make_round(
            (card(Suit.DENARI, 1),),
            (card(Suit.COPPE, 3),),
            (card(Suit.DENARI, 4),),
            (card(Suit.DENARI, 5),),
        )
        for seat, played in enumerate(
            [(Suit.DENARI, 1), (Suit.COPPE, 3), (Suit.DENARI, 4), (Suit.DENARI, 5)]
        ):
            round_.play(move(seat, *played), rules)
        assert round_.leader == SeatIndex(0)
        assert len(round_.won[0]) == 4
