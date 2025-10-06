from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

from autoclick_pro.util.nms import non_max_suppression


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


def _cluster_points(points: np.ndarray, bin_size: float = 40.0, min_cluster: int = 6) -> List[np.ndarray]:
    """
    Simple grid-based clustering of 2D points. Returns list of index arrays.
    """
    xs = points[:, 0]
    ys = points[:, 1]
    gx = np.floor(xs / bin_size).astype(int)
    gy = np.floor(ys / bin_size).astype(int)
    buckets: dict[tuple[int, int], List[int]] = {}
    for i, (bx, by) in enumerate(zip(gx, gy)):
        buckets.setdefault((bx, by), []).append(i)
    clusters = [np.array(idx_list, dtype=int) for idx_list in buckets.values() if len(idx_list) >= min_cluster]
    return clusters


def feature_match(
    screenshot_path: Path,
    template_path: Path,
    confidence_threshold: float = 0.5,
    method: str = "ORB",
    max_candidates: int = 5,
) -> FeatureMatchResult:
    """
    Feature-based matching using ORB/AKAZE + BFMatcher + RANSAC homography.
    Produces multiple candidates via simple clustering and non-maximum suppression.
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
    for pair in matches:
        if len(pair) != 2:
            continue
        m, n = pair
        if m.distance < 0.75 * n.distance:
            good.append(m)

    if len(good) < 4:
        return FeatureMatchResult([])

    pts_tmpl = np.float32([kp1[m.queryIdx].pt for m in good])
    pts_img = np.float32([kp2[m.trainIdx].pt for m in good])

    # Cluster by proximity in image space
    clusters = _cluster_points(pts_img, bin_size=40.0, min_cluster=6)
    candidates: List[Candidate] = []

    h, w = tmpl.shape[:2]
    tmpl_corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)

    for idxs in clusters:
        src = pts_tmpl[idxs].reshape(-1, 1, 2)
        dst = pts_img[idxs].reshape(-1, 1, 2)
        if src.shape[0] < 4 or dst.shape[0] < 4:
            continue
        H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
        if H is None:
            continue
        inliers = int(mask.sum()) if mask is not None else 0
        score = inliers / max(1, src.shape[0])
        projected = cv2.perspectiveTransform(tmpl_corners, H)
        xs = projected[:, 0, 0]
        ys = projected[:, 0, 1]
        x_min, y_min, x_max, y_max = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
        bbox = (x_min, y_min, max(1, x_max - x_min), max(1, y_max - y_min))
        if score >= confidence_threshold:
            candidates.append(Candidate(bbox=bbox, score=score))

    # Fallback: compute global homography if no clusters yielded candidates
    if not candidates:
        src = pts_tmpl.reshape(-1, 1, 2)
        dst = pts_img.reshape(-1, 1, 2)
        H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
        if H is not None:
            inliers = int(mask.sum()) if mask is not None else 0
            score = inliers / max(1, src.shape[0])
            projected = cv2.perspectiveTransform(tmpl_corners, H)
            xs = projected[:, 0, 0]
            ys = projected[:, 0, 1]
            x_min, y_min, x_max, y_max = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            bbox = (x_min, y_min, max(1, x_max - x_min), max(1, y_max - y_min))
            candidates.append(Candidate(bbox=bbox, score=score))

    # Non-maximum suppression on candidate boxes
    boxes = np.array([c.bbox for c in candidates], dtype=np.int32)
    scores = np.array([c.score for c in candidates], dtype=np.float32)
    keep_idx = non_max_suppression(boxes, scores, iou_threshold=0.3)
    candidates = [candidates[i] for i in keep_idx]

    candidates.sort(key=lambda c: c.score, reverse=True)
    return FeatureMatchResult(candidates=candidates[:max_candidates])