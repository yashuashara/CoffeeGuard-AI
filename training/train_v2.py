"""
CoffeeGuard AI - train the v2 model (MobileNetV2 transfer learning)
==================================================================
Reproduces models/coffeeguard_v2.npz.

    python training/train_v2.py --data dataset path/to/lara_dataset

Each --data folder has one sub-folder per class (healthy, miner, rust, phoma,
optionally cercospora). Several datasets can be combined.

What it does
1. Finds "twin" photos (flipped/rotated copies of the same leaf, cosine
   similarity >= 0.97 of their MobileNetV2 embeddings) and keeps every copy of
   a leaf on the SAME side of the train/val/test split, so the test score is
   for leaves the model has truly never seen.
2. Augments training photos (flips, lighting, rotation, cluttered backgrounds).
3. Features: MobileNetV2 embedding of the cropped leaf + 3 zoom tiles
   (mean & max pooled) + 64 lesion-colour features  ->  3,904 numbers.
4. Logistic regression, C and lesion-feature weight chosen on validation.
5. Reports test accuracy on clean AND field-like photos, then refits on all
   photos and exports plain NumPy weights for app.py.
"""
import argparse
import os
import sys

import cv2
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import cnn_features    # noqa: E402
import leaf_features   # noqa: E402

CLASSES = ["healthy", "miner", "rust", "phoma", "cercospora"]
D = 1280


def read(path, side=512):
    img = cv2.imread(path)
    h, w = img.shape[:2]
    s = side / max(h, w)
    return cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA) if s < 1 else img


def put_on_background(img, rng, field=False):
    """Rotate, re-light and paste the leaf on a cluttered soil/grass-like background."""
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rng.uniform(-35, 35) if field else rng.uniform(-90, 90),
                                rng.uniform(0.85, 1.0))
    rot = cv2.warpAffine(img, M, (w, h), borderValue=(255, 255, 255))
    g = 16 if field else int(rng.integers(4, 40))
    bg = cv2.resize(rng.integers(0, 255, (h // g + 1, w // g + 1, 3), dtype=np.uint8), (w, h))
    tone = np.array(rng.choice([[40, 70, 110], [40, 90, 60], [70, 90, 100]]), np.float32) if field else rng.uniform(20, 160, 3)
    bg = np.clip(cv2.GaussianBlur(bg, (0, 0), 6).astype(np.float32) * 0.35 + tone, 0, 255).astype(np.uint8)
    hsv = cv2.cvtColor(rot, cv2.COLOR_BGR2HSV)
    leaf = (hsv[..., 1] > 35) | (hsv[..., 2] < 120)
    leaf = cv2.morphologyEx(leaf.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0
    out = cv2.convertScaleAbs(np.where(leaf[..., None], rot, bg), alpha=rng.uniform(0.7, 1.2), beta=rng.uniform(-25, 20))
    if field:
        k = int(rng.choice([1, 3, 5]))
        out = cv2.GaussianBlur(out, (k, k), 0) if k > 1 else out
        ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, int(rng.integers(55, 85))])
        out = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    return out


def augment(img, k, rng):
    return [lambda: img, lambda: cv2.flip(img, 1), lambda: cv2.flip(img, 0),
            lambda: cv2.convertScaleAbs(img, alpha=0.8, beta=-10),
            lambda: cv2.convertScaleAbs(img, alpha=1.15, beta=10),
            lambda: put_on_background(img, rng), lambda: put_on_background(img, rng)][k]()


def features(images):
    return np.nan_to_num(np.vstack([leaf_features.extract(images[i:i + 16]) for i in range(0, len(images), 16)]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "models", "coffeeguard_v2.npz"))
    ap.add_argument("--limit", type=int, default=0, help="max photos per class per dataset (quick test)")
    a = ap.parse_args()

    paths, y, src = [], [], []
    for di, d in enumerate(a.data):
        for ci, c in enumerate(CLASSES):
            folder = os.path.join(d, c)
            if not os.path.isdir(folder):
                continue
            files = sorted(f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png")))
            files = files[:a.limit] if a.limit else files
            paths += [os.path.join(folder, f) for f in files]; y += [ci] * len(files); src += [di] * len(files)
    y = np.array(y)
    print("photos per class:", {c: int((y == i).sum()) for i, c in enumerate(CLASSES)})
    imgs = [read(p) for p in paths]

    # 1. group twins so copies of one leaf never cross the split
    E = np.vstack([cnn_features.embed([cv2.resize(im, (512, 256)) for im in imgs[i:i + 32]]) for i in range(0, len(imgs), 32)])
    _, groups = connected_components(csr_matrix(E @ E.T >= 0.97), directed=False)
    print(f"{len(paths)} photos = {groups.max() + 1} unique leaves")
    folds = [te for _, te in StratifiedGroupKFold(n_splits=7, shuffle=True, random_state=42).split(imgs, y, groups)]
    te, va = folds[0], folds[1]
    tr = np.setdiff1d(np.arange(len(y)), np.concatenate([te, va]))

    # 2-3. augment + features
    rng = np.random.default_rng(7)
    Xtr = np.vstack([features([augment(imgs[i], k, rng) for i in tr]) for k in range(7)])
    Ytr = np.concatenate([y[tr]] * 7)
    Xva, Xte = features([imgs[i] for i in va]), features([imgs[i] for i in te])
    Xfi = features([put_on_background(imgs[i], rng, field=True) for i in te])

    # 4. classifier
    def fit(X, Y, C, w):
        sc = StandardScaler().fit(X[:, 3 * D:])
        prep = lambda Z: np.hstack([Z[:, :3 * D], sc.transform(Z[:, 3 * D:]) * w / 8.0])
        return LogisticRegression(C=C, max_iter=5000, class_weight="balanced").fit(prep(X), Y), sc, prep
    best = max(((C, w) for C in (2.0, 5.0) for w in (1.0, 2.0)),
               key=lambda cw: f1_score(y[va], fit(Xtr, Ytr, *cw)[0].predict(fit(Xtr, Ytr, *cw)[2](Xva)), average="macro"))
    clf, sc, prep = fit(Xtr, Ytr, *best)
    present = sorted(set(y))
    for name, X in (("clean test", Xte), ("field-like test", Xfi)):
        p = clf.predict(prep(X))
        print(f"\n{name}: accuracy {accuracy_score(y[te], p):.3f}")
        print(classification_report(y[te], p, labels=present, target_names=[CLASSES[i] for i in present], digits=3, zero_division=0))

    # 5. final model on everything, exported as NumPy weights
    Xall = np.vstack([Xtr, Xva, Xte]); Yall = np.concatenate([Ytr, y[va], y[te]])
    clf, sc, _ = fit(Xall, Yall, *best)
    coef = np.zeros((len(CLASSES), Xall.shape[1]), np.float32); icpt = np.full(len(CLASSES), -30.0, np.float32)
    coef[clf.classes_] = clf.coef_; icpt[clf.classes_] = clf.intercept_   # classes absent from data get ~0 probability
    np.savez_compressed(a.out, coef=coef, intercept=icpt, hand_mean=sc.mean_.astype(np.float32),
                        hand_scale=sc.scale_.astype(np.float32), hand_weight=np.float32(best[1]), classes=np.array(CLASSES))
    print("\nsaved", a.out, "| C, weight =", best)


if __name__ == "__main__":
    main()
