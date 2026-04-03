# Asterfall Observatory

Asterfall Observatory is a local, terminal-based parser adventure written in Python 3. You climb into a storm-dark coastal signal station, explore its abandoned machinery and private rooms, solve interconnected puzzles, and restore the Dawn Signal before the weather closes in.

The game is fully text-only in a normal terminal. It does not rely on external libraries, GUI features, or terminal animation effects.

## Repo Overview

The project is organized as a small, expandable Python game rather than a single script:

- `main.py`: entry point for launching the game
- `game/parser.py`: parser normalization and command parsing
- `game/engine.py`: command handling, room flow, interaction logic, and win-state handling
- `game/map.py`: authored ASCII map rendering for explored areas
- `game/state.py`: runtime game state and world initialization
- `game/content.py`: authored rooms, items, NPCs, and replay variability
- `game/persistence.py`: save/load support
- `tests/`: parser and gameplay regression tests
- `pytest.py`: small local test runner shim so `python3 -m pytest` works without external dependencies

## Python Requirement

Python 3.10+ is recommended. The project uses only the standard library.

## Getting Started

No external dependencies are required.

Clone the repo, change into the project directory, and run the game with Python 3.

## Run

```bash
python3 main.py
```

To start a specific reproducible run:

```bash
python3 main.py 4517
```

## Run Tests

```bash
python3 -m pytest
```

## Command Format

The parser supports classic text adventure commands, including:

- `look`
- `map`
- `examine <thing>`
- `go <direction>`
- `north`, `south`, `east`, `west`, `n`, `s`, `e`, `w`
- `take <item>` or `get <item>`
- `drop <item>`
- `use <item>`
- `use <item> on <target>`
- `open <thing>`
- `unlock <thing>`
- `enter <code>`
- `inventory` or `i`
- `talk <character>`
- `help`
- `save` or `save <filename>`
- `load` or `load <filename>`
- `quit`
- `set levers <a> <b> <c>` when the game reveals that final syntax

The parser is forgiving about capitalization, punctuation, filler words such as `the` and `to`, and several common verb or noun synonyms.

The `map` command prints a spoiler-conscious ASCII layout showing your current room, visited rooms, nearby unexplored rooms, and known passages without fully revealing the observatory from the start.

Seed-variable critical-path items are always clued in-world with both room-level hints and examinable reveals, so randomized runs remain fair and solvable without changing the puzzle structure.

## Saves

By default, save files are written under `saves/`. This also applies to named saves such as `save slot1`, which will be written to `saves/slot1`. If you pass an explicit relative or absolute path with a directory component, that path is used as given.

Save/load preserves the full generated run state, including the current seed and any randomized clue or item placement.

## Replay Variability

Each run is generated from a reproducible seed shown at the start of the game. The seed controls:

- which exterior location hides the groundskeeper key
- where the transit token appears
- which room gets an optional extra reward
- which authored four-word archive code is used
- the final three-number lever alignment
- a small piece of atmospheric intro text

Save files preserve the generated world state and seed, so a run can be resumed exactly as it was created.
