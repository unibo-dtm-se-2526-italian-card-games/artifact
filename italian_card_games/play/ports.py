from typing import Protocol, runtime_checkable

from italian_card_games.history.records import MatchId
from italian_card_games.play.session import MatchSession


@runtime_checkable
class SessionStore(Protocol):
    """Keeps the offline matches in play, by id. An in-memory adapter provides one."""

    def add(self, match_id: MatchId, session: MatchSession) -> None:
        """FR-23: keep a new session. An id already in use raises ValueError."""
        ...

    def get(self, match_id: MatchId) -> MatchSession | None:
        """FR-23: the session with this id, or None if there is none."""
        ...
