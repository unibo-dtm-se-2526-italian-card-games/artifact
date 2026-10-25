"""Tests for Briscola scoring: card points and the result of the round (FR-20)."""

from fractions import Fraction

import pytest

from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.cards import Card, DeckFactory, Rank, Suit
from italian_card_games.engine.values import Outcome

# FR-20: points of each rank, the other ranks are worth nothing.
POINTS_BY_RANK = {1: 11, 3: 10, 10: 4, 9: 3, 8: 2, 2: 0, 4: 0, 5: 0, 6: 0, 7: 0}
WIN, LOSS, DRAW = Outcome.WIN, Outcome.LOSS, Outcome.DRAW


def card(suit: Suit, rank: int) -> Card:
    return Card(suit, Rank(rank))


class TestRoundScores:
    @pytest.mark.parametrize(("rank", "points"), POINTS_BY_RANK.items())
    def test_fr20_each_rank_is_worth_its_card_points(
        self, rank: int, points: int
    ) -> None:
        won = ((card(Suit.COPPE, rank),), ())
        assert BriscolaRules().round_scores(won) == (Fraction(points), Fraction(0))

    def test_fr20_a_score_is_the_sum_of_the_cards_a_seat_won(self) -> None:
        won = (
            (card(Suit.COPPE, 1), card(Suit.SPADE, 3), card(Suit.DENARI, 10)),
            (card(Suit.BASTONI, 9), card(Suit.BASTONI, 8)),
        )
        assert BriscolaRules().round_scores(won) == (Fraction(25), Fraction(5))

    def test_fr20_a_seat_that_won_nothing_scores_zero(self) -> None:
        assert BriscolaRules().round_scores(((), ())) == (Fraction(0), Fraction(0))

    def test_fr20_the_whole_deck_is_worth_120_points(self) -> None:
        cards = DeckFactory.ordered().cards
        scores = BriscolaRules().round_scores((cards[:20], cards[20:]))
        assert sum(scores) == 120

    def test_fr20_a_card_cannot_be_won_twice(self) -> None:
        won = ((card(Suit.COPPE, 1),), (card(Suit.COPPE, 1),))
        with pytest.raises(ValueError):
            BriscolaRules().round_scores(won)

    @pytest.mark.parametrize("piles", [0, 1, 3])
    def test_fr20_two_piles_are_required(self, piles: int) -> None:
        with pytest.raises(ValueError):
            BriscolaRules().round_scores(((),) * piles)


class TestRoundOutcomes:
    def test_fr20_61_points_win_the_match(self) -> None:
        scores = (Fraction(61), Fraction(59))
        assert BriscolaRules().round_outcomes(scores) == (WIN, LOSS)

    def test_fr20_the_second_seat_can_win(self) -> None:
        scores = (Fraction(40), Fraction(80))
        assert BriscolaRules().round_outcomes(scores) == (LOSS, WIN)

    def test_fr20_60_points_each_is_a_draw_for_both(self) -> None:
        scores = (Fraction(60), Fraction(60))
        assert BriscolaRules().round_outcomes(scores) == (DRAW, DRAW)

    def test_fr20_all_120_points_still_win(self) -> None:
        scores = (Fraction(0), Fraction(120))
        assert BriscolaRules().round_outcomes(scores) == (LOSS, WIN)

    @pytest.mark.parametrize("count", [0, 1, 3])
    def test_fr20_two_scores_are_required(self, count: int) -> None:
        with pytest.raises(ValueError):
            BriscolaRules().round_outcomes((Fraction(1),) * count)
