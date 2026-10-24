from dataclasses import dataclass
from enum import Enum

from italian_card_games.engine.cards import Card, Suit


@dataclass(frozen=True, slots=True)
class SeatIndex:
    """A position at the table, counted from 0."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError(f"a seat index cannot be negative, got {self.value}")


@dataclass(frozen=True, slots=True)
class Move:
    """A seat playing one card."""

    seat: SeatIndex
    card: Card


class Outcome(Enum):
    """How a seat ends a match."""

    WIN = "win"
    LOSS = "loss"


@dataclass(frozen=True, slots=True)
class Deal:
    """How a game deals a deck: a hand per seat, the stock left over, the trump suit."""

    hands: tuple[tuple[Card, ...], ...]
    stock: tuple[Card, ...]
    trump: Suit | None


@dataclass(frozen=True, slots=True)
class PlayerView:
    """What one seat may see: its hand, the moves on the table and the trump suit."""

    seat: SeatIndex
    hand: tuple[Card, ...]
    trick: tuple[Move, ...]
    trump: Suit | None = None

    def __post_init__(self) -> None:
        if len(set(self.hand)) != len(self.hand):
            raise ValueError("a hand cannot contain duplicate cards")
