"""Tests for the offline match routes: create, read and play (FR-23, FR-36)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

Json = dict[str, Any]
SUITS = ("denari", "coppe", "spade", "bastoni")


def register(client: TestClient, nickname: str = "Davide") -> None:
    response = client.post("/api/v1/players", json={"nickname": nickname})
    assert response.status_code == 201


def create(
    client: TestClient,
    game: str = "matazza",
    seed: int | None = 1,
    nickname: str = "Davide",
) -> Json:
    body = {"nickname": nickname, "game": game, "seed": seed}
    response = client.post("/api/v1/matches", json=body)
    assert response.status_code == 201
    state: Json = response.json()
    return state


def play(client: TestClient, match_id: str, card: Json) -> Any:
    return client.post(f"/api/v1/matches/{match_id}/moves", json=card)


def play_to_the_end(client: TestClient, state: Json) -> Json:
    """Play the first card of the hand that the rules accept, until the match ends."""
    while state["outcomes"] is None:
        for card in state["hand"]:
            response = play(client, state["id"], card)
            if response.status_code == 200:
                state = response.json()
                break
        else:
            pytest.fail("no card of the hand was accepted")
    return state


def card_not_in(hand: list[Json]) -> Json:
    return next(
        {"suit": suit, "rank": rank}
        for suit in SUITS
        for rank in range(1, 11)
        if {"suit": suit, "rank": rank} not in hand
    )


class TestCreate:
    def test_fr23_matazza_starts_with_the_three_bots_already_played(
        self, client: TestClient
    ) -> None:
        register(client)

        state = create(client, "matazza")

        assert state["id"] == "m1"
        assert state["game"] == "matazza"
        assert state["seat"] == 0
        assert state["current_seat"] == 0
        assert state["outcomes"] is None
        assert state["trump"] is None
        assert len(state["hand"]) == 10
        assert all(set(card) == {"suit", "rank"} for card in state["hand"])
        assert [move["seat"] for move in state["trick"]] == [1, 2, 3]
        assert [event["type"] for event in state["events"]] == ["card_played"] * 3

    def test_fr36_briscola_has_one_bot_and_a_trump(self, client: TestClient) -> None:
        register(client)

        state = create(client, "briscola")

        assert len(state["hand"]) == 3
        assert state["trump"] in SUITS
        assert [move["seat"] for move in state["trick"]] == [1]

    def test_fr23_the_same_seed_gives_the_same_deal(self, client: TestClient) -> None:
        register(client)

        first = create(client, seed=7)
        second = create(client, seed=7)

        assert first["id"] != second["id"]
        assert first["hand"] == second["hand"]

    def test_fr23_an_unregistered_nickname_is_not_found(
        self, client: TestClient
    ) -> None:
        body = {"nickname": "Nobody", "game": "matazza"}
        assert client.post("/api/v1/matches", json=body).status_code == 404

    def test_fr23_an_invalid_nickname_is_unprocessable(
        self, client: TestClient
    ) -> None:
        body = {"nickname": "a", "game": "matazza"}
        assert client.post("/api/v1/matches", json=body).status_code == 422

    def test_fr23_an_unknown_game_is_unprocessable(self, client: TestClient) -> None:
        register(client)
        body = {"nickname": "Davide", "game": "scopa"}
        assert client.post("/api/v1/matches", json=body).status_code == 422

    def test_fr23_the_game_is_required(self, client: TestClient) -> None:
        register(client)
        response = client.post("/api/v1/matches", json={"nickname": "Davide"})
        assert response.status_code == 422


class TestRead:
    def test_fr23_get_returns_the_same_view_without_events(
        self, client: TestClient
    ) -> None:
        register(client)
        created = create(client)

        response = client.get(f"/api/v1/matches/{created['id']}")

        assert response.status_code == 200
        assert response.json() == {**created, "events": []}

    def test_fr23_an_unknown_match_is_not_found(self, client: TestClient) -> None:
        assert client.get("/api/v1/matches/nope").status_code == 404


class TestMove:
    def test_fr23_a_legal_card_is_played_and_the_bots_reply(
        self, client: TestClient
    ) -> None:
        register(client)
        created = create(client, "briscola")
        card = created["hand"][0]

        response = play(client, created["id"], card)

        assert response.status_code == 200
        state = response.json()
        assert state["events"][0] == {"type": "card_played", "seat": 0, "card": card}
        assert card not in state["hand"]
        assert state["current_seat"] == 0

    def test_fr23_a_card_not_in_the_hand_is_a_conflict(
        self, client: TestClient
    ) -> None:
        register(client)
        created = create(client)

        response = play(client, created["id"], card_not_in(created["hand"]))

        assert response.status_code == 409
        assert client.get(f"/api/v1/matches/{created['id']}").json()["hand"] == (
            created["hand"]
        )

    @pytest.mark.parametrize(
        "card",
        [
            {"suit": "cups", "rank": 3},
            {"suit": "denari", "rank": 11},
            {"suit": "denari"},
        ],
    )
    def test_fr23_a_malformed_card_is_unprocessable(
        self, client: TestClient, card: Json
    ) -> None:
        register(client)
        created = create(client)

        assert play(client, created["id"], card).status_code == 422

    def test_fr23_an_unknown_match_is_not_found(self, client: TestClient) -> None:
        card = {"suit": "denari", "rank": 1}
        assert play(client, "nope", card).status_code == 404


class TestEnd:
    def test_fr36_a_finished_match_has_outcomes_and_a_game_ended_event(
        self, client: TestClient
    ) -> None:
        register(client)

        final = play_to_the_end(client, create(client, "briscola", seed=3))

        assert len(final["outcomes"]) == 2
        assert set(final["outcomes"]) <= {"win", "loss", "draw"}
        last = final["events"][-1]
        assert last == {"type": "game_ended", "outcomes": final["outcomes"]}

    def test_fr36_no_card_is_accepted_after_the_end(self, client: TestClient) -> None:
        register(client)
        final = play_to_the_end(client, create(client, "briscola", seed=3))

        response = play(client, final["id"], {"suit": "denari", "rank": 1})

        assert response.status_code == 409

    def test_fr36_the_finished_match_appears_in_history_and_stats(
        self, client: TestClient
    ) -> None:
        register(client)

        final = play_to_the_end(client, create(client, "briscola", seed=3))

        history = client.get("/api/v1/players/Davide/matches").json()
        assert [match["id"] for match in history] == [final["id"]]
        assert [p["name"] for p in history[0]["participants"]] == ["Davide", "Bot 1"]
        stats = client.get("/api/v1/players/Davide/stats").json()
        assert stats["briscola"]["played"] == 1

    def test_fr36_the_registered_casing_is_recorded(self, client: TestClient) -> None:
        register(client, "Davide")

        final = play_to_the_end(
            client, create(client, "briscola", seed=3, nickname="davide")
        )

        history = client.get("/api/v1/players/Davide/matches").json()
        assert history[0]["participants"][0]["name"] == "Davide"
        assert history[0]["id"] == final["id"]
