"""Tests for the invariants of MatchRecord (FR-31)."""

from datetime import UTC, datetime, timedelta, timezone
from fractions import Fraction

import pytest

from italian_card_games.engine.values import Outcome, SeatIndex
from italian_card_games.history.records import (
    MatchId,
    MatchRecord,
    ParticipantRecord,
    RoundRecord,
)

FINISHED_AT = datetime(2026, 10, 29, 18, 30, tzinfo=UTC)
ANNA = ParticipantRecord(SeatIndex(0), "anna", False, Outcome.WIN)
BOT = ParticipantRecord(SeatIndex(1), "bot", True, Outcome.LOSS)
A_ROUND = RoundRecord((Fraction(70), Fraction(50)))


def a_record(
    participants: tuple[ParticipantRecord, ...] = (ANNA, BOT),
    rounds: tuple[RoundRecord, ...] = (A_ROUND,),
    finished_at: datetime = FINISHED_AT,
) -> MatchRecord:
    return MatchRecord(MatchId("m-1"), "briscola", finished_at, participants, rounds)


class TestMatchRecord:
    def test_fr31_a_valid_record_keeps_its_fields(self) -> None:
        record = a_record()
        assert record.participants == (ANNA, BOT)
        assert record.rounds == (A_ROUND,)

    def test_fr31_a_record_is_immutable(self) -> None:
        record = a_record()
        with pytest.raises(AttributeError):
            record.game_type = "matazza"  # type: ignore[misc]

    def test_fr31_a_record_needs_a_round(self) -> None:
        with pytest.raises(ValueError, match="round"):
            a_record(rounds=())

    def test_fr31_participants_must_be_in_seat_order(self) -> None:
        with pytest.raises(ValueError, match="seats"):
            a_record(participants=(BOT, ANNA))

    def test_fr31_participants_cannot_skip_a_seat(self) -> None:
        third = ParticipantRecord(SeatIndex(2), "bot", True, Outcome.LOSS)
        with pytest.raises(ValueError, match="seats"):
            a_record(participants=(ANNA, third))

    def test_fr31_each_round_has_one_score_per_participant(self) -> None:
        short_round = RoundRecord((Fraction(120),))
        with pytest.raises(ValueError, match="score"):
            a_record(rounds=(A_ROUND, short_round))

    def test_fr31_the_finishing_time_needs_a_time_zone(self) -> None:
        with pytest.raises(ValueError, match="time zone"):
            a_record(finished_at=datetime(2026, 10, 29, 18, 30))

    def test_fr31_any_time_zone_is_accepted(self) -> None:
        rome = timezone(timedelta(hours=1))
        record = a_record(finished_at=datetime(2026, 10, 29, 19, 30, tzinfo=rome))
        assert record.finished_at == FINISHED_AT
