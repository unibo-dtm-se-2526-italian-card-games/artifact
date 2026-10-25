"""Tests that BriscolaRules is a Game: one round decides a match, so no standings (FR-01, FR-20)."""

from fractions import Fraction

from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.cards import DeckFactory
from italian_card_games.engine.ports import Game
from italian_card_games.engine.values import SeatIndex


class TestBriscolaAsAGame:
    def test_fr01_is_a_game(self) -> None:
        assert isinstance(BriscolaRules(), Game)

    def test_fr20_has_no_holder_because_no_card_gives_standing_points(self) -> None:
        hands = BriscolaRules().deal(DeckFactory.ordered()).hands
        assert BriscolaRules().round_holder(hands) is None

    def test_fr20_awards_no_standing_points(self) -> None:
        scores = (Fraction(70), Fraction(50))
        assert BriscolaRules().standing_points(scores, SeatIndex(0)) == (0, 0)

    def test_fr20_has_no_standing_totals_to_end_the_game(self) -> None:
        assert BriscolaRules().outcomes((0, 0)) is None
