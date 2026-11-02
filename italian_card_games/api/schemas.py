from pydantic import BaseModel


class GameInfo(BaseModel):
    """A game the server can play."""

    id: str
    player_count: int


class NewPlayer(BaseModel):
    """The request to register a nickname."""

    nickname: str


class PlayerInfo(BaseModel):
    """A registered player, with the nickname as they chose it."""

    nickname: str
