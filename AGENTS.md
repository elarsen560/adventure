# Repo Guidance

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
- Audio manager and audio asset generation:
  - `python3 -m pytest tests/test_audio.py`
  - If you are only changing mixer behavior and not asset generation, prefer a narrower node such as:
  - `python3 -m pytest tests/test_audio.py::test_audio_manager_crossfades_between_ambient_channels`

## Full Suite Expectations

- Run the full suite before commit/push.
- Also run the full suite after changes that touch multiple systems, persistence/state shape, or core engine flow.

## Notes

- The repo uses a local `pytest.py` shim rather than the external pytest package.
- The shim accepts optional file targets such as:
  - `python3 -m pytest tests/test_audio.py`
  - `python3 -m pytest tests/test_audio.py::test_audio_manager_crossfades_between_ambient_channels`
- `tests/test_audio.py` intentionally keeps one true asset-generation test, so that file is slower than parser/gameplay/companion files even after the test-efficiency pass.
