from pydantic import BaseModel


class GameInfo(BaseModel):
    """A game the server can play."""

    id: str
    player_count: int
