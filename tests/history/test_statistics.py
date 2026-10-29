"""Tests for StatisticsService counting matches per game type (FR-33)."""

from datetime import UTC, datetime
from fractions import Fraction

from italian_card_games.engine.values import Outcome, SeatIndex
from italian_card_games.history.records import (
    MatchId,
    MatchRecord,
    ParticipantRecord,
    RoundRecord,
)
from italian_card_games.history.statistics import GameStats, StatisticsService

FINISHED_AT = datetime(2026, 10, 29, 18, 30, tzinfo=UTC)


def a_record(game_type: str, *seats: tuple[str, bool, Outcome]) -> MatchRecord:
    """A one-round record whose seats are (name, is_bot, outcome) in seat order."""
    participants = tuple(
        ParticipantRecord(SeatIndex(seat), name, is_bot, outcome)
        for seat, (name, is_bot, outcome) in enumerate(seats)
    )
    scores = RoundRecord((Fraction(0),) * len(seats))
    return MatchRecord(MatchId("m"), game_type, FINISHED_AT, participants, (scores,))


def briscola(anna: Outcome, bot: Outcome) -> MatchRecord:
    return a_record("briscola", ("anna", False, anna), ("bot", True, bot))


def matazza(anna: Outcome) -> MatchRecord:
    others = Outcome.LOSS if anna is Outcome.WIN else Outcome.WIN
    return a_record(
        "matazza",
        ("bot-1", True, others),
        ("anna", False, anna),
        ("bot-2", True, Outcome.LOSS),
        ("bot-3", True, Outcome.LOSS),
    )


class TestStatistics:
    def test_fr33_no_records_give_no_stats(self) -> None:
        assert StatisticsService().stats_for("anna", []) == {}

    def test_fr33_wins_losses_and_draws_are_counted(self) -> None:
        records = [
            briscola(Outcome.WIN, Outcome.LOSS),
            briscola(Outcome.WIN, Outcome.LOSS),
            briscola(Outcome.LOSS, Outcome.WIN),
            briscola(Outcome.DRAW, Outcome.DRAW),
        ]
        stats = StatisticsService().stats_for("anna", records)
        assert stats == {"briscola": GameStats(played=4, wins=2, losses=1, draws=1)}

    def test_fr33_stats_are_split_per_game_type(self) -> None:
        records = [
            briscola(Outcome.WIN, Outcome.LOSS),
            matazza(Outcome.LOSS),
            matazza(Outcome.WIN),
            matazza(Outcome.LOSS),
        ]
        stats = StatisticsService().stats_for("anna", records)
        assert stats == {
            "briscola": GameStats(played=1, wins=1, losses=0, draws=0),
            "matazza": GameStats(played=3, wins=1, losses=2, draws=0),
        }

    def test_fr33_the_player_is_found_on_any_seat(self) -> None:
        stats = StatisticsService().stats_for("anna", [matazza(Outcome.WIN)])
        assert stats["matazza"].wins == 1

    def test_fr33_matches_of_other_players_are_ignored(self) -> None:
        other = a_record(
            "briscola", ("bruno", False, Outcome.WIN), ("bot", True, Outcome.LOSS)
        )
        stats = StatisticsService().stats_for("anna", [other])
        assert stats == {}

    def test_fr33_a_bot_with_the_same_name_is_not_the_player(self) -> None:
        record = a_record(
            "briscola", ("bruno", False, Outcome.LOSS), ("anna", True, Outcome.WIN)
        )
        assert StatisticsService().stats_for("anna", [record]) == {}

    def test_fr33_records_can_be_any_iterable(self) -> None:
        records = (briscola(Outcome.WIN, Outcome.LOSS) for _ in range(3))
        stats = StatisticsService().stats_for("anna", records)
        assert stats["briscola"].played == 3
