from collections.abc import Callable, Mapping
from datetime import datetime
from random import Random

from italian_card_games.engine.cards import Card
from italian_card_games.engine.events import DomainEvent
from italian_card_games.engine.match import Match
from italian_card_games.engine.ports import AIStrategy, Game
from italian_card_games.engine.values import Move, SeatIndex
from italian_card_games.history.ports import MatchRepository
from italian_card_games.history.recorder import MatchRecorder
from italian_card_games.history.records import MatchId, Participant
from italian_card_games.play.ports import SessionStore
from italian_card_games.play.runner import MatchRunner
from italian_card_games.play.service import (
    MatchNotFoundError,
    MatchStatus,
    UnknownGameError,
)
from italian_card_games.play.session import MatchSession


class OnlineMatchService:
    """FR-27, FR-28: runs matches with one or more humans, bots on the other seats.

    The caller says which seats are human and under what name; every other seat gets a
    bot named `Bot <seat>`. After a human's move the bots reply until it is a human's
    turn again or the match ends. Each human sees only their own seat's view. A
    finished match is saved once through the match repository. The game catalog,
    storage, bots, clock and ids are all injected.
    """

    def __init__(
        self,
        games: Mapping[str, Callable[[], Game]],
        matches: MatchRepository,
        sessions: SessionStore,
        bot_factory: Callable[[Game, Random], AIStrategy],
        clock: Callable[[], datetime],
        new_match_id: Callable[[], MatchId],
    ) -> None:
        self._games = games
        self._runner = MatchRunner(matches)
        self._sessions = sessions
        self._bot_factory = bot_factory
        self._clock = clock
        self._new_match_id = new_match_id

    def start(
        self,
        game_id: str,
        humans: Mapping[SeatIndex, str],
        seed: int | None = None,
    ) -> MatchId:
        """Create a match with these human seats; the bots play until a human's turn."""
        if game_id not in self._games:
            raise UnknownGameError(f"unknown game: {game_id}")
        game = self._games[game_id]()
        seat_count = game.player_count()
        if not humans:
            raise ValueError("a match needs at least one human")
        for seat in humans:
            if not 0 <= seat.value < seat_count:
                raise ValueError(f"seat {seat.value} is outside the table")
        rng = Random(seed)
        match_id = self._new_match_id()
        bots = {
            SeatIndex(i): self._bot_factory(game, rng)
            for i in range(seat_count)
            if SeatIndex(i) not in humans
        }
        participants = tuple(
            Participant(humans[SeatIndex(i)], False)
            if SeatIndex(i) in humans
            else Participant(f"Bot {i}", True)
            for i in range(seat_count)
        )
        recorder = MatchRecorder(match_id, game_id, participants, self._clock)
        session = MatchSession(game_id, Match(game, rng), bots, recorder)
        self._sessions.add(match_id, session)
        self._runner.bots_reply(session)
        return match_id

    def status(self, match_id: MatchId, seat: SeatIndex) -> MatchStatus:
        """The match as the human on this seat sees it, with no events."""
        session = self._session(match_id)
        self._ensure_human(session, seat)
        return self._status(match_id, session, seat, [])

    def play(self, match_id: MatchId, seat: SeatIndex, card: Card) -> MatchStatus:
        """Play a card for the human on this seat, then let the bots reply.

        A card out of turn or not allowed, or any card once the match is over, raises
        IllegalMoveError. A seat held by a bot raises ValueError.
        """
        session = self._session(match_id)
        self._ensure_human(session, seat)
        events = self._runner.apply(session, Move(seat, card))
        events += self._runner.bots_reply(session)
        return self._status(match_id, session, seat, events)

    def _session(self, match_id: MatchId) -> MatchSession:
        session = self._sessions.get(match_id)
        if session is None:
            raise MatchNotFoundError(f"no match {match_id.value}")
        return session

    def _ensure_human(self, session: MatchSession, seat: SeatIndex) -> None:
        seat_count = self._games[session.game_id]().player_count()
        if seat in session.bots or not 0 <= seat.value < seat_count:
            raise ValueError(f"seat {seat.value} is not a human seat")

    @staticmethod
    def _status(
        match_id: MatchId,
        session: MatchSession,
        seat: SeatIndex,
        events: list[DomainEvent],
    ) -> MatchStatus:
        match = session.match
        return MatchStatus(
            match_id,
            session.game_id,
            match.view_for(seat),
            match.current_seat,
            match.outcomes,
            tuple(events),
        )
