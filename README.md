# Italian Card Games

A Python library implementing classic Italian card games (e.g. Briscola, Scopa) on top of a clean, testable game engine.

Developed as a project for the Software Engineering course at DTM, University of Bologna.

> **Status:** Phase 3 (adapters). Matazza and Briscola are playable offline against bots from the command line; finished matches can be stored in SQLite, with history and statistics. A REST API (`/api/v1`) registers players and serves their match history and statistics. Playing a match through the API, the lobby and the web client are not built yet.

## Project structure

```bash
<root directory>
├── italian_card_games/     # main package
│   ├── engine/             # game rules and match flow (framework-free)
│   ├── history/            # match records, history and statistics (framework-free)
│   ├── lobby/              # nicknames and registered players (framework-free)
│   ├── api/                # REST API (FastAPI): routes on the ports, composition root in main.py
│   ├── ai/                 # bot strategies (adapters behind AIStrategy)
│   ├── persistence/        # MatchRepository and PlayerRepository adapters: in-memory and SQLite (SQLAlchemy)
│   ├── cli.py              # offline command-line game
│   ├── __init__.py         # python package marker
│   └── __main__.py         # application entry point
├── tests/                  # unit tests
├── docs/                   # project documentation (workflow guide, requirements, design)
├── .github/workflows/      # GitHub CI (check.yml) and release (deploy.yml) pipelines
├── LICENSE                 # Apache 2.0
├── pyproject.toml          # project configuration (Poetry)
├── renovate.json           # automatic dependency updates
└── release.config.mjs      # semantic-release configuration
```

## Getting started

Requirements: Python 3.11+ and [Poetry](https://python-poetry.org/).

```bash
pip install -r requirements.txt
poetry install
```

### Run tests

```bash
poetry run poe test
```

### Run tests with coverage

```bash
poetry run poe coverage
```

Then generate a report with `poe coverage-report` or `poe coverage-html`.

### Run static checks

Static analysis with `mypy` and `ruff`:

```bash
poetry run poe static-checks
```

### Format code

```bash
poetry run poe format
```

> You can enter a Poetry shell via `poetry shell` to avoid prefixing commands with `poetry run`.

### Run the application

Play one offline game as seat 0 against rule-based bots (three in Matazza, one in Briscola):

```bash
poetry run python -m italian_card_games --game briscola --seed 1
```

`--game` is `matazza` (default) or `briscola`; `--seed` fixes the shuffle. Each turn, type the number of the card to play.

### Run the REST API

```bash
poetry run uvicorn italian_card_games.api.main:build_app --factory
```

The data is kept in a SQLite file, `italian_card_games.db` in the current directory; set `ICG_DATABASE_URL` (for example `sqlite:///other.db`) to use another database. The OpenAPI document is at `/api/v1/openapi.json` and the interactive docs at `/api/v1/docs`. Routes: `GET /api/v1/games`, `POST /api/v1/players`, `GET /api/v1/players/{nickname}`, and `GET /api/v1/players/{nickname}/matches` and `/stats`.

## Contributing

- One branch per piece of work, one pull request into `develop`; `develop` is merged into `main` for releases.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/), since `semantic-release` computes version numbers from them.
- CI runs on all pushes, on multiple OS (Windows, macOS, Ubuntu) and Python versions.

## License

Distributed under the [Apache License 2.0](LICENSE).
