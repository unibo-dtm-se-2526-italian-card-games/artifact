from dataclasses import dataclass

from italian_card_games.engine.match import Match
from italian_card_games.engine.ports import AIStrategy
from italian_card_games.engine.values import SeatIndex
from italian_card_games.history.recorder import MatchRecorder


@dataclass(slots=True)
class MatchSession:
    """FR-23, FR-36: one offline match in play, with its bots and its recorder.

    The human sits on seat 0; `bots` holds one strategy for each other seat.
    """

    game_id: str
    match: Match
    bots: dict[SeatIndex, AIStrategy]
    recorder: MatchRecorder
