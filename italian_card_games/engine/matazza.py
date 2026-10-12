from italian_card_games.engine.cards import Rank
from italian_card_games.engine.values import Move, PlayerView, SeatIndex

PLAYER_COUNT = 4

# FR-08: card strength in a trick, strongest first.
_RANKS_BY_STRENGTH = (3, 2, 1, 10, 9, 8, 7, 6, 5, 4)
_STRENGTH = {
    value: len(_RANKS_BY_STRENGTH) - position
    for position, value in enumerate(_RANKS_BY_STRENGTH)
}


def _strength(rank: Rank) -> int:
    return _STRENGTH[rank.value]


class MatazzaRules:
    """The trick rules of Matazza: 4 players, follow the led suit, highest card wins."""

    def player_count(self) -> int:
        return PLAYER_COUNT

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

    def trick_winner(self, trick: tuple[Move, ...]) -> SeatIndex:
        """FR-10: the highest-strength card of the led suit wins the trick."""
        if len(trick) != PLAYER_COUNT:
            raise ValueError(f"a trick has {PLAYER_COUNT} moves, got {len(trick)}")
        if len({move.seat for move in trick}) != PLAYER_COUNT:
            raise ValueError("each seat plays exactly one card in a trick")
        led_suit = trick[0].card.suit
        led_moves = (move for move in trick if move.card.suit == led_suit)
        return max(led_moves, key=lambda move: _strength(move.card.rank)).seat
