from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from random import Random

from italian_card_games.engine.cards import Card
from italian_card_games.engine.events import DomainEvent
from italian_card_games.engine.match import Match
from italian_card_games.engine.ports import AIStrategy, Game
from italian_card_games.engine.values import Move, Outcome, PlayerView, SeatIndex
from italian_card_games.history.ports import MatchRepository
from italian_card_games.history.recorder import MatchRecorder
from italian_card_games.history.records import MatchId, Participant
from italian_card_games.play.ports import SessionStore
from italian_card_games.play.runner import MatchRunner
from italian_card_games.play.session import MatchSession

HUMAN_SEAT = SeatIndex(0)


class UnknownGameError(ValueError):
    """The game id is not in the catalog."""


class MatchNotFoundError(LookupError):
    """No offline match has this id."""


@dataclass(frozen=True, slots=True)
class MatchStatus:
    """FR-23, FR-36: a match as the human sees it, and what just happened in it.

    `events` are the events of the call that produced this status (the human's move
    and the bots' replies); a plain `status` call has none.
    """

    match_id: MatchId
    game_id: str
    view: PlayerView
    current_seat: SeatIndex
    outcomes: tuple[Outcome, ...] | None
    events: tuple[DomainEvent, ...] = ()


class OfflineMatchService:
    """FR-23, FR-36: runs offline matches for one human on seat 0 against bots.

    After every human move the bots reply until it is the human's turn again or the
    match ends. A finished match is saved once through the match repository. The
    game catalog, storage, bots, clock and ids are all injected.
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
        self, nickname: str, game_id: str, seed: int | None = None
    ) -> MatchStatus:
        """Create a match for this nickname; the bots play until the human's turn."""
        if game_id not in self._games:
            raise UnknownGameError(f"unknown game: {game_id}")
        game = self._games[game_id]()
        rng = Random(seed)
        match_id = self._new_match_id()
        bots = {
            SeatIndex(seat): self._bot_factory(game, rng)
            for seat in range(1, game.player_count())
        }
        participants = (Participant(nickname, False),) + tuple(
            Participant(f"Bot {seat.value}", True) for seat in bots
        )
        recorder = MatchRecorder(match_id, game_id, participants, self._clock)
        session = MatchSession(game_id, Match(game, rng), bots, recorder)
        self._sessions.add(match_id, session)
        return self._status(match_id, session, self._runner.bots_reply(session))

    def status(self, match_id: MatchId) -> MatchStatus:
        """The current state of a match, with no events."""
        return self._status(match_id, self._session(match_id), [])

    def play(self, match_id: MatchId, card: Card) -> MatchStatus:
        """Play a card for the human, then let the bots reply.

        An illegal card, or any card once the match is over, raises IllegalMoveError.
        """
        session = self._session(match_id)
        events = self._runner.apply(session, Move(HUMAN_SEAT, card))
        events += self._runner.bots_reply(session)
        return self._status(match_id, session, events)

    def _session(self, match_id: MatchId) -> MatchSession:
        session = self._sessions.get(match_id)
        if session is None:
            raise MatchNotFoundError(f"no match {match_id.value}")
        return session

    @staticmethod
    def _status(
        match_id: MatchId, session: MatchSession, events: list[DomainEvent]
    ) -> MatchStatus:
        match = session.match
        return MatchStatus(
            match_id,
            session.game_id,
            match.view_for(HUMAN_SEAT),
            match.current_seat,
            match.outcomes,
            tuple(events),
        )
