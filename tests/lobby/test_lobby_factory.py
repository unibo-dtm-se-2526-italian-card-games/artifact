"""Tests for the LobbyFactory (FR-27)."""

from random import Random

from italian_card_games.lobby.factory import LobbyFactory
from italian_card_games.lobby.join_code import JoinCode
from italian_card_games.lobby.nickname import Nickname
from italian_card_games.lobby.seat import Occupant

ANNA = Nickname("Anna")


class TestLobbyFactory:
    def test_fr27_the_lobby_gets_the_code_from_the_generator(self) -> None:
        factory = LobbyFactory(lambda: JoinCode("ABC234"))
        lobby = factory.create("matazza", 4, ANNA)
        assert lobby.code == JoinCode("ABC234")

    def test_fr27_the_lobby_has_the_given_game_and_seat_count(self) -> None:
        factory = LobbyFactory(lambda: JoinCode("ABC234"))
        lobby = factory.create("briscola", 2, ANNA)
        assert lobby.game_id == "briscola"
        assert len(lobby.seats) == 2

    def test_fr27_the_creator_takes_seat_zero(self) -> None:
        factory = LobbyFactory(lambda: JoinCode("ABC234"))
        lobby = factory.create("matazza", 4, ANNA)
        assert lobby.creator == ANNA
        assert lobby.seats[0].occupant == Occupant.human(ANNA)

    def test_fr27_each_lobby_asks_the_generator_for_a_fresh_code(self) -> None:
        codes = iter([JoinCode("AAAAAA"), JoinCode("BBBBBB")])
        factory = LobbyFactory(lambda: next(codes))
        first = factory.create("matazza", 4, ANNA)
        second = factory.create("matazza", 4, Nickname("Bruno"))
        assert (first.code, second.code) == (JoinCode("AAAAAA"), JoinCode("BBBBBB"))

    def test_fr27_a_seeded_random_gives_a_reproducible_code(self) -> None:
        rng = Random(3)
        factory = LobbyFactory(lambda: JoinCode.random(rng))
        expected = JoinCode.random(Random(3))
        assert factory.create("matazza", 4, ANNA).code == expected
