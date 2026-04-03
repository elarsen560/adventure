import os
from unittest.mock import MagicMock, patch

from game.companion import FALLBACK_MESSAGE, build_companion_context, build_companion_prompt, codex_available, companion_available, extract_response_text, request_codex_response, request_companion_response
from game.engine import Game


def test_context_assembly_includes_allowed_sections():
    context = build_companion_context(
        room_name="Cliff Path",
        room_text="Cliff Path\nStorm and stone.",
        inventory=["oil flask"],
        notes=["Check the gate."],
        map_text="[@ CP]",
        recent_history=[{"command": "look", "response": "You are here."}],
    )
    assert "Current room: Cliff Path" in context
    assert "Inventory: oil flask" in context
    assert "1. Check the gate." in context
    assert "Player: look" in context
    assert "Visible map:\n[@ CP]" in context


def test_prompt_includes_constraint_language():
    prompt = build_companion_prompt("Context block", "What should I try?")
    assert "Do not assume or invent hidden game state" in prompt
    assert "Keep your answer to one sentence, at most two." in prompt
    assert "Do not sound like an analyst, expert observer, or modern assistant." in prompt
    assert "Prefer hints, clues, or gentle nudges" in prompt
    assert "For map-based questions, stay grounded in the visible layout" in prompt
    assert "What should I try?" in prompt


def test_context_describes_companion_voice():
    context = build_companion_context(
        room_name="Cliff Path",
        room_text="Cliff Path\nStorm and stone.",
        inventory=[],
        notes=[],
        map_text="[@ CP]",
        recent_history=[],
    )
    assert "restrained companion in a classic parser adventure" in context
    assert "never omniscient" in context


def test_extract_response_text_prefers_output_text():
    payload = {"output_text": "Try examining the gate more closely."}
    assert extract_response_text(payload) == "Try examining the gate more closely."


def test_engine_ask_falls_back_without_api_key():
    with patch("game.engine.companion_available", return_value=False):
        game = Game(seed=4517)
        assert game.process("ask") == FALLBACK_MESSAGE


def test_engine_ask_uses_companion_response():
    with patch("game.engine.companion_available", return_value=True), patch(
        "game.engine.request_companion_response", return_value="Try examining the observatory again."
    ):
        game = Game(seed=4517)
        response = game.process("ask What should I do next?")
        assert response == "Try examining the observatory again."


def test_companion_available_true_when_codex_exists_without_api_key():
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        with patch("game.companion.codex_available", return_value=True):
            assert companion_available() is True
    finally:
        if old_key is not None:
            os.environ["OPENAI_API_KEY"] = old_key


def test_companion_available_reads_dotenv(tmp_path):
    old_cwd = os.getcwd()
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        os.chdir(tmp_path)
        (tmp_path / ".env").write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")
        assert companion_available() is True
    finally:
        os.chdir(old_cwd)
        if old_key is not None:
            os.environ["OPENAI_API_KEY"] = old_key


def test_request_companion_response_falls_back_on_invalid_api_result(tmp_path):
    old_cwd = os.getcwd()
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        os.chdir(tmp_path)
        (tmp_path / ".env").write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")
        fake_response = MagicMock()
        fake_response.read.return_value = b"{}"
        fake_context = MagicMock()
        fake_context.__enter__.return_value = fake_response
        fake_context.__exit__.return_value = False
        with patch("game.companion.request_codex_response", return_value=None), patch("urllib.request.urlopen", return_value=fake_context):
            assert request_companion_response("prompt") == FALLBACK_MESSAGE
    finally:
        os.chdir(old_cwd)
        if old_key is not None:
            os.environ["OPENAI_API_KEY"] = old_key


def test_request_codex_response_reads_output_last_message():
    fake_result = MagicMock(returncode=0)

    def fake_run(command, cwd, capture_output, text, timeout):
        output_path = command[command.index("--output-last-message") + 1]
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write("Check the gate again.")
        return fake_result

    with patch("game.companion.codex_available", return_value=True), patch("subprocess.run", side_effect=fake_run):
        assert request_codex_response("prompt") == "Check the gate again."


def test_request_companion_response_prefers_codex_over_api():
    with patch("game.companion.request_codex_response", return_value="Try the observatory."), patch(
        "game.companion.request_api_response", return_value="API answer"
    ):
        assert request_companion_response("prompt") == "Try the observatory."
