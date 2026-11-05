from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from italian_card_games.engine.cards import MAX_RANK, MIN_RANK, Card, Rank, Suit
from italian_card_games.engine.events import (
    CardPlayed,
    DomainEvent,
    GameEnded,
    RoundScored,
    StandingPointsAwarded,
    TrickWon,
)
from italian_card_games.engine.values import Move
from italian_card_games.history.records import MatchRecord
from italian_card_games.history.statistics import GameStats
from italian_card_games.play.service import MatchStatus


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


class NewMatch(BaseModel):
    """The request to start an offline match; a seed makes the shuffle repeatable."""

    nickname: str
    game: str
    seed: int | None = None


class CardInfo(BaseModel):
    """A card of the Italian deck: its suit and its rank from 1 to 10."""

    suit: Suit
    rank: int = Field(ge=MIN_RANK, le=MAX_RANK)

    @classmethod
    def from_card(cls, card: Card) -> "CardInfo":
        return cls(suit=card.suit, rank=card.rank.value)

    def to_card(self) -> Card:
        return Card(self.suit, Rank(self.rank))


class MoveInfo(BaseModel):
    """A card played on the table by a seat."""

    seat: int
    card: CardInfo

    @classmethod
    def from_move(cls, move: Move) -> "MoveInfo":
        return cls(seat=move.seat.value, card=CardInfo.from_card(move.card))


class CardPlayedInfo(BaseModel):
    """A seat played a card."""

    type: Literal["card_played"] = "card_played"
    seat: int
    card: CardInfo


class TrickWonInfo(BaseModel):
    """A seat took a complete trick."""

    type: Literal["trick_won"] = "trick_won"
    winner: int


class RoundScoredInfo(BaseModel):
    """A round ended; each seat's score is an exact fraction such as "1/3"."""

    type: Literal["round_scored"] = "round_scored"
    scores: list[str]


class StandingPointsAwardedInfo(BaseModel):
    """Standing points earned in the round, and the totals after them."""

    type: Literal["standing_points_awarded"] = "standing_points_awarded"
    points: list[int]
    totals: list[int]


class GameEndedInfo(BaseModel):
    """The match is over, with the outcome of each seat."""

    type: Literal["game_ended"] = "game_ended"
    outcomes: list[str]


EventInfo = Annotated[
    CardPlayedInfo
    | TrickWonInfo
    | RoundScoredInfo
    | StandingPointsAwardedInfo
    | GameEndedInfo,
    Field(discriminator="type"),
]


def event_info(event: DomainEvent) -> EventInfo:
    """Turn a domain event into its API form."""
    if isinstance(event, CardPlayed):
        card = CardInfo.from_card(event.move.card)
        return CardPlayedInfo(seat=event.move.seat.value, card=card)
    if isinstance(event, TrickWon):
        return TrickWonInfo(winner=event.winner.value)
    if isinstance(event, RoundScored):
        return RoundScoredInfo(scores=[str(score) for score in event.scores])
    if isinstance(event, StandingPointsAwarded):
        return StandingPointsAwardedInfo(
            points=list(event.points), totals=list(event.totals)
        )
    if isinstance(event, GameEnded):
        return GameEndedInfo(outcomes=[o.value for o in event.outcomes])
    raise ValueError(f"no API form for {type(event).__name__}")


class MatchState(BaseModel):
    """An offline match as the human on seat 0 sees it, and what just happened."""

    id: str
    game: str
    seat: int
    hand: list[CardInfo]
    trick: list[MoveInfo]
    trump: Suit | None
    current_seat: int
    outcomes: list[str] | None
    events: list[EventInfo]

    @classmethod
    def from_status(cls, status: MatchStatus) -> "MatchState":
        outcomes = status.outcomes
        return cls(
            id=status.match_id.value,
            game=status.game_id,
            seat=status.view.seat.value,
            hand=[CardInfo.from_card(card) for card in status.view.hand],
            trick=[MoveInfo.from_move(move) for move in status.view.trick],
            trump=status.view.trump,
            current_seat=status.current_seat.value,
            outcomes=None if outcomes is None else [o.value for o in outcomes],
            events=[event_info(event) for event in status.events],
        )
