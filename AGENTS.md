# Repo Guidance

## Working Style

- Treat this repo as a finished small game under active extension, not a prototype.
- Prefer thin, surgical changes over broad refactors.
- Preserve the game's authored tone, parser-first identity, and deterministic progression unless the user explicitly asks for design changes.
- Keep terminal mode intact when adding new presentation layers such as desktop UI.

## Architecture Expectations

- Keep gameplay logic in `game/engine.py`, `game/state.py`, and other engine/content modules.
- Prefer wrapping or reusing existing behavior over duplicating game logic in a frontend.
- For UI work, treat the Tkinter desktop wrapper as a presentation layer on top of `Game`, not a second game implementation.
- Use structured state directly for panels and side views; do not scrape transcript text to reconstruct map, inventory, or room state.
- Preserve save/load compatibility unless the task explicitly requires state-shape evolution. If state changes are necessary, default old saves safely.

## Content And Design Guardrails

- Do not casually rewrite room prose, story premise, puzzle ordering, or companion/NPC knowledge boundaries.
- Maintain the late-19th/early-20th-century observatory tone and the restrained parser-adventure feel.
- New helper systems should support discovery and clarity without turning the game into a point-and-click UI or a solver-heavy experience.

## Audio And Asset Guidance

- Keep the current audio architecture intact unless there is a clear technical reason to change it.
- Runtime-ready audio under `assets/audio/` should remain playable out of the box.
- Downloaded/source audio belongs under `assets/audio/source_downloads/` and should stay out of version control.
- If you change shipped audio provenance or licensing status, update both `assets/audio/ASSET_MANIFEST.md` and `assets/audio/ASSET_MANIFEST.json`.

## Documentation Expectations

- Update `README.md` whenever user-facing behavior, launch flow, commands, test workflow, or desktop/audio behavior changes.
- Keep repo-facing guidance in `AGENTS.md` aligned with the actual working approach used in the codebase.
- Treat manifest files and README sections as living documentation; do not leave known drift in place.

## Testing Scope

- Prefer the narrowest meaningful test scope while iterating.
- Use `python3 -m pytest <target>` for focused work, then run `python3 -m pytest` before final handoff or commit.
- When you choose a targeted run, explain in session output what you are testing and why that scope is sufficient.
- When you choose the full suite, explain that it is a final regression pass or that the change crosses subsystem boundaries.

## Typical Test Selection

- Parser, help text, notebook, instructions, map command parsing:
  - `python3 -m pytest tests/test_parser.py`
- Engine, progression, hazards, save/load, room behavior, NPC logic:
  - `python3 -m pytest tests/test_gameplay.py`
- Companion prompt/context behavior:
  - `python3 -m pytest tests/test_companion.py`
- Desktop wrapper/controller behavior:
  - `python3 -m pytest tests/test_tk_app.py`
- Audio manager and audio asset generation:
  - `python3 -m pytest tests/test_audio.py`
  - If you are only changing mixer behavior and not asset generation, prefer a narrower node such as:
  - `python3 -m pytest tests/test_audio.py::test_audio_manager_crossfades_between_ambient_channels`

## Full Suite Expectations

- Run the full suite before commit/push.
- Also run the full suite after changes that touch multiple systems, persistence/state shape, or core engine flow.

## Change Verification

- For presentation-layer changes, verify both the direct tests and that terminal-mode behavior still passes the full suite.
- For desktop-wrapper changes, ensure startup flow, restart flow, save/load refresh behavior, and quit behavior remain coherent.
- For audio changes, distinguish between audio-manager logic tests and full asset-generation tests; use the narrowest sufficient scope while iterating.

## Notes

- The repo uses a local `pytest.py` shim rather than the external pytest package.
- The shim accepts optional file targets such as:
  - `python3 -m pytest tests/test_audio.py`
  - `python3 -m pytest tests/test_audio.py::test_audio_manager_crossfades_between_ambient_channels`
- `tests/test_audio.py` intentionally keeps one true asset-generation test, so that file is slower than parser/gameplay/companion files even after the test-efficiency pass.
- When reporting work back to the user, state what scope you tested and why that scope was chosen.
