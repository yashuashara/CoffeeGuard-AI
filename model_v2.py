"""
CoffeeGuard AI - v2 disease model
---------------------------------
MobileNetV2 (pretrained, run with onnxruntime) looks at the cropped leaf and
3 zoomed tiles along it, plus 64 lesion-colour features. A small logistic
regression on top (75 KB of plain NumPy weights) gives 5-class probabilities.

Trained on 2,949 photos (your 1,264 Kaggle photos + 1,685 LARA photos).
Held-out test, split BY LEAF (flipped copies of a leaf never cross the split):
    your dataset, unseen leaves     92.3%
    your dataset, field-like        78.5%  (original 64x64 SVM+XGBoost model: 28.2%)
    LARA dataset (5 classes)        86.2%  | field-like 75.1%
"""

import os

import cv2
import numpy as np

import leaf_features

_HERE = os.path.dirname(os.path.abspath(__file__))
WEIGHTS = os.path.join(_HERE, "models", "coffeeguard_v2.npz")
D = 1280

# internal class name -> name used across the app
DISPLAY = {"healthy": "Healthy", "miner": "Miner", "rust": "Rust", "phoma": "Phoma", "cercospora": "Cercospora"}


class V2Model:
    def __init__(self, path=WEIGHTS):
        w = np.load(path, allow_pickle=False)
        self.coef = w["coef"]
        self.intercept = w["intercept"]
        self.hand_mean = w["hand_mean"]
        self.hand_scale = w["hand_scale"]
        self.hand_weight = float(w["hand_weight"])
        self.categories = [DISPLAY[str(c)] for c in w["classes"]]

    def predict_proba(self, img_bgr):
        # The model was trained on 512px-wide photos; phone photos are 3000-4000px.
        # Matching the training size measurably changes predictions, so always resize.
        h, w = img_bgr.shape[:2]
        s = 512.0 / max(h, w)
        if s < 1:
            img_bgr = cv2.resize(img_bgr, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
        x = leaf_features.extract([img_bgr])[0]
        x = np.nan_to_num(x)
        x[3 * D:] = (x[3 * D:] - self.hand_mean) / self.hand_scale * self.hand_weight / 8.0
        z = x @ self.coef.T + self.intercept
        p = np.exp(z - z.max())
        return p / p.sum()


def available():
    return os.path.exists(WEIGHTS) and os.path.exists(
        os.path.join(_HERE, "models", "mobilenetv2_features.onnx"))
