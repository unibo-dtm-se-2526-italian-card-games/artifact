# Requirements

Requirements for **italian_card_games**: a general-purpose engine for classic Italian 40-card games, playable offline against bots and online against other players.

IDs are stable. Tests and pull requests reference them (e.g. `FR-13`). A requirement is complete only when its *Done when* condition holds.

## 1. Scope and actors

- **Actor:** the *player*. There is no admin or spectator role.
- **Identity:** a player registers a nickname. Nicknames are unique and reserved: nobody else can use a registered one. There are no accounts with passwords or email, and no check that a returning player owns their nickname: anyone who enters a registered nickname can use it.
- **In scope:** the game engine, at least two games (Matazza, Briscola), rule-based and LLM-based bots, offline and online play, match history and statistics.
- **Stretch:** a logic-programming or constraint-solver bot (Prolog or Z3).
- **Out of scope:** accounts with passwords or email, spectators, expense splitting, real-money features.

## 2. Functional requirements

### 2.1 Engine (game-independent)

| ID | Requirement | Done when |
|---|---|---|
| FR-01 | The engine supports several games through one common `Game` interface. Adding a game does not change the engine core. | A second game (Briscola) is implemented against the same interface with no change to shared code other than extracted abstractions. |
| FR-02 | The engine provides the 40-card Italian deck (suits denari, coppe, spade, bastoni; ranks 1-10) with shuffling driven by an injectable random source. | Tests show 40 distinct cards, and the same seed gives the same order. |
| FR-03 | Each game declares its own player count and team structure. The engine does not assume 4 free-for-all players. | Matazza declares 4 free-for-all and Briscola declares 2 free-for-all; the interface allows other counts and teams. |
| FR-04 | A player (human or bot) is anything that returns a move given a game state. The engine has no special cases for either. | The same match runs with all-human, all-bot and mixed players through one code path. |
| FR-05 | A move is validated against the rules. An illegal move is rejected with an explicit error and the game state is unchanged. | A test per rule shows the illegal move is rejected and the state is identical before and after. |
| FR-06 | The view of the state given to a player contains only what that player may see (their own hand and public information). | A test shows another player's hand is absent from a player's view. |

### 2.2 Matazza

| ID | Requirement | Done when |
|---|---|---|
| FR-07 | A Matazza match has 4 players, free-for-all. At the start of each round the whole deck is shuffled and 10 cards are dealt to each player. | A round starts with four hands of 10 distinct cards and an empty trick. |
| FR-08 | Card strength in a trick, from highest to lowest, is `3 > 2 > 1 > 10 > 9 > 8 > 7 > 6 > 5 > 4`. | A test covers all 10 ranks against each other. |
| FR-09 | The first card of a trick sets its suit. A player holding a card of that suit must play one. A player with none may play any card. | Tests cover: following suit, forced follow, and discarding when void. |
| FR-10 | The trick is won by the highest-strength card of the led suit. The winner collects the 4 cards and leads the next trick. | A test shows an off-suit card never wins, and the winner leads next. |
| FR-11 | The first trick of a round is led by the player after the dealer. The dealer rotates by one seat each round. | A test over several rounds shows the dealer and first leader moving. |
| FR-12 | After 10 tricks the round ends. Each player's round score is exact: ranks 3, 2, 10, 9, 8 are worth 1/3, the 1 is worth 1, ranks 4, 5, 6, 7 are worth 0. Scores use exact fractions, never floats. | The four scores of any round sum to exactly 32/3. |
| FR-13 | Solo win is checked first, every round. If the other three players each score less than 1.0 (exactly 1.0 does not count), the remaining player wins the game at once and no standing points are awarded. | A test covers the boundary: a score of exactly 1.0 is not "less than 1.0", so it blocks the solo win. |
| FR-14 | Standing points when `numLow == 0` (no player under 1.0): the holder of the 8 of spades is excluded; the other three are compared. If the top two are tied, the holder takes both points. Otherwise the holder and the single top scorer take one each. | Worked examples A and B pass as tests. |
| FR-15 | Standing points when `numLow == 1`: if that player holds the 8 of spades, they take both points. Otherwise that player and the holder take one each. | A test per branch. |
| FR-16 | Standing points when `numLow == 2`: those two players take one point each, regardless of who holds the 8 of spades. | Worked example C passes as a test. |
| FR-17 | The case `numLow == 3` is unreachable because the solo-win check always fires first. If reached, the engine raises an error. | A test forces the state and expects the error. |
| FR-18 | The game ends when one player has 12 standing points (that player loses alone), or when two players have each reached 6 standing points (both lose). The check runs every time points are awarded. | Tests cover both conditions, including the two players reaching 6 in different rounds. |
| FR-19 | At the end of a game each player is recorded as having won, lost or drawn. Final standing points do not decide the outcome. A solo-win player wins and the other three lose. When the game ends by the 12-point or the two-at-6 rule, the losing players lose and all others win. Only a Briscola match tied at 60 points each is a draw for both players (FR-20). | A test per end condition checks the outcome for all four players. |

### 2.3 Briscola

| ID | Requirement | Done when |
|---|---|---|
| FR-20 | Briscola is playable through the same `Game` interface. A match has 2 players, free-for-all, and is a single round. 3 cards are dealt to each player in turn and the other 34 form the stock; the suit of the last card of the stock is the trump. Any card in hand may be played, with no duty to follow suit. The trick goes to the highest trump, otherwise to the highest card of the led suit, with strength `1 > 3 > 10 > 9 > 8 > 7 > 6 > 5 > 4 > 2`. After each trick the winner draws first and the other player second, so the last player to draw takes the trump card. Card points are 11 for the 1, 10 for the 3, 4 for the 10, 3 for the 9, 2 for the 8 and 0 for the rest, 120 in all. The round ends when all hands and the stock are empty. The player with the higher score wins and the other loses; 60 points each is a draw for both. | Briscola can be played from start to finish offline against a bot. Tests cover the strength order, trump, drawing order, card points summing to 120, the win and the 60-60 draw. |

### 2.4 AI

| ID | Requirement | Done when |
|---|---|---|
| FR-21 | Bots implement a common `AIStrategy` interface and receive the same player view as a human. | Two strategies are interchangeable without engine changes. |
| FR-22 | A rule-based strategy is the baseline. It always returns a legal move. | A test plays many seeded games with four rule-based bots without an illegal move. |
| FR-23 | Offline mode: one human plays against bots, three in Matazza and one in Briscola. | A game of each type can be completed from the UI or a CLI with one human and the bots it needs. |
| FR-24 | An LLM-based strategy implements the same interface. If it fails, times out, or returns an illegal move, the game falls back to the rule-based strategy for that move. | A test with a faulty LLM stub shows the fallback keeps the game going. |
| FR-25 | *(Stretch)* A Prolog or constraint-solver strategy implements the same interface. | The strategy plays a full game with legal moves. |

### 2.5 Lobby and online play

| ID | Requirement | Done when |
|---|---|---|
| FR-26 | A player registers a nickname before playing. Nicknames are unique: a nickname already registered is rejected. | Registering a new nickname lets the player reach the lobby; registering a taken one fails with an explicit error. |
| FR-27 | A player can create a lobby and share a code. Others join with that code. | Two clients meet in one lobby using a code. |
| FR-28 | The lobby creator starts the match. Empty seats are filled with bots. | A lobby with one human starts a full 4-player match. |
| FR-29 | All players in a match receive match updates in real time. | An action by one client is seen by the others without refreshing. |
| FR-30 | If a human disconnects during a match, a bot takes over their seat. | A test disconnects a player mid-match and the game continues. |

### 2.6 History and statistics

| ID | Requirement | Done when |
|---|---|---|
| FR-31 | Finished matches are persisted: game type, participants (human or bot), each player's score in every round, and the win, loss or draw of each player. The total standing points of a game are not stored. | A match survives a restart and can be read back, with its round scores and outcomes. |
| FR-32 | A player can retrieve their match history, including the round-by-round scores of each match. | History for a nickname lists their matches in order, each with its round scores. |
| FR-33 | A player can retrieve statistics: matches played, wins, losses and draws, per game type. | Stats match the stored history in a test. |

### 2.7 API and clients

| ID | Requirement | Done when |
|---|---|---|
| FR-34 | The REST API uses versioned routes (`/api/v1/...`) and publishes an OpenAPI specification. | The OpenAPI document is generated and describes every route. |
| FR-35 | Real-time lobby and match updates are delivered over WebSockets. | See FR-29. |
| FR-36 | A web client lets a player play an offline game against bots (FR-23). | A full offline game of each type can be played in the browser. |
| FR-37 | The web client lets a player create or join an online lobby and play. | Two browsers can play a match together. |
| FR-38 | The web client shows match history and statistics. | The data from FR-32 and FR-33 is visible in the UI. |

## 3. Non-functional requirements

| ID | Requirement | Done when |
|---|---|---|
| NFR-01 | **Architecture.** The domain core is framework-free (hexagonal). It never imports FastAPI, NiceGUI or SQLAlchemy. Those are adapters behind interfaces. | An automated check or test fails if the core imports a framework. |
| NFR-02 | **Coverage.** Test coverage is at least 70% on the domain core and at least 50% overall. | The CI coverage report meets both thresholds. |
| NFR-03 | **Acceptance tests.** Each functional requirement has at least one test that references its ID. | Each `FR-xx` appears in a test name or docstring. |
| NFR-04 | **Reproducibility.** Given the same seed and the same moves, a game produces the same result. | A test replays a recorded game and matches the final state. |
| NFR-05 | **Portability.** The project runs on Python 3.11 or newer, on Windows, macOS and Linux. | The CI matrix passes on all three systems. |
| NFR-06 | **Responsiveness.** A rule-based bot answers within 1 second. An LLM bot has a timeout of 10 seconds before the fallback (FR-24). | Timeouts are configurable and tested with a stub. |
| NFR-07 | **Delivery.** CI separates checking (lint, types, tests, coverage) from deploy. At least two SemVer releases are published to PyPI or TestPyPI. | Two tagged releases exist and installs work. |
| NFR-08 | **Process.** Commits follow Conventional Commits. Work goes through pull requests into `develop`, with CI passing. | The history and branch protection show this. |
| NFR-09 | **Deployability.** The full stack starts with Docker Compose. | `docker compose up` brings up API and client. |
| NFR-10 | **Documentation.** Decisions are recorded as ADRs, and the license choice is justified. | The ADRs and the license justification exist in the docs. |

## 4. User stories

- As a player, I want to register a unique nickname that nobody else can use, so that my history and statistics are mine.
- As a player, I want to play a game against bots, so that I can play when no one else is available.
- As a player, I want to create a lobby and share a code, so that I can play with my friends.
- As a lobby creator, I want empty seats filled with bots, so that I can start with fewer than four humans.
- As a player, I want the game to reject illegal moves with a clear message, so that I learn the rules.
- As a player, I want to see only my own hand, so that the game is fair.
- As a player, I want a bot to take my seat if I disconnect, so that the others are not stuck.
- As a player, I want to choose between Matazza and Briscola, so that I can play different games.
- As a player, I want to see my history and win/loss statistics, so that I can follow my progress.
- As a student of the course, I want each rule traced to a requirement and a test, so that I can show the work is complete.

## 5. Open questions

- **Briscola variants (FR-20):** Briscola is specified for 2 players. A 4-player version with teams is out of scope for now and would need team support in the `Game` interface.
