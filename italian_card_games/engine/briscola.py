from fractions import Fraction

from italian_card_games.engine.cards import Card, Deck, Rank, Suit
from italian_card_games.engine.values import (
    Deal,
    Move,
    Outcome,
    PlayerView,
    SeatIndex,
)

PLAYER_COUNT = 2
HAND_SIZE = 3

# FR-20: card strength in a trick, strongest first.
_RANKS_BY_STRENGTH = (1, 3, 10, 9, 8, 7, 6, 5, 4, 2)
_STRENGTH = {
    value: len(_RANKS_BY_STRENGTH) - position
    for position, value in enumerate(_RANKS_BY_STRENGTH)
}

# FR-20: points of a card by rank. Ranks 2, 4, 5, 6, 7 are worth nothing.
_POINTS_BY_RANK = {1: 11, 3: 10, 10: 4, 9: 3, 8: 2}


def _strength(rank: Rank) -> int:
    return _STRENGTH[rank.value]


class BriscolaRules:
    """The trick rules of Briscola: 2 players, any card may be played, trump wins."""

    def player_count(self) -> int:
        return PLAYER_COUNT

    def deal(self, deck: Deck) -> Deal:
        """FR-20: three cards each in turn, the rest is the stock, its last card is trump.

        The last card of the stock is turned up and drawn last, so it names the trump.
        """
        dealt = HAND_SIZE * PLAYER_COUNT
        hands = tuple(
            deck.cards[seat:dealt:PLAYER_COUNT] for seat in range(PLAYER_COUNT)
        )
        stock = deck.cards[dealt:]
        return Deal(hands, stock, stock[-1].suit)

    def legal_moves(self, view: PlayerView) -> tuple[Move, ...]:
        """FR-20: any card in hand may be played, there is no duty to follow suit."""
        return tuple(Move(view.seat, card) for card in view.hand)

    def trick_winner(
        self, trick: tuple[Move, ...], trump: Suit | None = None
    ) -> SeatIndex:
        """FR-20: the highest trump wins, else the highest card of the led suit."""
        if trump is None:
            raise ValueError("Briscola needs a trump suit to decide a trick")
        if len(trick) != PLAYER_COUNT:
            raise ValueError(f"a trick has {PLAYER_COUNT} moves, got {len(trick)}")
        if len({move.seat for move in trick}) != PLAYER_COUNT:
            raise ValueError("each seat plays exactly one card in a trick")
        led_suit = trick[0].card.suit
        contenders = [move for move in trick if move.card.suit == trump] or [
            move for move in trick if move.card.suit == led_suit
        ]
        return max(contenders, key=lambda move: _strength(move.card.rank)).seat

    def round_scores(self, won: tuple[tuple[Card, ...], ...]) -> tuple[Fraction, ...]:
        """FR-20: each seat's score is the sum of the points of the cards it won."""
        if len(won) != PLAYER_COUNT:
            raise ValueError(f"a round has {PLAYER_COUNT} piles, got {len(won)}")
        all_cards = [card for pile in won for card in pile]
        if len(set(all_cards)) != len(all_cards):
            raise ValueError("a card cannot be won twice in a round")
        return tuple(
            Fraction(sum(_POINTS_BY_RANK.get(card.rank.value, 0) for card in pile))
            for pile in won
        )

    def round_outcomes(self, scores: tuple[Fraction, ...]) -> tuple[Outcome, ...]:
        """FR-20: the higher score wins the match, equal scores are a draw for both.

        Of the 120 points, 61 or more win, so 60 each is the only tie. One round
        always decides a Briscola match, so this never returns None.
        """
        if len(scores) != PLAYER_COUNT:
            raise ValueError(f"a round has {PLAYER_COUNT} scores, got {len(scores)}")
        first, second = scores
        if first == second:
            return (Outcome.DRAW, Outcome.DRAW)
        if first > second:
            return (Outcome.WIN, Outcome.LOSS)
        return (Outcome.LOSS, Outcome.WIN)
