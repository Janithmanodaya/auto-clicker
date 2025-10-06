from __future__ import annotations

import time
from typing import Iterable

import pyautogui
from pynput.keyboard import Controller, Key


class Mouse:
    def __init__(self) -> None:
        # pyautogui failsafe can be disabled if desired; keep enabled by default
        pyautogui.FAILSAFE = True

    def click(self, x: int | None, y: int | None, button: str = "left") -> None:
        if x is not None and y is not None:
            pyautogui.moveTo(x, y, duration=0.0)
        pyautogui.click(button=button)

    def move(self, x: int, y: int, duration: float = 0.0) -> None:
        pyautogui.moveTo(x, y, duration=duration)

    def scroll(self, clicks: int) -> None:
        pyautogui.scroll(clicks)


class Keyboard:
    def __init__(self) -> None:
        self._ctl = Controller()

    def type_text_sequence(self, sequence: Iterable[str], delay_ms: int = 0) -> None:
        d = max(0, delay_ms) / 1000.0
        for item in sequence:
            if item.upper() in {"ENTER", "TAB", "ESC"}:
                key = getattr(Key, item.lower())
                self._ctl.press(key)
                self._ctl.release(key)
            else:
                # Treat as literal text
                self._ctl.type(item)
            if d:
                time.sleep(d)

    def press_keys(self, keys: Iterable[str], hold_ms: int = 50) -> None:
        """
        Press keys as a chord, e.g. ["ctrl", "shift", "s"]
        """
        resolved: list[Key | str] = []
        for k in keys:
            lk = k.lower()
            try:
                resolved.append(getattr(Key, lk))
            except AttributeError:
                resolved.append(k)

        for k in resolved:
            self._ctl.press(k)
        time.sleep(max(0, hold_ms) / 1000.0)
        for k in reversed(resolved):
            self._ctl.release(k)