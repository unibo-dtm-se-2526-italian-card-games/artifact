from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from italian_card_games.engine.values import Outcome
from italian_card_games.history.records import MatchRecord


@dataclass(frozen=True, slots=True)
class GameStats:
    """FR-33: a player's results in one game type."""

    played: int
    wins: int
    losses: int
    draws: int


class StatisticsService:
    """FR-33: computes a player's statistics from their match records."""

    def stats_for(
        self, nickname: str, records: Iterable[MatchRecord]
    ) -> dict[str, GameStats]:
        """Played, wins, losses and draws per game type, for a human's nickname.

        Only human seats count, so a bot with the same name is not the player.
        """
        results: dict[str, Counter[Outcome]] = {}
        for record in records:
            for participant in record.participants:
                if participant.name == nickname and not participant.is_bot:
                    counts = results.setdefault(record.game_type, Counter())
                    counts[participant.outcome] += 1
        return {
            game_type: GameStats(
                played=counts.total(),
                wins=counts[Outcome.WIN],
                losses=counts[Outcome.LOSS],
                draws=counts[Outcome.DRAW],
            )
            for game_type, counts in results.items()
        }
