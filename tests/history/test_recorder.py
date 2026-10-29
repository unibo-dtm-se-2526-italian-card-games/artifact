"""Tests for MatchRecorder building a MatchRecord from Gameplay events (FR-31)."""

from datetime import UTC, datetime
from fractions import Fraction
from random import Random

import pytest

from italian_card_games.ai.rule_based import RuleBasedStrategy
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
from italian_card_games.engine.match import Match
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.ports import Game
from italian_card_games.engine.values import Move, Outcome, SeatIndex
from italian_card_games.history.recorder import MatchRecorder
from italian_card_games.history.records import (
    MatchId,
    Participant,
    ParticipantRecord,
    RoundRecord,
)

MAX_MOVES = 10_000
FINISHED_AT = datetime(2026, 10, 29, 18, 30, tzinfo=UTC)
FOUR_PLAYERS = (
    Participant("anna", is_bot=False),
    Participant("bot-1", is_bot=True),
    Participant("bot-2", is_bot=True),
    Participant("bot-3", is_bot=True),
)
FIRST_SCORES = (Fraction(4), Fraction(10, 3), Fraction(2), Fraction(4, 3))
SECOND_SCORES = (Fraction(1, 3), Fraction(5), Fraction(3), Fraction(7, 3))
OUTCOMES = (Outcome.WIN, Outcome.LOSS, Outcome.LOSS, Outcome.LOSS)


def a_recorder(participants: tuple[Participant, ...] = FOUR_PLAYERS) -> MatchRecorder:
    return MatchRecorder(MatchId("m-1"), "matazza", participants, lambda: FINISHED_AT)


def a_move() -> Move:
    return Move(SeatIndex(1), Card(Suit.COPPE, Rank(3)))


def play_with_bots(game: Game, seed: int) -> tuple[Match, list[DomainEvent]]:
    rng = Random(seed)
    match = Match(game, rng)
    bots = [RuleBasedStrategy(game, rng) for _ in range(game.player_count())]
    events: list[DomainEvent] = []
    for _ in range(MAX_MOVES):
        if match.is_over:
            return match, events
        seat = match.current_seat
        events.extend(match.play(bots[seat.value].choose_move(match.view_for(seat))))
    raise AssertionError("the game did not end")


class TestRecordingAMatch:
    def test_fr31_no_record_while_the_match_goes_on(self) -> None:
        events = [CardPlayed(a_move()), RoundScored(FIRST_SCORES)]
        assert a_recorder().record(events) is None

    def test_fr31_game_ended_builds_the_record(self) -> None:
        record = a_recorder().record(
            [RoundScored(FIRST_SCORES), RoundScored(SECOND_SCORES), GameEnded(OUTCOMES)]
        )
        assert record is not None
        assert record.id == MatchId("m-1")
        assert record.game_type == "matazza"
        assert record.finished_at == FINISHED_AT

    def test_fr31_each_seat_keeps_its_name_kind_and_outcome(self) -> None:
        record = a_recorder().record([RoundScored(FIRST_SCORES), GameEnded(OUTCOMES)])
        assert record is not None
        assert record.participants == (
            ParticipantRecord(SeatIndex(0), "anna", False, Outcome.WIN),
            ParticipantRecord(SeatIndex(1), "bot-1", True, Outcome.LOSS),
            ParticipantRecord(SeatIndex(2), "bot-2", True, Outcome.LOSS),
            ParticipantRecord(SeatIndex(3), "bot-3", True, Outcome.LOSS),
        )

    def test_fr31_round_scores_are_kept_in_play_order(self) -> None:
        record = a_recorder().record(
            [RoundScored(FIRST_SCORES), RoundScored(SECOND_SCORES), GameEnded(OUTCOMES)]
        )
        assert record is not None
        assert record.rounds == (RoundRecord(FIRST_SCORES), RoundRecord(SECOND_SCORES))

    def test_fr31_events_can_arrive_one_move_at_a_time(self) -> None:
        recorder = a_recorder()
        assert recorder.record([RoundScored(FIRST_SCORES)]) is None
        assert recorder.record([RoundScored(SECOND_SCORES)]) is None
        record = recorder.record([GameEnded(OUTCOMES)])
        assert record is not None
        assert len(record.rounds) == 2

    def test_fr31_other_events_are_ignored(self) -> None:
        trick = (a_move(),)
        record = a_recorder().record(
            [
                CardPlayed(a_move()),
                TrickWon(SeatIndex(1), trick),
                RoundScored(FIRST_SCORES),
                StandingPointsAwarded((1, 1, 0, 0), (1, 1, 0, 0)),
                GameEnded(OUTCOMES),
            ]
        )
        assert record is not None
        assert record.rounds == (RoundRecord(FIRST_SCORES),)

    def test_fr31_the_clock_gives_the_finishing_time(self) -> None:
        times = iter([FINISHED_AT])
        recorder = MatchRecorder(
            MatchId("m-1"), "matazza", FOUR_PLAYERS, lambda: next(times)
        )
        record = recorder.record([RoundScored(FIRST_SCORES), GameEnded(OUTCOMES)])
        assert record is not None
        assert record.finished_at == FINISHED_AT


class TestInvalidRecording:
    def test_fr31_events_after_the_end_are_rejected(self) -> None:
        recorder = a_recorder()
        recorder.record([RoundScored(FIRST_SCORES), GameEnded(OUTCOMES)])
        with pytest.raises(ValueError, match="over"):
            recorder.record([RoundScored(SECOND_SCORES)])

    def test_fr31_outcomes_must_match_the_participants(self) -> None:
        recorder = a_recorder(FOUR_PLAYERS[:2])
        with pytest.raises(ValueError):
            recorder.record([RoundScored(FIRST_SCORES), GameEnded(OUTCOMES)])

    def test_fr31_a_match_without_rounds_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="round"):
            a_recorder().record([GameEnded(OUTCOMES)])


class TestRecordingRealMatches:
    def test_fr31_matazza_records_every_round_and_the_outcomes(self) -> None:
        match, events = play_with_bots(MatazzaRules(), seed=7)
        record = a_recorder().record(events)
        assert record is not None
        scored = [e.scores for e in events if isinstance(e, RoundScored)]
        assert [r.scores for r in record.rounds] == scored
        assert tuple(p.outcome for p in record.participants) == match.outcomes

    def test_fr31_briscola_records_its_single_round(self) -> None:
        match, events = play_with_bots(BriscolaRules(), seed=7)
        players = (Participant("anna", is_bot=False), Participant("bot", is_bot=True))
        record = MatchRecorder(
            MatchId("m-2"), "briscola", players, lambda: FINISHED_AT
        ).record(events)
        assert record is not None
        assert record.game_type == "briscola"
        assert len(record.rounds) == 1
        assert tuple(p.outcome for p in record.participants) == match.outcomes
