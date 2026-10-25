from fractions import Fraction

from italian_card_games.engine.cards import Card, Deck, Rank, Suit
from italian_card_games.engine.values import (
    Deal,
    Move,
    Outcome,
    PlayerView,
    SeatIndex,
)

PLAYER_COUNT = 4

# FR-14: the card whose holder is relevant when standing points are awarded.
_CURSED_CARD = Card(Suit.SPADE, Rank(8))

# FR-18: standing totals that end the game.
_LOSING_TOTAL = 12
_PAIR_LOSING_TOTAL = 6

# FR-08: card strength in a trick, strongest first.
_RANKS_BY_STRENGTH = (3, 2, 1, 10, 9, 8, 7, 6, 5, 4)
_STRENGTH = {
    value: len(_RANKS_BY_STRENGTH) - position
    for position, value in enumerate(_RANKS_BY_STRENGTH)
}


# FR-12: round score value of a card, by rank. Ranks 4, 5, 6, 7 are worth nothing.
_ONE_THIRD = Fraction(1, 3)
_SCORE_BY_RANK = {
    1: Fraction(1),
    **{value: _ONE_THIRD for value in (3, 2, 10, 9, 8)},
    **{value: Fraction(0) for value in (4, 5, 6, 7)},
}
_LOW_SCORE_LIMIT = Fraction(1)


def _strength(rank: Rank) -> int:
    return _STRENGTH[rank.value]


class MatazzaRules:
    """The trick rules of Matazza: 4 players, follow the led suit, highest card wins."""

    def player_count(self) -> int:
        return PLAYER_COUNT

    def deal(self, deck: Deck) -> Deal:
        """FR-07: deal the whole deck evenly, so there is no stock and no trump."""
        hands = tuple(deck.cards[seat::PLAYER_COUNT] for seat in range(PLAYER_COUNT))
        return Deal(hands, (), None)

    def legal_moves(self, view: PlayerView) -> tuple[Move, ...]:
        """FR-09: follow the led suit if you hold it, otherwise play any card.

        Whose turn it is belongs to the match, not to these rules.
        """
        hand = view.hand
        if view.trick:
            led_suit = view.trick[0].card.suit
            same_suit = tuple(card for card in hand if card.suit == led_suit)
            if same_suit:
                hand = same_suit
        return tuple(Move(view.seat, card) for card in hand)

    def trick_winner(
        self, trick: tuple[Move, ...], trump: Suit | None = None
    ) -> SeatIndex:
        """FR-10: the highest-strength card of the led suit wins the trick.

        Matazza has no trump suit, so `trump` is accepted and ignored.
        """
        if len(trick) != PLAYER_COUNT:
            raise ValueError(f"a trick has {PLAYER_COUNT} moves, got {len(trick)}")
        if len({move.seat for move in trick}) != PLAYER_COUNT:
            raise ValueError("each seat plays exactly one card in a trick")
        led_suit = trick[0].card.suit
        led_moves = (move for move in trick if move.card.suit == led_suit)
        return max(led_moves, key=lambda move: _strength(move.card.rank)).seat

    def round_scores(self, won: tuple[tuple[Card, ...], ...]) -> tuple[Fraction, ...]:
        """FR-12: each seat's score is the sum of the values of the cards it won."""
        if len(won) != PLAYER_COUNT:
            raise ValueError(f"a round has {PLAYER_COUNT} piles, got {len(won)}")
        all_cards = [card for pile in won for card in pile]
        if len(set(all_cards)) != len(all_cards):
            raise ValueError("a card cannot be won twice in a round")
        return tuple(
            sum((_SCORE_BY_RANK[card.rank.value] for card in pile), Fraction(0))
            for pile in won
        )

    def round_outcomes(
        self, scores: tuple[Fraction, ...]
    ) -> tuple[Outcome, ...] | None:
        """FR-13, FR-19: a seat wins alone if the other three each score below 1.0.

        The solo winner wins and the other three lose. Exactly 1.0 is not below
        1.0, so it blocks the solo win. Without a solo winner the match goes on.
        """
        if len(scores) != PLAYER_COUNT:
            raise ValueError(f"a round has {PLAYER_COUNT} scores, got {len(scores)}")
        for seat in range(PLAYER_COUNT):
            others = scores[:seat] + scores[seat + 1 :]
            if all(other < _LOW_SCORE_LIMIT for other in others):
                return tuple(
                    Outcome.WIN if other == seat else Outcome.LOSS
                    for other in range(PLAYER_COUNT)
                )
        return None

    def round_holder(self, hands: tuple[tuple[Card, ...], ...]) -> SeatIndex | None:
        """FR-14, FR-15: the seat dealt the 8 of spades, or None if nobody holds it."""
        for seat, hand in enumerate(hands):
            if _CURSED_CARD in hand:
                return SeatIndex(seat)
        return None

    def standing_points(
        self, scores: tuple[Fraction, ...], holder: SeatIndex
    ) -> tuple[int, ...]:
        """FR-14 to FR-17: the standing points each seat earns, by seat order.

        `holder` is the seat dealt the 8 of spades. The cases depend on `numLow`,
        the number of scores below 1.0.
        """
        if len(scores) != PLAYER_COUNT:
            raise ValueError(f"a round has {PLAYER_COUNT} scores, got {len(scores)}")
        if holder.value >= PLAYER_COUNT:
            raise ValueError(f"holder seat {holder.value} is out of range")
        low = [seat for seat, score in enumerate(scores) if score < _LOW_SCORE_LIMIT]
        awarded = [0] * PLAYER_COUNT
        if len(low) == 0:
            awarded[holder.value] += 1
            others = sorted(
                (seat for seat in range(PLAYER_COUNT) if seat != holder.value),
                key=lambda seat: scores[seat],
                reverse=True,
            )
            if scores[others[0]] == scores[others[1]]:
                awarded[holder.value] += 1
            else:
                awarded[others[0]] += 1
        elif len(low) == 1:
            awarded[low[0]] += 1
            awarded[holder.value] += 1
        elif len(low) == 2:
            for seat in low:
                awarded[seat] += 1
        else:
            raise ValueError("three low scores is a solo win, not a standings case")
        return tuple(awarded)

    def outcomes(self, standing_totals: tuple[int, ...]) -> tuple[Outcome, ...] | None:
        """FR-18, FR-19: the outcome of each seat if the game is over, else None.

        A seat with 12 or more standing points loses alone. Otherwise, if two or
        more seats have 6 or more, they all lose. Everyone else wins.
        """
        if len(standing_totals) != PLAYER_COUNT:
            raise ValueError(
                f"a game has {PLAYER_COUNT} totals, got {len(standing_totals)}"
            )
        losers = [t >= _LOSING_TOTAL for t in standing_totals]
        if not any(losers):
            losers = [t >= _PAIR_LOSING_TOTAL for t in standing_totals]
            if sum(losers) < 2:
                return None
        return tuple(Outcome.LOSS if lost else Outcome.WIN for lost in losers)
