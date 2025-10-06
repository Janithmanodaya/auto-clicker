from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Action:
    id: str
    type: str
    target: Optional[str] = None
    params: dict[str, Any] = field(default_factory=dict)
    delay_before_ms: int = 0
    delay_after_ms: int = 0
    repeat_count: int = 1


@dataclass
class Macro:
    id: str
    name: str
    description: str = ""
    timeline: List[Action] = field(default_factory=list)
    triggers: List[dict] = field(default_factory=list)


@dataclass
class Project:
    name: str
    version: str = "0.1"
    macros: List[Macro] = field(default_factory=list)
    keymaps: List[dict] = field(default_factory=list)
    objects: List[dict] = field(default_factory=list)
    global_settings: dict[str, Any] = field(default_factory=lambda: {"default_confidence": 0.85, "anti_detection": False})
    metadata: dict[str, Any] = field(default_factory=dict)