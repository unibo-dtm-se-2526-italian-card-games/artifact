"""Tests for Matazza end conditions and outcomes: the 12 and two-at-6 rules (FR-18, FR-19)."""

import pytest

from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.values import Outcome

WIN = Outcome.WIN
LOSS = Outcome.LOSS


def outcomes(*totals: int) -> tuple[Outcome, ...] | None:
    return MatazzaRules().outcomes(totals)


class TestGameContinues:
    def test_fr18_no_outcomes_at_the_start_of_a_game(self) -> None:
        assert outcomes(0, 0, 0, 0) is None

    def test_fr18_the_game_goes_on_below_12_with_one_player_at_6(self) -> None:
        assert outcomes(6, 3, 2, 0) is None

    def test_fr18_the_game_goes_on_with_one_player_at_11(self) -> None:
        assert outcomes(11, 0, 1, 0) is None

    def test_fr18_the_game_goes_on_with_two_players_at_5(self) -> None:
        assert outcomes(5, 5, 2, 0) is None


class TestTwelvePoints:
    def test_fr18_fr19_a_player_reaching_12_loses_alone(self) -> None:
        assert outcomes(2, 12, 0, 1) == (WIN, LOSS, WIN, WIN)

    def test_fr18_a_player_jumping_from_11_to_13_still_ends_the_game(self) -> None:
        assert outcomes(0, 0, 13, 1) == (WIN, WIN, LOSS, WIN)

    def test_fr19_the_first_seat_can_be_the_loser(self) -> None:
        assert outcomes(12, 1, 1, 0) == (LOSS, WIN, WIN, WIN)


class TestTwoAtSix:
    def test_fr18_fr19_two_players_at_6_both_lose(self) -> None:
        assert outcomes(6, 0, 6, 2) == (LOSS, WIN, LOSS, WIN)

    def test_fr18_the_two_players_can_reach_6_in_different_rounds(self) -> None:
        assert outcomes(6, 4, 0, 1) is None
        assert outcomes(6, 6, 0, 1) == (LOSS, LOSS, WIN, WIN)

    def test_fr18_totals_above_6_count_as_reached(self) -> None:
        assert outcomes(3, 7, 8, 0) == (WIN, LOSS, LOSS, WIN)

    def test_fr19_standing_points_do_not_decide_who_wins(self) -> None:
        assert outcomes(0, 6, 6, 5) == (WIN, LOSS, LOSS, WIN)


class TestInvalidInput:
    @pytest.mark.parametrize("size", [0, 3, 5])
    def test_fr18_a_wrong_number_of_totals_is_rejected(self, size: int) -> None:
        with pytest.raises(ValueError):
            MatazzaRules().outcomes((0,) * size)
