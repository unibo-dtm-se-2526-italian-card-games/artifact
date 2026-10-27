from collections.abc import Callable
from random import Random

from italian_card_games.ai.rule_based import RuleBasedStrategy
from italian_card_games.engine.events import (
    CardPlayed,
    DomainEvent,
    RoundScored,
    StandingPointsAwarded,
    TrickWon,
)
from italian_card_games.engine.match import Match
from italian_card_games.engine.ports import AIStrategy, Game
from italian_card_games.engine.values import Move, PlayerView, SeatIndex

HUMAN_SEAT = SeatIndex(0)


def play_offline(
    game: Game,
    read: Callable[[str], str],
    write: Callable[[str], None],
    rng: Random,
) -> Match:
    """FR-23: one human on seat 0 plays against rule-based bots until the match ends.

    `read` asks the human a question and returns the answer, `write` shows a line.
    """
    match = Match(game, rng)
    bots: dict[SeatIndex, AIStrategy] = {
        SeatIndex(seat): RuleBasedStrategy(game, rng)
        for seat in range(1, game.player_count())
    }
    while not match.is_over:
        seat = match.current_seat
        view = match.view_for(seat)
        if seat == HUMAN_SEAT:
            move = _ask_human(game, view, read, write)
        else:
            move = bots[seat].choose_move(view)
        for event in match.play(move):
            _show(event, write)
    _show_outcomes(match, write)
    return match


def _ask_human(
    game: Game,
    view: PlayerView,
    read: Callable[[str], str],
    write: Callable[[str], None],
) -> Move:
    choices = game.legal_moves(view)
    table = ", ".join(f"{move.card} (seat {move.seat.value})" for move in view.trick)
    write(f"On the table: {table or 'nothing'}")
    if view.trump is not None:
        write(f"Trump: {view.trump.name}")
    write(f"Your hand: {', '.join(str(card) for card in view.hand)}")
    for number, move in enumerate(choices, start=1):
        write(f"{number}) {move.card}")
    while True:
        answer = read("Choose a card: ").strip()
        if answer.isdecimal() and 1 <= int(answer) <= len(choices):
            return choices[int(answer) - 1]
        write(f"Please enter a number between 1 and {len(choices)}")


def _show(event: DomainEvent, write: Callable[[str], None]) -> None:
    if isinstance(event, CardPlayed):
        seat = event.move.seat
        who = "You play" if seat == HUMAN_SEAT else f"Seat {seat.value} plays"
        write(f"{who} {event.move.card}")
    elif isinstance(event, TrickWon):
        write(f"Seat {event.winner.value} wins the trick")
    elif isinstance(event, RoundScored):
        write(f"Round scores: {_by_seat(event.scores)}")
    elif isinstance(event, StandingPointsAwarded):
        write(f"Standing points: {_by_seat(event.totals)}")


def _by_seat(values: tuple[object, ...]) -> str:
    return ", ".join(f"seat {seat}: {value}" for seat, value in enumerate(values))


def _show_outcomes(match: Match, write: Callable[[str], None]) -> None:
    write("Game over")
    for seat, outcome in enumerate(match.outcomes or ()):
        write(f"Seat {seat}: {outcome.value}")
