from fractions import Fraction
from random import Random

from italian_card_games.engine.cards import Card
from italian_card_games.engine.ports import Game
from italian_card_games.engine.values import Move, PlayerView


class RuleBasedStrategy:
    """FR-22: the baseline bot, the same for every game.

    Last to play, it wins the trick with the cheapest card that wins it, or gives away
    the cheapest card if none does. Earlier in the trick it plays the cheapest card.
    A card is cheap when the game scores it low; equally cheap cards are drawn at
    random from the injected source, so a seeded match stays reproducible.
    """

    def __init__(self, game: Game, rng: Random) -> None:
        self._game = game
        self._rng = rng

    def choose_move(self, view: PlayerView) -> Move:
        moves = self._game.legal_moves(view)
        if len(view.trick) == self._game.player_count() - 1:
            winning = tuple(move for move in moves if self._wins(view, move))
            moves = winning or moves
        return self._cheapest(moves)

    def _wins(self, view: PlayerView, move: Move) -> bool:
        trick = (*view.trick, move)
        return self._game.trick_winner(trick, view.trump) == view.seat

    def _cheapest(self, moves: tuple[Move, ...]) -> Move:
        values = [self._value(move.card) for move in moves]
        cheapest = min(values)
        return self._rng.choice(
            [move for move, value in zip(moves, values) if value == cheapest]
        )

    def _value(self, card: Card) -> Fraction:
        """What the game scores for winning this card alone."""
        piles = tuple(
            (card,) if seat == 0 else () for seat in range(self._game.player_count())
        )
        return self._game.round_scores(piles)[0]
