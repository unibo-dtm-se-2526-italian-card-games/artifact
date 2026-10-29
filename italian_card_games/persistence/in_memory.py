from italian_card_games.history.records import MatchId, MatchRecord


class InMemoryMatchRepository:
    """A MatchRepository kept in a dict. It does not survive a restart."""

    def __init__(self) -> None:
        self._records: dict[MatchId, MatchRecord] = {}

    def save(self, record: MatchRecord) -> None:
        if record.id in self._records:
            raise ValueError(f"match {record.id.value} is already stored")
        self._records[record.id] = record

    def get(self, match_id: MatchId) -> MatchRecord | None:
        return self._records.get(match_id)

    def history_of(self, nickname: str) -> list[MatchRecord]:
        played = [
            record
            for record in self._records.values()
            if any(p.name == nickname and not p.is_bot for p in record.participants)
        ]
        return sorted(played, key=lambda record: record.finished_at)
