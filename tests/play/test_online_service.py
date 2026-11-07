"""Tests for OnlineMatchService: matches with several humans and bots (FR-27, FR-28)."""

from collections.abc import Callable
from datetime import UTC, datetime
from itertools import count

import pytest

from italian_card_games.ai.rule_based import RuleBasedStrategy
from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.cards import Card
from italian_card_games.engine.events import CardPlayed
from italian_card_games.engine.match import IllegalMoveError
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.ports import Game
from italian_card_games.engine.values import PlayerView, SeatIndex
from italian_card_games.history.records import MatchId
from italian_card_games.persistence.in_memory import (
    InMemoryMatchRepository,
    InMemorySessionStore,
)
from italian_card_games.play.online import OnlineMatchService
from italian_card_games.play.service import (
    MatchNotFoundError,
    MatchStatus,
    UnknownGameError,
)

NOW = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)
GAMES: dict[str, Callable[[], Game]] = {
    "matazza": MatazzaRules,
    "briscola": BriscolaRules,
}
ANNA = SeatIndex(0)
BRUNO = SeatIndex(1)
CARLA = SeatIndex(2)


@pytest.fixture
def matches() -> InMemoryMatchRepository:
    return InMemoryMatchRepository()


@pytest.fixture
def service(matches: InMemoryMatchRepository) -> OnlineMatchService:
    """The service with fixed ids (m1, m2, ...), a fixed clock and the rule-based bot."""
    numbers = count(1)
    return OnlineMatchService(
        games=GAMES,
        matches=matches,
        sessions=InMemorySessionStore(),
        bot_factory=RuleBasedStrategy,
        clock=lambda: NOW,
        new_match_id=lambda: MatchId(f"m{next(numbers)}"),
    )


def first_legal_card(game_id: str, view: PlayerView) -> Card:
    return GAMES[game_id]().legal_moves(view)[0].card


def play_to_the_end(
    service: OnlineMatchService, match_id: MatchId, game_id: str, seats: list[SeatIndex]
) -> MatchStatus:
    """Let whoever is to move play their first legal card, until the match ends."""
    status = service.status(match_id, seats[0])
    while status.outcomes is None:
        seat = status.current_seat
        view = service.status(match_id, seat).view
        status = service.play(match_id, seat, first_legal_card(game_id, view))
    return status


class TestStart:
    def test_fr28_returns_the_generated_match_id(
        self, service: OnlineMatchService
    ) -> None:
        assert service.start("matazza", {ANNA: "Anna"}, seed=1) == MatchId("m1")
        assert service.start("matazza", {ANNA: "Anna"}, seed=1) == MatchId("m2")

    def test_fr27_each_human_sees_their_own_hand(
        self, service: OnlineMatchService
    ) -> None:
        match_id = service.start("matazza", {ANNA: "Anna", BRUNO: "Bruno"}, seed=1)

        anna = service.status(match_id, ANNA)
        bruno = service.status(match_id, BRUNO)

        assert anna.view.seat == ANNA
        assert bruno.view.seat == BRUNO
        assert len(anna.view.hand) == 10
        assert set(anna.view.hand).isdisjoint(bruno.view.hand)

    def test_fr28_the_first_human_to_move_is_waited_for(
        self, service: OnlineMatchService
    ) -> None:
        # Seat 1 leads the first round of Matazza.
        match_id = service.start("matazza", {ANNA: "Anna", BRUNO: "Bruno"}, seed=1)

        assert service.status(match_id, ANNA).current_seat == BRUNO

    def test_fr28_bots_play_until_the_first_human_turn(
        self, service: OnlineMatchService
    ) -> None:
        # Seat 1 is a bot and leads; seat 2 is the first human to move.
        match_id = service.start("matazza", {ANNA: "Anna", CARLA: "Carla"}, seed=1)

        status = service.status(match_id, CARLA)

        assert status.current_seat == CARLA
        assert [move.seat.value for move in status.view.trick] == [1]

    def test_fr28_a_lone_human_plays_against_three_bots(
        self, service: OnlineMatchService
    ) -> None:
        match_id = service.start("matazza", {ANNA: "Anna"}, seed=1)

        status = service.status(match_id, ANNA)

        assert status.current_seat == ANNA
        assert [move.seat.value for move in status.view.trick] == [1, 2, 3]

    def test_fr27_the_same_seed_gives_the_same_deal(
        self, service: OnlineMatchService
    ) -> None:
        first = service.start("matazza", {ANNA: "Anna", BRUNO: "Bruno"}, seed=7)
        second = service.start("matazza", {ANNA: "Anna", BRUNO: "Bruno"}, seed=7)

        assert service.status(first, ANNA).view == service.status(second, ANNA).view

    def test_fr27_an_unknown_game_is_rejected(
        self, service: OnlineMatchService
    ) -> None:
        with pytest.raises(UnknownGameError):
            service.start("scopa", {ANNA: "Anna"}, seed=1)

    def test_fr28_a_match_needs_at_least_one_human(
        self, service: OnlineMatchService
    ) -> None:
        with pytest.raises(ValueError, match="human"):
            service.start("matazza", {}, seed=1)

    def test_fr27_a_seat_outside_the_table_is_rejected(
        self, service: OnlineMatchService
    ) -> None:
        with pytest.raises(ValueError, match="seat"):
            service.start("briscola", {SeatIndex(2): "Carla"}, seed=1)


class TestStatus:
    def test_fr27_an_unknown_match_is_not_found(
        self, service: OnlineMatchService
    ) -> None:
        with pytest.raises(MatchNotFoundError):
            service.status(MatchId("nope"), ANNA)

    def test_fr27_a_bot_seat_has_no_status(self, service: OnlineMatchService) -> None:
        match_id = service.start("matazza", {ANNA: "Anna"}, seed=1)

        with pytest.raises(ValueError, match="human"):
            service.status(match_id, SeatIndex(1))

    def test_fr27_a_plain_status_has_no_events(
        self, service: OnlineMatchService
    ) -> None:
        match_id = service.start("matazza", {ANNA: "Anna"}, seed=1)

        assert service.status(match_id, ANNA).events == ()


class TestPlay:
    def test_fr27_a_human_plays_and_the_bots_reply_until_the_next_human(
        self, service: OnlineMatchService
    ) -> None:
        match_id = service.start("matazza", {ANNA: "Anna", BRUNO: "Bruno"}, seed=1)
        view = service.status(match_id, BRUNO).view
        card = first_legal_card("matazza", view)

        status = service.play(match_id, BRUNO, card)

        first = status.events[0]
        assert isinstance(first, CardPlayed)
        assert first.move.seat == BRUNO
        assert first.move.card == card
        assert [type(event) for event in status.events[:3]] == [CardPlayed] * 3
        assert status.current_seat == ANNA
        assert status.view.seat == BRUNO
        assert card not in status.view.hand

    def test_fr27_the_other_human_then_plays_in_turn(
        self, service: OnlineMatchService
    ) -> None:
        match_id = service.start("matazza", {ANNA: "Anna", BRUNO: "Bruno"}, seed=1)
        bruno = service.status(match_id, BRUNO).view
        service.play(match_id, BRUNO, first_legal_card("matazza", bruno))
        anna = service.status(match_id, ANNA).view

        status = service.play(match_id, ANNA, first_legal_card("matazza", anna))

        assert status.view.seat == ANNA
        assert len(status.view.hand) == 9

    def test_fr27_moving_out_of_turn_is_rejected(
        self, service: OnlineMatchService
    ) -> None:
        match_id = service.start("matazza", {ANNA: "Anna", BRUNO: "Bruno"}, seed=1)
        anna = service.status(match_id, ANNA).view

        with pytest.raises(IllegalMoveError):
            service.play(match_id, ANNA, first_legal_card("matazza", anna))

    def test_fr27_a_card_not_in_hand_is_rejected(
        self, service: OnlineMatchService
    ) -> None:
        match_id = service.start("matazza", {ANNA: "Anna", BRUNO: "Bruno"}, seed=1)
        card = service.status(match_id, ANNA).view.hand[0]

        with pytest.raises(IllegalMoveError):
            service.play(match_id, BRUNO, card)

    def test_fr27_a_player_cannot_move_for_a_bot(
        self, service: OnlineMatchService
    ) -> None:
        match_id = service.start("matazza", {ANNA: "Anna"}, seed=1)
        card = service.status(match_id, ANNA).view.hand[0]

        with pytest.raises(ValueError, match="human"):
            service.play(match_id, SeatIndex(1), card)

    def test_fr27_an_unknown_match_is_not_found(
        self, service: OnlineMatchService
    ) -> None:
        card = service.status(
            service.start("matazza", {ANNA: "Anna"}, seed=1), ANNA
        ).view.hand[0]

        with pytest.raises(MatchNotFoundError):
            service.play(MatchId("nope"), ANNA, card)


class TestFinish:
    def test_fr27_four_humans_play_a_match_to_the_end(
        self, service: OnlineMatchService, matches: InMemoryMatchRepository
    ) -> None:
        seats = [SeatIndex(i) for i in range(4)]
        humans = {seat: f"Player{seat.value}" for seat in seats}
        match_id = service.start("matazza", humans, seed=2)

        status = play_to_the_end(service, match_id, "matazza", seats)

        assert status.outcomes is not None
        assert matches.get(match_id) is not None

    def test_fr28_a_lone_human_with_bots_is_recorded_with_bot_names(
        self, service: OnlineMatchService, matches: InMemoryMatchRepository
    ) -> None:
        match_id = service.start("matazza", {ANNA: "Anna"}, seed=3)

        play_to_the_end(service, match_id, "matazza", [ANNA])

        record = matches.get(match_id)
        assert record is not None
        assert [(p.name, p.is_bot) for p in record.participants] == [
            ("Anna", False),
            ("Bot 1", True),
            ("Bot 2", True),
            ("Bot 3", True),
        ]

    def test_fr27_two_humans_in_briscola_are_both_recorded(
        self, service: OnlineMatchService, matches: InMemoryMatchRepository
    ) -> None:
        match_id = service.start("briscola", {ANNA: "Anna", BRUNO: "Bruno"}, seed=4)

        play_to_the_end(service, match_id, "briscola", [ANNA, BRUNO])

        record = matches.get(match_id)
        assert record is not None
        assert record.game_type == "briscola"
        assert [(p.name, p.is_bot) for p in record.participants] == [
            ("Anna", False),
            ("Bruno", False),
        ]

    def test_fr27_a_finished_match_rejects_further_moves(
        self, service: OnlineMatchService
    ) -> None:
        match_id = service.start("briscola", {ANNA: "Anna", BRUNO: "Bruno"}, seed=4)
        card = service.status(match_id, ANNA).view.hand[0]
        play_to_the_end(service, match_id, "briscola", [ANNA, BRUNO])

        with pytest.raises(IllegalMoveError):
            service.play(match_id, ANNA, card)
