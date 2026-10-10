"""
CoffeeGuard AI - Action verdict
-------------------------------
Turns (disease, severity %) into ONE clear decision plus when to check again:

    act_now   - treat now and contact KVK / Coffee Board
    act_soon  - treat within the week
    watch     - remove affected leaves, re-check soon
    none      - no action, routine check

Bands use the same "% of leaf area affected" as the lesion scan. This is
decision SUPPORT, not a prescription: the card always tells farmers to
confirm product and dose with their local Coffee Board office or KVK.
"""

# (upper severity % limit, verdict, re-check in days)
RULES = {
    "Healthy":    [(101, "none", 14)],
    "Rust":       [(5, "watch", 7), (15, "act_soon", 7), (101, "act_now", 5)],
    "Phoma":      [(5, "watch", 7), (20, "act_soon", 7), (101, "act_now", 5)],
    "Cercospora": [(5, "watch", 10), (20, "act_soon", 7), (101, "act_now", 5)],
    "Miner":      [(10, "watch", 10), (30, "act_soon", 7), (101, "act_now", 5)],
    "Uncertain":  [(101, "retake", 0)],
}

COLORS = {"act_now": "#ef4444", "act_soon": "#f97316", "watch": "#eab308", "none": "#22c55e", "retake": "#9ca3af"}
ICONS = {"act_now": "🚨", "act_soon": "⚠️", "watch": "👀", "none": "✅", "retake": "📷"}

TEXT = {
    "en": {"act_now": "Treat now", "act_soon": "Treat this week", "watch": "Watch closely", "none": "No action needed",
           "retake": "Retake the photo",
           "recheck": "Check this plant again in {d} days", "recheck0": "Take a clearer photo to get advice",
           "call": "Contact your KVK or Coffee Board office today"},
    "hi": {"act_now": "अभी उपचार करें", "act_soon": "इस हफ़्ते उपचार करें", "watch": "ध्यान से निगरानी करें",
           "none": "कोई कार्रवाई ज़रूरी नहीं", "retake": "फ़ोटो दोबारा लें",
           "recheck": "{d} दिन बाद इस पौधे को फिर जाँचें", "recheck0": "सलाह के लिए साफ़ फ़ोटो लें",
           "call": "आज ही अपने KVK या कॉफ़ी बोर्ड कार्यालय से संपर्क करें"},
    "kn": {"act_now": "ಈಗಲೇ ಚಿಕಿತ್ಸೆ ಮಾಡಿ", "act_soon": "ಈ ವಾರದಲ್ಲಿ ಚಿಕಿತ್ಸೆ ಮಾಡಿ", "watch": "ಎಚ್ಚರಿಕೆಯಿಂದ ಗಮನಿಸಿ",
           "none": "ಯಾವುದೇ ಕ್ರಮ ಬೇಕಿಲ್ಲ", "retake": "ಫೋಟೋ ಮತ್ತೆ ತೆಗೆಯಿರಿ",
           "recheck": "{d} ದಿನಗಳ ನಂತರ ಈ ಗಿಡವನ್ನು ಮತ್ತೆ ಪರೀಕ್ಷಿಸಿ", "recheck0": "ಸಲಹೆಗಾಗಿ ಸ್ಪಷ್ಟ ಫೋಟೋ ತೆಗೆಯಿರಿ",
           "call": "ಇಂದೇ ನಿಮ್ಮ KVK ಅಥವಾ ಕಾಫಿ ಮಂಡಳಿ ಕಚೇರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ"},
    "ml": {"act_now": "ഉടൻ ചികിത്സിക്കുക", "act_soon": "ഈ ആഴ്ച തന്നെ ചികിത്സിക്കുക", "watch": "ശ്രദ്ധയോടെ നിരീക്ഷിക്കുക",
           "none": "നടപടി ആവശ്യമില്ല", "retake": "ഫോട്ടോ വീണ്ടും എടുക്കുക",
           "recheck": "{d} ദിവസത്തിന് ശേഷം ഈ ചെടി വീണ്ടും പരിശോധിക്കുക", "recheck0": "ഉപദേശത്തിന് വ്യക്തമായ ഫോട്ടോ എടുക്കുക",
           "call": "ഇന്നുതന്നെ നിങ്ങളുടെ KVK-യെയോ കോഫി ബോർഡ് ഓഫീസിനെയോ ബന്ധപ്പെടുക"},
}


def verdict(label, severity_percent):
    sev = 0.0 if severity_percent is None else float(severity_percent)
    level, days = "retake", 0
    for limit, lv, d in RULES.get(label, RULES["Uncertain"]):
        if sev < limit:
            level, days = lv, d
            break
    out = {"level": level, "recheck_days": days, "color": COLORS[level], "icon": ICONS[level], "text": {}}
    for lang, t in TEXT.items():
        out["text"][lang] = {
            "title": t[level],
            "recheck": t["recheck"].format(d=days) if days else t["recheck0"],
            "call": t["call"] if level == "act_now" else "",
        }
    return out
