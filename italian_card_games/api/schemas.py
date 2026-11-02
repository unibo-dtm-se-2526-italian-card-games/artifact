from datetime import datetime

from pydantic import BaseModel

from italian_card_games.history.records import MatchRecord
from italian_card_games.history.statistics import GameStats


class GameInfo(BaseModel):
    """A game the server can play."""

    id: str
    player_count: int


class NewPlayer(BaseModel):
    """The request to register a nickname."""

    nickname: str


class PlayerInfo(BaseModel):
    """A registered player, with the nickname as they chose it."""

    nickname: str


class ParticipantInfo(BaseModel):
    """Who sat in one seat of a finished match and how they ended."""

    seat: int
    name: str
    is_bot: bool
    outcome: str


class RoundInfo(BaseModel):
    """The score of each seat in one round, as exact fractions such as "1/3"."""

    scores: list[str]


class MatchInfo(BaseModel):
    """A finished match, with the finishing time in UTC."""

    id: str
    game_type: str
    finished_at: datetime
    participants: list[ParticipantInfo]
    rounds: list[RoundInfo]

    @classmethod
    def from_record(cls, record: MatchRecord) -> "MatchInfo":
        return cls(
            id=record.id.value,
            game_type=record.game_type,
            finished_at=record.finished_at,
            participants=[
                ParticipantInfo(
                    seat=p.seat.value,
                    name=p.name,
                    is_bot=p.is_bot,
                    outcome=p.outcome.value,
                )
                for p in record.participants
            ],
            rounds=[
                RoundInfo(scores=[str(score) for score in round_record.scores])
                for round_record in record.rounds
            ],
        )


class GameStatsInfo(BaseModel):
    """A player's results in one game type."""

    played: int
    wins: int
    losses: int
    draws: int

    @classmethod
    def from_stats(cls, stats: GameStats) -> "GameStatsInfo":
        return cls(
            played=stats.played,
            wins=stats.wins,
            losses=stats.losses,
            draws=stats.draws,
        )
