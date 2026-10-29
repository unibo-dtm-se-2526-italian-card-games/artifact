from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction

from italian_card_games.engine.values import Outcome, SeatIndex


@dataclass(frozen=True, slots=True)
class MatchId:
    """The identity of a recorded match."""

    value: str


@dataclass(frozen=True, slots=True)
class Participant:
    """Who sat in a seat: a human's nickname, or a bot's name."""

    name: str
    is_bot: bool


@dataclass(frozen=True, slots=True)
class ParticipantRecord:
    """FR-31: one seat of a finished match, who sat in it and how it ended."""

    seat: SeatIndex
    name: str
    is_bot: bool
    outcome: Outcome


@dataclass(frozen=True, slots=True)
class RoundRecord:
    """FR-31: each seat's score in one round, by seat order."""

    scores: tuple[Fraction, ...]


@dataclass(frozen=True, slots=True)
class MatchRecord:
    """FR-31: a finished match: round scores and outcomes, no standing points."""

    id: MatchId
    game_type: str
    finished_at: datetime
    participants: tuple[ParticipantRecord, ...]
    rounds: tuple[RoundRecord, ...]

    def __post_init__(self) -> None:
        if not self.rounds:
            raise ValueError("a match record needs at least one round")
        seats = tuple(p.seat for p in self.participants)
        if seats != tuple(SeatIndex(i) for i in range(len(seats))):
            raise ValueError("participants must fill seats 0 to n-1 in order")
        for round_record in self.rounds:
            if len(round_record.scores) != len(seats):
                raise ValueError("every round needs one score per participant")
