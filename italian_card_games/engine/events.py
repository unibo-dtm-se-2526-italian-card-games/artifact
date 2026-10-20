from dataclasses import dataclass

from italian_card_games.engine.values import Move, SeatIndex


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """A fact that happened in a match. Other parts of the system react to it."""


@dataclass(frozen=True, slots=True)
class CardPlayed(DomainEvent):
    """FR-05: a seat played a card."""

    move: Move


@dataclass(frozen=True, slots=True)
class TrickWon(DomainEvent):
    """FR-10: a seat took a complete trick, whose moves are in play order."""

    winner: SeatIndex
    moves: tuple[Move, ...]
