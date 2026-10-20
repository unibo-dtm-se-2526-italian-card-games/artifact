from dataclasses import dataclass
from fractions import Fraction
from random import Random

from italian_card_games.engine.cards import DECK_SIZE, Card, Deck, DeckFactory
from italian_card_games.engine.events import CardPlayed, DomainEvent, TrickWon
from italian_card_games.engine.ports import Game
from italian_card_games.engine.values import Move, Outcome, PlayerView, SeatIndex


class IllegalMoveError(ValueError):
    """A move that the rules or the turn order do not allow."""


@dataclass(slots=True)
class Round:
    """The state of one round: who holds what, the trick in play, and the cards won."""

    hands: tuple[tuple[Card, ...], ...]
    dealer: SeatIndex
    leader: SeatIndex
    trick: tuple[Move, ...]
    won: tuple[tuple[Card, ...], ...]

    @classmethod
    def deal(cls, deck: Deck, dealer: SeatIndex, player_count: int) -> "Round":
        """FR-07, FR-11: deal the whole deck evenly, the seat after the dealer leads."""
        if player_count < 1 or DECK_SIZE % player_count != 0:
            raise ValueError(f"{DECK_SIZE} cards cannot be split among {player_count}")
        if dealer.value >= player_count:
            raise ValueError(f"dealer seat {dealer.value} is out of range")
        hands = tuple(deck.cards[seat::player_count] for seat in range(player_count))
        leader = SeatIndex((dealer.value + 1) % player_count)
        return cls(hands, dealer, leader, (), ((),) * player_count)

    @property
    def current_seat(self) -> SeatIndex:
        """The seat that must play next: the leader, then each seat in turn."""
        if not self.trick:
            return self.leader
        return SeatIndex((self.trick[-1].seat.value + 1) % len(self.hands))

    @property
    def is_over(self) -> bool:
        """FR-12: the round ends when every card has been played."""
        return not any(self.hands)

    def view_for(self, seat: SeatIndex) -> PlayerView:
        """FR-06: what one seat may see, its own hand and the trick in play."""
        if seat.value >= len(self.hands):
            raise ValueError(f"seat {seat.value} is out of range")
        return PlayerView(seat, self.hands[seat.value], self.trick)

    def scores(self, game: Game) -> tuple[Fraction, ...]:
        """FR-12: each seat's score from the cards it won, once the round is over."""
        if not self.is_over:
            raise ValueError("the round is not over yet")
        return game.round_scores(self.won)

    def play(self, move: Move, game: Game) -> None:
        """FR-05, FR-09, FR-10: play a card, and resolve the trick when it is complete.

        An illegal move raises IllegalMoveError and leaves the round unchanged.
        """
        seat = move.seat
        if seat != self.current_seat:
            raise IllegalMoveError(f"it is seat {self.current_seat.value}'s turn")
        view = self.view_for(seat)
        if move not in game.legal_moves(view):
            raise IllegalMoveError(f"{move.card} is not a legal move for this seat")
        hands = list(self.hands)
        hands[seat.value] = tuple(c for c in hands[seat.value] if c != move.card)
        trick = self.trick + (move,)
        if len(trick) < len(hands):
            self.hands, self.trick = tuple(hands), trick
            return
        winner = game.trick_winner(trick)
        won = list(self.won)
        won[winner.value] += tuple(m.card for m in trick)
        self.hands, self.won = tuple(hands), tuple(won)
        self.leader, self.trick = winner, ()


class Match:
    """One play-through of a game: the rounds, the standing points and the outcome."""

    def __init__(self, game: Game, rng: Random) -> None:
        self._game = game
        self._rng = rng
        self._standing_totals = (0,) * game.player_count()
        self._outcomes: tuple[Outcome, ...] | None = None
        self.round = self._deal(SeatIndex(0))

    @property
    def current_seat(self) -> SeatIndex:
        """The seat that must play next."""
        return self.round.current_seat

    @property
    def standing_totals(self) -> tuple[int, ...]:
        """The standing points each seat has accumulated, by seat order."""
        return self._standing_totals

    @property
    def outcomes(self) -> tuple[Outcome, ...] | None:
        """FR-19: each seat's win or loss once the match is over, else None."""
        return self._outcomes

    @property
    def is_over(self) -> bool:
        return self._outcomes is not None

    def view_for(self, seat: SeatIndex) -> PlayerView:
        """FR-06: what one seat may see."""
        return self.round.view_for(seat)

    def play(self, move: Move) -> list[DomainEvent]:
        """FR-04, FR-05, FR-10: play a card and report what happened.

        An illegal move raises IllegalMoveError and leaves the match unchanged.
        """
        trick = self.round.trick + (move,)
        self.round.play(move, self._game)
        events: list[DomainEvent] = [CardPlayed(move)]
        if len(trick) == self._game.player_count():
            events.append(TrickWon(self.round.leader, trick))
        return events

    def _deal(self, dealer: SeatIndex) -> Round:
        """FR-02, NFR-04: deal a freshly shuffled deck from the injected random source."""
        deck = DeckFactory.shuffled(self._rng)
        return Round.deal(deck, dealer, self._game.player_count())
