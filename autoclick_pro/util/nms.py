from __future__ import annotations

import numpy as np


def iou(box_a: np.ndarray, box_b: np.ndarray) -> float:
    """
    Intersection over Union for axis-aligned boxes in format [x, y, w, h].
    """
    ax, ay, aw, ah = box_a
    bx, by, bw, bh = box_b
    ax2, ay2 = ax + aw, ay + ah
    bx2, by2 = bx + bw, by + bh
    ix1, iy1 = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return float(inter) / float(union) if union > 0 else 0.0


def non_max_suppression(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float = 0.3) -> list[int]:
    """
    Greedy NMS. Returns indices to keep.
    """
    if boxes.size == 0:
        return []
    idxs = scores.argsort()[::-1]
    keep: list[int] = []
    while idxs.size > 0:
        i = int(idxs[0])
        keep.append(i)
        if idxs.size == 1:
            break
        rest = idxs[1:]
        suppr = []
        bi = boxes[i]
        for j in rest:
            bj = boxes[int(j)]
            if iou(bi, bj) > iou_threshold:
                suppr.append(int(j))
        idxs = np.array([k for k in rest if int(k) not in suppr], dtype=int)
    return keep