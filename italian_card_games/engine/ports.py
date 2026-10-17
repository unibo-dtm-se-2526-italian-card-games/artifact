from fractions import Fraction
from typing import Protocol, runtime_checkable

from italian_card_games.engine.cards import Card
from italian_card_games.engine.values import Move, PlayerView, SeatIndex


@runtime_checkable
class Game(Protocol):
    """The rules of one card game. Matazza and Briscola each provide their own."""

    def player_count(self) -> int:
        """How many seats a match of this game needs."""
        ...

    def legal_moves(self, view: PlayerView) -> tuple[Move, ...]:
        """The moves the viewing seat is allowed to make right now."""
        ...

    def trick_winner(self, trick: tuple[Move, ...]) -> SeatIndex:
        """The seat that wins a complete trick, given its moves in play order."""
        ...

    def round_scores(self, won: tuple[tuple[Card, ...], ...]) -> tuple[Fraction, ...]:
        """Each seat's score for a round, from the cards that seat won, by seat order."""
        ...

    def solo_winner(self, scores: tuple[Fraction, ...]) -> SeatIndex | None:
        """The seat that wins the whole game from these round scores, or None."""
        ...


@runtime_checkable
class AIStrategy(Protocol):
    """Anything that can choose a move from a player view: a bot, or a human's input."""

    def choose_move(self, view: PlayerView) -> Move:
        """Pick one of the legal moves available to the viewing seat."""
        ...
