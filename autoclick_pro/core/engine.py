from __future__ import annotations

import threading
import time
from typing import Callable, Iterable, Optional

from autoclick_pro.input.simulator import Mouse, Keyboard
from autoclick_pro.logging.logger import get_logger


class Engine:
    """
    Minimal macro engine: executes a timeline of actions.
    Designed to run in a worker thread to keep UI responsive.
    """

    def __init__(self) -> None:
        self._log = get_logger()
        self._worker: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._simulation = True
        self._on_status: Optional[Callable[[str], None]] = None

        # Input backends
        self.mouse = Mouse()
        self.keyboard = Keyboard()

    # Control

    def set_simulation(self, enabled: bool) -> None:
        self._simulation = enabled
        self._log.info("engine_simulation_mode", enabled=enabled)

    def on_status(self, cb: Callable[[str], None]) -> None:
        self._on_status = cb

    def start(self, actions: Iterable[dict]) -> None:
        """Start executing actions in a new thread."""
        if self._worker and self._worker.is_alive():
            self._log.warning("engine_already_running")
            return
        self._stop.clear()
        self._pause.clear()
        self._context = {"last_detect": None}
        self._worker = threading.Thread(target=self._run, args=(list(actions),), daemon=True)
        self._worker.start()

    def pause(self) -> None:
        self._pause.set()
        self._emit("Paused")

    def resume(self) -> None:
        self._pause.clear()
        self._emit("Resumed")

    def stop(self) -> None:
        self._stop.set()
        self._emit("Stopped")

    def estop(self) -> None:
        self._stop.set()
        # Optionally add low-level abort hooks if using OS APIs
        self._emit("EMERGENCY STOP")

    # Internal

    def _emit(self, msg: str) -> None:
        if self._on_status:
            self._on_status(msg)

    def _run(self, actions: list[dict]) -> None:
        self._emit("Running")
        # Build index mapping for jumps
        id_to_index: dict[str, int] = {}
        for i, a in enumerate(actions):
            aid = str(a.get("id") or "")
            if aid:
                id_to_index[aid] = i

        i = 0
        while i < len(actions):
            if self._stop.is_set():
                break
            while self._pause.is_set() and not self._stop.is_set():
                time.sleep(0.05)

            action = actions[i]
            try:
                next_idx = self._execute(action, id_to_index=id_to_index, current_index=i, actions=actions)
            except Exception as e:
                self._log.error("engine_action_error", index=i, error=str(e))
                break

            if isinstance(next_idx, int):
                i = next_idx
            else:
                i += 1

        self._emit("Idle")

    def _execute(self, action: dict, *, id_to_index: dict[str, int] | None = None, current_index: int | None = None, actions: list[dict] | None = None) -> int | None:
        t = action.get("type")
        params = action.get("params", {})
        delay_before = int(action.get("delay_before_ms", 0))
        delay_after = int(action.get("delay_after_ms", 0))
        repeat = int(action.get("repeat_count", 1))

        if delay_before:
            time.sleep(delay_before / 1000.0)

        for _ in range(max(1, repeat)):
            if self._stop.is_set():
                break

            if t == "wait":
                ms = int(params.get("ms", 0))
                time.sleep(ms / 1000.0)

            elif t == "mouse_click":
                x = params.get("x")
                y = params.get("y")
                button = params.get("button", "left")
                if not self._simulation:
                    self.mouse.click(x, y, button)
                self._log.info("mouse_click", x=x, y=y, button=button)

            elif t == "key_sequence":
                seq = params.get("sequence", [])
                text_mode = params.get("text_mode", True)
                if not self._simulation:
                    if text_mode:
                        self.keyboard.type_text_sequence(seq)
                    else:
                        self.keyboard.press_keys(seq)
                self._log.info("key_sequence", sequence=seq, text_mode=text_mode)

            elif t == "detect":
                # Capture current screen and run template match
                from pathlib import Path
                from autoclick_pro.util.screen import grab_screen
                from autoclick_pro.detect.template_matcher import match_template

                tmpl = action.get("target")
                conf = float(params.get("conf", 0.85))
                screen_path = grab_screen()
                res = match_template(Path(screen_path), Path(str(tmpl)), confidence_threshold=conf)
                self._log.info("detect_result", target=tmpl, found=res.found, score=res.score, bbox=res.bbox)
                self._context["last_detect"] = {"found": res.found, "bbox": res.bbox, "score": res.score}
                action.setdefault("result", self._context["last_detect"])

            elif t == "conditional_jump":
                # Example params:
                # {"test": "last_detect", "true_target": "a5", "false_target": "a10"}
                test = params.get("test", "last_detect")
                true_target = params.get("true_target")
                false_target = params.get("false_target")
                cond = False
                if test == "last_detect":
                    ld = self._context.get("last_detect")
                    cond = bool(ld and ld.get("found"))
                elif isinstance(test, str) and test.startswith("var:"):
                    # Optional future var check
                    name = test.split(":", 1)[1]
                    cond = bool(self._context.get(name))
                # Determine next index
                target_id = true_target if cond else false_target
                if target_id and id_to_index and target_id in id_to_index:
                    next_index = id_to_index[target_id]
                    self._log.info("conditional_jump", cond=cond, target=target_id, index=next_index)
                    # return next index for outer loop to jump
                    return next_index
                else:
                    self._log.info("conditional_jump_no_target", cond=cond)
                    # fall-through (continue to next action)

            else:
                self._log.warning("unknown_action_type", type=t)

        if delay_after:
            time.sleep(delay_after / 1000.0)

        return None