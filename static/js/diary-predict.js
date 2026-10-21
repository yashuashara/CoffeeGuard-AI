/* Leaf Diary panel on the Predict page: saves each diagnosis, lets the farmer
   name the plant, compares with that plant's previous scan, and offers the
   report image + re-check reminder. */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const D = window.CGDiary;
  const L = {
    en: { saved: "✅ Saved to My Scans on this phone", which: "Which plant is this? (choose the same name to re-check a plant)", report: "🖼️ Share report image", pdf: "📑 Download PDF", pdfOk: "✅ PDF saved — print it or send it to your KVK officer.",
          remind: "⏰ Remind me to re-check", making: "Making report…", done: "✅ Report saved — share it on WhatsApp or show it to your KVK officer.",
          shared: "✅ Report shared.", notSaved: "Not saved — retake a clearer photo to get a result worth keeping." },
    hi: { saved: "✅ इस फ़ोन पर 'मेरी जाँचें' में सेव हुआ", which: "यह कौन सा पौधा है? (दोबारा जाँच के लिए वही नाम चुनें)", report: "🖼️ रिपोर्ट फ़ोटो भेजें", pdf: "📑 PDF डाउनलोड करें", pdfOk: "✅ PDF सेव हुई — प्रिंट करें या KVK अधिकारी को भेजें।",
          remind: "⏰ दोबारा जाँच की याद दिलाएँ", making: "रिपोर्ट बन रही है…", done: "✅ रिपोर्ट सेव हुई — WhatsApp पर भेजें या KVK अधिकारी को दिखाएँ।",
          shared: "✅ रिपोर्ट भेजी गई।", notSaved: "सेव नहीं हुआ — साफ़ फ़ोटो दोबारा लें।" },
    kn: { saved: "✅ ಈ ಫೋನ್‌ನಲ್ಲಿ 'ನನ್ನ ಪರೀಕ್ಷೆಗಳು' ನಲ್ಲಿ ಉಳಿಸಲಾಗಿದೆ", which: "ಇದು ಯಾವ ಗಿಡ? (ಮರುಪರೀಕ್ಷೆಗೆ ಅದೇ ಹೆಸರನ್ನು ಆರಿಸಿ)", report: "🖼️ ವರದಿ ಚಿತ್ರ ಹಂಚಿಕೊಳ್ಳಿ", pdf: "📑 PDF ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ", pdfOk: "✅ PDF ಉಳಿಸಲಾಗಿದೆ — ಮುದ್ರಿಸಿ ಅಥವಾ KVK ಅಧಿಕಾರಿಗೆ ಕಳುಹಿಸಿ.",
          remind: "⏰ ಮರುಪರೀಕ್ಷೆಗೆ ನೆನಪಿಸಿ", making: "ವರದಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ…", done: "✅ ವರದಿ ಉಳಿಸಲಾಗಿದೆ — WhatsApp ನಲ್ಲಿ ಕಳುಹಿಸಿ ಅಥವಾ KVK ಅಧಿಕಾರಿಗೆ ತೋರಿಸಿ.",
          shared: "✅ ವರದಿ ಹಂಚಿಕೊಳ್ಳಲಾಗಿದೆ.", notSaved: "ಉಳಿಸಿಲ್ಲ — ಸ್ಪಷ್ಟ ಫೋಟೋ ಮತ್ತೆ ತೆಗೆಯಿರಿ." },
    ml: { saved: "✅ ഈ ഫോണിൽ 'എന്റെ പരിശോധനകൾ' എന്നതിൽ സേവ് ചെയ്തു", which: "ഇത് ഏത് ചെടിയാണ്? (വീണ്ടും പരിശോധിക്കാൻ അതേ പേര് തിരഞ്ഞെടുക്കുക)", report: "🖼️ റിപ്പോർട്ട് ചിത്രം പങ്കിടുക", pdf: "📑 PDF ഡൗൺലോഡ് ചെയ്യുക", pdfOk: "✅ PDF സേവ് ചെയ്തു — പ്രിന്റ് ചെയ്യുക അല്ലെങ്കിൽ KVK ഉദ്യോഗസ്ഥന് അയക്കുക.",
          remind: "⏰ വീണ്ടും പരിശോധിക്കാൻ ഓർമ്മിപ്പിക്കുക", making: "റിപ്പോർട്ട് തയ്യാറാക്കുന്നു…", done: "✅ റിപ്പോർട്ട് സേവ് ചെയ്തു — WhatsApp-ൽ അയക്കുക അല്ലെങ്കിൽ KVK ഉദ്യോഗസ്ഥനെ കാണിക്കുക.",
          shared: "✅ റിപ്പോർട്ട് പങ്കിട്ടു.", notSaved: "സേവ് ചെയ്തില്ല — വ്യക്തമായ ഫോട്ടോ വീണ്ടും എടുക്കുക." },
  };
  let lang = "en", rec = null;
  const t = (k) => (L[lang] && L[lang][k]) || L.en[k];
  const store = { get(k, d) { try { return localStorage.getItem(k) || d; } catch (e) { return d; } },
                  set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };

  async function plantList() {
    const names = [...new Set((await D.all()).map((r) => r.plant))];
    $("diary-plants").innerHTML = names.map((n) => `<option value="${n.replace(/"/g, "&quot;")}">`).join("");
  }

  async function renderProgress() {
    const box = $("diary-progress");
    const prev = await D.previousOf(rec);
    if (!prev) { box.hidden = true; return; }
    const tr = D.trend(rec, prev);
    box.hidden = false;
    box.style.setProperty("--t", tr.color);
    box.innerHTML = `<div class="diary-compare">
        <figure><img src="${prev.overlay || ""}" alt=""><figcaption>${D.fmtDate(prev.ts, lang)} · <b>${D.sev(prev)}%</b></figcaption></figure>
        <span class="diary-arrow">→</span>
        <figure><img src="${rec.overlay || ""}" alt=""><figcaption>${D.fmtDate(rec.ts, lang)} · <b>${D.sev(rec)}%</b></figcaption></figure>
      </div>
      <div class="diary-trend">${tr.icon} ${D.w(lang, tr.key)}</div>`;
  }

  function labels() {
    $("diary-saved").textContent = t("saved");
    $("diary-plant-label").textContent = t("which");
    $("report-btn").textContent = t("report");
    $("pdf-btn").textContent = t("pdf");
    $("remind-btn").textContent = t("remind");
    if (rec) $("remind-btn").href = D.reminderUrl(rec, lang);
    $("remind-btn").hidden = !(rec && rec.verdict && rec.verdict.recheck_days);
  }

  async function onResult(data, curLang) {
    lang = curLang || lang;
    const box = $("diary-box");
    if (!D || !box) return;
    if (data.prediction === "Uncertain") { box.hidden = true; return; }
    try {
      if (!data._diaryId) {                       // save each result only once
        const r = D.fromResult(data, await D.nextPlantName());   // each new photo = its own plant
        r.id = await D.save(r);
        data._diaryId = r.id;
      }
      rec = await D.get(data._diaryId);
      $("diary-plant").value = rec.plant;
      $("diary-note").hidden = true;
      box.hidden = false;
      labels();
      await plantList();
      await renderProgress();
    } catch (e) {
      console.warn("Leaf Diary unavailable", e);   // e.g. private mode: diagnosis still works
      box.hidden = true;
    }
  }

  async function renamePlant() {
    if (!rec) return;
    const name = $("diary-plant").value.trim() || "My plant";
    if (name === rec.plant) return;
    rec.plant = name;
    store.set("cg-plant", name);
    await D.put(rec);
    labels();
    await plantList();
    await renderProgress();
  }
  $("diary-plant").addEventListener("change", renamePlant);
  $("diary-plant").addEventListener("blur", renamePlant);
  $("diary-plant").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); e.target.blur(); } });

  $("report-btn").addEventListener("click", async () => {
    if (!rec) return;
    await renamePlant();
    const btn = $("report-btn"), note = $("diary-note");
    btn.disabled = true; btn.textContent = t("making");
    try {
      const how = await D.shareReport(rec, lang);
      if (how !== "cancelled") { note.hidden = false; note.textContent = how === "shared" ? t("shared") : t("done"); }
    } catch (e) { note.hidden = false; note.textContent = "Couldn't create the report: " + e.message; }
    btn.disabled = false; btn.textContent = t("report");
  });

  $("pdf-btn").addEventListener("click", async () => {
    if (!rec) return;
    await renamePlant();
    const btn = $("pdf-btn"), note = $("diary-note");
    btn.disabled = true; btn.textContent = t("making");
    try { await D.downloadPdf(rec, lang); note.hidden = false; note.textContent = t("pdfOk"); }
    catch (e) { note.hidden = false; note.textContent = "Couldn't create the PDF: " + e.message; }
    btn.disabled = false; btn.textContent = t("pdf");
  });

  window.CGDiaryUI = { onResult, setLang(code) { lang = code; if (rec) { labels(); renderProgress(); } } };
})();
