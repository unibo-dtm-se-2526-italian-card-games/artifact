"""Tests for the end of a round and for player views (FR-06, FR-12)."""

from fractions import Fraction
from random import Random

import pytest

from italian_card_games.engine.cards import DeckFactory
from italian_card_games.engine.match import IllegalMoveError, Round
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.values import Move, SeatIndex

RULES = MatazzaRules()


def dealt(seed: int = 0, dealer: int = 0) -> Round:
    deck = DeckFactory.shuffled(Random(seed))
    return Round.deal(deck, SeatIndex(dealer), RULES.player_count())


def play_one_card(round_: Round) -> None:
    """The current seat plays the first legal card in its hand."""
    view = round_.view_for(round_.current_seat)
    round_.play(RULES.legal_moves(view)[0], RULES)


def play_out(round_: Round) -> None:
    while not round_.is_over:
        play_one_card(round_)


class TestRoundEnd:
    def test_fr12_a_freshly_dealt_round_is_not_over(self) -> None:
        assert not dealt().is_over

    def test_fr12_the_round_is_not_over_after_nine_tricks(self) -> None:
        round_ = dealt()
        for _ in range(9 * 4):
            play_one_card(round_)
        assert not round_.is_over

    @pytest.mark.parametrize("seed", range(5))
    def test_fr12_the_round_ends_after_ten_tricks_with_all_cards_won(
        self, seed: int
    ) -> None:
        round_ = dealt(seed)
        play_out(round_)
        assert round_.is_over
        assert round_.trick == ()
        assert sum(len(pile) for pile in round_.won) == 40
        assert all(len(pile) % 4 == 0 for pile in round_.won)

    @pytest.mark.parametrize("seed", range(5))
    def test_fr12_the_four_scores_of_a_round_sum_to_32_thirds(self, seed: int) -> None:
        round_ = dealt(seed)
        play_out(round_)
        assert sum(round_.scores(RULES), Fraction(0)) == Fraction(32, 3)

    def test_fr12_scores_are_read_from_the_cards_each_seat_won(self) -> None:
        round_ = dealt()
        play_out(round_)
        assert round_.scores(RULES) == RULES.round_scores(round_.won)

    def test_fr12_scores_before_the_round_is_over_are_rejected(self) -> None:
        round_ = dealt()
        play_one_card(round_)
        with pytest.raises(ValueError):
            round_.scores(RULES)

    def test_fr05_no_card_can_be_played_once_the_round_is_over(self) -> None:
        round_ = dealt()
        play_out(round_)
        move = Move(round_.current_seat, DeckFactory.ordered().cards[0])
        with pytest.raises(IllegalMoveError):
            round_.play(move, RULES)


class TestPlayerView:
    def test_fr06_a_view_holds_the_hand_of_its_own_seat(self) -> None:
        round_ = dealt()
        for seat in range(4):
            view = round_.view_for(SeatIndex(seat))
            assert view.seat == SeatIndex(seat)
            assert view.hand == round_.hands[seat]

    def test_fr06_a_view_never_contains_the_cards_of_another_seat(self) -> None:
        round_ = dealt()
        view = round_.view_for(SeatIndex(2))
        others = {c for seat in (0, 1, 3) for c in round_.hands[seat]}
        assert not others & set(view.hand)

    def test_fr06_a_view_shows_the_moves_already_on_the_table(self) -> None:
        round_ = dealt()
        first = RULES.legal_moves(round_.view_for(round_.current_seat))[0]
        round_.play(first, RULES)
        view = round_.view_for(SeatIndex(3))
        assert view.trick == (first,)

    def test_fr06_a_view_follows_the_hand_as_cards_are_played(self) -> None:
        round_ = dealt()
        seat = round_.current_seat
        played = RULES.legal_moves(round_.view_for(seat))[0]
        round_.play(played, RULES)
        assert played.card not in round_.view_for(seat).hand
        assert len(round_.view_for(seat).hand) == 9

    def test_fr06_a_seat_outside_the_table_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            dealt().view_for(SeatIndex(4))
