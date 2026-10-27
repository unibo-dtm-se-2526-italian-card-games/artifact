"""Tests for the rule-based baseline strategy (FR-21, FR-22)."""

from random import Random

import pytest

from italian_card_games.ai.rule_based import RuleBasedStrategy
from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.cards import Card, Rank, Suit
from italian_card_games.engine.match import Match
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.ports import AIStrategy, Game
from italian_card_games.engine.values import Move, PlayerView, SeatIndex

MAX_MOVES = 10_000


def card(suit: Suit, rank: int) -> Card:
    return Card(suit, Rank(rank))


def move(seat: int, suit: Suit, rank: int) -> Move:
    return Move(SeatIndex(seat), card(suit, rank))


def play_to_the_end(game: Game, seed: int) -> Match:
    """Seat a rule-based strategy on every seat and check each move is legal."""
    match = Match(game, Random(seed))
    strategies = [
        RuleBasedStrategy(game, Random(seed * 4 + seat))
        for seat in range(game.player_count())
    ]
    for _ in range(MAX_MOVES):
        if match.is_over:
            return match
        seat = match.current_seat
        view = match.view_for(seat)
        chosen = strategies[seat.value].choose_move(view)
        assert chosen in game.legal_moves(view)
        match.play(chosen)
    raise AssertionError("the game did not end")


class TestPort:
    def test_fr21_the_strategy_is_an_ai_strategy(self) -> None:
        assert isinstance(RuleBasedStrategy(MatazzaRules(), Random(0)), AIStrategy)


class TestFullGames:
    @pytest.mark.parametrize("seed", range(20))
    def test_fr22_four_bots_finish_a_matazza_game_with_legal_moves(
        self, seed: int
    ) -> None:
        assert play_to_the_end(MatazzaRules(), seed).is_over

    @pytest.mark.parametrize("seed", range(20))
    def test_fr22_two_bots_finish_a_briscola_match_with_legal_moves(
        self, seed: int
    ) -> None:
        assert play_to_the_end(BriscolaRules(), seed).is_over


class TestBriscola:
    def test_fr22_last_to_play_wins_the_trick_with_the_cheapest_winning_card(
        self,
    ) -> None:
        view = PlayerView(
            seat=SeatIndex(1),
            hand=(
                card(Suit.COPPE, 1),
                card(Suit.COPPE, 3),
                card(Suit.SPADE, 2),
            ),
            trick=(move(0, Suit.COPPE, 4),),
            trump=Suit.DENARI,
        )
        strategy = RuleBasedStrategy(BriscolaRules(), Random(0))
        assert strategy.choose_move(view) == Move(SeatIndex(1), card(Suit.COPPE, 3))

    def test_fr22_last_to_play_uses_a_worthless_trump_rather_than_a_costly_card(
        self,
    ) -> None:
        view = PlayerView(
            seat=SeatIndex(1),
            hand=(card(Suit.COPPE, 1), card(Suit.DENARI, 2)),
            trick=(move(0, Suit.COPPE, 4),),
            trump=Suit.DENARI,
        )
        strategy = RuleBasedStrategy(BriscolaRules(), Random(0))
        assert strategy.choose_move(view) == Move(SeatIndex(1), card(Suit.DENARI, 2))

    def test_fr22_last_to_play_dumps_the_cheapest_card_when_it_cannot_win(
        self,
    ) -> None:
        view = PlayerView(
            seat=SeatIndex(1),
            hand=(
                card(Suit.SPADE, 1),
                card(Suit.SPADE, 4),
                card(Suit.SPADE, 3),
            ),
            trick=(move(0, Suit.COPPE, 3),),
            trump=Suit.DENARI,
        )
        strategy = RuleBasedStrategy(BriscolaRules(), Random(0))
        assert strategy.choose_move(view) == Move(SeatIndex(1), card(Suit.SPADE, 4))

    def test_fr22_leading_plays_the_cheapest_card(self) -> None:
        view = PlayerView(
            seat=SeatIndex(0),
            hand=(
                card(Suit.COPPE, 1),
                card(Suit.SPADE, 4),
                card(Suit.BASTONI, 3),
            ),
            trick=(),
            trump=Suit.DENARI,
        )
        strategy = RuleBasedStrategy(BriscolaRules(), Random(0))
        assert strategy.choose_move(view) == Move(SeatIndex(0), card(Suit.SPADE, 4))


class TestMatazza:
    def test_fr22_leading_plays_the_cheapest_card(self) -> None:
        view = PlayerView(
            seat=SeatIndex(0),
            hand=(
                card(Suit.COPPE, 3),
                card(Suit.SPADE, 4),
                card(Suit.BASTONI, 1),
            ),
            trick=(),
        )
        strategy = RuleBasedStrategy(MatazzaRules(), Random(0))
        assert strategy.choose_move(view) == Move(SeatIndex(0), card(Suit.SPADE, 4))

    def test_fr22_last_to_play_wins_with_the_cheapest_winning_card(self) -> None:
        view = PlayerView(
            seat=SeatIndex(3),
            hand=(
                card(Suit.COPPE, 1),
                card(Suit.COPPE, 10),
                card(Suit.COPPE, 4),
            ),
            trick=(
                move(0, Suit.COPPE, 5),
                move(1, Suit.COPPE, 7),
                move(2, Suit.COPPE, 6),
            ),
        )
        strategy = RuleBasedStrategy(MatazzaRules(), Random(0))
        assert strategy.choose_move(view) == Move(SeatIndex(3), card(Suit.COPPE, 10))

    def test_fr22_last_to_play_follows_the_suit_even_when_it_cannot_win(self) -> None:
        view = PlayerView(
            seat=SeatIndex(3),
            hand=(card(Suit.COPPE, 4), card(Suit.SPADE, 7)),
            trick=(
                move(0, Suit.COPPE, 3),
                move(1, Suit.COPPE, 7),
                move(2, Suit.COPPE, 6),
            ),
        )
        strategy = RuleBasedStrategy(MatazzaRules(), Random(0))
        assert strategy.choose_move(view) == Move(SeatIndex(3), card(Suit.COPPE, 4))


class TestTies:
    @staticmethod
    def tied_view() -> PlayerView:
        return PlayerView(
            seat=SeatIndex(0),
            hand=(card(Suit.COPPE, 4), card(Suit.SPADE, 5)),
            trick=(),
        )

    def test_fr22_equally_cheap_cards_are_both_chosen_over_different_seeds(
        self,
    ) -> None:
        chosen = {
            RuleBasedStrategy(MatazzaRules(), Random(seed))
            .choose_move(self.tied_view())
            .card
            for seed in range(20)
        }
        assert chosen == {card(Suit.COPPE, 4), card(Suit.SPADE, 5)}

    def test_nfr04_the_same_seed_makes_the_same_choice(self) -> None:
        first = RuleBasedStrategy(MatazzaRules(), Random(7))
        second = RuleBasedStrategy(MatazzaRules(), Random(7))
        assert first.choose_move(self.tied_view()) == second.choose_move(
            self.tied_view()
        )
