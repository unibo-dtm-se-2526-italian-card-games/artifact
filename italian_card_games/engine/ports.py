from fractions import Fraction
from typing import Protocol, runtime_checkable

from italian_card_games.engine.cards import Card, Deck, Suit
from italian_card_games.engine.values import (
    Deal,
    Move,
    Outcome,
    PlayerView,
    SeatIndex,
)


@runtime_checkable
class Game(Protocol):
    """The rules of one card game. Matazza and Briscola each provide their own."""

    def player_count(self) -> int:
        """How many seats a match of this game needs."""
        ...

    def deal(self, deck: Deck) -> Deal:
        """Split a shuffled deck into the hands, the stock and the trump suit."""
        ...

    def legal_moves(self, view: PlayerView) -> tuple[Move, ...]:
        """The moves the viewing seat is allowed to make right now."""
        ...

    def trick_winner(
        self, trick: tuple[Move, ...], trump: Suit | None = None
    ) -> SeatIndex:
        """The seat that wins a complete trick, given its moves in play order.

        `trump` is the trump suit of the round, None for games without one.
        """
        ...

    def round_scores(self, won: tuple[tuple[Card, ...], ...]) -> tuple[Fraction, ...]:
        """Each seat's score for a round, from the cards that seat won, by seat order."""
        ...

    def round_outcomes(
        self, scores: tuple[Fraction, ...]
    ) -> tuple[Outcome, ...] | None:
        """Each seat's outcome if this round alone ends the match, else None."""
        ...

    def standing_points(
        self, scores: tuple[Fraction, ...], holder: SeatIndex
    ) -> tuple[int, ...]:
        """The standing points each seat earns from a round, by seat order."""
        ...

    def round_holder(self, hands: tuple[tuple[Card, ...], ...]) -> SeatIndex | None:
        """The seat dealt the key card of the game, or None if the game has none."""
        ...

    def outcomes(self, standing_totals: tuple[int, ...]) -> tuple[Outcome, ...] | None:
        """Each seat's win or loss if the game is over after these totals, else None."""
        ...


@runtime_checkable
class AIStrategy(Protocol):
    """Anything that can choose a move from a player view: a bot, or a human's input."""

    def choose_move(self, view: PlayerView) -> Move:
        """Pick one of the legal moves available to the viewing seat."""
        ...
