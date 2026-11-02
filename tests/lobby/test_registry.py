"""Tests for NicknameRegistry (FR-26)."""

import pytest

from italian_card_games.lobby.nickname import Nickname
from italian_card_games.lobby.player import RegisteredPlayer
from italian_card_games.lobby.registry import NicknameRegistry, NicknameTakenError
from italian_card_games.persistence.in_memory import InMemoryPlayerRepository


@pytest.fixture
def registry() -> NicknameRegistry:
    return NicknameRegistry(InMemoryPlayerRepository())


class TestRegister:
    def test_fr26_registering_a_new_nickname_returns_the_player(
        self, registry: NicknameRegistry
    ) -> None:
        player = registry.register(Nickname("anna"))
        assert player == RegisteredPlayer(Nickname("anna"))

    def test_fr26_a_registered_player_can_be_found_afterwards(
        self, registry: NicknameRegistry
    ) -> None:
        registry.register(Nickname("anna"))
        assert registry.find(Nickname("anna")) == RegisteredPlayer(Nickname("anna"))

    def test_fr26_a_taken_nickname_is_rejected_with_an_explicit_error(
        self, registry: NicknameRegistry
    ) -> None:
        registry.register(Nickname("anna"))
        with pytest.raises(NicknameTakenError, match="anna"):
            registry.register(Nickname("anna"))

    def test_fr26_a_nickname_differing_only_in_case_is_rejected(
        self, registry: NicknameRegistry
    ) -> None:
        registry.register(Nickname("Anna"))
        with pytest.raises(NicknameTakenError, match="ANNA"):
            registry.register(Nickname("ANNA"))

    def test_fr26_a_rejected_registration_keeps_the_first_casing(
        self, registry: NicknameRegistry
    ) -> None:
        registry.register(Nickname("Anna"))
        with pytest.raises(NicknameTakenError):
            registry.register(Nickname("ANNA"))
        found = registry.find(Nickname("anna"))
        assert found is not None
        assert found.nickname.value == "Anna"

    def test_fr26_the_taken_error_is_a_value_error(self) -> None:
        assert issubclass(NicknameTakenError, ValueError)

    def test_fr26_different_nicknames_can_all_register(
        self, registry: NicknameRegistry
    ) -> None:
        registry.register(Nickname("anna"))
        registry.register(Nickname("bruno"))
        assert registry.find(Nickname("bruno")) is not None


class TestFind:
    def test_fr26_an_unregistered_nickname_is_not_found(
        self, registry: NicknameRegistry
    ) -> None:
        assert registry.find(Nickname("anna")) is None

    def test_fr26_find_ignores_case(self, registry: NicknameRegistry) -> None:
        registry.register(Nickname("DaVide"))
        found = registry.find(Nickname("davide"))
        assert found is not None
        assert found.nickname.value == "DaVide"
