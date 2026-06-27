# Contributing

## Development setup

Clone the repo and install dependencies:

```bash
git clone https://github.com/msleigh/flafl
cd flafl
uv sync --group dev
```

Install the pre-commit hooks so linting runs automatically before each commit:

```bash
uv run pre-commit install
```

## Running tests

```bash
uv run pytest
```

For coverage:

```bash
uv run coverage run -m pytest
uv run coverage report
```

## Linting and formatting

This project uses [ruff](https://docs.astral.sh/ruff/) for both linting and
formatting. The pre-commit hooks handle this automatically, but you can also
run manually:

```bash
uv run ruff check .        # lint
uv run ruff format .       # format
```

## Submitting changes

1. Branch from `main`
2. Make your changes and ensure tests pass
3. Open a pull request against `main`

Commit messages should follow [Conventional Commits](https://www.conventionalcommits.org/)
where possible (`feat:`, `fix:`, `docs:`, etc.) — these feed the auto-generated
changelog on each release.
