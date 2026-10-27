from random import Random

from italian_card_games.engine.ports import Game
from italian_card_games.engine.values import Move, PlayerView


class RandomStrategy:
    """FR-21: plays any legal move at random, using the injected random source."""

    def __init__(self, game: Game, rng: Random) -> None:
        self._game = game
        self._rng = rng

    def choose_move(self, view: PlayerView) -> Move:
        return self._rng.choice(self._game.legal_moves(view))
