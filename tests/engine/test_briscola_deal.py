"""Tests for how Briscola deals a deck: 3 cards each, a stock and a trump (FR-20)."""

from random import Random

from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.cards import DeckFactory
from italian_card_games.engine.values import Deal


def deal(seed: int = 0) -> Deal:
    return BriscolaRules().deal(DeckFactory.shuffled(Random(seed)))


class TestBriscolaDeal:
    def test_fr20_each_of_the_two_players_gets_three_cards(self) -> None:
        hands = deal().hands
        assert len(hands) == 2
        assert all(len(hand) == 3 for hand in hands)

    def test_fr20_the_rest_of_the_deck_is_the_stock(self) -> None:
        assert len(deal().stock) == 34

    def test_fr20_hands_and_stock_use_the_whole_deck_once(self) -> None:
        dealt = deal()
        cards = [c for hand in dealt.hands for c in hand] + list(dealt.stock)
        assert len(cards) == 40
        assert set(cards) == set(DeckFactory.ordered().cards)

    def test_fr20_the_trump_is_the_suit_of_the_last_card_of_the_stock(self) -> None:
        dealt = deal()
        assert dealt.trump == dealt.stock[-1].suit

    def test_fr20_the_cards_are_dealt_in_turn_from_the_top_of_the_deck(self) -> None:
        deck = DeckFactory.shuffled(Random(3))
        dealt = BriscolaRules().deal(deck)
        assert dealt.hands == (deck.cards[0:6:2], deck.cards[1:6:2])
        assert dealt.stock == deck.cards[6:]

    def test_fr20_the_same_deck_gives_the_same_deal(self) -> None:
        assert deal(seed=7) == deal(seed=7)

    def test_fr20_different_seeds_give_different_deals(self) -> None:
        assert deal(seed=1).hands != deal(seed=2).hands
