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
        for idx, action in enumerate(actions):
            if self._stop.is_set():
                break
            while self._pause.is_set() and not self._stop.is_set():
                time.sleep(0.05)

            try:
                self._execute(action)
            except Exception as e:
                self._log.error("engine_action_error", index=idx, error=str(e))
                break

        self._emit("Idle")

    def _execute(self, action: dict) -> None:
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

            else:
                self._log.warning("unknown_action_type", type=t)

        if delay_after:
            time.sleep(delay_after / 1000.0)