from __future__ import annotations

from pathlib import Path
from typing import Tuple

import cv2


def annotate_detection(screenshot_path: Path, bbox: Tuple[int, int, int, int] | None, score: float, out_path: Path | None = None) -> Path:
    """
    Draw bbox and score onto screenshot and save to out_path.
    """
    img = cv2.imread(str(screenshot_path))
    if img is None:
        raise RuntimeError(f"Failed to load screenshot: {screenshot_path}")
    if bbox is not None:
        x, y, w, h = bbox
        cv2.rectangle(img, (x, y), (x + w, y + h), (80, 180, 255), 2)
        label = f"score={score:.3f}"
        cv2.putText(img, label, (x, max(0, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80, 180, 255), 1, cv2.LINE_AA)
    else:
        cv2.putText(img, "No match", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (80, 80, 80), 2, cv2.LINE_AA)
    out = out_path or (Path("screens") / "annotated.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), img)
    return out