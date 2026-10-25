"""Tests for whole seeded Briscola matches played to the end (FR-01, FR-04, FR-19, FR-20)."""

from fractions import Fraction
from random import Random

import pytest

from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.cards import Card, Rank, Suit
from italian_card_games.engine.events import (
    CardPlayed,
    DomainEvent,
    GameEnded,
    RoundScored,
    StandingPointsAwarded,
    TrickWon,
)
from italian_card_games.engine.match import IllegalMoveError, Match
from italian_card_games.engine.ports import AIStrategy
from italian_card_games.engine.values import Move, Outcome, PlayerView

MAX_MOVES = 10_000
CARDS_IN_DECK = 40
TRICKS_IN_ROUND = 20
WHOLE_DECK_POINTS = Fraction(120)


class FirstLegalMoveBot:
    def choose_move(self, view: PlayerView) -> Move:
        return BriscolaRules().legal_moves(view)[0]


class LastLegalMoveBot:
    def choose_move(self, view: PlayerView) -> Move:
        return BriscolaRules().legal_moves(view)[-1]


class RandomBot:
    def __init__(self, seed: int) -> None:
        self._rng = Random(seed)

    def choose_move(self, view: PlayerView) -> Move:
        return self._rng.choice(BriscolaRules().legal_moves(view))


class ScriptedBriscola(BriscolaRules):
    """Briscola whose round scores are scripted, to reach a result by choice."""

    def __init__(self, scores: tuple[Fraction, ...]) -> None:
        self._scores = scores

    def round_scores(self, won: tuple[tuple[Card, ...], ...]) -> tuple[Fraction, ...]:
        return self._scores


def play_match(
    strategies: list[AIStrategy], seed: int, game: BriscolaRules | None = None
) -> tuple[Match, list[DomainEvent]]:
    """Ask each seat's strategy for a move, through one loop, until the match ends."""
    match = Match(game or BriscolaRules(), Random(seed))
    events: list[DomainEvent] = []
    for _ in range(MAX_MOVES):
        if match.is_over:
            return match, events
        seat = match.current_seat
        move = strategies[seat.value].choose_move(match.view_for(seat))
        events.extend(match.play(move))
    raise AssertionError("the match did not end")


def random_bots(seed: int) -> list[AIStrategy]:
    return [RandomBot(seed * 2 + seat) for seat in range(2)]


class TestFullMatch:
    def test_fr20_a_match_of_two_bots_runs_to_the_end(self) -> None:
        match, _ = play_match(random_bots(1), seed=1)
        assert match.is_over

    def test_fr20_strategies_of_different_kinds_play_the_same_match(self) -> None:
        mixed: list[AIStrategy] = [FirstLegalMoveBot(), LastLegalMoveBot()]
        match, _ = play_match(mixed, seed=2)
        assert match.is_over

    @pytest.mark.parametrize("seed", range(20))
    def test_fr20_one_round_of_forty_cards_and_twenty_tricks_is_the_whole_match(
        self, seed: int
    ) -> None:
        _, events = play_match(random_bots(seed), seed=seed)
        assert sum(isinstance(e, CardPlayed) for e in events) == CARDS_IN_DECK
        assert sum(isinstance(e, TrickWon) for e in events) == TRICKS_IN_ROUND
        assert sum(isinstance(e, RoundScored) for e in events) == 1

    @pytest.mark.parametrize("seed", range(20))
    def test_fr19_the_match_ends_exactly_once_without_standing_points(
        self, seed: int
    ) -> None:
        _, events = play_match(random_bots(seed), seed=seed)
        assert sum(isinstance(e, GameEnded) for e in events) == 1
        assert isinstance(events[-1], GameEnded)
        assert not any(isinstance(e, StandingPointsAwarded) for e in events)

    def test_fr20_a_move_after_the_match_is_over_is_rejected(self) -> None:
        match, _ = play_match(random_bots(1), seed=1)
        with pytest.raises(IllegalMoveError):
            match.play(Move(match.current_seat, Card(Suit.COPPE, Rank(1))))


class TestResult:
    @pytest.mark.parametrize("seed", range(20))
    def test_fr20_the_scores_of_the_round_add_up_to_120_points(self, seed: int) -> None:
        _, events = play_match(random_bots(seed), seed=seed)
        scored = [e for e in events if isinstance(e, RoundScored)]
        assert sum(scored[0].scores) == WHOLE_DECK_POINTS

    @pytest.mark.parametrize("seed", range(20))
    def test_fr19_the_outcomes_follow_from_the_scores(self, seed: int) -> None:
        match, events = play_match(random_bots(seed), seed=seed)
        scored = [e for e in events if isinstance(e, RoundScored)]
        assert match.outcomes == BriscolaRules().round_outcomes(scored[0].scores)

    @pytest.mark.parametrize("seed", range(20))
    def test_fr19_a_decisive_match_has_one_winner_and_one_loser(
        self, seed: int
    ) -> None:
        match, _ = play_match(random_bots(seed), seed=seed)
        assert match.outcomes in (
            (Outcome.WIN, Outcome.LOSS),
            (Outcome.LOSS, Outcome.WIN),
            (Outcome.DRAW, Outcome.DRAW),
        )

    def test_fr20_a_60_60_round_ends_the_match_in_a_draw(self) -> None:
        sixty = (Fraction(60), Fraction(60))
        match, events = play_match(random_bots(1), seed=1, game=ScriptedBriscola(sixty))
        assert match.outcomes == (Outcome.DRAW, Outcome.DRAW)
        assert events[-1] == GameEnded((Outcome.DRAW, Outcome.DRAW))

    def test_fr20_the_standing_totals_stay_at_zero(self) -> None:
        match, _ = play_match(random_bots(1), seed=1)
        assert match.standing_totals == (0, 0)


class TestReproducibility:
    @pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
    def test_nfr04_the_same_seed_and_moves_give_the_same_match(self, seed: int) -> None:
        first_match, first_events = play_match(random_bots(seed), seed=seed)
        second_match, second_events = play_match(random_bots(seed), seed=seed)
        assert first_events == second_events
        assert first_match.outcomes == second_match.outcomes

    def test_nfr04_a_different_seed_gives_a_different_match(self) -> None:
        _, first = play_match(random_bots(1), seed=1)
        _, second = play_match(random_bots(2), seed=2)
        assert first != second
