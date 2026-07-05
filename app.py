import os
import cv2
import numpy as np
import pickle
from flask import Flask, render_template, request, jsonify
import base64
from sklearn.svm import SVC
from sklearn.ensemble import VotingClassifier
from xgboost import XGBClassifier

app = Flask(__name__)

# Load model and scaler
model = pickle.load(open("model.pkl", "rb"))
scaler = pickle.load(open("scaler.pkl", "rb"))

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
        # Read image
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    print("1. Image received")

    if img is None:
        return jsonify({'error': 'Invalid image file'}), 400

    # Extract features
    features = get_features(img)
    print("2. Features extracted")

    if features is None:
        return jsonify({'error': 'Feature extraction failed'}), 500

    features = features.reshape(1, -1)

    # Scaling
    try:
        features = scaler.transform(features)
        print("3. Scaling done")
    except Exception as e:
        print(f"Scaling error: {e}")
        return jsonify({'error': f'Scaling failed: {str(e)}'}), 500

    # Predict
    try:
        print("4. Starting prediction...")
        prediction = model.predict(features)[0]
        print("5. Prediction done")

        probabilities = model.predict_proba(features)[0]
        print("6. Probability done")
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port, debug=False)
    