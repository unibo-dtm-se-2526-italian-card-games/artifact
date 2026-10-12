"""Contract tests for the Game and AIStrategy ports (FR-01, FR-04, FR-21)."""

from italian_card_games.engine.cards import Card, Rank, Suit
from italian_card_games.engine.ports import AIStrategy, Game
from italian_card_games.engine.values import Move, PlayerView, SeatIndex

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
