from typing import Protocol, runtime_checkable

from italian_card_games.lobby.nickname import Nickname
from italian_card_games.lobby.player import RegisteredPlayer


@runtime_checkable
class PlayerRepository(Protocol):
    """Stores registered players. SQLite and in-memory adapters each provide one."""

    def add(self, player: RegisteredPlayer) -> None:
        """FR-26: store a player. A nickname already taken, in any case, raises ValueError."""
        ...

    def get(self, nickname: Nickname) -> RegisteredPlayer | None:
        """FR-26: the player with this nickname (any case), or None if there is none."""
        ...
