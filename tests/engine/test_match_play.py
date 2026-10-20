"""Tests for starting a Match and playing cards (FR-05, FR-06, FR-11, NFR-04)."""

from random import Random

import pytest

from italian_card_games.engine.cards import Card, DeckFactory
from italian_card_games.engine.events import CardPlayed, TrickWon
from italian_card_games.engine.match import IllegalMoveError, Match
from italian_card_games.engine.matazza import MatazzaRules
from italian_card_games.engine.values import Move, SeatIndex


def a_match(seed: int = 1) -> Match:
    return Match(MatazzaRules(), Random(seed))


def first_legal_move(match: Match) -> Move:
    seat = match.current_seat
    return MatazzaRules().legal_moves(match.view_for(seat))[0]


def all_cards_in_hands(match: Match) -> list[Card]:
    return [card for seat in range(4) for card in match.view_for(SeatIndex(seat)).hand]


class TestStart:
    def test_fr11_the_match_deals_the_whole_deck_evenly(self) -> None:
        match = a_match()
        assert [len(match.view_for(SeatIndex(s)).hand) for s in range(4)] == [10] * 4
        assert sorted(all_cards_in_hands(match), key=str) == sorted(
            DeckFactory.ordered().cards, key=str
        )

    def test_fr11_the_first_dealer_is_seat_zero_so_seat_one_leads(self) -> None:
        match = a_match()
        assert match.round.dealer == SeatIndex(0)
        assert match.current_seat == SeatIndex(1)

    def test_nfr04_the_same_seed_deals_the_same_hands(self) -> None:
        first, second = a_match(seed=7), a_match(seed=7)
        assert all_cards_in_hands(first) == all_cards_in_hands(second)

    def test_nfr04_a_different_seed_deals_different_hands(self) -> None:
        assert all_cards_in_hands(a_match(seed=7)) != all_cards_in_hands(a_match(seed=8))

    def test_a_new_match_has_no_standing_points_and_no_outcome(self) -> None:
        match = a_match()
        assert match.standing_totals == (0, 0, 0, 0)
        assert match.outcomes is None
        assert not match.is_over


class TestViews:
    def test_fr06_a_view_holds_only_the_hand_of_its_seat(self) -> None:
        match = a_match()
        for seat in range(4):
            view = match.view_for(SeatIndex(seat))
            assert view.seat == SeatIndex(seat)
            assert view.hand == match.round.hands[seat]
            assert view.trick == ()

    def test_fr06_the_trick_in_play_is_visible_to_every_seat(self) -> None:
        match = a_match()
        move = first_legal_move(match)
        match.play(move)
        assert match.view_for(SeatIndex(3)).trick == (move,)


class TestPlay:
    def test_fr05_playing_a_card_reports_a_card_played_event(self) -> None:
        match = a_match()
        move = first_legal_move(match)
        assert match.play(move) == [CardPlayed(move)]

    def test_fr05_the_turn_passes_to_the_next_seat(self) -> None:
        match = a_match()
        match.play(first_legal_move(match))
        assert match.current_seat == SeatIndex(2)

    def test_fr10_the_fourth_card_also_reports_the_trick_winner(self) -> None:
        match = a_match()
        moves: list[Move] = []
        events = []
        for _ in range(4):
            move = first_legal_move(match)
            moves.append(move)
            events = match.play(move)
        winner = MatazzaRules().trick_winner(tuple(moves))
        assert events == [CardPlayed(moves[-1]), TrickWon(winner, tuple(moves))]

    def test_fr10_the_trick_winner_leads_the_next_trick(self) -> None:
        match = a_match()
        moves = []
        for _ in range(4):
            moves.append(first_legal_move(match))
            match.play(moves[-1])
        assert match.current_seat == MatazzaRules().trick_winner(tuple(moves))

    def test_fr05_a_move_out_of_turn_is_rejected_and_changes_nothing(self) -> None:
        match = a_match()
        out_of_turn = Move(SeatIndex(2), match.round.hands[2][0])
        with pytest.raises(IllegalMoveError):
            match.play(out_of_turn)
        assert match.current_seat == SeatIndex(1)
        assert match.round.trick == ()
        assert len(match.round.hands[2]) == 10

    def test_fr09_an_illegal_card_is_rejected_and_changes_nothing(self) -> None:
        match = a_match()
        hand = match.round.hands[1]
        stranger = next(c for c in DeckFactory.ordered().cards if c not in hand)
        with pytest.raises(IllegalMoveError):
            match.play(Move(SeatIndex(1), stranger))
        assert len(match.round.hands[1]) == 10
