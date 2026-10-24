from italian_card_games.engine.cards import Rank, Suit
from italian_card_games.engine.values import Move, PlayerView, SeatIndex

PLAYER_COUNT = 2

# FR-20: card strength in a trick, strongest first.
_RANKS_BY_STRENGTH = (1, 3, 10, 9, 8, 7, 6, 5, 4, 2)
_STRENGTH = {
    value: len(_RANKS_BY_STRENGTH) - position
    for position, value in enumerate(_RANKS_BY_STRENGTH)
}


def _strength(rank: Rank) -> int:
    return _STRENGTH[rank.value]


class BriscolaRules:
    """The trick rules of Briscola: 2 players, any card may be played, trump wins."""

    def player_count(self) -> int:
        return PLAYER_COUNT

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
