import pytest
from fastapi.testclient import TestClient

from italian_card_games.api.app import create_app
from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.persistence.in_memory import (
    InMemoryMatchRepository,
    InMemoryPlayerRepository,
)


@pytest.fixture
def client() -> TestClient:
    """The API on empty in-memory repositories."""
    app = create_app(
        players=InMemoryPlayerRepository(),
        matches=InMemoryMatchRepository(),
        games={"matazza": MatazzaRules, "briscola": BriscolaRules},
    )
    return TestClient(app)
