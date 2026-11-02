"""Tests for the Nickname value object (FR-26)."""

import pytest

from italian_card_games.lobby.nickname import Nickname


class TestNicknameValidation:
    def test_fr26_a_valid_nickname_keeps_its_value(self) -> None:
        assert Nickname("Davide_92").value == "Davide_92"

    def test_fr26_surrounding_spaces_are_trimmed(self) -> None:
        assert Nickname("  anna  ").value == "anna"

    @pytest.mark.parametrize("text", ["a-b", "A_1", "x" * 3, "x" * 20])
    def test_fr26_letters_digits_underscore_and_hyphen_are_allowed(
        self, text: str
    ) -> None:
        assert Nickname(text).value == text

    @pytest.mark.parametrize("text", ["", "   ", "ab", "  ab  "])
    def test_fr26_a_nickname_needs_at_least_three_characters(self, text: str) -> None:
        with pytest.raises(ValueError, match="3"):
            Nickname(text)

    def test_fr26_a_nickname_has_at_most_twenty_characters(self) -> None:
        with pytest.raises(ValueError, match="20"):
            Nickname("x" * 21)

    @pytest.mark.parametrize("text", ["anna rossi", "anna!", "a/b/c", "anna@home"])
    def test_fr26_other_characters_are_rejected(self, text: str) -> None:
        with pytest.raises(ValueError, match="letters"):
            Nickname(text)


class TestNicknameIdentity:
    def test_fr26_nicknames_differing_only_in_case_are_equal(self) -> None:
        assert Nickname("Davide") == Nickname("davide")

    def test_fr26_equal_nicknames_have_the_same_hash(self) -> None:
        assert len({Nickname("Davide"), Nickname("DAVIDE")}) == 1

    def test_fr26_different_nicknames_are_not_equal(self) -> None:
        assert Nickname("anna") != Nickname("anne")

    def test_fr26_the_chosen_casing_is_kept_for_display(self) -> None:
        assert str(Nickname("DaVide")) == "DaVide"

    def test_fr26_the_key_ignores_case_and_is_used_for_uniqueness(self) -> None:
        assert Nickname("DaVide").key == "davide"

    def test_fr26_a_nickname_is_immutable(self) -> None:
        nickname = Nickname("anna")
        with pytest.raises(AttributeError):
            nickname.value = "bob"  # type: ignore[misc]

    def test_fr26_a_nickname_is_not_equal_to_a_plain_string(self) -> None:
        assert Nickname("anna") != "anna"
