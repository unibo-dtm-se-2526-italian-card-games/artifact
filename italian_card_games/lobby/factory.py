from collections.abc import Callable

from italian_card_games.lobby.join_code import JoinCode
from italian_card_games.lobby.lobby import Lobby
from italian_card_games.lobby.nickname import Nickname


class LobbyFactory:
    """FR-27: creates lobbies, each with a fresh join code from an injected generator.

    The factory does not check that the code is unused; the lobby repository rejects
    a duplicate, and the caller asks for a new lobby in that rare case.
    """

    def __init__(self, new_code: Callable[[], JoinCode]) -> None:
        self._new_code = new_code

    def create(self, game_id: str, player_count: int, creator: Nickname) -> Lobby:
        """A new lobby with the creator on seat 0 and a fresh code."""
        return Lobby(self._new_code(), game_id, player_count, creator)
