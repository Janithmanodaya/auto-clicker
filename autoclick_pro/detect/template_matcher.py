from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np


@dataclass
class MatchResult:
    found: bool
    bbox: Optional[Tuple[int, int, int, int]]
    score: float


def match_template(
    screenshot_path: Path,
    template_path: Path,
    confidence_threshold: float = 0.85,
    roi: Optional[Tuple[int, int, int, int]] = None,
    method: int = cv2.TM_CCOEFF_NORMED,
) -> MatchResult:
    """
    Basic template matcher using OpenCV normalized correlation.
    Supports optional ROI (x, y, w, h).
    """
    img = cv2.imread(str(screenshot_path), cv2.IMREAD_COLOR)
    tmpl = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
    if img is None or tmpl is None:
        return MatchResult(False, None, 0.0)

    if roi is not None:
        x, y, w, h = roi
        x = max(0, x)
        y = max(0, y)
        w = max(1, w)
        h = max(1, h)
        img = img[y : y + h, x : x + w].copy()

    # Multi-scale search (coarse; small pyramid)
    scales = [1.0, 0.9, 0.8, 1.1]
    best_score = -1.0
    best_bbox = None

    for s in scales:
        new_w = max(1, int(tmpl.shape[1] * s))
        new_h = max(1, int(tmpl.shape[0] * s))
        resized = cv2.resize(tmpl, (new_w, new_h), interpolation=cv2.INTER_AREA)
        res = cv2.matchTemplate(img, resized, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        score = max_val
        if score > best_score:
            best_score = score
            top_left = max_loc
            h, w = resized.shape[:2]
            best_bbox = (top_left[0], top_left[1], w, h)

    found = best_score >= confidence_threshold
    return MatchResult(found, best_bbox, float(best_score))