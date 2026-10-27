"""Tests for the offline command-line game, one human against bots (FR-23)."""

from collections.abc import Iterator
from itertools import chain, repeat
from random import Random

import pytest

from italian_card_games.cli import main, play_offline
from italian_card_games.engine.briscola import BriscolaRules
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.ports import Game

BRISCOLA_CARDS_PER_PLAYER = 20


class ScriptedHuman:
    """Answers the prompts from a list, then keeps answering with the last choice."""

    def __init__(self, answers: list[str], then: str = "1") -> None:
        self._answers: Iterator[str] = chain(answers, repeat(then))
        self.prompts = 0

    def read(self, prompt: str) -> str:
        self.prompts += 1
        return next(self._answers)


def play(
    game: Game, human: ScriptedHuman, seed: int = 1
) -> tuple[list[str], bool, list[str]]:
    """Run an offline game and return its output, whether it ended and the outcomes."""
    lines: list[str] = []
    match = play_offline(game, human.read, lines.append, Random(seed))
    outcomes = match.outcomes
    expected = (
        [f"Seat {seat}: {outcome.value}" for seat, outcome in enumerate(outcomes)]
        if outcomes
        else []
    )
    return lines, match.is_over, expected


class TestOfflineBriscola:
    def test_fr23_a_human_and_one_bot_play_a_match_to_the_end(self) -> None:
        _, is_over, _ = play(BriscolaRules(), ScriptedHuman([]))
        assert is_over

    def test_fr23_the_human_is_asked_once_for_each_card_of_the_match(self) -> None:
        human = ScriptedHuman([])
        play(BriscolaRules(), human)
        assert human.prompts == BRISCOLA_CARDS_PER_PLAYER

    def test_fr23_the_human_sees_the_trump_hand_and_choices(self) -> None:
        lines, _, _ = play(BriscolaRules(), ScriptedHuman([]))
        assert any(line.startswith("Trump: ") for line in lines)
        assert any(line.startswith("Your hand: ") for line in lines)
        assert any(line.startswith("1) ") for line in lines)

    def test_fr23_the_moves_of_the_bot_are_announced(self) -> None:
        lines, _, _ = play(BriscolaRules(), ScriptedHuman([]))
        assert any(line.startswith("Seat 1 plays ") for line in lines)

    def test_fr19_the_outcome_of_each_seat_is_printed_at_the_end(self) -> None:
        lines, _, expected = play(BriscolaRules(), ScriptedHuman([]))
        assert "Game over" in lines
        assert expected
        assert all(line in lines for line in expected)


class TestOfflineMatazza:
    def test_fr23_a_human_and_three_bots_play_a_game_to_the_end(self) -> None:
        _, is_over, _ = play(MatazzaRules(), ScriptedHuman([]))
        assert is_over

    def test_fr23_matazza_has_no_trump_line(self) -> None:
        lines, _, _ = play(MatazzaRules(), ScriptedHuman([]))
        assert not any(line.startswith("Trump: ") for line in lines)

    def test_fr23_the_moves_of_all_three_bots_are_announced(self) -> None:
        lines, _, _ = play(MatazzaRules(), ScriptedHuman([]))
        for seat in (1, 2, 3):
            assert any(line.startswith(f"Seat {seat} plays ") for line in lines)

    def test_fr19_the_outcome_of_each_seat_is_printed_at_the_end(self) -> None:
        lines, _, expected = play(MatazzaRules(), ScriptedHuman([]))
        assert "Game over" in lines
        assert all(line in lines for line in expected)


class TestInput:
    def test_fr23_an_invalid_answer_is_refused_and_asked_again(self) -> None:
        human = ScriptedHuman(["x", "0", "99", ""])
        lines, is_over, _ = play(BriscolaRules(), human)
        assert is_over
        assert sum(line.startswith("Please enter a number") for line in lines) == 4
        assert human.prompts == BRISCOLA_CARDS_PER_PLAYER + 4


class TestMain:
    @staticmethod
    def run(argv: list[str]) -> tuple[int, list[str]]:
        lines: list[str] = []
        status = main(argv, ScriptedHuman([]).read, lines.append)
        return status, lines

    def test_fr23_the_game_option_chooses_briscola(self) -> None:
        status, lines = self.run(["--game", "briscola", "--seed", "3"])
        assert status == 0
        assert any(line.startswith("Trump: ") for line in lines)
        assert "Game over" in lines

    def test_fr23_the_game_option_chooses_matazza(self) -> None:
        status, lines = self.run(["--game", "matazza", "--seed", "3"])
        assert status == 0
        assert any(line.startswith("Seat 3 plays ") for line in lines)

    def test_fr23_matazza_is_the_default_game(self) -> None:
        _, lines = self.run(["--seed", "3"])
        assert any(line.startswith("Seat 3 plays ") for line in lines)

    def test_fr23_a_game_without_a_seed_still_runs_to_the_end(self) -> None:
        status, lines = self.run(["--game", "briscola"])
        assert status == 0
        assert "Game over" in lines

    def test_nfr04_the_seed_option_makes_the_game_reproducible(self) -> None:
        _, first = self.run(["--seed", "9"])
        _, second = self.run(["--seed", "9"])
        assert first == second

    def test_fr23_an_unknown_game_is_refused(self) -> None:
        with pytest.raises(SystemExit) as refused:
            self.run(["--game", "scopa"])
        assert refused.value.code == 2


class TestReproducibility:
    def test_nfr04_the_same_seed_gives_the_same_game_output(self) -> None:
        first, _, _ = play(MatazzaRules(), ScriptedHuman([]), seed=5)
        second, _, _ = play(MatazzaRules(), ScriptedHuman([]), seed=5)
        assert first == second

    def test_nfr04_different_seeds_give_different_games(self) -> None:
        first, _, _ = play(MatazzaRules(), ScriptedHuman([]), seed=5)
        second, _, _ = play(MatazzaRules(), ScriptedHuman([]), seed=6)
        assert first != second
