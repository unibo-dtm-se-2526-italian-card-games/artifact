from typing import Protocol, runtime_checkable

from italian_card_games.lobby.join_code import JoinCode
from italian_card_games.lobby.lobby import Lobby
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


@runtime_checkable
class LobbyRepository(Protocol):
    """Keeps the lobbies, by join code. Lobbies are short-lived, so an in-memory adapter is enough."""

    def add(self, lobby: Lobby) -> None:
        """FR-27: keep a new lobby. A code already in use raises ValueError."""
        ...

    def get(self, code: JoinCode) -> Lobby | None:
        """FR-27: the lobby with this code, or None if there is none."""
        ...

    def remove(self, code: JoinCode) -> None:
        """FR-27: forget the lobby with this code. An unknown code does nothing."""
        ...
