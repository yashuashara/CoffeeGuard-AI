"""
CoffeeGuard AI - Lesion Severity Scan
-------------------------------------
Estimates HOW MUCH of the leaf is damaged (not just WHICH disease) and
produces a "scan" overlay image that highlights the damaged tissue.

How it works (pure OpenCV, no extra model, ~20 ms, fits Render free tier):
  1. Leaf mask   = largest connected blob of leaf-coloured pixels
                   (healthy green + lesion browns/oranges/yellows),
                   with holes filled so lesions inside the leaf count.
  2. Lesion mask = pixels INSIDE the leaf that are NOT healthy green:
                   rust orange/yellow, necrotic brown, dark Phoma spots,
                   pale miner trails.
  3. Severity %  = lesion pixels / leaf pixels * 100
  4. Overlay     = healthy tissue dimmed, lesions painted as a red-amber
                   heatmap with a glowing outline, leaf outlined in green.

Severity bands follow the common field-scouting idea of "% leaf area
affected". They are an ESTIMATE from colour, not a lab measurement -
say so honestly in the pitch.
"""

import base64

import cv2
import numpy as np

MAX_SIDE = 640  # keep memory + response size small

SEVERITY_BANDS = [
    # (upper % limit, key, colour)
    (5.0, "minimal", "#22c55e"),
    (15.0, "mild", "#eab308"),
    (35.0, "moderate", "#f97316"),
    (101.0, "severe", "#ef4444"),
]


def _resize(img):
    h, w = img.shape[:2]
    scale = MAX_SIDE / max(h, w)
    if scale < 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def _leaf_mask(hsv):
    green = cv2.inRange(hsv, (25, 40, 40), (95, 255, 255))
    lesion_colours = cv2.inRange(hsv, (5, 90, 20), (30, 255, 255))
    combined = cv2.bitwise_or(green, lesion_colours)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)

    n, labels, stats, _ = cv2.connectedComponentsWithStats(combined, connectivity=8)
    if n <= 1:
        return None
    largest = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
    leaf = np.uint8(labels == largest) * 255

    # Fill holes: dark Phoma spots / miner trails inside the leaf are leaf too
    contours, _ = cv2.findContours(leaf, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(leaf)
    cv2.drawContours(filled, contours, -1, 255, thickness=cv2.FILLED)
    return filled


def _lesion_mask(hsv, leaf):
    h, s, v = cv2.split(hsv)

    # Hue split measured on the dataset samples: lesion browns/oranges sit at
    # OpenCV hue ~8-21, while healthy (incl. yellow-green leaves and the pale
    # midrib) sit at ~23-90. Keeping that gap stops normal yellowing from
    # being counted as disease.
    healthy_green = cv2.inRange(hsv, (23, 35, 45), (90, 255, 255))
    rust_orange = cv2.inRange(hsv, (5, 110, 70), (21, 255, 255))      # rust pustules
    necrotic_brown = cv2.inRange(hsv, (0, 45, 25), (21, 255, 190))    # Phoma / miner blotches
    very_dark = cv2.inRange(v, 0, 50)                                  # black necrotic centres

    lesion = rust_orange | necrotic_brown | very_dark
    lesion = cv2.bitwise_and(lesion, cv2.bitwise_not(healthy_green))
    lesion = cv2.bitwise_and(lesion, leaf)

    # Ignore the thin rim at the leaf edge (shadows / background bleed)
    rim_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    inner_leaf = cv2.erode(leaf, rim_kernel, iterations=1)
    lesion = cv2.bitwise_and(lesion, inner_leaf)

    # Remove salt noise, merge nearby specks into lesions
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    lesion = cv2.morphologyEx(lesion, cv2.MORPH_OPEN, kernel, iterations=1)
    lesion = cv2.morphologyEx(lesion, cv2.MORPH_CLOSE, kernel, iterations=1)
    return lesion


def _overlay(img, leaf, lesion):
    out = img.copy()

    # Background: darken + desaturate so the leaf pops
    bg = leaf == 0
    grey = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    out[bg] = (grey[bg] * 0.25).astype(np.uint8)

    # Healthy tissue: slightly dimmed, cool green tint
    healthy = (leaf > 0) & (lesion == 0)
    tint = np.zeros_like(img)
    tint[:] = (90, 200, 60)  # BGR green
    out[healthy] = cv2.addWeighted(img, 0.55, tint, 0.15, 0)[healthy]

    # Lesions: heatmap by distance-to-lesion-core (hot centre, amber edge)
    if lesion.any():
        dist = cv2.distanceTransform(lesion, cv2.DIST_L2, 5)
        dist = cv2.GaussianBlur(dist, (0, 0), 3)
        norm = np.clip(dist / (np.percentile(dist[lesion > 0], 95) + 1e-6), 0, 1)
        heat_idx = (120 + norm * 135).astype(np.uint8)  # amber -> red in INFERNO-ish range
        heat = cv2.applyColorMap(heat_idx, cv2.COLORMAP_INFERNO)
        hot = lesion > 0
        out[hot] = cv2.addWeighted(img, 0.30, heat, 0.70, 0)[hot]

        # Glowing lesion outline
        glow = cv2.dilate(lesion, np.ones((5, 5), np.uint8), iterations=1) - lesion
        glow = cv2.GaussianBlur(glow, (0, 0), 1.5)
        glow_f = (glow.astype(np.float32) / 255.0)[..., None]
        out = (out * (1 - glow_f) + np.array([40, 200, 255]) * glow_f).astype(np.uint8)

    # Leaf outline
    contours, _ = cv2.findContours(leaf, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(out, contours, -1, (94, 197, 34), 2, cv2.LINE_AA)
    return out


def _to_data_url(img, quality=82):
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return "data:image/jpeg;base64," + base64.b64encode(buf).decode("ascii") if ok else None


def severity_scan(img):
    """
    Returns a dict:
        percent       float, % of leaf area showing lesions
        level         'minimal' | 'mild' | 'moderate' | 'severe'
        color         hex colour for the level
        lesion_count  number of separate lesion spots
        overlay       data URL (JPEG) of the scan visualisation
        original      data URL (JPEG) of the resized original (for the slider)
    or None if no leaf region is found.
    """
    img = _resize(img)
    blurred = cv2.GaussianBlur(img, (3, 3), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    leaf = _leaf_mask(hsv)
    if leaf is None or leaf.sum() == 0:
        return None
    lesion = _lesion_mask(hsv, leaf)

    leaf_px = int(np.count_nonzero(leaf))
    lesion_px = int(np.count_nonzero(lesion))
    percent = round(100.0 * lesion_px / max(leaf_px, 1), 1)

    n, _, stats, _ = cv2.connectedComponentsWithStats(lesion, connectivity=8)
    min_spot = max(12, leaf_px // 4000)
    lesion_count = int(np.sum(stats[1:, cv2.CC_STAT_AREA] >= min_spot)) if n > 1 else 0

    level, color = "severe", "#ef4444"
    for limit, key, col in SEVERITY_BANDS:
        if percent < limit:
            level, color = key, col
            break

    return {
        "percent": percent,
        "level": level,
        "color": color,
        "lesion_count": lesion_count,
        "overlay": _to_data_url(_overlay(img, leaf, lesion)),
        "original": _to_data_url(img),
    }
