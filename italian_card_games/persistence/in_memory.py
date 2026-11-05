from italian_card_games.history.records import MatchId, MatchRecord
from italian_card_games.lobby.nickname import Nickname
from italian_card_games.lobby.player import RegisteredPlayer
from italian_card_games.play.session import MatchSession


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


class InMemoryPlayerRepository:
    """A PlayerRepository kept in a dict. It does not survive a restart."""

    def __init__(self) -> None:
        # Nickname hashes by its lower-case key, so the lookup ignores case.
        self._players: dict[Nickname, RegisteredPlayer] = {}

    def add(self, player: RegisteredPlayer) -> None:
        if player.nickname in self._players:
            raise ValueError(f"nickname {player.nickname.value} is already taken")
        self._players[player.nickname] = player

    def get(self, nickname: Nickname) -> RegisteredPlayer | None:
        return self._players.get(nickname)


class InMemorySessionStore:
    """A SessionStore kept in a dict. Matches in play do not survive a restart."""

    def __init__(self) -> None:
        self._sessions: dict[MatchId, MatchSession] = {}

    def add(self, match_id: MatchId, session: MatchSession) -> None:
        if match_id in self._sessions:
            raise ValueError(f"session {match_id.value} is already stored")
        self._sessions[match_id] = session

    def get(self, match_id: MatchId) -> MatchSession | None:
        return self._sessions.get(match_id)
