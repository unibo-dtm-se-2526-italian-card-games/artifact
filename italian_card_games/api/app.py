from collections.abc import Callable, Mapping

from fastapi import APIRouter, FastAPI, HTTPException, status

from italian_card_games.api.schemas import (
    GameInfo,
    GameStatsInfo,
    MatchInfo,
    NewPlayer,
    PlayerInfo,
)
from italian_card_games.engine.ports import Game
from italian_card_games.history.ports import MatchRepository
from italian_card_games.history.statistics import StatisticsService
from italian_card_games.lobby.nickname import Nickname
from italian_card_games.lobby.player import RegisteredPlayer
from italian_card_games.lobby.ports import PlayerRepository
from italian_card_games.lobby.registry import NicknameRegistry, NicknameTakenError

API_PREFIX = "/api/v1"


def _parse_nickname(text: str) -> Nickname:
    """FR-26: build a Nickname, turning the domain's rejection into a 422."""
    try:
        return Nickname(text)
    except ValueError as error:
        # Plain 422: Starlette renamed its constant for this code between versions.
        raise HTTPException(422, str(error)) from error


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
    registry = NicknameRegistry(players)
    statistics = StatisticsService()
    router = APIRouter(prefix=API_PREFIX)

    def registered_player(text: str) -> RegisteredPlayer:
        """The player with this nickname (any case); 422 if invalid, 404 if unknown."""
        wanted = _parse_nickname(text)
        player = registry.find(wanted)
        if player is None:
            detail = f"nickname {wanted.value} is not registered"
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail)
        return player

    @router.get("/games", response_model=list[GameInfo])
    def list_games() -> list[GameInfo]:
        """List the games that can be played, with the number of players of each."""
        return [
            GameInfo(id=game_id, player_count=games[game_id]().player_count())
            for game_id in sorted(games)
        ]

    @router.post(
        "/players",
        response_model=PlayerInfo,
        status_code=status.HTTP_201_CREATED,
        responses={status.HTTP_409_CONFLICT: {"description": "Nickname taken"}},
    )
    def register_player(body: NewPlayer) -> PlayerInfo:
        """FR-26: register a new nickname. A taken one, in any letter case, is a 409."""
        nickname = _parse_nickname(body.nickname)
        try:
            player = registry.register(nickname)
        except NicknameTakenError as error:
            raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
        return PlayerInfo(nickname=player.nickname.value)

    @router.get(
        "/players/{nickname}",
        response_model=PlayerInfo,
        responses={status.HTTP_404_NOT_FOUND: {"description": "Not registered"}},
    )
    def get_player(nickname: str) -> PlayerInfo:
        """FR-26: select an existing player by nickname, ignoring letter case."""
        player = registered_player(nickname)
        return PlayerInfo(nickname=player.nickname.value)

    @router.get(
        "/players/{nickname}/matches",
        response_model=list[MatchInfo],
        responses={status.HTTP_404_NOT_FOUND: {"description": "Not registered"}},
    )
    def player_history(nickname: str) -> list[MatchInfo]:
        """FR-32: the finished matches of a player, oldest first, with round scores."""
        player = registered_player(nickname)
        records = matches.history_of(player.nickname.value)
        return [MatchInfo.from_record(record) for record in records]

    @router.get(
        "/players/{nickname}/stats",
        response_model=dict[str, GameStatsInfo],
        responses={status.HTTP_404_NOT_FOUND: {"description": "Not registered"}},
    )
    def player_stats(nickname: str) -> dict[str, GameStatsInfo]:
        """FR-33: a player's matches played, wins, losses and draws per game type."""
        player = registered_player(nickname)
        records = matches.history_of(player.nickname.value)
        stats = statistics.stats_for(player.nickname.value, records)
        return {game: GameStatsInfo.from_stats(s) for game, s in stats.items()}

    app.include_router(router)
    return app
