from italian_card_games.engine.values import SeatIndex
from italian_card_games.lobby.join_code import JoinCode
from italian_card_games.lobby.nickname import Nickname
from italian_card_games.lobby.seat import Occupant, Seat

MIN_SEATS = 2


class LobbyError(ValueError):
    """A lobby rule was broken."""


class AlreadyJoinedError(LobbyError):
    """The nickname already holds a seat in this lobby."""


class LobbyFullError(LobbyError):
    """Every seat of the lobby is taken."""


class LobbyStartedError(LobbyError):
    """The match has already started, so the lobby no longer changes."""


class NotCreatorError(LobbyError):
    """Only the creator of the lobby can start the match."""


class NotInLobbyError(LobbyError):
    """The nickname holds no seat in this lobby."""


class Lobby:
    """FR-27, FR-28: a waiting room where seats are filled before a match starts.

    The creator takes seat 0. Others join with the lobby's code and take the lowest
    empty seat. Only the creator starts the match, and empty seats then fill with
    bots. If the creator leaves, the next human by seat order becomes the creator.
    The lobby knows no game rules: it is given the game id and the seat count.
    """

    def __init__(
        self, code: JoinCode, game_id: str, player_count: int, creator: Nickname
    ) -> None:
        if player_count < MIN_SEATS:
            raise ValueError(f"a lobby needs at least {MIN_SEATS} seats")
        self.code = code
        self.game_id = game_id
        self._seats = [Seat(SeatIndex(i)) for i in range(player_count)]
        self._seats[0].occupant = Occupant.human(creator)
        self._creator: Nickname | None = creator
        self._started = False

    @property
    def seats(self) -> tuple[Seat, ...]:
        return tuple(self._seats)

    @property
    def creator(self) -> Nickname | None:
        """The human who may start the match, or None if no human is left."""
        return self._creator

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def is_empty(self) -> bool:
        """True when no human holds a seat."""
        return self._creator is None

    def join(self, nickname: Nickname) -> SeatIndex:
        """Take the lowest empty seat and return its position."""
        self._ensure_not_started()
        if self._seat_of(nickname) is not None:
            raise AlreadyJoinedError(f"{nickname} is already in this lobby")
        for seat in self._seats:
            if seat.is_empty:
                seat.occupant = Occupant.human(nickname)
                return seat.position
        raise LobbyFullError("the lobby is full")

    def leave(self, nickname: Nickname) -> None:
        """Free the seat of this nickname, passing the creator role on if needed."""
        self._ensure_not_started()
        seat = self._seat_of(nickname)
        if seat is None:
            raise NotInLobbyError(f"{nickname} is not in this lobby")
        seat.occupant = None
        if nickname == self._creator:
            self._creator = self._first_human()

    def fill_with_bots(self) -> None:
        """Put a bot on every empty seat."""
        self._ensure_not_started()
        for seat in self._seats:
            if seat.is_empty:
                seat.occupant = Occupant.bot()

    def start(self, requested_by: Nickname) -> tuple[Occupant, ...]:
        """Fill the empty seats with bots and return the occupants in seat order."""
        self._ensure_not_started()
        if requested_by != self._creator:
            raise NotCreatorError("only the creator can start the match")
        self.fill_with_bots()
        self._started = True
        return tuple(seat.occupant for seat in self._seats if seat.occupant is not None)

    def _ensure_not_started(self) -> None:
        if self._started:
            raise LobbyStartedError("the match has already started")

    def _seat_of(self, nickname: Nickname) -> Seat | None:
        for seat in self._seats:
            if seat.occupant is not None and seat.occupant.nickname == nickname:
                return seat
        return None

    def _first_human(self) -> Nickname | None:
        for seat in self._seats:
            if seat.occupant is not None and seat.occupant.nickname is not None:
                return seat.occupant.nickname
        return None
