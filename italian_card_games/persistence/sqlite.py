from datetime import UTC, datetime
from fractions import Fraction

from sqlalchemy import Engine, ForeignKey, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    selectinload,
)

from italian_card_games.engine.values import Outcome, SeatIndex
from italian_card_games.history.records import (
    MatchId,
    MatchRecord,
    ParticipantRecord,
    RoundRecord,
)


class _Base(DeclarativeBase):
    pass


class _ParticipantRow(_Base):
    __tablename__ = "participants"

    match_id: Mapped[str] = mapped_column(ForeignKey("matches.id"), primary_key=True)
    seat: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    is_bot: Mapped[bool]
    outcome: Mapped[str]


class _ScoreRow(_Base):
    """One seat's score in one round, kept exact as a fraction like "1/3"."""

    __tablename__ = "round_scores"

    match_id: Mapped[str] = mapped_column(ForeignKey("matches.id"), primary_key=True)
    round_number: Mapped[int] = mapped_column(primary_key=True)
    seat: Mapped[int] = mapped_column(primary_key=True)
    score: Mapped[str]


class _MatchRow(_Base):
    """A finished match. The time is stored in UTC, since SQLite keeps no time zone."""

    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(primary_key=True)
    game_type: Mapped[str]
    finished_at: Mapped[datetime] = mapped_column(index=True)
    participants: Mapped[list[_ParticipantRow]] = relationship(
        order_by=_ParticipantRow.seat, cascade="all, delete-orphan"
    )
    scores: Mapped[list[_ScoreRow]] = relationship(
        order_by=(_ScoreRow.round_number, _ScoreRow.seat),
        cascade="all, delete-orphan",
    )


class SqlMatchRepository:
    """FR-31: a MatchRepository on a SQL database through SQLAlchemy.

    The tables are created on the injected engine if they do not exist yet.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        _Base.metadata.create_all(engine)

    def save(self, record: MatchRecord) -> None:
        with Session(self._engine) as session:
            session.add(_to_row(record))
            try:
                session.commit()
            except IntegrityError as error:
                message = f"match {record.id.value} is already stored"
                raise ValueError(message) from error

    def get(self, match_id: MatchId) -> MatchRecord | None:
        with Session(self._engine) as session:
            row = session.get(_MatchRow, match_id.value)
            return None if row is None else _to_record(row)

    def history_of(self, nickname: str) -> list[MatchRecord]:
        query = (
            select(_MatchRow)
            .join(_MatchRow.participants)
            .where(_ParticipantRow.name == nickname, _ParticipantRow.is_bot.is_(False))
            .distinct()
            .order_by(_MatchRow.finished_at, _MatchRow.id)
            .options(
                selectinload(_MatchRow.participants), selectinload(_MatchRow.scores)
            )
        )
        with Session(self._engine) as session:
            return [_to_record(row) for row in session.scalars(query)]


def _to_row(record: MatchRecord) -> _MatchRow:
    return _MatchRow(
        id=record.id.value,
        game_type=record.game_type,
        finished_at=record.finished_at.astimezone(UTC).replace(tzinfo=None),
        participants=[
            _ParticipantRow(
                seat=p.seat.value, name=p.name, is_bot=p.is_bot, outcome=p.outcome.value
            )
            for p in record.participants
        ],
        scores=[
            _ScoreRow(round_number=number, seat=seat, score=str(score))
            for number, round_record in enumerate(record.rounds)
            for seat, score in enumerate(round_record.scores)
        ],
    )


def _to_record(row: _MatchRow) -> MatchRecord:
    rounds: dict[int, list[Fraction]] = {}
    for score in row.scores:
        rounds.setdefault(score.round_number, []).append(Fraction(score.score))
    return MatchRecord(
        MatchId(row.id),
        row.game_type,
        row.finished_at.replace(tzinfo=UTC),
        tuple(
            ParticipantRecord(SeatIndex(p.seat), p.name, p.is_bot, Outcome(p.outcome))
            for p in row.participants
        ),
        tuple(RoundRecord(tuple(scores)) for scores in rounds.values()),
    )
