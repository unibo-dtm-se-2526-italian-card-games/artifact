"""Tests for a round with a stock and a trump: drawing after each trick (FR-20)."""

from random import Random

from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.cards import Card, DeckFactory, Rank, Suit
from italian_card_games.engine.match import Round
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.values import Deal, Move, SeatIndex

RULES = BriscolaRules()
TRUMP = Suit.DENARI
SEAT0, SEAT1 = SeatIndex(0), SeatIndex(1)


def card(suit: Suit, rank: int) -> Card:
    return Card(suit, Rank(rank))


def a_round() -> Round:
    """Seat 0 leads. The stock ends with the turned-up trump card, the 2 of coins."""
    return Round(
        hands=(
            (card(Suit.COPPE, 1), card(Suit.COPPE, 4), card(Suit.SPADE, 4)),
            (card(Suit.COPPE, 3), card(Suit.COPPE, 5), card(Suit.SPADE, 5)),
        ),
        dealer=SEAT1,
        leader=SEAT0,
        trick=(),
        won=((), ()),
        stock=(
            card(Suit.BASTONI, 4),
            card(Suit.BASTONI, 5),
            card(Suit.BASTONI, 6),
            card(TRUMP, 2),
        ),
        trump=TRUMP,
    )


def play(round_: Round, seat: SeatIndex, c: Card) -> None:
    round_.play(Move(seat, c), RULES)


class TestStart:
    def test_fr20_a_round_keeps_the_stock_and_trump_of_its_deal(self) -> None:
        deal = RULES.deal(DeckFactory.shuffled(Random(5)))
        round_ = Round.start(deal, SEAT0)
        assert round_.stock == deal.stock
        assert round_.trump == deal.trump

    def test_fr20_a_game_without_a_stock_starts_a_round_with_none(self) -> None:
        deal = MatazzaRules().deal(DeckFactory.shuffled(Random(5)))
        round_ = Round.start(deal, SEAT0)
        assert round_.stock == ()
        assert round_.trump is None

    def test_fr20_a_deal_with_hands_only_leaves_the_stock_empty(self) -> None:
        hands = ((card(Suit.COPPE, 1),), (card(Suit.COPPE, 2),))
        round_ = Round.start(Deal(hands, (), None), SEAT0)
        assert round_.stock == ()


class TestView:
    def test_fr20_a_seat_sees_the_trump_suit(self) -> None:
        assert a_round().view_for(SEAT1).trump == TRUMP

    def test_fr20_a_seat_does_not_see_the_stock(self) -> None:
        view = a_round().view_for(SEAT0)
        assert all(c not in view.hand for c in a_round().stock)


class TestDrawing:
    def test_fr20_a_card_played_does_not_draw_until_the_trick_is_complete(self) -> None:
        round_ = a_round()
        play(round_, SEAT0, card(Suit.COPPE, 1))
        assert len(round_.hands[0]) == 2
        assert len(round_.stock) == 4

    def test_fr20_the_trick_winner_draws_first_then_the_other_seat(self) -> None:
        round_ = a_round()
        play(round_, SEAT0, card(Suit.COPPE, 1))
        play(round_, SEAT1, card(Suit.COPPE, 3))  # the ace wins: seat 0 draws first
        assert round_.hands == (
            (card(Suit.COPPE, 4), card(Suit.SPADE, 4), card(Suit.BASTONI, 4)),
            (card(Suit.COPPE, 5), card(Suit.SPADE, 5), card(Suit.BASTONI, 5)),
        )
        assert round_.stock == (card(Suit.BASTONI, 6), card(TRUMP, 2))
        assert round_.leader == SEAT0

    def test_fr20_the_last_card_of_the_stock_goes_to_the_last_drawer(self) -> None:
        round_ = a_round()
        play(round_, SEAT0, card(Suit.COPPE, 1))
        play(round_, SEAT1, card(Suit.COPPE, 3))
        play(round_, SEAT0, card(Suit.COPPE, 4))
        play(round_, SEAT1, card(Suit.COPPE, 5))  # the five wins: seat 1 draws first
        assert card(Suit.BASTONI, 6) in round_.hands[1]
        assert card(TRUMP, 2) in round_.hands[0]
        assert round_.stock == ()
        assert round_.leader == SEAT1

    def test_fr20_a_trump_beats_the_led_suit_and_wins_the_trick(self) -> None:
        round_ = a_round()
        round_.hands = (
            round_.hands[0],
            (card(TRUMP, 4), card(Suit.COPPE, 5), card(Suit.SPADE, 5)),
        )
        play(round_, SEAT0, card(Suit.COPPE, 1))
        play(round_, SEAT1, card(TRUMP, 4))
        assert round_.leader == SEAT1
        assert card(TRUMP, 4) in round_.won[1]
        assert card(Suit.COPPE, 1) in round_.won[1]

    def test_fr20_nothing_is_drawn_once_the_stock_is_empty(self) -> None:
        round_ = a_round()
        round_.stock = ()
        play(round_, SEAT0, card(Suit.COPPE, 1))
        play(round_, SEAT1, card(Suit.COPPE, 3))
        assert [len(hand) for hand in round_.hands] == [2, 2]


class TestWholeRound:
    def test_fr20_a_round_ends_when_stock_and_hands_are_empty(self) -> None:
        round_ = Round.start(RULES.deal(DeckFactory.shuffled(Random(11))), SEAT0)
        while not round_.is_over:
            seat = round_.current_seat
            move = RULES.legal_moves(round_.view_for(seat))[0]
            round_.play(move, RULES)
        assert round_.stock == ()
        won = [c for pile in round_.won for c in pile]
        assert set(won) == set(DeckFactory.ordered().cards)
        assert len(won) == 40

    def test_fr20_the_scores_of_a_whole_round_add_up_to_120(self) -> None:
        round_ = Round.start(RULES.deal(DeckFactory.shuffled(Random(11))), SEAT0)
        while not round_.is_over:
            move = RULES.legal_moves(round_.view_for(round_.current_seat))[0]
            round_.play(move, RULES)
        assert sum(round_.scores(RULES)) == 120
