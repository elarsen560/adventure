from __future__ import annotations

import random

from game.models import NPC


NPC_ROLE_DEFINITIONS = {
    "clue_interpreter": {
        "description": "Helps the player interpret visible documents or known clues.",
    },
    "access_insight": {
        "description": "Points toward the strongest current gating dependency.",
    },
    "hidden_detail_spotter": {
        "description": "Draws attention to an overlooked physical detail already present in the world.",
    },
    "hazard_warning": {
        "description": "Warns about the run's active environmental hazard.",
    },
    "item_gate": {
        "description": "Can hand over a bounded progression-helping item under engine-controlled conditions.",
    },
}


FEATURED_NPCS = {
    "mr_finch": {
        "id": "mr_finch",
        "display_name": "Mr. Finch",
        "short_description": "A stooped lamp-keeper in a tar-dark coat, smelling faintly of salt and paraffin.",
        "personality_style": "Dry, deliberate, and sparing with praise; sounds like a keeper who has watched many storms do their work.",
        "speech_examples": [
            "A station speaks plain enough, if you let it finish the sentence.",
            "Locks are seldom stubborn without a reason.",
        ],
        "eligible_rooms": ["front_gate", "courtyard", "foyer", "east_hall", "library"],
        "eligible_roles": ["access_insight", "clue_interpreter", "item_gate"],
        "knowledge_scope": "Observed station routines, doors, locks, and the habits of keepers.",
        "restricted_knowledge": "Must not reveal hidden item locations unless the engine explicitly approves it; must not give the final lever alignment directly.",
        "hint_style": "Measured and mildly pointed.",
        "aliases": ("finch", "mr finch", "keeper"),
    },
    "mrs_grey": {
        "id": "mrs_grey",
        "display_name": "Mrs. Grey",
        "short_description": "A neat housekeeper with rain pearls on her sleeves and an expression of calm refusal.",
        "personality_style": "Quietly exacting, courteous, and faintly severe.",
        "speech_examples": [
            "Rooms keep their own memory when people do not.",
            "One sees more by setting a thing in order than by staring at it.",
        ],
        "eligible_rooms": ["foyer", "library", "west_hall", "keepers_quarters"],
        "eligible_roles": ["hidden_detail_spotter", "clue_interpreter", "item_gate"],
        "knowledge_scope": "Private habits of the observatory household, stored papers, and what tends to be overlooked indoors.",
        "restricted_knowledge": "Must not reveal unseen rooms or the full final solution.",
        "hint_style": "Indirect, domestic, and observant.",
        "aliases": ("grey", "mrs grey", "housekeeper"),
    },
    "abel_rowse": {
        "id": "abel_rowse",
        "display_name": "Abel Rowse",
        "short_description": "A weather-beaten fisherman in a reefer coat, studying the stonework as though it were a tide chart.",
        "personality_style": "Plain-spoken, wary, and more comfortable with seawater than walls.",
        "speech_examples": [
            "Bad iron tells on itself before it parts.",
            "A man needn't love machinery to know when it means to bite.",
        ],
        "eligible_rooms": ["cliff_path", "front_gate", "courtyard", "sea_cave", "west_hall"],
        "eligible_roles": ["hazard_warning", "hidden_detail_spotter", "access_insight"],
        "knowledge_scope": "Weather, wear, strain, and the look of unsafe mechanisms.",
        "restricted_knowledge": "Must not reveal abstract code solutions or hidden archival information.",
        "hint_style": "Blunt, practical, and local.",
        "aliases": ("abel", "rowse", "fisherman"),
    },
    "sister_hale": {
        "id": "sister_hale",
        "display_name": "Sister Hale",
        "short_description": "A mission sister in a dark travelling cloak, with hands folded as though the storm were merely another liturgy.",
        "personality_style": "Gentle, steady, and grave without melodrama.",
        "speech_examples": [
            "A careful eye is often the whole of grace required.",
            "There is no shame in reading a place before crossing it.",
        ],
        "eligible_rooms": ["courtyard", "conservatory", "library", "dome_antechamber"],
        "eligible_roles": ["clue_interpreter", "hazard_warning", "access_insight"],
        "knowledge_scope": "Human motives, old observatory customs, and the emotional weight of recorded instructions.",
        "restricted_knowledge": "Must not reveal hidden machinery details unless engine-approved.",
        "hint_style": "Softly suggestive.",
        "aliases": ("hale", "sister hale", "sister"),
    },
    "captain_vale": {
        "id": "captain_vale",
        "display_name": "Captain Vale",
        "short_description": "A retired packet captain with a storm scarf, one gloved hand resting on the head of a stick.",
        "personality_style": "Authoritative, spare, and used to being obeyed without raising his voice.",
        "speech_examples": [
            "A sound station leaves no half-finished business behind it.",
            "If passage is denied, attend to the denial before the destination.",
        ],
        "eligible_rooms": ["front_gate", "foyer", "east_hall", "lift_landing", "dome_antechamber"],
        "eligible_roles": ["access_insight", "hazard_warning", "item_gate"],
        "knowledge_scope": "Transit, access, disciplined procedure, and practical sequencing.",
        "restricted_knowledge": "Must not reveal the exact final command or hidden item placements without engine approval.",
        "hint_style": "Firm but not explicit.",
        "aliases": ("vale", "captain vale", "captain"),
    },
    "miss_fenn": {
        "id": "miss_fenn",
        "display_name": "Miss Fenn",
        "short_description": "A junior astronomer with ink on her cuffs and the preoccupied gaze of a woman still solving something.",
        "personality_style": "Quick, thoughtful, and faintly distracted by patterns only she can half-finish.",
        "speech_examples": [
            "Orders and alignments are cousins, though not twins.",
            "One must be careful which mark belongs to a lock and which to the heavens.",
        ],
        "eligible_rooms": ["library", "archive", "east_hall", "orrery_dome"],
        "eligible_roles": ["clue_interpreter", "access_insight", "hidden_detail_spotter"],
        "knowledge_scope": "Observatory records, chart notation, and the difference between symbolic systems.",
        "restricted_knowledge": "Must not reveal final lever numbers unless the player already visibly has them.",
        "hint_style": "Analytical but still restrained.",
        "aliases": ("fenn", "miss fenn", "astronomer"),
    },
    "tomas_quill": {
        "id": "tomas_quill",
        "display_name": "Tomas Quill",
        "short_description": "A mechanic's assistant with blackened fingernails and a face that brightens around difficult apparatus.",
        "personality_style": "Earnest, mechanically minded, and eager to be useful without overreaching.",
        "speech_examples": [
            "A dry gear will tell against itself before a man notices.",
            "Best not to trust a machine until you've looked it in the teeth.",
        ],
        "eligible_rooms": ["workshop", "generator_room", "pump_room", "lift_landing"],
        "eligible_roles": ["hazard_warning", "access_insight", "item_gate"],
        "knowledge_scope": "Mechanical wear, maintenance, and which parts usually fail first.",
        "restricted_knowledge": "Must not reveal hidden documents or narrative secrets.",
        "hint_style": "Practical and mechanic-like.",
        "aliases": ("tomas", "quill", "assistant"),
    },
    "elia_march": {
        "id": "elia_march",
        "display_name": "Elia March",
        "short_description": "A retired chart-copyist with silver spectacles and fingers stained by old blue-black ink.",
        "personality_style": "Patient, exact, and fond of careful distinctions.",
        "speech_examples": [
            "Most confusion begins when one symbol is mistaken for another.",
            "The hand that wrote a note usually meant more than the note first says.",
        ],
        "eligible_rooms": ["library", "archive", "keepers_quarters", "foyer"],
        "eligible_roles": ["clue_interpreter", "hidden_detail_spotter", "item_gate"],
        "knowledge_scope": "Handwriting, marginalia, catalogues, and records kept for private use.",
        "restricted_knowledge": "Must not reveal hidden physical objects unless engine-approved.",
        "hint_style": "Precise and gently interpretive.",
        "aliases": ("elia", "march", "copyist"),
    },
    "dr_morrow": {
        "id": "dr_morrow",
        "display_name": "Dr. Morrow",
        "short_description": "A physician-traveller with a damp valise and an expression sharpened by sleeplessness.",
        "personality_style": "Measured, dry, and attentive to strain, fatigue, and risk.",
        "speech_examples": [
            "Neglect announces itself in posture before it announces itself in failure.",
            "One needn't be brave where caution will suffice.",
        ],
        "eligible_rooms": ["foyer", "west_hall", "generator_room", "lift_landing", "dome_antechamber"],
        "eligible_roles": ["hazard_warning", "access_insight", "hidden_detail_spotter"],
        "knowledge_scope": "Risk, stress, bodily caution, and the look of dangerous spaces.",
        "restricted_knowledge": "Must not reveal puzzle codes or final settings.",
        "hint_style": "Calmly cautionary.",
        "aliases": ("morrow", "doctor", "dr morrow"),
    },
    "old_ned_brier": {
        "id": "old_ned_brier",
        "display_name": "Old Ned Brier",
        "short_description": "An elderly groundsman in patched oilskins, with a lantern held low and a gaze turned toward practical things.",
        "personality_style": "Weathered, patient, and given to coastal sayings that still manage to be useful.",
        "speech_examples": [
            "What shines where it shouldn't is worth a second look.",
            "A hidden thing is rarely hidden from all sides at once.",
        ],
        "eligible_rooms": ["cliff_path", "front_gate", "courtyard", "conservatory", "sea_cave"],
        "eligible_roles": ["hidden_detail_spotter", "access_insight", "item_gate"],
        "knowledge_scope": "Grounds, hidden corners, practical stowage, and what keepers leave near hand.",
        "restricted_knowledge": "Must not reveal the exact final puzzle answer or unseen late-game details.",
        "hint_style": "Folksy but grounded.",
        "aliases": ("ned", "brier", "groundsman"),
    },
}


def featured_npc_ids() -> list[str]:
    return list(FEATURED_NPCS)


def featured_npc_profile(npc_id: str) -> dict | None:
    return FEATURED_NPCS.get(npc_id)


def featured_npc_entity(npc_id: str) -> NPC:
    profile = FEATURED_NPCS[npc_id]
    return NPC(
        profile["id"],
        profile["display_name"],
        profile["short_description"],
        aliases=tuple(profile.get("aliases", ())),
    )


def role_room_valid(role: str, room_id: str, hazard_room: str) -> bool:
    if role == "hazard_warning":
        return room_id == hazard_room
    if role == "item_gate":
        return room_id in {"courtyard", "foyer", "library", "west_hall", "east_hall", "sea_cave"}
    return True


def valid_role_room_pairs(profile: dict, hazard_room: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for role in profile["eligible_roles"]:
        for room_id in profile["eligible_rooms"]:
            if role_room_valid(role, room_id, hazard_room):
                pairs.append((role, room_id))
    return pairs


def generate_featured_npc(seed: int, hazard_room: str) -> tuple[str, str, str]:
    rng = random.Random(seed + 811)
    candidate_ids = [npc_id for npc_id, profile in FEATURED_NPCS.items() if valid_role_room_pairs(profile, hazard_room)]
    npc_id = rng.choice(sorted(candidate_ids))
    pairs = valid_role_room_pairs(FEATURED_NPCS[npc_id], hazard_room)
    role, room_id = rng.choice(sorted(pairs))
    return npc_id, room_id, role


def validate_featured_npc_assignment(npc_id: str | None, room_id: str | None, role: str | None, hazard_room: str) -> None:
    if not npc_id or not room_id or not role:
        raise ValueError("Featured NPC assignment is incomplete.")
    profile = featured_npc_profile(npc_id)
    if not profile:
        raise ValueError(f"Unknown featured NPC: {npc_id}")
    if room_id not in profile["eligible_rooms"]:
        raise ValueError(f"Invalid room assignment for {npc_id}: {room_id}")
    if role not in profile["eligible_roles"]:
        raise ValueError(f"Invalid role assignment for {npc_id}: {role}")
    if not role_room_valid(role, room_id, hazard_room):
        raise ValueError(f"Invalid role-room pairing for {npc_id}: {role} in {room_id}")

