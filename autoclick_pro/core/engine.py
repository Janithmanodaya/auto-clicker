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
        # Build index mapping for jumps and labels
        id_to_index: dict[str, int] = {}
        label_to_index: dict[str, int] = {}
        for i, a in enumerate(actions):
            aid = str(a.get("id") or "")
            if aid:
                id_to_index[aid] = i
            if a.get("type") == "label":
                lname = str(a.get("target") or aid)
                if lname:
                    label_to_index[lname] = i

        i = 0
        loop_iters: dict[int, int] = {}
        while i < len(actions):
            if self._stop.is_set():
                break
            while self._pause.is_set() and not self._stop.is_set():
                time.sleep(0.05)

            action = actions[i]
            try:
                next_idx = self._execute(action, id_to_index=id_to_index | label_to_index, current_index=i, actions=actions, loop_iters=loop_iters)
            except Exception as e:
                self._log.error("engine_action_error", index=i, error=str(e))
                break

            if isinstance(next_idx, int):
                i = next_idx
            else:
                i += 1

        self._emit("Idle")

    def _execute(self, action: dict, *, id_to_index: dict[str, int] | None = None, current_index: int | None = None, actions: list[dict] | None = None, loop_iters: dict[int, int] | None = None) -> int | None:
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
                # Capture current screen and run template match or feature match
                from pathlib import Path
                from autoclick_pro.util.screen import grab_screen
                from autoclick_pro.detect.template_matcher import match_template
                from autoclick_pro.detect.feature_matcher import feature_match

                tmpl = action.get("target")
                conf = float(params.get("conf", 0.85))
                method = params.get("method", "template")
                screen_path = grab_screen()
                if method == "feature":
                    res = feature_match(Path(screen_path), Path(str(tmpl)), confidence_threshold=conf)
                    # Normalize to first/best candidate
                    best = res.candidates[0] if res.candidates else None
                    found = best is not None and best.score >= conf
                    bbox = best.bbox if best else None
                    score = best.score if best else 0.0
                    self._log.info("detect_result_feature", target=tmpl, found=found, score=score, bbox=bbox, candidates=len(res.candidates))
                    self._context["last_detect"] = {"found": found, "bbox": bbox, "score": score, "candidates": [c.to_dict() for c in res.candidates]}
                else:
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

            elif t == "label":
                # No-op; labels are jump targets
                self._log.info("label", name=action.get("target") or action.get("id"))

            elif t == "loop_until":
                # Params:
                # {"label": "start", "until": {"test": "last_detect", "value": True}, "max_iters": 100}
                label = params.get("label")
                until = params.get("until", {"test": "last_detect", "value": True})
                max_iters = int(params.get("max_iters", 100))
                # Evaluate condition
                test = until.get("test", "last_detect")
                value = until.get("value", True)
                cond = False
                if test == "last_detect":
                    ld = self._context.get("last_detect")
                    cond = bool(ld and bool(ld.get("found")) == bool(value))
                elif isinstance(test, str) and test.startswith("var:"):
                    name = test.split(":", 1)[1]
                    cond = bool(self._context.get(name)) == bool(value)

                idx_key = int(current_index if current_index is not None else -1)
                if loop_iters is not None:
                    count = loop_iters.get(idx_key, 0)
                else:
                    count = 0

                if cond:
                    self._log.info("loop_until_condition_met", label=label, iters=count)
                    # continue to next action
                    return None
                elif count >= max_iters:
                    self._log.warning("loop_until_max_iters", label=label, max_iters=max_iters)
                    return None
                else:
                    # increment and jump to label
                    if loop_iters is not None:
                        loop_iters[idx_key] = count + 1
                    if label and id_to_index and label in id_to_index:
                        next_index = id_to_index[label]
                        self._log.info("loop_until_jump", label=label, next_index=next_index, iters=loop_iters.get(idx_key, 0))
                        return next_index
                    else:
                        self._log.warning("loop_until_label_not_found", label=label)
                        return None

            else:
                self._log.warning("unknown_action_type", type=t)

        if delay_after:
            time.sleep(delay_after / 1000.0)

        return None