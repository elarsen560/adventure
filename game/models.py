from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    description: str
    aliases: tuple[str, ...] = ()
    portable: bool = True
    use_text: str | None = None


@dataclass(frozen=True)
class NPC:
    id: str
    name: str
    description: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Room:
    id: str
    name: str
    description: str
    exits: dict[str, str]
    features: dict[str, str] = field(default_factory=dict)
    aliases: tuple[str, ...] = ()
