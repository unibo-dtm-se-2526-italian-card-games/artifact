"""Tests for the catalog of games the engine offers (FR-01, FR-03)."""

from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.catalog import GAMES
from italian_card_games.engine.matazza import MatazzaRules


class TestCatalog:
    def test_fr01_the_catalog_offers_matazza_and_briscola(self) -> None:
        assert set(GAMES) == {"matazza", "briscola"}

    def test_fr01_each_id_builds_the_rules_of_its_game(self) -> None:
        assert isinstance(GAMES["matazza"](), MatazzaRules)
        assert isinstance(GAMES["briscola"](), BriscolaRules)

    def test_fr03_each_game_declares_its_own_player_count(self) -> None:
        counts = {
            game_id: factory().player_count() for game_id, factory in GAMES.items()
        }
        assert counts == {"matazza": 4, "briscola": 2}
