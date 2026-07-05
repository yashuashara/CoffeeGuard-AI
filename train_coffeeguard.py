"""
CoffeeGuard AI - SVM + XGBoost Training Script
------------------------------------------------
This script is written to match app.py's get_features() EXACTLY:
    - Resize to 64x64
    - Grayscale (1 channel) + BGR (3 channels) + HSV (3 channels)
    - Total features = 64 * 64 * 7 = 28,672

IMPORTANT: If your feature extraction here doesn't match app.py's
get_features() exactly (same resize size, same channel order), your
model.pkl / scaler.pkl will silently produce wrong predictions or crash
with a shape-mismatch error. Do NOT use the old train.ipynb (128x128 +
histogram) - it produces 16,640 features, which is incompatible.

Dataset expected structure (from the Kaggle "coffee-leaf-diseases" set):
    dataset/
        healthy/*.jpg
        miner/*.jpg
        phoma/*.jpg
        rust/*.jpg

Usage:
    python train_coffeeguard.py --data_dir dataset --out_dir .

Requires: opencv-python, numpy, scikit-learn, xgboost
    pip install opencv-python-headless numpy scikit-learn xgboost
"""

import os
import argparse
import pickle

import cv2
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from xgboost import XGBClassifier

# Must match app.py's `categories` list order exactly:
# categories = ['Healthy', 'Miner', 'Phoma', 'Rust']
CATEGORIES = ["healthy", "miner", "phoma", "rust"]


def get_features(img):
    """
    Must be IDENTICAL to app.py's get_features().
    64x64 resize -> grayscale + BGR + HSV -> flatten & concatenate.
    Order matters: gray, then bgr, then hsv.
    """
    img = cv2.resize(img, (64, 64))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_flat = gray.flatten()

    bgr_flat = img.flatten()

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv_flat = hsv.flatten()

    return np.concatenate((gray_flat, bgr_flat, hsv_flat))


def load_dataset(data_dir):
    X, y = [], []
    for idx, cat in enumerate(CATEGORIES):
        folder = os.path.join(data_dir, cat)
        if not os.path.isdir(folder):
            print(f"WARNING: missing folder {folder}, skipping.")
            continue

        files = os.listdir(folder)
        print(f"Loading '{cat}': {len(files)} files")

        for fname in files:
            path = os.path.join(folder, fname)
            img = cv2.imread(path)
            if img is None:
                continue
            X.append(get_features(img))
            y.append(idx)

    X = np.array(X)
    y = np.array(y)
    print(f"\nTotal dataset shape: {X.shape}, labels: {y.shape}")
    expected_features = 64 * 64 * 7
    assert X.shape[1] == expected_features, (
        f"Feature mismatch! Got {X.shape[1]}, expected {expected_features}. "
        f"Check get_features() matches app.py exactly."
    )
    return X, y


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_dir",
        default=r"C:\coffee-leaf-disease\dataset",
        help="Path to dataset folder",
    )
    parser.add_argument("--out_dir", default=".", help="Where to save model.pkl / scaler.pkl")
    args = parser.parse_args()

    print("=== Loading dataset ===")
    X, y = load_dataset(args.data_dir)

    print("\n=== Splitting train/test ===")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("\n=== Scaling features ===")
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    print("\n=== Training SVM + XGBoost ensemble ===")
    svm = SVC(
        kernel="linear",
        C=5,
        probability=True,
        class_weight="balanced",
    )

    xgb = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=42,
    )

    model = VotingClassifier(
        estimators=[("svm", svm), ("xgb", xgb)],
        voting="soft",
    )

    model.fit(X_train, y_train)

    print("\n=== Evaluating ===")
    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    print(f"Accuracy: {acc:.4f}")
    print(classification_report(y_test, pred, target_names=CATEGORIES))
    print(confusion_matrix(y_test, pred))

    print("\n=== Saving model.pkl and scaler.pkl ===")
    model_path = os.path.join(args.out_dir, "model.pkl")
    scaler_path = os.path.join(args.out_dir, "scaler.pkl")
    pickle.dump(model, open(model_path, "wb"))
    pickle.dump(scaler, open(scaler_path, "wb"))
    print(f"Saved: {model_path}")
    print(f"Saved: {scaler_path}")
    print("\nDone. Copy both files into your Flask app's root directory (next to app.py).")


if __name__ == "__main__":
    main()
