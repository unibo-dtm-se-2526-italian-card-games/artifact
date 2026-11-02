from collections.abc import Callable

from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.ports import Game

# FR-01: the games on offer, by id. Adding a game means adding one line here.
GAMES: dict[str, Callable[[], Game]] = {
    "matazza": MatazzaRules,
    "briscola": BriscolaRules,
}
