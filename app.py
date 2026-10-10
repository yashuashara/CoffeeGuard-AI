import os

# ── Limit threads BEFORE importing numpy/sklearn/onnxruntime ──
# Prevents spawning dozens of threads (each ~8MB stack) on shared containers
# Critical for staying within Render free tier's 512MB RAM limit
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import gc
import sqlite3
import threading
import time
from collections import defaultdict, deque

import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify

import model_v2
import quality
from decision import verdict
from severity import severity_scan
from translations import farmer_card, LANGUAGES

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # 12 MB upload limit


@app.url_defaults
def static_cache_bust(endpoint, values):
    # Every url_for('static', ...) gets ?v=<file modified time>. Each deploy changes
    # the URL, so browsers and the offline service worker can never serve old CSS/JS.
    if endpoint == 'static' and 'filename' in values:
        try:
            values['v'] = int(os.stat(os.path.join(app.static_folder, values['filename'])).st_mtime)
        except OSError:
            pass

# ───────────────────────── Model ─────────────────────────
# v2 (default): MobileNetV2 transfer learning + leaf crop + zoom tiles + lesion features.
# Falls back to the original 64x64-pixel SVM + XGBoost model if v2 files are missing
# or COFFEEGUARD_MODEL=v1 is set.
USE_V2 = model_v2.available() and os.environ.get("COFFEEGUARD_MODEL", "v2") != "v1"
if USE_V2:
    v2 = model_v2.V2Model()
    categories = v2.categories
    MODEL_NAME = "v2 · MobileNetV2 transfer learning"
else:
    import pickle
    from sklearn.svm import SVC  # noqa: F401  (needed to unpickle)
    from sklearn.ensemble import VotingClassifier  # noqa: F401
    from xgboost import XGBClassifier  # noqa: F401
    model = pickle.load(open("model.pkl", "rb"))
    scaler = pickle.load(open("scaler.pkl", "rb"))
    categories = ['Healthy', 'Miner', 'Phoma', 'Rust']
    MODEL_NAME = "v1 · SVM + XGBoost"
gc.collect()

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
    },
    'Cercospora': {
        'status': 'diseased',
        'description': 'Cercospora leaf spot (brown eye spot, Cercospora coffeicola) detected. It forms round brown spots with a pale centre and a yellow halo, and is most common on nutrient-stressed plants in strong sun.',
        'recommendation': 'Correct nutrition with balanced fertiliser, maintain adequate shade, and apply a copper-based fungicide if spots keep spreading.',
        'color': '#a855f7'
    },
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
    force any image into one of the disease categories.

    Two checks, for two different failure modes we actually hit testing
    this:
      1. area_ratio (largest CONNECTED blob, not a simple overall pixel
         count) — catches scattered incidental color in the background
         (a small orange bag, patterned clothing) that a naive sum would
         wrongly add up and pass.
      2. texture_variance — color alone cannot tell a leaf apart from a
         flat surface painted/printed in a similar color (a yellow or
         mustard wall is a real failure case we hit). A real leaf has
         natural texture — veins, lesion edges, uneven lighting — a flat
         painted wall does not. Measured as the variance of the Laplacian
         within the matched region only.
    """
    # Normalise size first: Laplacian variance depends on resolution. At a
    # fixed 256px, leaves score ~300-400 and flat walls ~5.
    h, w = img.shape[:2]
    scale = 256.0 / max(h, w)
    img = cv2.resize(img, (max(1, int(w * scale)), max(1, int(h * scale))),
                     interpolation=cv2.INTER_AREA)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(hsv, (25, 40, 40), (95, 255, 255))
    # Saturation floor 140 separates skin (S~60-130) from lesion colours (S~170-233)
    brown_mask = cv2.inRange(hsv, (5, 140, 20), (30, 255, 200))
    combined = cv2.bitwise_or(green_mask, brown_mask)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(combined, connectivity=8)
    if num_labels <= 1:
        return 0.0, 0.0

    largest_label = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
    largest_area = int(stats[largest_label, cv2.CC_STAT_AREA])
    area_ratio = float(largest_area) / combined.size

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    texture_variance = float(laplacian[labels == largest_label].var())
    return area_ratio, texture_variance


def get_features_v1(img):
    """Original v1 features: 64x64 gray + BGR + HSV = 28,672 values."""
    img = cv2.resize(img, (64, 64))
    return np.concatenate((cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).flatten(), img.flatten(),
                           cv2.cvtColor(img, cv2.COLOR_BGR2HSV).flatten()))


def predict_probs(img):
    if USE_V2:
        return v2.predict_proba(img)
    features = scaler.transform(get_features_v1(img).reshape(1, -1))
    return model.predict_proba(features)[0]


def downscale(img, max_side=1600):
    h, w = img.shape[:2]
    s = max_side / max(h, w)
    return cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA) if s < 1 else img


# ───────────────────────── Pages ─────────────────────────
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/predict')
def predict_page():
    return render_template('predict.html')


@app.route('/map')
def map_page():
    return render_template('map.html')


@app.route('/sw.js')
def service_worker():
    # Served from the site root so it can control every page (offline support)
    resp = app.send_static_file('sw.js')
    resp.headers['Service-Worker-Allowed'] = '/'
    resp.headers['Cache-Control'] = 'no-cache'
    return resp


@app.route('/manifest.webmanifest')
def manifest():
    return app.send_static_file('manifest.webmanifest')


# ───────────────────────── Diagnosis API ─────────────────────────
@app.route('/api/predict', methods=['POST'])
def api_predict():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        raw = file.read()
        img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({'error': 'Invalid image file'}), 400
        received_kb = round(len(raw) / 1024, 1)

        # Step 1: photo quality — tell the farmer exactly how to fix the photo
        q = quality.check(img)
        if q:
            return jsonify({'error': 'bad_photo', 'quality': q,
                            'message': q['tips']['en']['title'] + '. ' + q['tips']['en']['tip']}), 422

        img = downscale(img)

        # Step 2 (Gate 1): reject images that don't look leaf-like at all
        area_ratio, texture_variance = leaf_region_stats(img)
        if area_ratio < 0.20:
            return jsonify({
                'error': 'not_a_leaf',
                'message': "This doesn't look like a coffee leaf image. Please upload a clear, close-up photo of a single leaf for accurate results."
            }), 422
        if texture_variance < 150.0:
            return jsonify({
                'error': 'not_a_leaf',
                'message': "This looks like a flat, uniform surface rather than a real leaf (e.g. a wall or fabric can share a leaf's color). Please upload a clear, close-up photo of an actual coffee leaf."
            }), 422

        # Step 3: disease model
        probabilities = predict_probs(img)
        idx = int(np.argmax(probabilities))
        label = categories[idx]
        confidence = float(probabilities[idx]) * 100
        all_probs = {categories[i]: round(float(probabilities[i]) * 100, 2) for i in range(len(categories))}

        # Step 4: lesion scan (where + how much)
        sev = severity_scan(img)
        sev_pct = sev['percent'] if sev else None

        # Step 5 (Gate 2): don't present a confident diagnosis when the model isn't confident
        if confidence < 45.0:
            return jsonify({
                'prediction': 'Uncertain',
                'confidence': round(confidence, 2),
                'status': 'uncertain',
                'description': "The model isn't confident enough to give a reliable diagnosis from this image.",
                'recommendation': 'Try a clearer, well-lit, close-up photo of a single leaf against a plain background.',
                'color': '#9ca3af',
                'probabilities': all_probs,
                'severity': sev,
                'verdict': verdict('Uncertain', sev_pct),
                'farmer_card': farmer_card('Uncertain'),
                'languages': LANGUAGES,
                'model': MODEL_NAME,
                'received_kb': received_kb,
            })

        info = disease_info[label]
        return jsonify({
            'prediction': label,
            'confidence': round(confidence, 2),
            'status': info['status'],
            'description': info['description'],
            'recommendation': info['recommendation'],
            'color': info['color'],
            'probabilities': all_probs,
            'severity': sev,
            'verdict': verdict(label, sev_pct),           # Spray now / Watch / No action
            'farmer_card': farmer_card(label),            # 4-language action card
            'languages': LANGUAGES,
            'model': MODEL_NAME,
            'received_kb': received_kb,
        })
    except Exception as e:
        print(f"Global API error: {e}")
        return jsonify({'error': f'Internal Server Error: {str(e)}'}), 500


# ───────────────────────── Outbreak map (opt-in) ─────────────────────────
# Farmers can choose to add a scan to a shared map. Location is rounded to
# 2 decimals (~1 km) before it is stored, and no photo or personal data is kept.
# NOTE: on Render's free tier the disk is temporary, so map data resets on redeploy.
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
DB_PATH = os.path.join(DATA_DIR, "scans.db")
_db_lock = threading.Lock()
_rate = defaultdict(deque)
ALLOWED = set(disease_info) | {"Uncertain"}


def _db():
    os.makedirs(DATA_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("CREATE TABLE IF NOT EXISTS scans (ts INTEGER, disease TEXT, severity REAL, level TEXT, lat REAL, lon REAL)")
    return con


@app.route('/api/report', methods=['POST'])
def api_report():
    d = request.get_json(silent=True) or {}
    try:
        lat, lon = float(d.get('lat')), float(d.get('lon'))
        severity = max(0.0, min(100.0, float(d.get('severity') or 0)))
    except (TypeError, ValueError):
        return jsonify({'error': 'bad_request'}), 400
    disease, level = str(d.get('disease')), str(d.get('level', ''))[:12]
    if disease not in ALLOWED or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return jsonify({'error': 'bad_request'}), 400
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0]
    now = time.time()
    q = _rate[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= 10:
        return jsonify({'error': 'too_many_reports'}), 429
    q.append(now)
    with _db_lock, _db() as con:
        con.execute("INSERT INTO scans VALUES (?,?,?,?,?,?)",
                    (int(now), disease, round(severity, 1), level, round(lat, 2), round(lon, 2)))
    return jsonify({'ok': True, 'lat': round(lat, 2), 'lon': round(lon, 2)})


@app.route('/api/outbreaks')
def api_outbreaks():
    days = max(1, min(365, int(request.args.get('days', 30))))
    since = int(time.time()) - days * 86400
    with _db_lock, _db() as con:
        rows = con.execute(
            "SELECT lat, lon, disease, COUNT(*), AVG(severity), MAX(ts) FROM scans WHERE ts >= ? "
            "GROUP BY lat, lon, disease", (since,)).fetchall()
        total = con.execute("SELECT disease, COUNT(*) FROM scans WHERE ts >= ? GROUP BY disease", (since,)).fetchall()
    points = [{'lat': r[0], 'lon': r[1], 'disease': r[2], 'count': r[3], 'avg_severity': round(r[4] or 0, 1),
               'last_seen': r[5], 'color': disease_info.get(r[2], {}).get('color', '#9ca3af')} for r in rows]
    return jsonify({'days': days, 'points': points, 'totals': {d: c for d, c in total}})


@app.route('/api/info')
def api_info():
    return jsonify({'model': MODEL_NAME, 'classes': categories})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port, debug=False)
