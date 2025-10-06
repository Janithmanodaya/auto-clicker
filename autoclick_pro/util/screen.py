from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
from mss import mss
from PIL import Image


def grab_screen(out_path: Path | None = None) -> Path:
    """
    Capture entire primary screen to a PNG file and return the path.
    If out_path is None, writes to 'screens/screen.png' in cwd.
    """
    out = out_path or Path("screens") / "screen.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    with mss() as sct:
        mon = sct.monitors[1]
        img = sct.grab(mon)
        Image.frombytes("RGB", img.size, img.rgb).save(out)
    return out


def grab_region(x: int, y: int, w: int, h: int, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with mss() as sct:
        img = sct.grab({"top": y, "left": x, "width": w, "height": h})
        Image.frombytes("RGB", img.size, img.rgb).save(out_path)
    return out_path