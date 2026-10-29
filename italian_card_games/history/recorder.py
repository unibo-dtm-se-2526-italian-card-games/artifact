from collections.abc import Callable, Iterable
from datetime import datetime

from italian_card_games.engine.events import DomainEvent, GameEnded, RoundScored
from italian_card_games.engine.values import SeatIndex
from italian_card_games.history.records import (
    MatchId,
    MatchRecord,
    Participant,
    ParticipantRecord,
    RoundRecord,
)


class MatchRecorder:
    """FR-31: follows one match's events and builds its record when the match ends.

    Only RoundScored and GameEnded matter; every other event is ignored, so the
    standing points never reach the record. `clock` gives the finishing time.
    """

    def __init__(
        self,
        match_id: MatchId,
        game_type: str,
        participants: tuple[Participant, ...],
        clock: Callable[[], datetime],
    ) -> None:
        self._match_id = match_id
        self._game_type = game_type
        self._participants = participants
        self._clock = clock
        self._rounds: list[RoundRecord] = []
        self._record: MatchRecord | None = None

    def record(self, events: Iterable[DomainEvent]) -> MatchRecord | None:
        """Take the next events of the match; return the record once it has ended."""
        for event in events:
            if self._record is not None:
                raise ValueError("the match is over, no more events can be recorded")
            if isinstance(event, RoundScored):
                self._rounds.append(RoundRecord(event.scores))
            elif isinstance(event, GameEnded):
                self._record = self._build(event)
        return self._record

    def _build(self, ended: GameEnded) -> MatchRecord:
        if len(ended.outcomes) != len(self._participants):
            raise ValueError(
                f"{len(ended.outcomes)} outcomes for "
                f"{len(self._participants)} participants"
            )
        participants = tuple(
            ParticipantRecord(SeatIndex(seat), p.name, p.is_bot, outcome)
            for seat, (p, outcome) in enumerate(zip(self._participants, ended.outcomes))
        )
        return MatchRecord(
            self._match_id,
            self._game_type,
            self._clock(),
            participants,
            tuple(self._rounds),
        )
