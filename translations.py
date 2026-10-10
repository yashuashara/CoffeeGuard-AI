"""
CoffeeGuard AI - Farmer Action Cards (multilingual)
---------------------------------------------------
Short, plain-language actions a farmer can follow, in the languages of
India's main coffee-growing states:
    en - English
    hi - Hindi
    kn - Kannada   (Karnataka: Coorg, Chikmagalur, Hassan)
    ml - Malayalam (Kerala: Wayanad, Idukki)

NOTE: written to be simple and safe, but have a native speaker (and
ideally a KVK / Coffee Board officer) proof-read before relying on it.
"""

LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी",
    "kn": "ಕನ್ನಡ",
    "ml": "മലയാളം",
}

UI = {
    "en": {"card": "What to do now", "area": "Leaf area affected", "spots": "Lesion spots",
           "severity": "Severity", "dose": "Confirm the right dose with your local Coffee Board office or KVK."},
    "hi": {"card": "अब क्या करें", "area": "पत्ती का प्रभावित हिस्सा", "spots": "धब्बे",
           "severity": "गंभीरता", "dose": "सही मात्रा के लिए अपने नज़दीकी कॉफ़ी बोर्ड कार्यालय या KVK से पूछें।"},
    "kn": {"card": "ಈಗ ಏನು ಮಾಡಬೇಕು", "area": "ಎಲೆಯ ಬಾಧಿತ ಭಾಗ", "spots": "ಚುಕ್ಕೆಗಳು",
           "severity": "ತೀವ್ರತೆ", "dose": "ಸರಿಯಾದ ಪ್ರಮಾಣಕ್ಕಾಗಿ ಹತ್ತಿರದ ಕಾಫಿ ಮಂಡಳಿ ಕಚೇರಿ ಅಥವಾ KVK ಅನ್ನು ಸಂಪರ್ಕಿಸಿ."},
    "ml": {"card": "ഇനി എന്ത് ചെയ്യണം", "area": "ബാധിച്ച ഇലഭാഗം", "spots": "പുള്ളികൾ",
           "severity": "തീവ്രത", "dose": "കൃത്യമായ അളവിന് അടുത്തുള്ള കോഫി ബോർഡ് ഓഫീസിനെയോ KVK-യെയോ സമീപിക്കുക."},
}

SEVERITY = {
    "en": {"minimal": "Minimal", "mild": "Mild", "moderate": "Moderate", "severe": "Severe"},
    "hi": {"minimal": "न्यूनतम", "mild": "हल्का", "moderate": "मध्यम", "severe": "गंभीर"},
    "kn": {"minimal": "ಕನಿಷ್ಠ", "mild": "ಸೌಮ್ಯ", "moderate": "ಮಧ್ಯಮ", "severe": "ತೀವ್ರ"},
    "ml": {"minimal": "വളരെ കുറവ്", "mild": "നേരിയത്", "moderate": "മിതമായത്", "severe": "ഗുരുതരം"},
}

CARDS = {
    "Healthy": {
        "en": {"name": "Healthy leaf", "actions": [
            "Continue regular watering and fertiliser.",
            "Check leaves once a week, especially in the monsoon.",
            "Keep shade trees trimmed for light and air flow."]},
        "hi": {"name": "स्वस्थ पत्ती", "actions": [
            "नियमित सिंचाई और खाद जारी रखें।",
            "हर हफ़्ते पत्तियों की जाँच करें, ख़ासकर मानसून में।",
            "रोशनी और हवा के लिए छाया वाले पेड़ों की छँटाई करते रहें।"]},
        "kn": {"name": "ಆರೋಗ್ಯಕರ ಎಲೆ", "actions": [
            "ನಿಯಮಿತ ನೀರು ಮತ್ತು ಗೊಬ್ಬರ ಮುಂದುವರಿಸಿ.",
            "ಪ್ರತಿ ವಾರ, ವಿಶೇಷವಾಗಿ ಮಳೆಗಾಲದಲ್ಲಿ, ಎಲೆಗಳನ್ನು ಪರೀಕ್ಷಿಸಿ.",
            "ಬೆಳಕು ಮತ್ತು ಗಾಳಿಗಾಗಿ ನೆರಳಿನ ಮರಗಳನ್ನು ಸವರುತ್ತಿರಿ."]},
        "ml": {"name": "ആരോഗ്യമുള്ള ഇല", "actions": [
            "പതിവായി നനയും വളപ്രയോഗവും തുടരുക.",
            "എല്ലാ ആഴ്ചയും, പ്രത്യേകിച്ച് മഴക്കാലത്ത്, ഇലകൾ പരിശോധിക്കുക.",
            "വെളിച്ചത്തിനും വായുസഞ്ചാരത്തിനും തണൽ മരങ്ങൾ കോതി നിർത്തുക."]},
    },
    "Rust": {
        "en": {"name": "Coffee leaf rust", "actions": [
            "Spray Bordeaux mixture (copper) before and after the monsoon.",
            "Pick off and burn badly infected leaves.",
            "Plant rust-resistant varieties when replanting."]},
        "hi": {"name": "पत्ती का रतुआ (लीफ़ रस्ट)", "actions": [
            "मानसून से पहले और बाद में बोर्डो मिश्रण (कॉपर) का छिड़काव करें।",
            "बहुत ज़्यादा संक्रमित पत्तियाँ तोड़कर जला दें।",
            "दोबारा लगाते समय रतुआ-रोधी किस्में लगाएँ।"]},
        "kn": {"name": "ಎಲೆ ತುಕ್ಕು ರೋಗ", "actions": [
            "ಮಳೆಗಾಲದ ಮೊದಲು ಮತ್ತು ನಂತರ ಬೋರ್ಡೋ ಮಿಶ್ರಣ (ತಾಮ್ರ) ಸಿಂಪಡಿಸಿ.",
            "ಹೆಚ್ಚು ಸೋಂಕಿತ ಎಲೆಗಳನ್ನು ಕಿತ್ತು ಸುಟ್ಟುಹಾಕಿ.",
            "ಮರು ನಾಟಿ ಮಾಡುವಾಗ ತುಕ್ಕು ರೋಗ ನಿರೋಧಕ ತಳಿಗಳನ್ನು ಬೆಳೆಸಿ."]},
        "ml": {"name": "ഇല തുരുമ്പ് രോഗം", "actions": [
            "മഴക്കാലത്തിന് മുമ്പും ശേഷവും ബോർഡോ മിശ്രിതം (ചെമ്പ്) തളിക്കുക.",
            "രോഗം കൂടിയ ഇലകൾ പറിച്ച് കത്തിച്ചുകളയുക.",
            "വീണ്ടും നടുമ്പോൾ തുരുമ്പ് രോഗ പ്രതിരോധ ഇനങ്ങൾ നടുക."]},
    },
    "Phoma": {
        "en": {"name": "Phoma leaf spot", "actions": [
            "Spray a copper-based fungicide.",
            "Prune branches so air can move through the bush.",
            "Avoid wetting the leaves when watering."]},
        "hi": {"name": "फोमा पत्ती धब्बा रोग", "actions": [
            "कॉपर-आधारित फफूंदनाशक का छिड़काव करें।",
            "झाड़ी में हवा आने के लिए टहनियों की छँटाई करें।",
            "सिंचाई करते समय पत्तियों को गीला न करें।"]},
        "kn": {"name": "ಫೋಮಾ ಎಲೆ ಚುಕ್ಕೆ ರೋಗ", "actions": [
            "ತಾಮ್ರ ಆಧಾರಿತ ಶಿಲೀಂಧ್ರನಾಶಕ ಸಿಂಪಡಿಸಿ.",
            "ಗಿಡದೊಳಗೆ ಗಾಳಿ ಸಂಚರಿಸಲು ಕೊಂಬೆಗಳನ್ನು ಸವರಿ.",
            "ನೀರು ಹಾಯಿಸುವಾಗ ಎಲೆಗಳನ್ನು ಒದ್ದೆ ಮಾಡಬೇಡಿ."]},
        "ml": {"name": "ഫോമ ഇലപ്പുള്ളി രോഗം", "actions": [
            "ചെമ്പ് അടങ്ങിയ കുമിൾനാശിനി തളിക്കുക.",
            "ചെടിയിൽ വായുസഞ്ചാരം ലഭിക്കാൻ കൊമ്പുകോതുക.",
            "നനയ്ക്കുമ്പോൾ ഇലകൾ നനയാതെ ശ്രദ്ധിക്കുക."]},
    },
    "Miner": {
        "en": {"name": "Leaf miner (insect)", "actions": [
            "Pick off and destroy leaves with mines.",
            "Protect natural enemies such as parasitic wasps.",
            "Use an insecticide only if the damage keeps spreading."]},
        "hi": {"name": "लीफ़ माइनर (कीट)", "actions": [
            "सुरंग वाली पत्तियाँ तोड़कर नष्ट करें।",
            "परजीवी ततैया जैसे प्राकृतिक शत्रु कीटों को बचाएँ।",
            "नुकसान बढ़ता रहे तभी कीटनाशक का उपयोग करें।"]},
        "kn": {"name": "ಎಲೆ ಸುರಂಗ ಕೀಟ", "actions": [
            "ಸುರಂಗವಿರುವ ಎಲೆಗಳನ್ನು ಕಿತ್ತು ನಾಶಮಾಡಿ.",
            "ಪರಾವಲಂಬಿ ಕಣಜಗಳಂತಹ ಸ್ನೇಹಿ ಕೀಟಗಳನ್ನು ರಕ್ಷಿಸಿ.",
            "ಹಾನಿ ಹೆಚ್ಚುತ್ತಲೇ ಇದ್ದರೆ ಮಾತ್ರ ಕೀಟನಾಶಕ ಬಳಸಿ."]},
        "ml": {"name": "ഇല തുരപ്പൻ പുഴു", "actions": [
            "തുരങ്കമുള്ള ഇലകൾ പറിച്ച് നശിപ്പിക്കുക.",
            "പരാദ കടന്നലുകൾ പോലുള്ള മിത്രകീടങ്ങളെ സംരക്ഷിക്കുക.",
            "നാശം പടരുന്നുണ്ടെങ്കിൽ മാത്രം കീടനാശിനി ഉപയോഗിക്കുക."]},
    },
    "Cercospora": {
        "en": {"name": "Cercospora (brown eye spot)", "actions": [
            "Give balanced fertiliser - weak, hungry plants get it most.",
            "Keep enough shade; too much direct sun makes it worse.",
            "Spray a copper-based fungicide if spots keep spreading."]},
        "hi": {"name": "सर्कोस्पोरा (भूरा आँख धब्बा)", "actions": [
            "संतुलित खाद दें - कमज़ोर, भूखे पौधों पर यह ज़्यादा होता है।",
            "पर्याप्त छाया रखें; ज़्यादा सीधी धूप से यह बढ़ता है।",
            "धब्बे फैलते रहें तो कॉपर-आधारित फफूंदनाशक छिड़कें।"]},
        "kn": {"name": "ಸರ್ಕೋಸ್ಪೋರಾ (ಕಂದು ಕಣ್ಣು ಚುಕ್ಕೆ)", "actions": [
            "ಸಮತೋಲಿತ ಗೊಬ್ಬರ ನೀಡಿ - ದುರ್ಬಲ, ಪೋಷಕಾಂಶ ಕೊರತೆಯ ಗಿಡಗಳಿಗೆ ಇದು ಹೆಚ್ಚು.",
            "ಸಾಕಷ್ಟು ನೆರಳು ಇರಲಿ; ಹೆಚ್ಚು ನೇರ ಬಿಸಿಲು ಇದನ್ನು ಹೆಚ್ಚಿಸುತ್ತದೆ.",
            "ಚುಕ್ಕೆಗಳು ಹರಡುತ್ತಿದ್ದರೆ ತಾಮ್ರ ಆಧಾರಿತ ಶಿಲೀಂಧ್ರನಾಶಕ ಸಿಂಪಡಿಸಿ."]},
        "ml": {"name": "സെർക്കോസ്പോറ (തവിട്ട് കൺപുള്ളി)", "actions": [
            "സമീകൃത വളം നൽകുക - ദുർബലമായ, പോഷകക്കുറവുള്ള ചെടികളിലാണ് ഇത് കൂടുതൽ.",
            "ആവശ്യത്തിന് തണൽ നിലനിർത്തുക; നേരിട്ടുള്ള വെയിൽ കൂടിയാൽ രോഗം കൂടും.",
            "പുള്ളികൾ പടരുന്നുണ്ടെങ്കിൽ ചെമ്പ് അടങ്ങിയ കുമിൾനാശിനി തളിക്കുക."]},
    },
    "Uncertain": {
        "en": {"name": "Not sure", "actions": [
            "Take a close-up photo of one leaf in good daylight.",
            "Place the leaf on plain paper or soil.",
            "If spots keep spreading, show the leaf to your KVK."]},
        "hi": {"name": "पक्का नहीं", "actions": [
            "अच्छी धूप में एक पत्ती की नज़दीक से फ़ोटो लें।",
            "पत्ती को सादे कागज़ या मिट्टी पर रखें।",
            "धब्बे फैलते रहें तो पत्ती KVK को दिखाएँ।"]},
        "kn": {"name": "ಖಚಿತವಿಲ್ಲ", "actions": [
            "ಉತ್ತಮ ಬೆಳಕಿನಲ್ಲಿ ಒಂದೇ ಎಲೆಯ ಹತ್ತಿರದ ಫೋಟೋ ತೆಗೆಯಿರಿ.",
            "ಎಲೆಯನ್ನು ಸಾದಾ ಕಾಗದ ಅಥವಾ ಮಣ್ಣಿನ ಮೇಲೆ ಇಡಿ.",
            "ಚುಕ್ಕೆಗಳು ಹರಡುತ್ತಿದ್ದರೆ ಎಲೆಯನ್ನು KVK ಗೆ ತೋರಿಸಿ."]},
        "ml": {"name": "ഉറപ്പില്ല", "actions": [
            "നല്ല വെളിച്ചത്തിൽ ഒരു ഇലയുടെ അടുത്തുനിന്നുള്ള ഫോട്ടോ എടുക്കുക.",
            "ഇല വെറും കടലാസിലോ മണ്ണിലോ വയ്ക്കുക.",
            "പുള്ളികൾ പടരുന്നുണ്ടെങ്കിൽ ഇല KVK-യെ കാണിക്കുക."]},
    },
}


def farmer_card(label):
    """All languages at once, so the page can switch instantly without re-uploading."""
    card = CARDS.get(label, CARDS["Uncertain"])
    return {lang: {**card[lang], "ui": UI[lang], "severity": SEVERITY[lang]} for lang in LANGUAGES}
