from dataclasses import dataclass

from italian_card_games.lobby.nickname import Nickname


@dataclass(frozen=True, slots=True)
class RegisteredPlayer:
    """FR-26: a human who registered a nickname. Identified by that nickname alone."""

    nickname: Nickname
