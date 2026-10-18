"""Tests for dealing a round: hands, first leader and dealer rules (FR-07, FR-11)."""

from random import Random

import pytest

from italian_card_games.engine.cards import DeckFactory
from italian_card_games.engine.match import Round
from italian_card_games.engine.values import SeatIndex


def deal(seed: int = 0, dealer: int = 0, player_count: int = 4) -> Round:
    deck = DeckFactory.shuffled(Random(seed))
    return Round.deal(deck, SeatIndex(dealer), player_count)


class TestHands:
    def test_fr07_four_players_get_ten_cards_each(self) -> None:
        round_ = deal()
        assert len(round_.hands) == 4
        assert all(len(hand) == 10 for hand in round_.hands)

    def test_fr07_the_hands_are_distinct_and_use_the_whole_deck(self) -> None:
        round_ = deal()
        dealt = [card for hand in round_.hands for card in hand]
        assert set(dealt) == set(DeckFactory.ordered().cards)
        assert len(dealt) == 40

    def test_fr07_a_round_starts_with_an_empty_trick_and_no_cards_won(self) -> None:
        round_ = deal()
        assert round_.trick == ()
        assert round_.won == ((), (), (), ())

    def test_fr07_the_same_deck_gives_the_same_deal(self) -> None:
        assert deal(seed=7).hands == deal(seed=7).hands

    def test_fr07_different_seeds_give_different_deals(self) -> None:
        assert deal(seed=1).hands != deal(seed=2).hands

    def test_fr07_the_hand_size_follows_the_player_count(self) -> None:
        round_ = deal(player_count=2)
        assert [len(hand) for hand in round_.hands] == [20, 20]


class TestFirstLeader:
    @pytest.mark.parametrize(("dealer", "leader"), [(0, 1), (1, 2), (2, 3), (3, 0)])
    def test_fr11_the_first_leader_is_the_seat_after_the_dealer(
        self, dealer: int, leader: int
    ) -> None:
        round_ = deal(dealer=dealer)
        assert round_.dealer == SeatIndex(dealer)
        assert round_.leader == SeatIndex(leader)


class TestInvalidDeal:
    def test_fr07_a_dealer_outside_the_table_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            deal(dealer=4)

    @pytest.mark.parametrize("player_count", [0, 3, 6])
    def test_fr07_a_player_count_that_does_not_split_the_deck_is_rejected(
        self, player_count: int
    ) -> None:
        with pytest.raises(ValueError):
            deal(player_count=player_count)
