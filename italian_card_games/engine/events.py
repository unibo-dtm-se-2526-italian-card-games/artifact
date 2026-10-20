from dataclasses import dataclass
from fractions import Fraction

from italian_card_games.engine.values import Move, Outcome, SeatIndex


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


@dataclass(frozen=True, slots=True)
class RoundScored(DomainEvent):
    """FR-12: a round ended, with each seat's score by seat order."""

    scores: tuple[Fraction, ...]


@dataclass(frozen=True, slots=True)
class StandingPointsAwarded(DomainEvent):
    """FR-14 to FR-16: the points each seat earned, and the totals after them."""

    points: tuple[int, ...]
    totals: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class GameEnded(DomainEvent):
    """FR-18, FR-19: the match is over, with one outcome per seat."""

    outcomes: tuple[Outcome, ...]
