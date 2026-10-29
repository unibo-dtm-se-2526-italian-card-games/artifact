"""Contract tests every MatchRepository adapter must pass (FR-31, FR-32, FR-33).

Subclass MatchRepositoryContract in a `test_*.py` file and override the
`repository` fixture with an empty repository of the adapter under test.
"""

from datetime import UTC, datetime, timedelta
from fractions import Fraction

import pytest

from italian_card_games.engine.values import Outcome, SeatIndex
from italian_card_games.history.ports import MatchRepository
from italian_card_games.history.records import (
    MatchId,
    MatchRecord,
    ParticipantRecord,
    RoundRecord,
)
from italian_card_games.history.statistics import StatisticsService

START = datetime(2026, 10, 29, 18, 0, tzinfo=UTC)


def briscola(
    match_id: str, minutes: int, anna: Outcome = Outcome.WIN, name: str = "anna"
) -> MatchRecord:
    """A finished Briscola match: `name` (human) on seat 0 against a bot."""
    bot = {Outcome.WIN: Outcome.LOSS, Outcome.LOSS: Outcome.WIN}.get(anna, anna)
    return MatchRecord(
        MatchId(match_id),
        "briscola",
        START + timedelta(minutes=minutes),
        (
            ParticipantRecord(SeatIndex(0), name, False, anna),
            ParticipantRecord(SeatIndex(1), "bot", True, bot),
        ),
        (RoundRecord((Fraction(70), Fraction(50))),),
    )


def matazza(match_id: str, minutes: int) -> MatchRecord:
    """A finished two-round Matazza match: anna (human) on seat 2, with exact thirds."""
    return MatchRecord(
        MatchId(match_id),
        "matazza",
        START + timedelta(minutes=minutes),
        (
            ParticipantRecord(SeatIndex(0), "bot-1", True, Outcome.LOSS),
            ParticipantRecord(SeatIndex(1), "bot-2", True, Outcome.LOSS),
            ParticipantRecord(SeatIndex(2), "anna", False, Outcome.WIN),
            ParticipantRecord(SeatIndex(3), "bot-3", True, Outcome.LOSS),
        ),
        (
            RoundRecord((Fraction(4), Fraction(10, 3), Fraction(2), Fraction(4, 3))),
            RoundRecord((Fraction(1, 3), Fraction(5), Fraction(3), Fraction(7, 3))),
        ),
    )


class MatchRepositoryContract:
    @pytest.fixture
    def repository(self) -> MatchRepository:
        raise NotImplementedError("override with the adapter under test")

    def test_fr31_the_adapter_satisfies_the_port(
        self, repository: MatchRepository
    ) -> None:
        assert isinstance(repository, MatchRepository)

    def test_fr31_an_unknown_match_is_none(self, repository: MatchRepository) -> None:
        assert repository.get(MatchId("missing")) is None

    def test_fr31_a_saved_match_reads_back_equal(
        self, repository: MatchRepository
    ) -> None:
        record = matazza("m-1", 0)
        repository.save(record)
        assert repository.get(MatchId("m-1")) == record

    def test_fr31_a_draw_reads_back(self, repository: MatchRepository) -> None:
        record = briscola("m-1", 0, Outcome.DRAW)
        repository.save(record)
        assert repository.get(MatchId("m-1")) == record

    def test_fr31_a_match_id_is_saved_once(self, repository: MatchRepository) -> None:
        repository.save(briscola("m-1", 0))
        with pytest.raises(ValueError, match="m-1"):
            repository.save(briscola("m-1", 5))

    def test_fr32_history_lists_the_player_matches_oldest_first(
        self, repository: MatchRepository
    ) -> None:
        later, first, middle = briscola("b", 20), matazza("a", 0), briscola("c", 10)
        for record in (later, first, middle):
            repository.save(record)
        assert repository.history_of("anna") == [first, middle, later]

    def test_fr32_history_keeps_the_round_by_round_scores(
        self, repository: MatchRepository
    ) -> None:
        repository.save(matazza("m-1", 0))
        (record,) = repository.history_of("anna")
        assert [r.scores for r in record.rounds] == [
            (Fraction(4), Fraction(10, 3), Fraction(2), Fraction(4, 3)),
            (Fraction(1, 3), Fraction(5), Fraction(3), Fraction(7, 3)),
        ]

    def test_fr32_history_leaves_out_other_players(
        self, repository: MatchRepository
    ) -> None:
        repository.save(briscola("m-1", 0, name="bruno"))
        assert repository.history_of("anna") == []

    def test_fr32_history_leaves_out_a_bot_with_the_same_name(
        self, repository: MatchRepository
    ) -> None:
        repository.save(briscola("m-1", 0))
        assert repository.history_of("bot") == []

    def test_fr33_stats_match_the_stored_history(
        self, repository: MatchRepository
    ) -> None:
        repository.save(briscola("m-1", 0, Outcome.WIN))
        repository.save(briscola("m-2", 1, Outcome.LOSS))
        repository.save(briscola("m-3", 2, Outcome.DRAW))
        repository.save(matazza("m-4", 3))
        stats = StatisticsService().stats_for("anna", repository.history_of("anna"))
        assert stats["briscola"].played == 3
        assert stats["briscola"].draws == 1
        assert stats["matazza"].wins == 1
