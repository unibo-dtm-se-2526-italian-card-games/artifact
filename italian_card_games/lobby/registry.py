from italian_card_games.lobby.nickname import Nickname
from italian_card_games.lobby.player import RegisteredPlayer
from italian_card_games.lobby.ports import PlayerRepository


class NicknameTakenError(ValueError):
    """The nickname is already registered, in any letter case."""


class NicknameRegistry:
    """FR-26: registers nicknames and keeps them unique across all players."""

    def __init__(self, repository: PlayerRepository) -> None:
        self._repository = repository

    def register(self, nickname: Nickname) -> RegisteredPlayer:
        """Register a nickname; one already taken raises NicknameTakenError.

        The repository decides whether the name is taken, so the answer stays
        right when two registrations race: its unique constraint is the last word.
        """
        player = RegisteredPlayer(nickname)
        try:
            self._repository.add(player)
        except ValueError as error:
            raise NicknameTakenError(
                f"nickname {nickname.value} is already taken"
            ) from error
        return player

    def find(self, nickname: Nickname) -> RegisteredPlayer | None:
        """The registered player with this nickname (any case), or None."""
        return self._repository.get(nickname)
