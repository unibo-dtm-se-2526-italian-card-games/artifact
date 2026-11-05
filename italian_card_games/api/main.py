import os
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI
from sqlalchemy import create_engine

from italian_card_games.ai.rule_based import RuleBasedStrategy
from italian_card_games.api.app import create_app
from italian_card_games.engine.catalog import GAMES
from italian_card_games.history.records import MatchId
from italian_card_games.persistence.in_memory import InMemorySessionStore
from italian_card_games.persistence.sqlite import (
    SqlMatchRepository,
    SqlPlayerRepository,
)
from italian_card_games.play.service import OfflineMatchService

DATABASE_URL_VARIABLE = "ICG_DATABASE_URL"
DEFAULT_DATABASE_URL = "sqlite:///italian_card_games.db"


def build_app(database_url: str | None = None) -> FastAPI:
    """The composition root: wire the API to SQLite repositories on one database.

    The URL is the argument, else the ICG_DATABASE_URL variable, else a file in
    the working directory. Serve it with
    `uvicorn italian_card_games.api.main:build_app --factory`.
    """
    url = database_url or os.environ.get(DATABASE_URL_VARIABLE, DEFAULT_DATABASE_URL)
    engine = create_engine(url)
    matches = SqlMatchRepository(engine)
    offline_matches = OfflineMatchService(
        games=GAMES,
        matches=matches,
        sessions=InMemorySessionStore(),
        bot_factory=RuleBasedStrategy,
        clock=lambda: datetime.now(UTC),
        new_match_id=lambda: MatchId(uuid4().hex),
    )
    return create_app(
        players=SqlPlayerRepository(engine),
        matches=matches,
        games=GAMES,
        offline_matches=offline_matches,
    )
