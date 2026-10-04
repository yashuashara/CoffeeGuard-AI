import os

# ── Limit threads BEFORE importing numpy/sklearn/xgboost ──
# Prevents spawning dozens of threads (each ~8MB stack) on shared containers
# Critical for staying within Render free tier's 512MB RAM limit
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import gc
import cv2
import numpy as np
import pickle
from flask import Flask, render_template, request, jsonify
from sklearn.svm import SVC
from sklearn.ensemble import VotingClassifier
from xgboost import XGBClassifier

app = Flask(__name__)

# Load model and scaler
model = pickle.load(open("model.pkl", "rb"))
scaler = pickle.load(open("scaler.pkl", "rb"))
gc.collect()  # Free temporary pickle deserialization memory

categories = ['Healthy', 'Miner', 'Phoma', 'Rust']

disease_info = {
    'Healthy': {
        'status': 'healthy',
        'description': 'The coffee leaf appears healthy with no visible signs of disease. The leaf shows normal green coloration and structure.',
        'recommendation': 'Continue regular care. Maintain proper irrigation, fertilization, and monitoring schedules.',
        'color': '#22c55e'
    },
    'Miner': {
        'status': 'diseased',
        'description': 'Coffee Leaf Miner (Leucoptera coffeella) damage detected. This insect larvae feeds between leaf surfaces creating serpentine mines, causing significant reduction in photosynthetic area.',
        'recommendation': 'Apply appropriate insecticides. Implement biological control using natural predators like wasps. Remove and destroy heavily infested leaves.',
        'color': '#f59e0b'
    },
    'Phoma': {
        'status': 'diseased',
        'description': 'Phoma leaf spot detected. Caused by the fungus Phoma costarricensis, this disease creates dark brown to black necrotic lesions on leaves, often with concentric rings.',
        'recommendation': 'Apply copper-based fungicides. Improve air circulation through pruning. Avoid overhead irrigation to reduce leaf wetness.',
        'color': '#ef4444'
    },
    'Rust': {
        'status': 'diseased',
        'description': 'Coffee Leaf Rust (Hemileia vastatrix) detected. This is the most economically devastating coffee disease worldwide, producing orange-yellow powdery spots on leaf undersides.',
        'recommendation': 'Apply systemic fungicides (triazoles). Plant resistant varieties. Ensure proper shade management and nutrition to strengthen plant immunity.',
        'color': '#f97316'
    }
}

def leaf_region_stats(img):
    """
    Finds the single largest contiguous blob of leaf-like color (greens
    for healthy tissue, browns/oranges/yellows for common lesions like
    rust, phoma, and miner damage) and returns:
        (area_ratio, texture_variance)

    This is a cheap heuristic gate, not a classifier — its only job is to
    catch images that are clearly NOT a leaf before they reach the disease
    model, which otherwise has no "not a leaf" option and will confidently
    force any image into one of the 4 disease categories.

    Two checks, for two different failure modes we actually hit testing
    this:
      1. area_ratio (largest CONNECTED blob, not a simple overall pixel
         count) — catches scattered incidental color in the background
         (a small orange bag, patterned clothing) that a naive sum would
         wrongly add up and pass.
      2. texture_variance — color alone cannot tell a leaf apart from a
         flat surface painted/printed in a similar color (a yellow or
         mustard wall is a real failure case we hit: it is one huge,
         solid, uniformly-colored region, which actually makes it score
         *higher* on a pure connected-blob-size check, not lower). A real
         leaf has natural texture — veins, lesion edges, uneven lighting,
         surface irregularity — a flat painted wall does not. This is
         measured as the variance of the Laplacian (standard blur/texture
         metric) within the matched region only.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Healthy/green leaf tissue
    green_mask = cv2.inRange(hsv, (25, 40, 40), (95, 255, 255))
    # Brown/orange/yellow lesions (rust, phoma, miner trails, dried spots).
    # Saturation floor is set high (140) because skin tones share the same
    # hue range as these lesions but sit at much lower saturation
    # (tested: real skin ~S60-130 vs real lesion colors ~S170-233) —
    # this is what actually separates "hand" from "diseased leaf", not hue.
    brown_mask = cv2.inRange(hsv, (5, 140, 20), (30, 255, 200))

    combined = cv2.bitwise_or(green_mask, brown_mask)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(combined, connectivity=8)
    if num_labels <= 1:
        return 0.0, 0.0  # no matching pixels at all

    # stats[0] is always the background label; look only at real components
    largest_label = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
    largest_area = int(stats[largest_label, cv2.CC_STAT_AREA])
    area_ratio = float(largest_area) / combined.size

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    texture_variance = float(laplacian[labels == largest_label].var())

    return area_ratio, texture_variance


def get_features(img):
    try:
        # Resize to 64x64 (Model expects exactly 28,672 features: 64*64*7)
        img = cv2.resize(img, (64, 64))

        # Channel 1: Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_flat = gray.flatten()

        # Channels 2-4: BGR (Original color)
        bgr_flat = img.flatten()

        # Channels 5-7: HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv_flat = hsv.flatten()

        # Combine all channels: 1 (Gray) + 3 (BGR) + 3 (HSV) = 7
        # 64 * 64 * 7 = 28,672 features
        features = np.concatenate((gray_flat, bgr_flat, hsv_flat))

        return features

    except Exception as e:
        print(f"Error in feature extraction: {e}")
        return None


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/predict')
def predict_page():
    return render_template('predict.html')


@app.route('/api/predict', methods=['POST'])
def api_predict():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Read image
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({'error': 'Invalid image file'}), 400

        # Gate 1: reject images that don't look leaf-like at all
        # (prevents confidently diagnosing hands, walls, random objects, etc.)
        area_ratio, texture_variance = leaf_region_stats(img)
        LEAF_RATIO_THRESHOLD = 0.20
        TEXTURE_VARIANCE_THRESHOLD = 150.0
        if area_ratio < LEAF_RATIO_THRESHOLD:
            return jsonify({
                'error': 'not_a_leaf',
                'message': "This doesn't look like a coffee leaf image. Please upload a clear, close-up photo of a single leaf for accurate results."
            }), 422
        if texture_variance < TEXTURE_VARIANCE_THRESHOLD:
            return jsonify({
                'error': 'not_a_leaf',
                'message': "This looks like a flat, uniform surface rather than a real leaf (e.g. a wall or fabric can share a leaf's color). Please upload a clear, close-up photo of an actual coffee leaf."
            }), 422

        # Extract features
        features = get_features(img)
        if features is None:
            return jsonify({'error': 'Feature extraction failed'}), 500
        features = features.reshape(1, -1)
        
        # Scaling
        try:
            features = scaler.transform(features)
        except Exception as e:
            print(f"Scaling error: {e}")
            return jsonify({'error': f'Scaling failed: {str(e)}'}), 500

        # Predict
        try:
            prediction = model.predict(features)[0]
            probabilities = model.predict_proba(features)[0]
        except Exception as e:
            print(f"Prediction error: {e}")
            return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

        label = categories[prediction]
        confidence = float(probabilities[prediction]) * 100
        info = disease_info[label]

        # Get all probabilities
        all_probs = {categories[i]: round(float(probabilities[i]) * 100, 2) for i in range(len(categories))}

        # Gate 2: even for leaf-like images, don't present a confident
        # diagnosis when the model itself isn't confident — this is the
        # case that most often misleads people (e.g. an unclear or
        # borderline photo getting a seemingly authoritative answer).
        CONFIDENCE_THRESHOLD = 45.0
        if confidence < CONFIDENCE_THRESHOLD:
            return jsonify({
                'prediction': 'Uncertain',
                'confidence': round(confidence, 2),
                'status': 'uncertain',
                'description': "The model isn't confident enough to give a reliable diagnosis from this image.",
                'recommendation': 'Try a clearer, well-lit, close-up photo of a single leaf against a plain background.',
                'color': '#9ca3af',
                'probabilities': all_probs
            })

        return jsonify({
            'prediction': label,
            'confidence': round(confidence, 2),
            'status': info['status'],
            'description': info['description'],
            'recommendation': info['recommendation'],
            'color': info['color'],
            'probabilities': all_probs
        })
    except Exception as e:
        print(f"Global API error: {e}")
        return jsonify({'error': f'Internal Server Error: {str(e)}'}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port, debug=False)
    