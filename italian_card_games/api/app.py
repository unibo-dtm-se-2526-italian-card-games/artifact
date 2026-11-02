from collections.abc import Callable, Mapping

from fastapi import APIRouter, FastAPI

from italian_card_games.api.schemas import GameInfo
from italian_card_games.engine.ports import Game
from italian_card_games.history.ports import MatchRepository
from italian_card_games.lobby.ports import PlayerRepository

API_PREFIX = "/api/v1"


def create_app(
    players: PlayerRepository,
    matches: MatchRepository,
    games: Mapping[str, Callable[[], Game]],
) -> FastAPI:
    """FR-34: build the REST API on the given ports; it never builds an adapter itself.

    `games` maps a game id to a factory of its rules. Every route lives under
    /api/v1, and the OpenAPI document is published at /api/v1/openapi.json.
    """
    app = FastAPI(
        title="italian_card_games",
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=None,
    )
    app.state.players = players
    app.state.matches = matches
    router = APIRouter(prefix=API_PREFIX)

    @router.get("/games", response_model=list[GameInfo])
    def list_games() -> list[GameInfo]:
        """List the games that can be played, with the number of players of each."""
        return [
            GameInfo(id=game_id, player_count=games[game_id]().player_count())
            for game_id in sorted(games)
        ]

    app.include_router(router)
    return app
