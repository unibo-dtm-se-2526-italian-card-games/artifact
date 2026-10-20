"""Tests for whole seeded games played to the end (FR-04, FR-12, FR-19, NFR-04)."""

from fractions import Fraction
from random import Random

import pytest

from italian_card_games.engine.events import (
    DomainEvent,
    GameEnded,
    RoundScored,
    StandingPointsAwarded,
)
from italian_card_games.engine.match import Match
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.ports import AIStrategy
from italian_card_games.engine.values import Move, PlayerView

MAX_MOVES = 10_000
FULL_ROUND_SCORE = Fraction(32, 3)


class FirstLegalMoveBot:
    def choose_move(self, view: PlayerView) -> Move:
        return MatazzaRules().legal_moves(view)[0]


class LastLegalMoveBot:
    def choose_move(self, view: PlayerView) -> Move:
        return MatazzaRules().legal_moves(view)[-1]


class RandomBot:
    def __init__(self, seed: int) -> None:
        self._rng = Random(seed)

    def choose_move(self, view: PlayerView) -> Move:
        return self._rng.choice(MatazzaRules().legal_moves(view))


def play_game(
    strategies: list[AIStrategy], seed: int
) -> tuple[Match, list[DomainEvent]]:
    """Ask each seat's strategy for a move, through one loop, until the match ends."""
    match = Match(MatazzaRules(), Random(seed))
    events: list[DomainEvent] = []
    for _ in range(MAX_MOVES):
        if match.is_over:
            return match, events
        seat = match.current_seat
        move = strategies[seat.value].choose_move(match.view_for(seat))
        events.extend(match.play(move))
    raise AssertionError("the game did not end")


def random_bots(seed: int) -> list[AIStrategy]:
    return [RandomBot(seed * 4 + seat) for seat in range(4)]


class TestFullGame:
    def test_fr04_a_game_of_four_bots_runs_to_the_end(self) -> None:
        match, _ = play_game(random_bots(1), seed=1)
        assert match.is_over

    def test_fr04_strategies_of_different_kinds_play_the_same_game(self) -> None:
        mixed: list[AIStrategy] = [
            FirstLegalMoveBot(),
            LastLegalMoveBot(),
            RandomBot(3),
            FirstLegalMoveBot(),
        ]
        match, _ = play_game(mixed, seed=2)
        assert match.is_over

    @pytest.mark.parametrize("seed", range(20))
    def test_fr19_every_seat_ends_with_one_outcome(self, seed: int) -> None:
        match, events = play_game(random_bots(seed), seed=seed)
        assert match.outcomes is not None
        assert len(match.outcomes) == 4
        assert isinstance(events[-1], GameEnded)
        assert events[-1].outcomes == match.outcomes

    @pytest.mark.parametrize("seed", range(20))
    def test_fr19_the_game_ends_exactly_once(self, seed: int) -> None:
        _, events = play_game(random_bots(seed), seed=seed)
        assert sum(isinstance(event, GameEnded) for event in events) == 1


class TestInvariants:
    @pytest.mark.parametrize("seed", range(20))
    def test_fr12_the_scores_of_every_round_sum_to_the_whole_deck(
        self, seed: int
    ) -> None:
        _, events = play_game(random_bots(seed), seed=seed)
        scored = [event for event in events if isinstance(event, RoundScored)]
        assert scored
        assert all(sum(event.scores) == FULL_ROUND_SCORE for event in scored)

    @pytest.mark.parametrize("seed", range(20))
    def test_fr14_every_round_without_a_solo_win_awards_two_points(
        self, seed: int
    ) -> None:
        match, events = play_game(random_bots(seed), seed=seed)
        awarded = [e for e in events if isinstance(e, StandingPointsAwarded)]
        assert all(sum(event.points) == 2 for event in awarded)
        assert sum(match.standing_totals) == 2 * len(awarded)

    @pytest.mark.parametrize("seed", range(20))
    def test_fr18_the_outcomes_follow_from_the_final_totals(self, seed: int) -> None:
        match, events = play_game(random_bots(seed), seed=seed)
        solo_win = not isinstance(events[-2], StandingPointsAwarded)
        if not solo_win:
            assert MatazzaRules().outcomes(match.standing_totals) == match.outcomes


class TestReproducibility:
    @pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
    def test_nfr04_the_same_seed_and_moves_give_the_same_game(self, seed: int) -> None:
        first_match, first_events = play_game(random_bots(seed), seed=seed)
        second_match, second_events = play_game(random_bots(seed), seed=seed)
        assert first_events == second_events
        assert first_match.outcomes == second_match.outcomes
        assert first_match.standing_totals == second_match.standing_totals

    def test_nfr04_a_different_seed_gives_a_different_game(self) -> None:
        _, first = play_game(random_bots(1), seed=1)
        _, second = play_game(random_bots(2), seed=2)
        assert first != second
