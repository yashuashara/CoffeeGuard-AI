"""
CoffeeGuard AI v2 - feature pipeline (no PyTorch / TensorFlow needed)
---------------------------------------------------------------------
Three ideas combined:

1. LEAF CROP  - find the leaf (same mask as the severity scan), crop to it
                and rotate it to landscape, so no pixels are wasted on
                background and the leaf is always the same way round.
2. ZOOM TILES - a coffee leaf is ~2:1, so squashing it into one 224x224
                image shrinks lesions to a few pixels. We also look at 3
                overlapping square tiles along the leaf, so the CNN sees
                lesions ~2x larger. Tile features are mean- and max-pooled
                (max-pooling keeps a single strong lesion from being
                averaged away).
3. LESION FEATURES - hand-crafted colour statistics of the lesion pixels
                (rust = orange, Phoma = dark brown/black, miner = tan
                trails, Cercospora = brown spot with yellow halo) plus
                lesion %, spot count and spot sizes.

Final vector = [whole-leaf CNN | mean tile CNN | max tile CNN] (3 x 1280)
             + 64 lesion features.
"""

import cv2
import numpy as np

import cnn_features
from severity import _leaf_mask, _lesion_mask

N_HAND = 64


def _find_leaf(img):
    """Returns (crop, mask_of_crop) or (img, None) if no sensible leaf found."""
    h, w = img.shape[:2]
    s = 384.0 / max(h, w)
    small = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(cv2.GaussianBlur(small, (3, 3), 0), cv2.COLOR_BGR2HSV)
    leaf = _leaf_mask(hsv)
    if leaf is None:
        return img, None
    frac = np.count_nonzero(leaf) / leaf.size
    if not (0.03 < frac < 0.95):
        return img, None
    ys, xs = np.nonzero(leaf)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    my, mx = int((y1 - y0) * 0.06) + 2, int((x1 - x0) * 0.06) + 2
    y0, x0 = max(0, y0 - my), max(0, x0 - mx)
    y1, x1 = min(small.shape[0], y1 + my), min(small.shape[1], x1 + mx)
    crop = img[int(y0 / s):int(y1 / s), int(x0 / s):int(x1 / s)]
    if crop.size == 0:
        return img, None
    return crop, leaf


def _landscape(img):
    h, w = img.shape[:2]
    return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE) if h > w else img


def views(img):
    """Whole leaf + 3 overlapping square zoom tiles along its length."""
    crop, _ = _find_leaf(img)
    crop = _landscape(crop)
    h, w = crop.shape[:2]
    tiles = []
    side = h
    if w > h * 1.15:
        for x in np.linspace(0, w - side, 3).astype(int):
            tiles.append(crop[:, x:x + side])
    else:  # roughly square leaf/close-up: use 3 vertical-ish crops of a 2x zoom
        side = int(min(h, w) * 0.7)
        for x in np.linspace(0, w - side, 3).astype(int):
            y = (h - side) // 2
            tiles.append(crop[y:y + side, x:x + side])
    return crop, tiles


def lesion_features(img):
    """64 hand-crafted colour/shape features of the lesions on the leaf."""
    h, w = img.shape[:2]
    s = 512.0 / max(h, w)
    small = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA) if s < 1 else img
    hsv = cv2.cvtColor(cv2.GaussianBlur(small, (3, 3), 0), cv2.COLOR_BGR2HSV)
    f = np.zeros(N_HAND, np.float32)
    leaf = _leaf_mask(hsv)
    if leaf is None or not leaf.any():
        return f
    lesion = _lesion_mask(hsv, leaf)
    lp = leaf > 0
    les = lesion > 0
    n_leaf = lp.sum()
    n_les = les.sum()
    H, S, V = hsv[..., 0].astype(np.float32), hsv[..., 1].astype(np.float32), hsv[..., 2].astype(np.float32)

    f[0] = n_les / n_leaf
    n, _, stats, _ = cv2.connectedComponentsWithStats(lesion, connectivity=8)
    areas = stats[1:, cv2.CC_STAT_AREA] / n_leaf if n > 1 else np.zeros(1)
    areas = areas[areas > 2e-4] if (areas > 2e-4).any() else np.zeros(1)
    f[1] = np.log1p(len(areas)) if areas.any() else 0
    f[2], f[3], f[4] = areas.max(), areas.mean(), np.median(areas)

    if n_les:
        for j, ch in enumerate([H, S, V]):
            v = ch[les]
            f[5 + 2 * j], f[6 + 2 * j] = v.mean() / 180 if j == 0 else v.mean() / 255, v.std() / 255
        f[11] = (V[les] < 60).mean()                                  # black necrotic (Phoma)
        f[12] = ((H[les] < 21) & (S[les] > 140) & (V[les] > 110)).mean()  # bright orange (rust)
        f[13] = (S[les] < 110).mean()                                 # pale/tan (miner)
        hist = np.histogram(H[les], bins=12, range=(0, 24))[0].astype(np.float32)
        f[14:26] = hist / max(hist.sum(), 1)
        vh = np.histogram(V[les], bins=8, range=(0, 256))[0].astype(np.float32)
        f[26:34] = vh / max(vh.sum(), 1)
        # ring around lesions: yellow halo = Cercospora / rust chlorosis
        ring = cv2.dilate(lesion, np.ones((7, 7), np.uint8), iterations=2) > 0
        ring = ring & ~les & lp
        if ring.any():
            f[34] = ((H[ring] >= 20) & (H[ring] <= 32) & (S[ring] > 90)).mean()
            f[35] = H[ring].mean() / 180
            f[36] = S[ring].mean() / 255

    # whole-leaf colour (yellowing, overall tone)
    for j, (ch, rng) in enumerate([(H, (0, 90)), (S, (0, 256)), (V, (0, 256))]):
        hh = np.histogram(ch[lp], bins=8, range=rng)[0].astype(np.float32)
        f[37 + 8 * j:45 + 8 * j] = hh / max(hh.sum(), 1)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_32F)
    f[61] = np.log1p(lap[lp].var())
    f[62] = np.log1p(lap[les].var()) if n_les else 0
    f[63] = n_leaf / leaf.size
    return f


def extract(images_bgr):
    """List of BGR images -> (N, 3*1280 + 64) feature matrix."""
    batch, owners = [], []
    for k, im in enumerate(images_bgr):
        whole, tiles = views(im)
        batch.append(whole)
        batch.extend(tiles)
        owners.append(len(tiles))
    emb = []
    for i in range(0, len(batch), 32):
        emb.append(cnn_features.embed(batch[i:i + 32]))
    emb = np.vstack(emb)
    out, pos = [], 0
    for k, im in enumerate(images_bgr):
        nt = owners[k]
        whole = emb[pos]
        tiles = emb[pos + 1:pos + 1 + nt]
        pos += 1 + nt
        out.append(np.concatenate([whole, tiles.mean(0), tiles.max(0), lesion_features(im)]))
    return np.array(out, np.float32)
