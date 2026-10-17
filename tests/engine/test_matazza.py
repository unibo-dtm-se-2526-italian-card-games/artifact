"""Tests for the Matazza trick rules: strength, follow-suit and trick winner (FR-08, FR-09, FR-10)."""

from fractions import Fraction
from itertools import combinations

import pytest

from italian_card_games.engine.cards import Card, DeckFactory, Rank, Suit
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.ports import Game
from italian_card_games.engine.values import Move, PlayerView, SeatIndex

# FR-08: strongest first.
STRENGTH_ORDER = [3, 2, 1, 10, 9, 8, 7, 6, 5, 4]


def card(suit: Suit, rank: int) -> Card:
    return Card(suit, Rank(rank))


def move(seat: int, suit: Suit, rank: int) -> Move:
    return Move(SeatIndex(seat), card(suit, rank))


def view(seat: int, hand: tuple[Card, ...], trick: tuple[Move, ...]) -> PlayerView:
    return PlayerView(SeatIndex(seat), hand, trick)


def moves_of(seat: int, hand: tuple[Card, ...]) -> tuple[Move, ...]:
    return tuple(Move(SeatIndex(seat), c) for c in hand)


class TestMatazzaRulesAsAGame:
    def test_is_a_game(self) -> None:
        assert isinstance(MatazzaRules(), Game)

    def test_fr03_declares_four_players(self) -> None:
        assert MatazzaRules().player_count() == 4


class TestTrickWinnerStrength:
    @pytest.mark.parametrize(
        ("stronger", "weaker"),
        list(combinations(STRENGTH_ORDER, 2)),
    )
    def test_fr08_stronger_rank_beats_weaker_rank_in_the_led_suit(
        self, stronger: int, weaker: int
    ) -> None:
        for stronger_first in (True, False):
            first, second = (stronger, weaker) if stronger_first else (weaker, stronger)
            trick = (
                move(0, Suit.COPPE, first),
                move(1, Suit.COPPE, second),
                move(2, Suit.SPADE, 3),  # off-suit fillers cannot win
                move(3, Suit.DENARI, 2),
            )
            winner = MatazzaRules().trick_winner(trick)
            assert winner == SeatIndex(0 if stronger_first else 1)

    def test_fr08_three_is_the_strongest_and_four_the_weakest(self) -> None:
        trick = (
            move(0, Suit.DENARI, 4),
            move(1, Suit.DENARI, 5),
            move(2, Suit.DENARI, 3),
            move(3, Suit.DENARI, 10),
        )
        assert MatazzaRules().trick_winner(trick) == SeatIndex(2)


class TestTrickWinnerFollowSuit:
    def test_fr10_off_suit_card_never_wins(self) -> None:
        trick = (
            move(0, Suit.COPPE, 4),  # weakest rank, but it sets the suit
            move(1, Suit.SPADE, 3),  # strongest rank, wrong suit
            move(2, Suit.DENARI, 2),
            move(3, Suit.BASTONI, 1),
        )
        assert MatazzaRules().trick_winner(trick) == SeatIndex(0)

    def test_fr10_highest_card_of_the_led_suit_wins(self) -> None:
        trick = (
            move(0, Suit.SPADE, 7),
            move(1, Suit.SPADE, 10),
            move(2, Suit.DENARI, 3),
            move(3, Suit.SPADE, 1),
        )
        assert MatazzaRules().trick_winner(trick) == SeatIndex(3)

    def test_fr10_winner_is_reported_by_seat_not_by_play_order(self) -> None:
        trick = (
            move(2, Suit.BASTONI, 5),
            move(3, Suit.BASTONI, 2),
            move(0, Suit.BASTONI, 6),
            move(1, Suit.BASTONI, 9),
        )
        assert MatazzaRules().trick_winner(trick) == SeatIndex(3)

    @pytest.mark.parametrize("played", [0, 1, 2, 3, 5])
    def test_rejects_a_trick_without_four_moves(self, played: int) -> None:
        seats = (0, 1, 2, 3, 0)[:played]
        trick = tuple(move(s, Suit.COPPE, 4 + s) for s in seats)
        with pytest.raises(ValueError):
            MatazzaRules().trick_winner(trick)

    def test_rejects_a_trick_where_a_seat_plays_twice(self) -> None:
        trick = (
            move(0, Suit.COPPE, 4),
            move(1, Suit.COPPE, 5),
            move(2, Suit.COPPE, 6),
            move(1, Suit.COPPE, 7),
        )
        with pytest.raises(ValueError):
            MatazzaRules().trick_winner(trick)


class TestLegalMoves:
    def test_fr09_leader_may_play_any_card(self) -> None:
        hand = (card(Suit.COPPE, 4), card(Suit.SPADE, 3), card(Suit.DENARI, 1))
        assert MatazzaRules().legal_moves(view(0, hand, ())) == moves_of(0, hand)

    def test_fr09_must_follow_the_led_suit_when_holding_it(self) -> None:
        hand = (card(Suit.COPPE, 4), card(Suit.SPADE, 3), card(Suit.SPADE, 9))
        trick = (move(3, Suit.SPADE, 5),)
        legal = MatazzaRules().legal_moves(view(0, hand, trick))
        assert legal == moves_of(0, (card(Suit.SPADE, 3), card(Suit.SPADE, 9)))

    def test_fr09_forced_follow_even_with_one_card_of_the_suit(self) -> None:
        hand = (card(Suit.COPPE, 3), card(Suit.COPPE, 2), card(Suit.SPADE, 4))
        trick = (move(1, Suit.SPADE, 10), move(2, Suit.SPADE, 7))
        legal = MatazzaRules().legal_moves(view(3, hand, trick))
        assert legal == moves_of(3, (card(Suit.SPADE, 4),))

    def test_fr09_may_discard_any_card_when_void_in_the_led_suit(self) -> None:
        hand = (card(Suit.COPPE, 4), card(Suit.DENARI, 3), card(Suit.BASTONI, 9))
        trick = (move(1, Suit.SPADE, 5),)
        legal = MatazzaRules().legal_moves(view(2, hand, trick))
        assert legal == moves_of(2, hand)

    def test_fr09_the_led_suit_is_the_first_card_not_the_latest(self) -> None:
        hand = (card(Suit.COPPE, 4), card(Suit.SPADE, 3))
        trick = (move(0, Suit.COPPE, 5), move(1, Suit.SPADE, 10))
        legal = MatazzaRules().legal_moves(view(2, hand, trick))
        assert legal == moves_of(2, (card(Suit.COPPE, 4),))

    def test_fr09_moves_belong_to_the_viewing_seat(self) -> None:
        hand = (card(Suit.COPPE, 4),)
        legal = MatazzaRules().legal_moves(view(2, hand, ()))
        assert all(m.seat == SeatIndex(2) for m in legal)


def a_full_deal() -> tuple[tuple[Card, ...], ...]:
    """The ordered deck split suit by suit: each seat captured ranks 1 to 10 of one suit."""
    cards = DeckFactory.ordered().cards
    return tuple(cards[start : start + 10] for start in range(0, 40, 10))


class TestRoundScores:
    @pytest.mark.parametrize("rank", [3, 2, 10, 9, 8])
    def test_fr12_these_ranks_are_worth_a_third(self, rank: int) -> None:
        won = ((card(Suit.COPPE, rank),), (), (), ())
        assert MatazzaRules().round_scores(won)[0] == Fraction(1, 3)

    def test_fr12_the_ace_is_worth_one_point(self) -> None:
        won = ((card(Suit.COPPE, 1),), (), (), ())
        assert MatazzaRules().round_scores(won)[0] == Fraction(1)

    @pytest.mark.parametrize("rank", [4, 5, 6, 7])
    def test_fr12_these_ranks_are_worth_nothing(self, rank: int) -> None:
        won = ((card(Suit.COPPE, rank),), (), (), ())
        assert MatazzaRules().round_scores(won)[0] == Fraction(0)

    def test_fr12_the_suit_does_not_change_the_value(self) -> None:
        won = tuple((card(suit, 3),) for suit in Suit)
        assert MatazzaRules().round_scores(won) == (Fraction(1, 3),) * 4

    def test_fr12_a_seat_adds_up_all_the_cards_it_won(self) -> None:
        hand = (card(Suit.COPPE, 1), card(Suit.COPPE, 3), card(Suit.COPPE, 2))
        won = (hand, (), (), ())
        assert MatazzaRules().round_scores(won)[0] == Fraction(5, 3)

    def test_fr12_scores_follow_the_seat_order(self) -> None:
        won = a_full_deal()
        reordered = (won[2], won[0], won[3], won[1])
        scores = MatazzaRules().round_scores(reordered)
        assert scores == tuple(MatazzaRules().round_scores(won)[i] for i in (2, 0, 3, 1))

    def test_fr12_the_four_scores_of_a_round_sum_to_32_thirds(self) -> None:
        scores = MatazzaRules().round_scores(a_full_deal())
        assert sum(scores) == Fraction(32, 3)

    def test_fr12_scores_are_exact_fractions_never_floats(self) -> None:
        scores = MatazzaRules().round_scores(a_full_deal())
        assert all(isinstance(score, Fraction) for score in scores)

    def test_fr12_a_round_needs_one_pile_per_seat(self) -> None:
        with pytest.raises(ValueError):
            MatazzaRules().round_scores(a_full_deal()[:3])

    def test_fr12_a_card_cannot_be_won_twice(self) -> None:
        deal = a_full_deal()
        duplicated = (deal[0], deal[0], deal[2], deal[3])
        with pytest.raises(ValueError):
            MatazzaRules().round_scores(duplicated)


class TestSoloWinner:
    @pytest.mark.parametrize("seat", [0, 1, 2, 3])
    def test_fr13_the_player_above_three_low_scores_wins_alone(self, seat: int) -> None:
        low = Fraction(1, 3)
        scores = tuple(Fraction(29, 3) if i == seat else low for i in range(4))
        assert MatazzaRules().solo_winner(scores) == SeatIndex(seat)

    def test_fr13_a_score_of_exactly_one_blocks_the_solo_win(self) -> None:
        scores = (Fraction(28, 3), Fraction(1), Fraction(1, 3), Fraction(1, 3))
        assert MatazzaRules().solo_winner(scores) is None

    def test_fr13_a_score_just_under_one_still_allows_the_solo_win(self) -> None:
        scores = (Fraction(26, 3), Fraction(2, 3), Fraction(2, 3), Fraction(2, 3))
        assert MatazzaRules().solo_winner(scores) == SeatIndex(0)

    def test_fr13_two_low_scores_are_not_enough(self) -> None:
        scores = (Fraction(5), Fraction(4), Fraction(1, 3), Fraction(1, 3))
        assert MatazzaRules().solo_winner(scores) is None

    def test_fr13_four_scores_are_required(self) -> None:
        with pytest.raises(ValueError):
            MatazzaRules().solo_winner((Fraction(1), Fraction(1)))
