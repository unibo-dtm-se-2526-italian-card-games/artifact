from dataclasses import dataclass

from italian_card_games.engine.values import SeatIndex
from italian_card_games.lobby.nickname import Nickname


@dataclass(frozen=True, slots=True)
class Occupant:
    """FR-27, FR-28: who sits in a seat, a human with a nickname or a bot.

    A bot has no name of its own: the lobby names it by its seat when the match
    starts. Two humans are equal when their nicknames are, ignoring letter case.
    """

    nickname: Nickname | None = None

    @classmethod
    def human(cls, nickname: Nickname) -> "Occupant":
        return cls(nickname)

    @classmethod
    def bot(cls) -> "Occupant":
        return cls(None)

    @property
    def is_bot(self) -> bool:
        return self.nickname is None


@dataclass(slots=True)
class Seat:
    """FR-27: a position at the lobby's table, empty or held by an occupant."""

    position: SeatIndex
    occupant: Occupant | None = None

    @property
    def is_empty(self) -> bool:
        return self.occupant is None
