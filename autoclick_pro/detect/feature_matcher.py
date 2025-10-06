from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np


@dataclass
class Candidate:
    bbox: Tuple[int, int, int, int]
    score: float  # ratio of inliers / matches

    def to_dict(self) -> dict:
        x, y, w, h = self.bbox
        return {"bbox": [x, y, w, h], "score": float(self.score)}


@dataclass
class FeatureMatchResult:
    candidates: List[Candidate]


def feature_match(
    screenshot_path: Path,
    template_path: Path,
    confidence_threshold: float = 0.5,
    method: str = "ORB",
    max_candidates: int = 5,
) -> FeatureMatchResult:
    """
    Feature-based matching using ORB/AKAZE + BFMatcher + RANSAC homography.
    Returns multiple candidate bboxes sorted by score.
    """
    img_color = cv2.imread(str(screenshot_path), cv2.IMREAD_COLOR)
    tmpl_color = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
    if img_color is None or tmpl_color is None:
        return FeatureMatchResult([])

    img = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    tmpl = cv2.cvtColor(tmpl_color, cv2.COLOR_BGR2GRAY)

    if method.upper() == "AKAZE":
        det = cv2.AKAZE_create()
    else:
        det = cv2.ORB_create(nfeatures=2000)

    kp1, des1 = det.detectAndCompute(tmpl, None)
    kp2, des2 = det.detectAndCompute(img, None)
    if des1 is None or des2 is None or len(kp1) < 4 or len(kp2) < 4:
        return FeatureMatchResult([])

    # Use Hamming distance for ORB/AKAZE
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(des1, des2, k=2)

    good: list[cv2.DMatch] = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good.append(m)

    if len(good) < 4:
        return FeatureMatchResult([])

    # Cluster matches by proximity (basic approach)
    pts_tmpl = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    pts_img = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    # Compute homography
    H, mask = cv2.findHomography(pts_tmpl, pts_img, cv2.RANSAC, 5.0)
    if H is None:
        return FeatureMatchResult([])

    inliers = int(mask.sum()) if mask is not None else 0
    score = inliers / max(1, len(good))

    h, w = tmpl.shape[:2]
    corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    projected = cv2.perspectiveTransform(corners, H)
    xs = projected[:, 0, 0]
    ys = projected[:, 0, 1]
    x_min, y_min, x_max, y_max = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    bbox = (x_min, y_min, x_max - x_min, y_max - y_min)

    candidates = [Candidate(bbox=bbox, score=score)]
    # Note: For multiple candidates, a robust approach would run sliding window clusters;
    # here we return a single candidate derived from homography. Placeholder for future NMS.

    candidates.sort(key=lambda c: c.score, reverse=True)
    return FeatureMatchResult(candidates=candidates[:max_candidates])