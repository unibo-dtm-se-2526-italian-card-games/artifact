from collections.abc import Callable
from datetime import UTC, datetime
from itertools import count

import pytest
from fastapi.testclient import TestClient

from italian_card_games.ai.rule_based import RuleBasedStrategy
from italian_card_games.api.app import create_app
from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.ports import Game
from italian_card_games.history.records import MatchId
from italian_card_games.persistence.in_memory import (
    InMemoryMatchRepository,
    InMemoryPlayerRepository,
    InMemorySessionStore,
)
from italian_card_games.play.service import OfflineMatchService

NOW = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)


@pytest.fixture
def matches() -> InMemoryMatchRepository:
    """The match store behind `client`, so a test can put finished matches in it."""
    return InMemoryMatchRepository()


@pytest.fixture
def client(matches: InMemoryMatchRepository) -> TestClient:
    """The API on empty in-memory repositories, with ids m1, m2, ... and a fixed clock."""
    games: dict[str, Callable[[], Game]] = {
        "matazza": MatazzaRules,
        "briscola": BriscolaRules,
    }
    numbers = count(1)
    offline_matches = OfflineMatchService(
        games=games,
        matches=matches,
        sessions=InMemorySessionStore(),
        bot_factory=RuleBasedStrategy,
        clock=lambda: NOW,
        new_match_id=lambda: MatchId(f"m{next(numbers)}"),
    )
    app = create_app(
        players=InMemoryPlayerRepository(),
        matches=matches,
        games=games,
        offline_matches=offline_matches,
    )
    return TestClient(app)
