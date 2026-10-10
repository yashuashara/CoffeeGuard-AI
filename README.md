# CoffeeGuard AI 🍃

**Coffee leaf disease detection that tells a farmer not just *what* is wrong, but *where*, *how bad* it is, and *what to do next*, in their own language, even on weak signal.**

🔗 Live demo: https://coffeeguard-ai-nc20.onrender.com/ (free server: the first load can take ~30 s to wake up)

---

## What it does

| Feature | What the farmer gets |
|---|---|
| **Diagnosis** | Healthy, leaf rust, Phoma, leaf miner or Cercospora, with a confidence score |
| **AI Lesion Scan** 🔥 | Heatmap of exactly where the damage is, with a before/after slider |
| **Severity** | % of leaf area affected: minimal / mild / moderate / severe |
| **One clear decision** | 🚨 Treat now · ⚠️ Treat this week · 👀 Watch · ✅ No action, plus when to check again |
| **Voice** 🔊 | Advice read aloud in English, हिन्दी, ಕನ್ನಡ, മലയാളം |
| **Whole-plant check** 🌳 | Scan 3–5 leaves and get one plant-level result |
| **Photo quality check** 📷 | "Too blurry / too dark / glare / too small" with exactly how to fix it |
| **Works on weak signal** 📶 | Photos compressed in the browser (~40–90% less data); no signal? the scan is saved and diagnosed automatically when signal returns; installable as an app |
| **Send to KVK** 💬 | One tap to share the result on WhatsApp with an extension officer |
| **Outbreak map** 📍 | Opt-in: scans with ~1 km location build a live disease map for the Coffee Board, KVKs and FPOs |

## Why it's different

Existing plant-disease apps mostly give a disease name only. A 2022 study of 17 apps found only 4 estimated severity, only one showed infected areas (and only after manual adjustment), most needed English, and 35% needed constant internet. The Coffee Board's *Coffee Krishi Taranga* voice service has no photo diagnosis. CoffeeGuard combines **coffee-specific diagnosis + automatic severity heatmap + a clear decision + voice in local languages + offline support**, and refuses to guess on bad photos.

## Honest accuracy

The training photos include flipped copies of the same leaf, so the data is split **by leaf**: no copy of a test leaf is ever seen in training. "Field-like" = the same photos rotated, re-lit, blurred and placed on cluttered backgrounds.

| Test set | v1 (64×64 pixels → SVM + XGBoost) | **v2 (MobileNetV2 transfer learning)** |
|---|---|---|
| Your dataset, unseen leaves | 95.0%* | **92.3%** |
| Your dataset, field-like photos | 28.2% | **78.5%** |
| LARA dataset (5 classes) | — | **86.2%** |
| LARA dataset, field-like | — | **75.1%** |

\* v1 was trained on this whole dataset, including these leaves, so its 95% is not a fair unseen-leaf score.

## How it works

```
Photo ─► Quality check ─► Not-a-leaf gate ─► Leaf crop + 3 zoom tiles ─► MobileNetV2 (ONNX) ─┐
                                                                    + 64 lesion-colour features ├► classifier ─► Confidence gate
         Lesion scan (OpenCV) ─► severity % + heatmap ───────────────────────────────────────────┘          │
                                                     Verdict (treat now / this week / watch) + 4-language card ◄┘
```

- **Transfer learning:** MobileNetV2 pretrained on ImageNet, run with `onnxruntime` (no PyTorch/TensorFlow), 9 MB model, ~100 ms per photo on CPU, fits Render's free 512 MB tier (~200 MB RAM).
- **Zoom tiles:** a coffee leaf is ~2:1, so squeezing it into one 224×224 image shrinks lesions. The model also sees 3 square tiles along the leaf.
- **Lesion features:** colour statistics of the lesions (rust orange, Phoma dark brown, miner tan, Cercospora halo).
- **Classifier:** logistic regression stored as plain NumPy weights (`models/coffeeguard_v2.npz`, 75 KB).

## Tech stack

Python · Flask · OpenCV · onnxruntime (MobileNetV2) · NumPy · scikit-learn · SQLite · Leaflet · Service Worker (PWA) · Web Speech API · Gunicorn · Render

## Run locally

```bash
pip install -r requirements.txt
python app.py                 # http://localhost:5005
```

Set `COFFEEGUARD_MODEL=v1` to run the original SVM + XGBoost model (needs `git lfs pull` for `model.pkl`).

## Datasets

- Kaggle *coffee-leaf-diseases* (healthy, miner, Phoma, rust): 1,264 photos / 718 unique leaves
- LARA coffee leaf dataset, Esgario et al. (2020), *Computers and Electronics in Agriculture* 169: github.com/esgario/lara2018

## Limitations & roadmap

- Field-like accuracy uses simulated field photos; next step: test on real Indian plantation photos.
- Advice is decision support: confirm product and dose with your Coffee Board office or KVK. Translations should be reviewed by native speakers and agronomists.
- Outbreak-map data on the free Render tier resets on redeploy (move to a managed database for production).
- Voice depends on the phone having a Hindi / Kannada / Malayalam text-to-speech voice installed.
- Planned: fully on-device diagnosis, WhatsApp bot, more crops (tea, pepper, cardamom).

## Author

**Yashvi Ashara**, M.Sc Blockchain Technology, MIT-WPU Pune
