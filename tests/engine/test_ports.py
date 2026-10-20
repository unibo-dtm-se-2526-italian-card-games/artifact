"""Contract tests for the Game and AIStrategy ports (FR-01, FR-04, FR-21)."""

from fractions import Fraction

from italian_card_games.engine.cards import Card, Rank, Suit
from italian_card_games.engine.ports import AIStrategy, Game
from italian_card_games.engine.values import Move, Outcome, PlayerView, SeatIndex

EIGHT_OF_SPADES = Card(Suit.SPADE, Rank(8))
ACE_OF_COINS = Card(Suit.DENARI, Rank(1))
THREE_OF_CUPS = Card(Suit.COPPE, Rank(3))


class AnyCardGame:
    """A fake game with no rules: every card in hand can be played."""

    def player_count(self) -> int:
        return 2

    def legal_moves(self, view: PlayerView) -> tuple[Move, ...]:
        return tuple(Move(view.seat, card) for card in view.hand)

    def trick_winner(self, trick: tuple[Move, ...]) -> SeatIndex:
        return trick[0].seat

    def round_scores(self, won: tuple[tuple[Card, ...], ...]) -> tuple[Fraction, ...]:
        return tuple(Fraction(len(cards)) for cards in won)

    def solo_winner(self, scores: tuple[Fraction, ...]) -> SeatIndex | None:
        return None

    def outcomes(self, standing_totals: tuple[int, ...]) -> tuple[Outcome, ...] | None:
        return None

    def standing_points(
        self, scores: tuple[Fraction, ...], holder: SeatIndex
    ) -> tuple[int, ...]:
        awarded = [0] * len(scores)
        awarded[holder.value] = 2
        return tuple(awarded)

    def round_holder(self, hands: tuple[tuple[Card, ...], ...]) -> SeatIndex | None:
        for seat, hand in enumerate(hands):
            if EIGHT_OF_SPADES in hand:
                return SeatIndex(seat)
        return None


class FirstLegalMoveBot:
    """A fake strategy that always plays the first legal move."""

    def __init__(self, game: Game) -> None:
        self._game = game

    def choose_move(self, view: PlayerView) -> Move:
        return self._game.legal_moves(view)[0]


class LastLegalMoveBot:
    """A second fake strategy, to show that strategies are interchangeable."""

    def __init__(self, game: Game) -> None:
        self._game = game

    def choose_move(self, view: PlayerView) -> Move:
        return self._game.legal_moves(view)[-1]


class NotAGame:
    def player_count(self) -> int:
        return 2


class GameWithoutTrickWinner:
    """Has the first two game methods but not trick_winner."""

    def player_count(self) -> int:
        return 2

    def legal_moves(self, view: PlayerView) -> tuple[Move, ...]:
        return ()


class GameWithoutScoring:
    """Has the trick methods but neither round_scores nor solo_winner."""

    def player_count(self) -> int:
        return 2

    def legal_moves(self, view: PlayerView) -> tuple[Move, ...]:
        return ()

    def trick_winner(self, trick: tuple[Move, ...]) -> SeatIndex:
        return trick[0].seat


class GameWithoutStandings:
    """Has every method except standing_points and round_holder."""

    def player_count(self) -> int:
        return 2

    def legal_moves(self, view: PlayerView) -> tuple[Move, ...]:
        return ()

    def trick_winner(self, trick: tuple[Move, ...]) -> SeatIndex:
        return trick[0].seat

    def round_scores(self, won: tuple[tuple[Card, ...], ...]) -> tuple[Fraction, ...]:
        return ()

    def solo_winner(self, scores: tuple[Fraction, ...]) -> SeatIndex | None:
        return None

    def outcomes(self, standing_totals: tuple[int, ...]) -> tuple[Outcome, ...] | None:
        return None


class NotAStrategy:
    def pick(self, view: PlayerView) -> Move:
        return Move(view.seat, view.hand[0])


def a_view() -> PlayerView:
    return PlayerView(SeatIndex(0), (EIGHT_OF_SPADES, ACE_OF_COINS, THREE_OF_CUPS), ())


class TestGame:
    def test_a_class_with_the_game_methods_is_a_game(self):
        assert isinstance(AnyCardGame(), Game)

    def test_a_class_missing_a_method_is_not_a_game(self):
        assert not isinstance(NotAGame(), Game)

    def test_a_class_without_trick_winner_is_not_a_game(self) -> None:
        assert not isinstance(GameWithoutTrickWinner(), Game)

    def test_a_class_without_scoring_methods_is_not_a_game(self) -> None:
        assert not isinstance(GameWithoutScoring(), Game)

    def test_a_class_without_standing_methods_is_not_a_game(self) -> None:
        assert not isinstance(GameWithoutStandings(), Game)

    def test_awards_standing_points_from_round_scores_and_the_holder(self) -> None:
        game: Game = AnyCardGame()
        scores = (Fraction(1), Fraction(2))
        assert game.standing_points(scores, SeatIndex(1)) == (0, 2)

    def test_names_the_holder_of_the_key_card_from_the_dealt_hands(self) -> None:
        game: Game = AnyCardGame()
        hands = ((ACE_OF_COINS,), (THREE_OF_CUPS, EIGHT_OF_SPADES))
        assert game.round_holder(hands) == SeatIndex(1)

    def test_reports_no_holder_when_the_key_card_is_not_dealt(self) -> None:
        game: Game = AnyCardGame()
        assert game.round_holder(((ACE_OF_COINS,), (THREE_OF_CUPS,))) is None

    def test_scores_a_round_from_the_cards_each_seat_won(self) -> None:
        game: Game = AnyCardGame()
        won = ((ACE_OF_COINS, THREE_OF_CUPS), (EIGHT_OF_SPADES,))
        assert game.round_scores(won) == (Fraction(2), Fraction(1))

    def test_reports_no_solo_winner_when_the_game_has_none(self) -> None:
        game: Game = AnyCardGame()
        assert game.solo_winner((Fraction(1), Fraction(1))) is None

    def test_names_the_winner_of_a_trick(self) -> None:
        game: Game = AnyCardGame()
        trick = (Move(SeatIndex(1), ACE_OF_COINS), Move(SeatIndex(0), THREE_OF_CUPS))
        assert game.trick_winner(trick) == SeatIndex(1)

    def test_reports_how_many_seats_it_needs(self) -> None:
        game: Game = AnyCardGame()
        assert game.player_count() == 2

    def test_legal_moves_are_asked_from_what_a_seat_can_see(self) -> None:
        game: Game = AnyCardGame()
        moves = game.legal_moves(a_view())
        assert moves == (
            Move(SeatIndex(0), EIGHT_OF_SPADES),
            Move(SeatIndex(0), ACE_OF_COINS),
            Move(SeatIndex(0), THREE_OF_CUPS),
        )


class TestAIStrategy:
    def test_a_class_with_choose_move_is_a_strategy(self):
        assert isinstance(FirstLegalMoveBot(AnyCardGame()), AIStrategy)

    def test_a_class_without_choose_move_is_not_a_strategy(self):
        assert not isinstance(NotAStrategy(), AIStrategy)

    def test_chooses_a_move_from_a_player_view(self) -> None:
        bot: AIStrategy = FirstLegalMoveBot(AnyCardGame())
        assert bot.choose_move(a_view()) == Move(SeatIndex(0), EIGHT_OF_SPADES)

    def test_two_strategies_are_interchangeable(self) -> None:
        game = AnyCardGame()
        view = a_view()
        strategies: list[AIStrategy] = [FirstLegalMoveBot(game), LastLegalMoveBot(game)]
        for strategy in strategies:
            assert strategy.choose_move(view) in game.legal_moves(view)
