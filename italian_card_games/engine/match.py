from dataclasses import dataclass

from italian_card_games.engine.cards import DECK_SIZE, Card, Deck
from italian_card_games.engine.values import Move, SeatIndex


@dataclass(slots=True)
class Round:
    """The state of one round: who holds what, the trick in play, and the cards won."""

    hands: tuple[tuple[Card, ...], ...]
    dealer: SeatIndex
    leader: SeatIndex
    trick: tuple[Move, ...]
    won: tuple[tuple[Card, ...], ...]

    @classmethod
    def deal(cls, deck: Deck, dealer: SeatIndex, player_count: int) -> "Round":
        """FR-07, FR-11: deal the whole deck evenly, the seat after the dealer leads."""
        if player_count < 1 or DECK_SIZE % player_count != 0:
            raise ValueError(f"{DECK_SIZE} cards cannot be split among {player_count}")
        if dealer.value >= player_count:
            raise ValueError(f"dealer seat {dealer.value} is out of range")
        hands = tuple(deck.cards[seat::player_count] for seat in range(player_count))
        leader = SeatIndex((dealer.value + 1) % player_count)
        return cls(hands, dealer, leader, (), ((),) * player_count)
