"""Tests for finding the holder of the 8 of spades, the cursed card (FR-14, FR-15)."""

from random import Random

import pytest

from italian_card_games.engine.cards import Card, DeckFactory, Rank, Suit
from italian_card_games.engine.match import Round
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.ports import Game
from italian_card_games.engine.values import SeatIndex

EIGHT_OF_SPADES = Card(Suit.SPADE, Rank(8))
ACE_OF_COINS = Card(Suit.DENARI, Rank(1))
THREE_OF_CUPS = Card(Suit.COPPE, Rank(3))


class TestRoundHolder:
    def test_fr14_the_holder_is_the_seat_dealt_the_eight_of_spades(self) -> None:
        hands = (
            (ACE_OF_COINS,),
            (THREE_OF_CUPS,),
            (EIGHT_OF_SPADES,),
            (),
        )
        assert MatazzaRules().round_holder(hands) == SeatIndex(2)

    def test_fr14_the_holder_is_found_among_several_cards_in_a_hand(self) -> None:
        hands = (
            (ACE_OF_COINS, THREE_OF_CUPS),
            (),
            (),
            (THREE_OF_CUPS, EIGHT_OF_SPADES),
        )
        assert MatazzaRules().round_holder(hands) == SeatIndex(3)

    def test_fr14_the_holder_of_a_dealt_ordered_deck(self) -> None:
        # In the ordered deck the 8 of spades is card 27, so seat 27 % 4 = 3 gets it.
        deal = Round.deal(DeckFactory.ordered(), SeatIndex(0), 4)
        assert MatazzaRules().round_holder(deal.hands) == SeatIndex(3)

    @pytest.mark.parametrize("seed", range(10))
    def test_fr14_every_dealt_round_has_exactly_one_holder(self, seed: int) -> None:
        deal = Round.deal(DeckFactory.shuffled(Random(seed)), SeatIndex(0), 4)
        holder = MatazzaRules().round_holder(deal.hands)
        assert holder is not None
        assert EIGHT_OF_SPADES in deal.hands[holder.value]

    def test_fr14_there_is_no_holder_when_the_card_is_not_dealt(self) -> None:
        assert MatazzaRules().round_holder(((ACE_OF_COINS,), (), (), ())) is None

    def test_matazza_rules_still_satisfy_the_game_port(self) -> None:
        assert isinstance(MatazzaRules(), Game)
