"""Tests for the JoinCode value object (FR-27)."""

from random import Random

import pytest

from italian_card_games.lobby.join_code import ALPHABET, LENGTH, JoinCode


class TestJoinCodeValidation:
    def test_fr27_a_valid_code_keeps_its_value(self) -> None:
        assert JoinCode("ABC234").value == "ABC234"

    def test_fr27_a_code_is_six_characters_long(self) -> None:
        assert LENGTH == 6

    def test_fr27_surrounding_spaces_are_trimmed(self) -> None:
        assert JoinCode("  ABC234 ").value == "ABC234"

    def test_fr27_letter_case_is_ignored(self) -> None:
        assert JoinCode("abc234") == JoinCode("ABC234")
        assert JoinCode("abc234").value == "ABC234"

    @pytest.mark.parametrize("text", ["", "ABC23", "ABC2345"])
    def test_fr27_a_code_of_the_wrong_length_is_rejected(self, text: str) -> None:
        with pytest.raises(ValueError, match="6"):
            JoinCode(text)

    @pytest.mark.parametrize("text", ["ABC0DE", "ABC1DE", "ABCODE", "ABCIDE"])
    def test_fr27_look_alike_characters_are_rejected(self, text: str) -> None:
        with pytest.raises(ValueError, match="characters"):
            JoinCode(text)

    @pytest.mark.parametrize("text", ["ABC-DE", "ABC DE", "ABC!DE"])
    def test_fr27_other_characters_are_rejected(self, text: str) -> None:
        with pytest.raises(ValueError, match="characters"):
            JoinCode(text)

    def test_fr27_the_alphabet_has_no_look_alikes(self) -> None:
        assert not set("01OI") & set(ALPHABET)


class TestJoinCodeIdentity:
    def test_fr27_equal_codes_have_the_same_hash(self) -> None:
        assert hash(JoinCode("abc234")) == hash(JoinCode("ABC234"))

    def test_fr27_different_codes_are_not_equal(self) -> None:
        assert JoinCode("ABC234") != JoinCode("ABC235")

    def test_fr27_str_is_the_value(self) -> None:
        assert str(JoinCode("ABC234")) == "ABC234"


class TestJoinCodeRandom:
    def test_fr27_a_random_code_is_valid(self) -> None:
        code = JoinCode.random(Random(1))
        assert len(code.value) == LENGTH
        assert set(code.value) <= set(ALPHABET)

    def test_fr27_the_same_seed_gives_the_same_code(self) -> None:
        assert JoinCode.random(Random(7)) == JoinCode.random(Random(7))

    def test_fr27_different_seeds_give_different_codes(self) -> None:
        codes = {JoinCode.random(Random(seed)) for seed in range(20)}
        assert len(codes) > 1
