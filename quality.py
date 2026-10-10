"""
CoffeeGuard AI - Photo quality check
------------------------------------
Runs BEFORE diagnosis and tells the farmer exactly what is wrong with the
photo and how to fix it, instead of a vague "image unclear" (a common
complaint about existing plant-disease apps).

Thresholds were measured on 154 real coffee-leaf photos vs the same photos
artificially blurred / darkened:
    sharpness (Laplacian variance @512px): good photos >= 88 (1st percentile),
                                           blurred (sigma 2) <= 5   -> cut-off 20
    brightness (mean V):                   good photos >= 110,
                                           underexposed x0.4 ~ 58   -> cut-off 55
"""

import cv2
import numpy as np

from severity import _leaf_mask

MIN_SIDE = 150
SHARPNESS_MIN = 20.0
BRIGHTNESS_MIN = 55.0
GLARE_MAX = 0.25

TIPS = {
    "too_small": {
        "en": ("Photo is too small", "Move closer so the leaf fills most of the photo."),
        "hi": ("फ़ोटो बहुत छोटी है", "पास जाकर फ़ोटो लें ताकि पत्ती ज़्यादातर फ़्रेम में आए।"),
        "kn": ("ಫೋಟೋ ತುಂಬಾ ಚಿಕ್ಕದಾಗಿದೆ", "ಎಲೆ ಫೋಟೋದ ಬಹುಭಾಗ ತುಂಬುವಂತೆ ಹತ್ತಿರದಿಂದ ತೆಗೆಯಿರಿ."),
        "ml": ("ഫോട്ടോ വളരെ ചെറുതാണ്", "ഇല ഫോട്ടോയുടെ ഭൂരിഭാഗവും നിറയുന്ന വിധം അടുത്തുനിന്ന് എടുക്കുക."),
    },
    "too_dark": {
        "en": ("Photo is too dark", "Take the photo in daylight or step out of deep shade."),
        "hi": ("फ़ोटो बहुत अंधेरी है", "दिन की रोशनी में या घनी छाया से बाहर आकर फ़ोटो लें।"),
        "kn": ("ಫೋಟೋ ತುಂಬಾ ಕತ್ತಲಾಗಿದೆ", "ಹಗಲು ಬೆಳಕಿನಲ್ಲಿ ಅಥವಾ ದಟ್ಟ ನೆರಳಿನಿಂದ ಹೊರಬಂದು ಫೋಟೋ ತೆಗೆಯಿರಿ."),
        "ml": ("ഫോട്ടോ വളരെ ഇരുണ്ടതാണ്", "പകൽ വെളിച്ചത്തിലോ കനത്ത തണലിൽ നിന്ന് മാറിയോ ഫോട്ടോ എടുക്കുക."),
    },
    "blurry": {
        "en": ("Photo is blurry", "Hold the phone steady and tap the leaf on screen to focus."),
        "hi": ("फ़ोटो धुंधली है", "फ़ोन स्थिर रखें और फ़ोकस के लिए स्क्रीन पर पत्ती को छुएँ।"),
        "kn": ("ಫೋಟೋ ಮಸುಕಾಗಿದೆ", "ಫೋನ್ ಅಲುಗಾಡದಂತೆ ಹಿಡಿದು, ಫೋಕಸ್‌ಗಾಗಿ ಪರದೆಯ ಮೇಲೆ ಎಲೆಯನ್ನು ಸ್ಪರ್ಶಿಸಿ."),
        "ml": ("ഫോട്ടോ മങ്ങിയതാണ്", "ഫോൺ അനങ്ങാതെ പിടിച്ച്, ഫോക്കസിനായി സ്ക്രീനിൽ ഇലയിൽ തൊടുക."),
    },
    "glare": {
        "en": ("Too much glare on the leaf", "Tilt the leaf or stand so the sun is not reflecting on it."),
        "hi": ("पत्ती पर बहुत चमक है", "पत्ती को थोड़ा झुकाएँ या ऐसे खड़े हों कि उस पर धूप की चमक न पड़े।"),
        "kn": ("ಎಲೆಯ ಮೇಲೆ ತುಂಬಾ ಹೊಳಪು ಇದೆ", "ಎಲೆಯ ಮೇಲೆ ಬಿಸಿಲು ಪ್ರತಿಫಲಿಸದಂತೆ ಎಲೆಯನ್ನು ಓರೆಯಾಗಿಸಿ ಅಥವಾ ಬದಿಗೆ ನಿಲ್ಲಿ."),
        "ml": ("ഇലയിൽ അമിതമായ തിളക്കം", "ഇലയിൽ വെയിൽ പ്രതിഫലിക്കാത്ത വിധം ഇല ചരിക്കുകയോ മാറി നിൽക്കുകയോ ചെയ്യുക."),
    },
}


def check(img):
    """Returns None if the photo is fine, else {'issue', 'metrics', 'tips': {lang: {title, tip}}}."""
    h, w = img.shape[:2]
    issue, metrics = None, {}
    if min(h, w) < MIN_SIDE:
        issue = "too_small"
    else:
        s = 512.0 / max(h, w)
        small = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA) if s < 1 else img
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        brightness = float(hsv[..., 2].mean())
        sharpness = float(cv2.Laplacian(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
        # Overall contrast tells a blurry leaf (still has a leaf-vs-background outline,
        # std >= 44 on our photos) from a flat wall or cloth (std ~1). Flat surfaces are
        # passed on to the not-a-leaf gate instead of being called "blurry".
        contrast = float(cv2.cvtColor(cv2.resize(small, (128, 64)), cv2.COLOR_BGR2GRAY).std())
        metrics = {"brightness": round(brightness, 1), "sharpness": round(sharpness, 1), "contrast": round(contrast, 1)}
        if contrast < 8.0:
            return None
        if brightness < BRIGHTNESS_MIN:
            issue = "too_dark"
        elif sharpness < SHARPNESS_MIN:
            issue = "blurry"
        else:
            leaf = _leaf_mask(cv2.GaussianBlur(hsv, (3, 3), 0))
            if leaf is not None and leaf.any():
                lp = leaf > 0
                glare = float(((hsv[..., 2] > 245) & (hsv[..., 1] < 40))[lp].mean())
                metrics["glare"] = round(glare, 3)
                if glare > GLARE_MAX:
                    issue = "glare"
    if issue is None:
        return None
    return {"issue": issue, "metrics": metrics,
            "tips": {lang: {"title": t, "tip": tip} for lang, (t, tip) in TIPS[issue].items()}}
