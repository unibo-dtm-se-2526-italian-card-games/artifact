from dataclasses import dataclass

from italian_card_games.engine.cards import DECK_SIZE, Card, Deck
from italian_card_games.engine.ports import Game
from italian_card_games.engine.values import Move, PlayerView, SeatIndex


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

    def play(self, move: Move, game: Game) -> None:
        """FR-05, FR-09, FR-10: play a card, and resolve the trick when it is complete.

        An illegal move raises IllegalMoveError and leaves the round unchanged.
        """
        seat = move.seat
        if seat != self.current_seat:
            raise IllegalMoveError(f"it is seat {self.current_seat.value}'s turn")
        view = PlayerView(seat, self.hands[seat.value], self.trick)
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
