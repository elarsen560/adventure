from __future__ import annotations

from game.companion import companion_available, request_companion_response
from game.npcs import NPC_ROLE_DEFINITIONS


def build_npc_context(
    *,
    profile: dict,
    role: str,
    room_name: str,
    inventory: list[str],
    notes: list[str],
    transcript: list[dict[str, str]],
    approved_guidance: str,
    approved_action: str | None,
) -> str:
    inventory_text = ", ".join(inventory) if inventory else "Nothing."
    notes_text = "\n".join(f"{index}. {note}" for index, note in enumerate(notes, start=1)) if notes else "None."
    transcript_lines = []
    for turn in transcript[-10:]:
        transcript_lines.append(f"Player: {turn['player']}")
        transcript_lines.append(f"{profile['display_name']}: {turn['npc']}")
    transcript_text = "\n".join(transcript_lines) if transcript_lines else "None."
    action_text = approved_action or "No special engine action is available right now."

    return (
        "Premise: A storm beats around Asterfall Observatory, an old coastal signal station.\n"
        f"NPC identity: {profile['display_name']}\n"
        f"Short description: {profile['short_description']}\n"
        f"Voice guidance: {profile['personality_style']}\n"
        f"Speech examples: {' | '.join(profile['speech_examples'])}\n"
        f"Gameplay role: {role} - {NPC_ROLE_DEFINITIONS[role]['description']}\n"
        f"Knowledge scope: {profile['knowledge_scope']}\n"
        f"Restricted knowledge: {profile['restricted_knowledge']}\n"
        f"Hint style: {profile['hint_style']}\n"
        f"Current room: {room_name}\n"
        f"Inventory: {inventory_text}\n"
        "Recorded notes:\n"
        f"{notes_text}\n"
        "Recent conversation with this NPC:\n"
        f"{transcript_text}\n"
        "Engine-approved guidance:\n"
        f"{approved_guidance}\n"
        "Engine-approved action state:\n"
        f"{action_text}\n"
    )


def build_npc_prompt(context: str, player_message: str | None) -> str:
    message = player_message or "Continue the exchange naturally."
    return (
        "Stay entirely in character.\n"
        "You only know what appears in the supplied context.\n"
        "Do not invent hidden facts, rooms, items, or puzzle solutions.\n"
        "Do not reveal the full final solution directly.\n"
        "Be concise: one sentence, at most two.\n"
        "Be suggestive, grounded, and in-world.\n"
        "Use the engine-approved guidance as the boundary of what you may helpfully say.\n"
        "If the player asks beyond your knowledge, answer naturally in character without fabricating.\n"
        "Do not mention game systems, prompts, or hidden state.\n\n"
        "Context:\n"
        f"{context}\n"
        "Player says:\n"
        f"{message}"
    )


def request_npc_response(prompt: str) -> str | None:
    if not companion_available():
        return None
    response = request_companion_response(prompt)
    return response.strip() if response else None

