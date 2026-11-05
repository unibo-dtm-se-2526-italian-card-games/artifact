from datetime import UTC, datetime
from itertools import count
from random import Random

import pytest

from italian_card_games.ai.rule_based import RuleBasedStrategy
from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.cards import Card, DeckFactory
from italian_card_games.engine.events import CardPlayed
from italian_card_games.engine.match import IllegalMoveError
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.values import Outcome, SeatIndex
from italian_card_games.history.records import MatchId
from italian_card_games.persistence.in_memory import (
    InMemoryMatchRepository,
    InMemorySessionStore,
)
from italian_card_games.play.service import (
    MatchNotFoundError,
    MatchStatus,
    OfflineMatchService,
    UnknownGameError,
)

HUMAN = SeatIndex(0)
NOW = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)
GAMES = {"matazza": MatazzaRules, "briscola": BriscolaRules}


@pytest.fixture
def matches() -> InMemoryMatchRepository:
    return InMemoryMatchRepository()


@pytest.fixture
def service(matches: InMemoryMatchRepository) -> OfflineMatchService:
    """The service with fixed ids (m1, m2, ...), a fixed clock and the rule-based bot."""
    numbers = count(1)
    return OfflineMatchService(
        games=GAMES,
        matches=matches,
        sessions=InMemorySessionStore(),
        bot_factory=RuleBasedStrategy,
        clock=lambda: NOW,
        new_match_id=lambda: MatchId(f"m{next(numbers)}"),
    )


def first_legal_card(status: MatchStatus) -> Card:
    game = GAMES[status.game_id]()
    return game.legal_moves(status.view)[0].card


def play_to_the_end(service: OfflineMatchService, status: MatchStatus) -> MatchStatus:
    while status.outcomes is None:
        status = service.play(status.match_id, first_legal_card(status))
    return status


class TestStart:
    def test_gives_the_human_seat_0_view_and_the_generated_id(
        self, service: OfflineMatchService
    ) -> None:
        status = service.start("Davide", "matazza", seed=1)

        assert status.match_id == MatchId("m1")
        assert status.game_id == "matazza"
        assert status.view.seat == HUMAN
        assert len(status.view.hand) == 10
        assert status.current_seat == HUMAN
        assert status.outcomes is None

    def test_matazza_bots_lead_until_it_is_the_human_turn(
        self, service: OfflineMatchService
    ) -> None:
        status = service.start("Davide", "matazza", seed=1)

        assert [move.seat.value for move in status.view.trick] == [1, 2, 3]
        assert [type(event) for event in status.events] == [CardPlayed] * 3

    def test_briscola_has_one_bot_that_leads(
        self, service: OfflineMatchService
    ) -> None:
        status = service.start("Davide", "briscola", seed=1)

        assert [move.seat.value for move in status.view.trick] == [1]
        assert status.view.trump is not None

    def test_the_same_seed_gives_the_same_deal(
        self, service: OfflineMatchService
    ) -> None:
        first = service.start("Davide", "matazza", seed=7)
        second = service.start("Davide", "matazza", seed=7)

        assert first.match_id != second.match_id
        assert first.view == second.view

    def test_an_unknown_game_is_rejected(self, service: OfflineMatchService) -> None:
        with pytest.raises(UnknownGameError):
            service.start("Davide", "scopa", seed=1)


class TestStatus:
    def test_returns_the_current_view(self, service: OfflineMatchService) -> None:
        started = service.start("Davide", "matazza", seed=1)

        again = service.status(started.match_id)

        assert again.view == started.view
        assert again.current_seat == HUMAN
        assert again.events == ()

    def test_an_unknown_match_is_not_found(self, service: OfflineMatchService) -> None:
        with pytest.raises(MatchNotFoundError):
            service.status(MatchId("nope"))


class TestPlay:
    def test_plays_the_human_card_then_the_bots_reply(
        self, service: OfflineMatchService
    ) -> None:
        started = service.start("Davide", "matazza", seed=1)
        card = first_legal_card(started)

        status = service.play(started.match_id, card)

        first = status.events[0]
        assert isinstance(first, CardPlayed)
        assert first.move.seat == HUMAN
        assert first.move.card == card
        assert card not in status.view.hand
        assert status.current_seat == HUMAN
        assert len(status.view.hand) == 9

    def test_a_card_not_in_the_hand_is_illegal_and_changes_nothing(
        self, service: OfflineMatchService
    ) -> None:
        started = service.start("Davide", "matazza", seed=1)
        foreign = next(
            card
            for card in DeckFactory.shuffled(Random(0)).cards
            if card not in started.view.hand
        )

        with pytest.raises(IllegalMoveError):
            service.play(started.match_id, foreign)

        assert service.status(started.match_id).view == started.view

    def test_an_unknown_match_is_not_found(self, service: OfflineMatchService) -> None:
        started = service.start("Davide", "matazza", seed=1)

        with pytest.raises(MatchNotFoundError):
            service.play(MatchId("nope"), first_legal_card(started))


class TestEnd:
    @pytest.mark.parametrize("game_id", ["matazza", "briscola"])
    def test_a_finished_match_gives_one_outcome_per_seat(
        self, service: OfflineMatchService, game_id: str
    ) -> None:
        started = service.start("Davide", game_id, seed=3)

        final = play_to_the_end(service, started)

        assert final.outcomes is not None
        assert len(final.outcomes) == GAMES[game_id]().player_count()
        assert all(isinstance(outcome, Outcome) for outcome in final.outcomes)
        assert service.status(final.match_id).outcomes == final.outcomes

    def test_a_finished_match_is_recorded_once_with_the_nickname(
        self, service: OfflineMatchService, matches: InMemoryMatchRepository
    ) -> None:
        started = service.start("Davide", "briscola", seed=3)
        assert matches.get(started.match_id) is None

        final = play_to_the_end(service, started)

        record = matches.get(final.match_id)
        assert record is not None
        assert record.game_type == "briscola"
        assert record.finished_at == NOW
        assert [(p.name, p.is_bot) for p in record.participants] == [
            ("Davide", False),
            ("Bot 1", True),
        ]
        assert tuple(p.outcome for p in record.participants) == final.outcomes
        assert matches.history_of("Davide") == [record]

    def test_a_match_in_play_is_not_recorded(
        self, service: OfflineMatchService, matches: InMemoryMatchRepository
    ) -> None:
        started = service.start("Davide", "matazza", seed=3)

        service.play(started.match_id, first_legal_card(started))

        assert matches.history_of("Davide") == []

    def test_no_move_is_accepted_after_the_end(
        self, service: OfflineMatchService, matches: InMemoryMatchRepository
    ) -> None:
        final = play_to_the_end(service, service.start("Davide", "briscola", seed=3))

        with pytest.raises(IllegalMoveError):
            service.play(final.match_id, DeckFactory.shuffled(Random(0)).cards[0])

        assert len(matches.history_of("Davide")) == 1
