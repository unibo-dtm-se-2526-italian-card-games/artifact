from typing import Protocol, runtime_checkable

from italian_card_games.history.records import MatchId, MatchRecord


@runtime_checkable
class MatchRepository(Protocol):
    """Stores finished matches. SQLite and in-memory adapters each provide one."""

    def save(self, record: MatchRecord) -> None:
        """FR-31: store a finished match. An id already stored raises ValueError."""
        ...

    def get(self, match_id: MatchId) -> MatchRecord | None:
        """FR-31: the match stored under this id, or None if there is none."""
        ...

    def history_of(self, nickname: str) -> list[MatchRecord]:
        """FR-32: the matches a human played under this nickname, oldest first."""
        ...
