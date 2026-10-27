# Italian Card Games

A Python library implementing classic Italian card games (e.g. Briscola, Scopa) on top of a clean, testable game engine.

Developed as a project for the Software Engineering course at DTM, University of Bologna.

> **Status:** Phase 1 (foundations). Documentation only, no game code yet.

## Project structure

```bash
<root directory>
├── italian_card_games/     # main package
│   ├── engine/             # game rules and match flow (framework-free)
│   ├── ai/                 # bot strategies (adapters behind AIStrategy)
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

## Contributing

- One branch per piece of work, one pull request into `develop`; `develop` is merged into `main` for releases.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/), since `semantic-release` computes version numbers from them.
- CI runs on all pushes, on multiple OS (Windows, macOS, Ubuntu) and Python versions.

See [docs/WORKFLOW_GUIDE.md](docs/WORKFLOW_GUIDE.md) for the full workflow.

## License

Distributed under the [Apache License 2.0](LICENSE).
