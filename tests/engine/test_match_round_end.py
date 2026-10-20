"""Tests for what a Match does when a round ends (FR-11, FR-13 to FR-19)."""

from fractions import Fraction
from random import Random

import pytest

from italian_card_games.engine.cards import Card, DeckFactory
from italian_card_games.engine.events import (
    CardPlayed,
    DomainEvent,
    GameEnded,
    RoundScored,
    StandingPointsAwarded,
    TrickWon,
)
from italian_card_games.engine.match import IllegalMoveError, Match
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.values import Move, Outcome, SeatIndex

CARDS_PER_ROUND = 40
HOLDER = SeatIndex(3)
WIN, LOSS = Outcome.WIN, Outcome.LOSS


def thirds(*amounts: int) -> tuple[Fraction, ...]:
    """Round scores written in thirds: thirds(3, 6) is (1, 2)."""
    return tuple(Fraction(amount, 3) for amount in amounts)


class ScriptedMatazza(MatazzaRules):
    """Matazza whose round scores are scripted and whose holder is always seat 3."""

    def __init__(self, *scripted: tuple[Fraction, ...]) -> None:
        self._scripted = list(scripted)

    def round_scores(self, won: tuple[tuple[Card, ...], ...]) -> tuple[Fraction, ...]:
        return self._scripted.pop(0)

    def round_holder(self, hands: tuple[tuple[Card, ...], ...]) -> SeatIndex | None:
        return HOLDER


def a_match(*scripted: tuple[Fraction, ...]) -> Match:
    return Match(ScriptedMatazza(*scripted), Random(1))


def first_legal_move(match: Match) -> Move:
    return MatazzaRules().legal_moves(match.view_for(match.current_seat))[0]


def play_rounds(match: Match, rounds: int = 1) -> list[DomainEvent]:
    """Play whole rounds and return the events of the very last move."""
    events: list[DomainEvent] = []
    for _ in range(rounds * CARDS_PER_ROUND):
        events = match.play(first_legal_move(match))
    return events


TWO_LOW_SCORES = thirds(1, 2, 15, 14)  # seats 0 and 1 are low, one point each
HOLDER_LOW_SCORES = thirds(10, 10, 10, 2)  # seat 3 is low and holds the cursed card


class TestStandingPoints:
    def test_fr14_the_last_card_reports_the_scores_and_the_points_awarded(self) -> None:
        scores = thirds(3, 6, 12, 11)
        match = a_match(scores)
        events = play_rounds(match)
        assert isinstance(events[0], CardPlayed)
        assert isinstance(events[1], TrickWon)
        assert events[2:] == [
            RoundScored(scores),
            StandingPointsAwarded((0, 0, 1, 1), (0, 0, 1, 1)),
        ]

    def test_fr14_the_points_accumulate_over_the_rounds(self) -> None:
        match = a_match(thirds(3, 6, 12, 11), thirds(3, 6, 12, 11))
        play_rounds(match, 2)
        assert match.standing_totals == (0, 0, 2, 2)

    def test_fr14_a_round_with_no_end_condition_leaves_the_match_going(self) -> None:
        match = a_match(thirds(3, 6, 12, 11))
        play_rounds(match)
        assert match.outcomes is None
        assert not match.is_over

    def test_fr13_a_score_of_exactly_one_blocks_the_solo_win(self) -> None:
        match = a_match(thirds(3, 1, 1, 27))
        events = play_rounds(match)
        assert isinstance(events[-1], StandingPointsAwarded)
        assert not match.is_over


class TestNextRound:
    def test_fr11_the_next_round_is_dealt_by_the_next_seat(self) -> None:
        match = a_match(thirds(3, 6, 12, 11))
        play_rounds(match)
        assert match.round.dealer == SeatIndex(1)
        assert match.current_seat == SeatIndex(2)

    def test_fr11_the_next_round_starts_with_full_hands_and_no_won_cards(self) -> None:
        match = a_match(thirds(3, 6, 12, 11))
        play_rounds(match)
        assert [len(hand) for hand in match.round.hands] == [10] * 4
        assert match.round.won == ((),) * 4
        assert match.round.trick == ()

    def test_fr11_the_dealer_comes_back_to_seat_zero_after_a_full_turn(self) -> None:
        match = a_match(*[TWO_LOW_SCORES] * 4)
        play_rounds(match, 4)
        assert match.round.dealer == SeatIndex(0)

    def test_nfr04_every_round_is_a_new_shuffle_of_the_whole_deck(self) -> None:
        match = a_match(thirds(3, 6, 12, 11))
        before = match.round.hands
        play_rounds(match)
        assert match.round.hands != before
        assert sum(len(hand) for hand in match.round.hands) == CARDS_PER_ROUND


class TestSoloWin:
    SCORES = thirds(31, 0, 1, 1)  # seat 0 wins the round, the others are below 1.0

    def test_fr13_a_solo_win_ends_the_match_without_standing_points(self) -> None:
        match = a_match(self.SCORES)
        events = play_rounds(match)
        assert events[2:] == [
            RoundScored(self.SCORES),
            GameEnded((WIN, LOSS, LOSS, LOSS)),
        ]
        assert match.standing_totals == (0, 0, 0, 0)

    def test_fr19_the_solo_winner_wins_and_the_others_lose(self) -> None:
        match = a_match(self.SCORES)
        play_rounds(match)
        assert match.outcomes == (WIN, LOSS, LOSS, LOSS)
        assert match.is_over

    def test_fr13_the_solo_win_is_checked_before_the_standing_points(self) -> None:
        # Three low scores would be an error in standing_points (FR-17).
        match = a_match(thirds(2, 2, 2, 26))
        play_rounds(match)
        assert match.outcomes == (LOSS, LOSS, LOSS, WIN)

    def test_a_card_cannot_be_played_once_the_match_is_over(self) -> None:
        match = a_match(self.SCORES)
        play_rounds(match)
        with pytest.raises(IllegalMoveError):
            match.play(Move(SeatIndex(0), DeckFactory.ordered().cards[0]))


class TestEndConditions:
    def test_fr18_twelve_standing_points_lose_alone(self) -> None:
        match = a_match(*[HOLDER_LOW_SCORES] * 6)
        events = play_rounds(match, 6)
        assert match.standing_totals == (0, 0, 0, 12)
        assert events[-2:] == [
            StandingPointsAwarded((0, 0, 0, 2), (0, 0, 0, 12)),
            GameEnded((WIN, WIN, WIN, LOSS)),
        ]

    def test_fr18_one_seat_at_six_does_not_end_the_match(self) -> None:
        match = a_match(*[HOLDER_LOW_SCORES] * 3)
        play_rounds(match, 3)
        assert match.standing_totals == (0, 0, 0, 6)
        assert not match.is_over

    def test_fr18_two_seats_at_six_both_lose(self) -> None:
        match = a_match(*[TWO_LOW_SCORES] * 6)
        events = play_rounds(match, 6)
        assert match.standing_totals == (6, 6, 0, 0)
        assert events[-1] == GameEnded((LOSS, LOSS, WIN, WIN))

    def test_fr19_the_outcomes_are_kept_once_the_match_is_over(self) -> None:
        match = a_match(*[TWO_LOW_SCORES] * 6)
        play_rounds(match, 6)
        assert match.outcomes == (LOSS, LOSS, WIN, WIN)
        assert match.is_over

    def test_fr18_the_match_stops_dealing_once_it_is_over(self) -> None:
        match = a_match(*[TWO_LOW_SCORES] * 6)
        play_rounds(match, 6)
        assert match.round.is_over
