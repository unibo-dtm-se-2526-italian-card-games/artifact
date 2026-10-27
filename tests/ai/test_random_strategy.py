"""Tests for the random strategy, a second interchangeable AIStrategy (FR-21)."""

from random import Random

import pytest

from italian_card_games.ai.random_strategy import RandomStrategy
from italian_card_games.ai.rule_based import RuleBasedStrategy
from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.cards import Card, Rank, Suit
from italian_card_games.engine.match import Match
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.ports import AIStrategy, Game
from italian_card_games.engine.values import PlayerView, SeatIndex

MAX_MOVES = 10_000


def play_to_the_end(game: Game, seed: int) -> Match:
    """Seat a random strategy on seat 0 and a rule-based one on the others."""
    match = Match(game, Random(seed))
    strategies: list[AIStrategy] = [RandomStrategy(game, Random(seed))] + [
        RuleBasedStrategy(game, Random(seed * 4 + seat))
        for seat in range(1, game.player_count())
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


def a_view() -> PlayerView:
    return PlayerView(
        seat=SeatIndex(0),
        hand=(
            Card(Suit.COPPE, Rank(4)),
            Card(Suit.SPADE, Rank(5)),
            Card(Suit.BASTONI, Rank(1)),
        ),
        trick=(),
    )


class TestRandomStrategy:
    def test_fr21_the_strategy_is_an_ai_strategy(self) -> None:
        assert isinstance(RandomStrategy(MatazzaRules(), Random(0)), AIStrategy)

    @pytest.mark.parametrize("seed", range(10))
    def test_fr21_it_plays_legal_moves_through_a_matazza_game(self, seed: int) -> None:
        assert play_to_the_end(MatazzaRules(), seed).is_over

    @pytest.mark.parametrize("seed", range(10))
    def test_fr21_it_plays_legal_moves_through_a_briscola_match(
        self, seed: int
    ) -> None:
        assert play_to_the_end(BriscolaRules(), seed).is_over

    def test_fr21_every_legal_move_can_be_chosen_over_different_seeds(self) -> None:
        chosen = {
            RandomStrategy(MatazzaRules(), Random(seed)).choose_move(a_view())
            for seed in range(30)
        }
        assert chosen == set(MatazzaRules().legal_moves(a_view()))

    def test_nfr04_the_same_seed_makes_the_same_choice(self) -> None:
        first = RandomStrategy(MatazzaRules(), Random(7))
        second = RandomStrategy(MatazzaRules(), Random(7))
        assert first.choose_move(a_view()) == second.choose_move(a_view())
