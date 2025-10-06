from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from autoclick_pro.data.model import Action, Macro, Project


def save_project(path: Path, project: Project) -> None:
    def ser_action(a: Action) -> dict[str, Any]:
        return {
            "id": a.id,
            "type": a.type,
            "target": a.target,
            "params": a.params,
            "delay_before_ms": a.delay_before_ms,
            "delay_after_ms": a.delay_after_ms,
            "repeat_count": a.repeat_count,
        }

    def ser_macro(m: Macro) -> dict[str, Any]:
        return {
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "timeline": [ser_action(a) for a in m.timeline],
            "triggers": m.triggers,
        }

    data = {
        "name": project.name,
        "version": project.version,
        "macros": [ser_macro(m) for m in project.macros],
        "keymaps": project.keymaps,
        "objects": project.objects,
        "global_settings": project.global_settings,
        "metadata": project.metadata,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_project(path: Path) -> Project:
    raw = json.loads(path.read_text(encoding="utf-8"))

    macros: list[Macro] = []
    for m in raw.get("macros", []):
        acts: list[Action] = []
        for a in m.get("timeline", []):
            acts.append(
                Action(
                    id=str(a.get("id", "")),
                    type=str(a.get("type", "")),
                    target=a.get("target"),
                    params=a.get("params", {}),
                    delay_before_ms=int(a.get("delay_before_ms", 0)),
                    delay_after_ms=int(a.get("delay_after_ms", 0)),
                    repeat_count=int(a.get("repeat_count", 1)),
                )
            )
        macros.append(Macro(id=str(m.get("id", "")), name=str(m.get("name", "")), description=str(m.get("description", "")), timeline=acts, triggers=m.get("triggers", [])))

    return Project(
        name=str(raw.get("name", "Project")),
        version=str(raw.get("version", "0.1")),
        macros=macros,
        keymaps=raw.get("keymaps", []),
        objects=raw.get("objects", []),
        global_settings=raw.get("global_settings", {"default_confidence": 0.85, "anti_detection": False}),
        metadata=raw.get("metadata", {}),
    )