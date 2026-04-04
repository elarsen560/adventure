# Asterfall Observatory

Asterfall Observatory is a local, terminal-based parser adventure written in Python 3. You climb into a storm-dark coastal signal station, explore its abandoned machinery and private rooms, solve interconnected puzzles, and restore the Dawn Signal before the weather closes in.

The game is fully text-only in a normal terminal. It does not rely on external libraries, GUI features, or terminal animation effects.

## Repo Overview

The project is organized as a small, expandable Python game rather than a single script:

- `main.py`: entry point for launching the game
- `game/parser.py`: parser normalization and command parsing
- `game/engine.py`: command handling, room flow, interaction logic, and win-state handling
- `game/ambient.py`: deterministic atmospheric ambient-text selection
- `game/companion.py`: optional constrained companion integration via Codex CLI or OpenAI API
- `game/hazards.py`: seeded environmental hazard selection and resolution rules
- `game/map.py`: authored ASCII map rendering for explored areas
- `game/npcs.py`: featured NPC archetypes, generation rules, and role assignment
- `game/npc_dialogue.py`: bounded featured-NPC dialogue prompt construction
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

The optional companion prefers a local authenticated `codex exec` session if the Codex CLI is installed and logged in. If Codex CLI is unavailable, it can fall back to the OpenAI API when `OPENAI_API_KEY` is set.

You can keep environment settings in a local `.env` file. The companion currently reads `OPENAI_API_KEY` and optional `OPENAI_MODEL` from either the live environment or that file.

## Run

```bash
python3 main.py
```

To start a specific reproducible run:

```bash
python3 main.py 4517
```

To launch in debug mode for testing:

```bash
python3 main.py --debug
python3 main.py 4517 --debug
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
- `ask [question]`
- `note <text>`
- `notes`
- `new note <text>`
- `read notes`
- `inventory` or `i`
- `talk <character> [message]`
- `help`
- `save` or `save <filename>`
- `load` or `load <filename>`
- `quit`
- `set levers <a> <b> <c>` when the game reveals that final syntax

When debug mode is enabled, these extra commands are also available:

- `goto <room>`
- `full map`
- `rooms`

The parser is forgiving about capitalization, punctuation, filler words such as `the` and `to`, and several common verb or noun synonyms.

The `map` command prints a spoiler-conscious ASCII layout showing your current room, visited rooms, nearby unexplored rooms, and known passages without fully revealing the observatory from the start.

In debug mode, `full map` reveals the complete authored layout immediately and `rooms` prints valid room ids and names for fast navigation/testing.

You can also keep a player-authored notebook with `note <text>` or `new note <text>`, and review it with `notes` or `read notes`.

Each run also includes exactly one featured in-world NPC selected from a curated cast. The featured NPC has a seeded room, a bounded gameplay role, and short replayable dialogue that stays grounded in engine-approved knowledge. Static characters such as Wren still use the same `talk` command.

You can consult an optional constrained companion with `ask <question>` or just `ask` for a general suggestion. By default the game prefers a local authenticated `codex exec` session when available; otherwise it can use the OpenAI API if `OPENAI_API_KEY` is configured. The companion only receives currently visible game context, your inventory, your notes, the visible map, recent turn history, and a short excerpt of recent NPC exchanges; it is designed to help interpret known information rather than reveal hidden state.

During normal play, the observatory may occasionally emit short atmospheric ambient lines tied to your location and the station's changing condition. These are intentionally infrequent, deterministic within a run, and do not reveal puzzle solutions.

Each run also includes one seeded mid-game environmental hazard in a valid authored room. Hazards are foreshadowed in-room, can be resolved through ordinary observation, and are meant to add tension without changing the underlying puzzle structure.

Seed-variable critical-path items are always clued in-world with both room-level hints and examinable reveals, so randomized runs remain fair and solvable without changing the puzzle structure.

## Saves

By default, save files are written under `saves/`. This also applies to named saves such as `save slot1`, which will be written to `saves/slot1`. If you pass an explicit relative or absolute path with a directory component, that path is used as given.

Save/load preserves the full generated run state, including the current seed and any randomized clue or item placement.

## Replay Variability

Each run is generated from a reproducible seed shown at the start of the game. The seed controls:

- which exterior location hides the groundskeeper key
- where the transit token appears
- which room gets an optional extra reward
- which featured NPC appears, where they wait, and what bounded gameplay role they serve
- which environmental hazard appears in which authored mid-game room
- which authored four-word archive code is used
- the final three-number lever alignment
- a small piece of atmospheric intro text

Save files preserve the generated world state and seed, so a run can be resumed exactly as it was created.
