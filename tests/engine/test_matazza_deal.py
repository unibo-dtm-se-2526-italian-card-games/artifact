"""Tests for how Matazza deals a deck: the whole deck, evenly, no stock (FR-07)."""

from random import Random

from italian_card_games.engine.cards import DeckFactory
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.values import Deal


def deal(seed: int = 0) -> Deal:
    return MatazzaRules().deal(DeckFactory.shuffled(Random(seed)))


class TestMatazzaDeal:
    def test_fr07_four_players_get_ten_cards_each(self) -> None:
        hands = deal().hands
        assert len(hands) == 4
        assert all(len(hand) == 10 for hand in hands)

    def test_fr07_the_hands_are_distinct_and_use_the_whole_deck(self) -> None:
        dealt = [card for hand in deal().hands for card in hand]
        assert set(dealt) == set(DeckFactory.ordered().cards)
        assert len(dealt) == 40

    def test_fr07_the_whole_deck_is_dealt_so_there_is_no_stock(self) -> None:
        assert deal().stock == ()

    def test_fr07_matazza_has_no_trump_suit(self) -> None:
        assert deal().trump is None

    def test_fr07_the_same_deck_gives_the_same_deal(self) -> None:
        assert deal(seed=7) == deal(seed=7)

    def test_fr07_different_seeds_give_different_deals(self) -> None:
        assert deal(seed=1).hands != deal(seed=2).hands
