"""Tests for Matazza standing points: the numLow cases (FR-14, FR-15, FR-16, FR-17)."""

from fractions import Fraction

import pytest

from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.values import SeatIndex


def thirds(*amounts: int) -> tuple[Fraction, ...]:
    """Round scores written in thirds: thirds(3, 6) is (1, 2). A full round sums to 32."""
    return tuple(Fraction(amount, 3) for amount in amounts)


def points(scores: tuple[Fraction, ...], holder: int) -> tuple[int, ...]:
    return MatazzaRules().standing_points(scores, SeatIndex(holder))


class TestNoLowScores:
    def test_fr14_example_a_the_holder_and_the_top_scorer_take_one_point_each(
        self,
    ) -> None:
        scores = thirds(3, 6, 12, 11)  # P1=1.00, P2=2.00, P3=4.00, P4=3.67
        assert points(scores, holder=3) == (0, 0, 1, 1)

    def test_fr14_example_b_a_tie_for_the_top_gives_the_holder_both_points(
        self,
    ) -> None:
        scores = thirds(9, 9, 11, 3)  # P1=3.00, P2=3.00, P3=3.67, P4=1.00
        assert points(scores, holder=2) == (0, 0, 2, 0)

    def test_fr14_the_holder_is_excluded_even_with_the_highest_score(self) -> None:
        scores = thirds(6, 9, 5, 12)
        assert points(scores, holder=3) == (0, 1, 0, 1)

    def test_fr14_three_tied_non_holders_give_the_holder_both_points(self) -> None:
        scores = thirds(9, 9, 9, 5)
        assert points(scores, holder=3) == (0, 0, 0, 2)

    def test_fr14_a_tie_below_the_top_does_not_count(self) -> None:
        scores = thirds(12, 6, 6, 8)
        assert points(scores, holder=3) == (1, 0, 0, 1)

    def test_fr14_a_score_of_exactly_one_is_not_low(self) -> None:
        scores = thirds(3, 3, 3, 23)
        assert points(scores, holder=0) == (1, 0, 0, 1)


class TestOneLowScore:
    def test_fr15_a_low_holder_takes_both_points(self) -> None:
        scores = thirds(2, 10, 10, 10)
        assert points(scores, holder=0) == (2, 0, 0, 0)

    def test_fr15_a_low_non_holder_and_the_holder_take_one_point_each(self) -> None:
        scores = thirds(2, 10, 10, 10)
        assert points(scores, holder=2) == (1, 0, 1, 0)

    def test_fr15_a_score_just_under_one_is_low(self) -> None:
        scores = thirds(2, 3, 3, 24)
        assert points(scores, holder=1) == (1, 1, 0, 0)


class TestTwoLowScores:
    def test_fr16_example_c_the_two_low_players_take_one_point_each(self) -> None:
        scores = thirds(1, 2, 15, 14)  # P1=0.33, P2=0.67, P3=5.00, P4=4.67
        assert points(scores, holder=0) == (1, 1, 0, 0)

    def test_fr16_the_holder_is_irrelevant_when_not_among_the_low_players(self) -> None:
        scores = thirds(1, 2, 15, 14)
        assert points(scores, holder=3) == (1, 1, 0, 0)


class TestEveryRoundAwardsTwoPoints:
    @pytest.mark.parametrize(
        ("scores", "holder"),
        [
            (thirds(3, 6, 12, 11), 3),
            (thirds(9, 9, 11, 3), 2),
            (thirds(1, 2, 15, 14), 0),
            (thirds(2, 10, 10, 10), 0),
            (thirds(2, 10, 10, 10), 2),
            (thirds(9, 9, 9, 5), 3),
        ],
    )
    def test_fr14_to_fr16_the_points_of_a_round_sum_to_two(
        self, scores: tuple[Fraction, ...], holder: int
    ) -> None:
        assert sum(points(scores, holder)) == 2


class TestInvalidInput:
    def test_fr17_three_low_scores_raise_an_error(self) -> None:
        with pytest.raises(ValueError):
            points(thirds(2, 2, 2, 26), holder=0)

    def test_four_scores_are_required(self) -> None:
        with pytest.raises(ValueError):
            points(thirds(10, 10, 12), holder=0)

    def test_the_holder_must_be_one_of_the_four_seats(self) -> None:
        with pytest.raises(ValueError):
            points(thirds(3, 6, 12, 11), holder=4)
