from __future__ import annotations

import threading
import time
from typing import List, Optional

from pynput import mouse, keyboard

from autoclick_pro.data.model import Action
from autoclick_pro.logging.logger import get_logger


class Recorder:
    """
    Records mouse and keyboard events into normalized Actions.
    """
    def __init__(self) -> None:
        self._log = get_logger()
        self._mouse_listener: Optional[mouse.Listener] = None
        self._key_listener: Optional[keyboard.Listener] = None
        self._running = False
        self._start_ts = 0.0
        self._actions: List[Action] = []
        self._lock = threading.Lock()

    def start(self) -> None:
        if self._running:
            return
        self._actions.clear()
        self._start_ts = time.time()
        self._running = True

        self._mouse_listener = mouse.Listener(on_click=self._on_click)
        self._key_listener = keyboard.Listener(on_press=self._on_key_press)
        self._mouse_listener.start()
        self._key_listener.start()
        self._log.info("recorder_started")

    def stop(self) -> List[Action]:
        self._running = False
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._key_listener:
            self._key_listener.stop()
        self._log.info("recorder_stopped", count=len(self._actions))
        # Add small waits between events to preserve timing roughly
        return list(self._actions)

    # Handlers

    def _elapsed_ms(self) -> int:
        return int((time.time() - self._start_ts) * 1000)

    def _on_click(self, x: int, y: int, button, pressed: bool) -> None:
        if not self._running or not pressed:
            return
        with self._lock:
            aid = f"a{len(self._actions)+1}"
            self._actions.append(Action(id=aid, type="mouse_click", target=None, params={"x": x, "y": y, "button": str(button).split(".")[-1]}))

    def _on_key_press(self, key) -> None:
        if not self._running:
            return
        with self._lock:
            aid = f"a{len(self._actions)+1}"
            # Convert key to string
            try:
                txt = key.char if hasattr(key, "char") and key.char else str(key)
            except Exception:
                txt = str(key)
            self._actions.append(Action(id=aid, type="key_sequence", target=None, params={"sequence": [txt]}))