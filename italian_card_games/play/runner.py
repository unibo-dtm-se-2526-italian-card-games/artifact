from italian_card_games.engine.events import DomainEvent
from italian_card_games.engine.values import Move
from italian_card_games.history.ports import MatchRepository
from italian_card_games.play.session import MatchSession


class MatchRunner:
    """FR-23, FR-27: plays moves in a session and lets its bots reply.

    A seat with a bot in the session is played by the bot; every other seat is a human
    that moves through `apply`. This is the same for one human or several. A finished
    match is saved once through the match repository.
    """

    def __init__(self, matches: MatchRepository) -> None:
        self._matches = matches

    def apply(self, session: MatchSession, move: Move) -> list[DomainEvent]:
        """Play one move, and save the record if it ended the match."""
        events = session.match.play(move)
        record = session.recorder.record(events)
        if record is not None:
            self._matches.save(record)
        return events

    def bots_reply(self, session: MatchSession) -> list[DomainEvent]:
        """Let the bots play until it is a human's turn or the match ends."""
        events: list[DomainEvent] = []
        match = session.match
        while not match.is_over and match.current_seat in session.bots:
            seat = match.current_seat
            move = session.bots[seat].choose_move(match.view_for(seat))
            events += self.apply(session, move)
        return events
