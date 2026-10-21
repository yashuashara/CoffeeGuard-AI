/* CoffeeGuard AI — Leaf Diary (jury feedback, round 1)
 * - Saves every diagnosis ON THE PHONE (IndexedDB): photo, heatmap, disease,
 *   severity, verdict and advice in all 4 languages. No login, works offline,
 *   photos never leave the device.
 * - Builds a shareable REPORT IMAGE in the farmer's language.
 * - Groups scans by plant and compares with the previous scan
 *   (Improving / Getting worse / Stable / Recovered).
 * - Re-check reminder via Google Calendar.
 */
(function () {
  "use strict";
  const DB = "cg-diary", STORE = "scans";

  // ───────── storage ─────────
  function open() {
    return new Promise((res, rej) => {
      const r = indexedDB.open(DB, 1);
      r.onupgradeneeded = () => r.result.createObjectStore(STORE, { keyPath: "id", autoIncrement: true });
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error);
    });
  }
  async function tx(mode, fn) {
    const db = await open();
    return new Promise((res, rej) => {
      const t = db.transaction(STORE, mode), req = fn(t.objectStore(STORE));
      t.oncomplete = () => res(req && "result" in req ? req.result : undefined);
      t.onerror = () => rej(t.error);
    });
  }
  const save = (rec) => tx("readwrite", (s) => s.add(rec));
  const put = (rec) => tx("readwrite", (s) => s.put(rec));
  const get = (id) => tx("readonly", (s) => s.get(id));
  const del = (id) => tx("readwrite", (s) => s.delete(id));
  const all = async () => ((await tx("readonly", (s) => s.getAll())) || []).sort((a, b) => a.ts - b.ts);
  const clear = () => tx("readwrite", (s) => s.clear());

  function fromResult(data, plant) {
    return {
      ts: Date.now(), plant: (plant || "").trim() || "My plant",
      prediction: data.prediction, confidence: data.confidence, color: data.color,
      severity: data.severity ? { percent: data.severity.percent, level: data.severity.level,
        lesion_count: data.severity.lesion_count, color: data.severity.color } : null,
      verdict: data.verdict, card: data.farmer_card,
      overlay: data.severity ? data.severity.overlay : null, original: data.severity ? data.severity.original : null,
    };
  }

  // ───────── words for reports & progress (4 languages) ─────────
  const W = {
    en: { title: "Leaf Health Report", date: "Date", plant: "Plant", leaf: "Leaf area affected", what: "What to do",
          next: "Next check", vs: "Compared with", improving: "Improving — treatment is working", worse: "Getting worse — contact KVK today",
          stable: "No big change", recovered: "Recovered — leaf looks healthy", first: "First scan of this plant",
          note: "Decision support only. Confirm product and dose with your Coffee Board office or KVK.",
          remind: "Re-check plant", example: "EXAMPLE DATA — for demonstration", conf: "confidence" },
    hi: { title: "पत्ती स्वास्थ्य रिपोर्ट", date: "तारीख़", plant: "पौधा", leaf: "पत्ती का प्रभावित हिस्सा", what: "क्या करें",
          next: "अगली जाँच", vs: "पिछली जाँच से तुलना", improving: "सुधार हो रहा है — उपचार काम कर रहा है", worse: "बिगड़ रहा है — आज ही KVK से संपर्क करें",
          stable: "कोई बड़ा बदलाव नहीं", recovered: "ठीक हो गया — पत्ती स्वस्थ दिख रही है", first: "इस पौधे की पहली जाँच",
          note: "केवल निर्णय सहायता। उत्पाद और मात्रा अपने कॉफ़ी बोर्ड कार्यालय या KVK से पक्की करें।",
          remind: "पौधे की दोबारा जाँच", example: "उदाहरण डेटा — प्रदर्शन के लिए", conf: "विश्वास" },
    kn: { title: "ಎಲೆ ಆರೋಗ್ಯ ವರದಿ", date: "ದಿನಾಂಕ", plant: "ಗಿಡ", leaf: "ಎಲೆಯ ಬಾಧಿತ ಭಾಗ", what: "ಏನು ಮಾಡಬೇಕು",
          next: "ಮುಂದಿನ ಪರೀಕ್ಷೆ", vs: "ಹಿಂದಿನ ಪರೀಕ್ಷೆಯೊಂದಿಗೆ ಹೋಲಿಕೆ", improving: "ಸುಧಾರಿಸುತ್ತಿದೆ — ಚಿಕಿತ್ಸೆ ಫಲ ನೀಡುತ್ತಿದೆ", worse: "ಹದಗೆಡುತ್ತಿದೆ — ಇಂದೇ KVK ಸಂಪರ್ಕಿಸಿ",
          stable: "ದೊಡ್ಡ ಬದಲಾವಣೆ ಇಲ್ಲ", recovered: "ಗುಣಮುಖವಾಗಿದೆ — ಎಲೆ ಆರೋಗ್ಯಕರವಾಗಿದೆ", first: "ಈ ಗಿಡದ ಮೊದಲ ಪರೀಕ್ಷೆ",
          note: "ಇದು ನಿರ್ಧಾರಕ್ಕೆ ಸಹಾಯ ಮಾತ್ರ. ಉತ್ಪನ್ನ ಮತ್ತು ಪ್ರಮಾಣವನ್ನು ಕಾಫಿ ಮಂಡಳಿ ಕಚೇರಿ ಅಥವಾ KVK ಯಿಂದ ಖಚಿತಪಡಿಸಿ.",
          remind: "ಗಿಡವನ್ನು ಮತ್ತೆ ಪರೀಕ್ಷಿಸಿ", example: "ಉದಾಹರಣೆ ಡೇಟಾ — ಪ್ರದರ್ಶನಕ್ಕಾಗಿ", conf: "ವಿಶ್ವಾಸ" },
    ml: { title: "ഇല ആരോഗ്യ റിപ്പോർട്ട്", date: "തീയതി", plant: "ചെടി", leaf: "ബാധിച്ച ഇലഭാഗം", what: "എന്ത് ചെയ്യണം",
          next: "അടുത്ത പരിശോധന", vs: "മുൻ പരിശോധനയുമായി താരതമ്യം", improving: "മെച്ചപ്പെടുന്നു — ചികിത്സ ഫലിക്കുന്നു", worse: "മോശമാകുന്നു — ഇന്നുതന്നെ KVK-യെ ബന്ധപ്പെടുക",
          stable: "വലിയ മാറ്റമില്ല", recovered: "സുഖപ്പെട്ടു — ഇല ആരോഗ്യകരമാണ്", first: "ഈ ചെടിയുടെ ആദ്യ പരിശോധന",
          note: "തീരുമാനത്തിനുള്ള സഹായം മാത്രം. ഉൽപ്പന്നവും അളവും കോഫി ബോർഡ് ഓഫീസിൽ നിന്നോ KVK-യിൽ നിന്നോ ഉറപ്പാക്കുക.",
          remind: "ചെടി വീണ്ടും പരിശോധിക്കുക", example: "ഉദാഹരണ ഡാറ്റ — പ്രദർശനത്തിന്", conf: "വിശ്വാസ്യത" },
  };
  const w = (lang, k) => (W[lang] && W[lang][k]) || W.en[k];
  const LOCALE = { en: "en-IN", hi: "hi-IN", kn: "kn-IN", ml: "ml-IN" };
  const fmtDate = (ts, lang) => new Date(ts).toLocaleDateString(LOCALE[lang] || "en-IN", { day: "numeric", month: "short", year: "numeric" });
  const recheckTs = (rec) => rec.ts + ((rec.verdict && rec.verdict.recheck_days) || 0) * 86400000;
  const sev = (rec) => (rec.severity ? rec.severity.percent : 0);

  // Compare a scan with the previous scan of the same plant
  function trend(rec, prev) {
    if (!prev) return { key: "first", icon: "🆕", color: "#9ca3af" };
    if (rec.prediction === "Healthy" && prev.prediction !== "Healthy") return { key: "recovered", icon: "✅", color: "#22c55e" };
    const d = sev(rec) - sev(prev);
    if (d <= -2) return { key: "improving", icon: "📉", color: "#22c55e", d };
    if (d >= 2) return { key: "worse", icon: "📈", color: "#ef4444", d };
    return { key: "stable", icon: "➖", color: "#eab308", d };
  }
  // Old builds saved every scan as "My plant"; treat each of those as its own plant
  const LEGACY = "My plant";
  const groupKey = (r) => (r.plant === LEGACY ? LEGACY + "#" + r.id : r.plant);
  // New scans get their own plant ("Plant 1", "Plant 2", ...) unless the farmer picks an existing name
  async function nextPlantName() {
    const names = new Set((await all()).map((r) => r.plant));
    let n = 1;
    while (names.has("Plant " + n)) n++;
    return "Plant " + n;
  }
  async function previousOf(rec) {
    const same = (await all()).filter((r) => groupKey(r) === groupKey(rec) && r.ts < rec.ts && r.id !== rec.id);
    return same.length ? same[same.length - 1] : null;
  }

  // ───────── report image (canvas) ─────────
  function loadImg(src) {
    return new Promise((res) => { if (!src) return res(null); const i = new Image(); i.onload = () => res(i); i.onerror = () => res(null); i.src = src; });
  }
  function wrap(ctx, text, x, y, maxW, lh) {
    const words = String(text).split(/\s+/); let line = "", lines = [];
    for (const word of words) {
      const test = line ? line + " " + word : word;
      if (ctx.measureText(test).width > maxW && line) { lines.push(line); line = word; } else line = test;
    }
    if (line) lines.push(line);
    lines.forEach((l, i) => ctx.fillText(l, x, y + i * lh));
    return y + lines.length * lh;
  }
  function rrect(ctx, x, y, w_, h, r) { ctx.beginPath(); ctx.roundRect ? ctx.roundRect(x, y, w_, h, r) : ctx.rect(x, y, w_, h); }

  async function reportCanvas(rec, lang, prev) {
    const c = card(rec, lang), v = rec.verdict ? rec.verdict.text[lang] || rec.verdict.text.en : null;
    const Wd = 1080, P = 56, cv = document.createElement("canvas"); cv.width = Wd; cv.height = 2000;
    const ctx = cv.getContext("2d"), F = (s, b) => `${b ? "700" : "400"} ${s}px "Noto Sans", "Nirmala UI", Arial, sans-serif`;
    ctx.fillStyle = "#0a0f0d"; ctx.fillRect(0, 0, Wd, cv.height);
    ctx.fillStyle = "#16a34a"; ctx.fillRect(0, 0, Wd, 150);
    ctx.fillStyle = "#fff"; ctx.font = F(30, true); ctx.fillText("🍃 CoffeeGuard AI", P, 62);
    ctx.font = F(44, true); ctx.fillText(w(lang, "title"), P, 120);
    let y = 200;
    if (rec.demo) { ctx.fillStyle = "#f59e0b"; ctx.font = F(26, true); ctx.fillText("⚠ " + w(lang, "example"), P, y); y += 46; }
    ctx.fillStyle = "#a7c4b8"; ctx.font = F(28);
    ctx.fillText(`${w(lang, "date")}: ${fmtDate(rec.ts, lang)}     ${w(lang, "plant")}: ${rec.plant}`, P, y); y += 34;
    const [o, s] = await Promise.all([loadImg(rec.original), loadImg(rec.overlay)]);
    const iw = (Wd - 2 * P - 24) / 2, ih = iw / 2;
    if (o) { ctx.save(); rrect(ctx, P, y, iw, ih, 18); ctx.clip(); ctx.drawImage(o, P, y, iw, ih); ctx.restore(); }
    if (s) { ctx.save(); rrect(ctx, P + iw + 24, y, iw, ih, 18); ctx.clip(); ctx.drawImage(s, P + iw + 24, y, iw, ih); ctx.restore(); }
    y += ih + 70;
    ctx.fillStyle = rec.color || "#22c55e"; ctx.font = F(54, true); y = wrap(ctx, c ? c.name : rec.prediction, P, y, Wd - 2 * P, 62);
    ctx.fillStyle = "#a7c4b8"; ctx.font = F(26); ctx.fillText(`${rec.confidence}% ${w(lang, "conf")}`, P, y); y += 60;
    if (rec.severity) {
      ctx.fillStyle = "#f0fdf4"; ctx.font = F(64, true); ctx.fillText(rec.severity.percent + "%", P, y + 10);
      ctx.font = F(28); ctx.fillStyle = "#a7c4b8";
      const lvl = c && c.severity ? c.severity[rec.severity.level] : rec.severity.level;
      ctx.fillText(`${w(lang, "leaf")} · ${lvl}`, P + 230, y); y += 70;
    }
    if (v) {
      const vc = rec.verdict.color || "#22c55e";
      ctx.fillStyle = vc + "33"; rrect(ctx, P, y, Wd - 2 * P, 150, 22); ctx.fill();
      ctx.fillStyle = vc; ctx.font = F(40, true); ctx.fillText(`${rec.verdict.icon || ""} ${v.title}`, P + 28, y + 62);
      ctx.fillStyle = "#f0fdf4"; ctx.font = F(27); wrap(ctx, "🗓 " + v.recheck, P + 28, y + 108, Wd - 2 * P - 56, 34);
      y += 190;
    }
    if (prev) {
      const t = trend(rec, prev);
      ctx.fillStyle = "#a7c4b8"; ctx.font = F(26); ctx.fillText(`${w(lang, "vs")} (${fmtDate(prev.ts, lang)}): ${sev(prev)}% → ${sev(rec)}%`, P, y); y += 44;
      ctx.fillStyle = t.color; ctx.font = F(34, true); y = wrap(ctx, `${t.icon} ${w(lang, t.key)}`, P, y, Wd - 2 * P, 42) + 24;
    }
    if (c) {
      ctx.fillStyle = "#86efac"; ctx.font = F(32, true); ctx.fillText(w(lang, "what"), P, y); y += 50;
      ctx.font = F(29); ctx.fillStyle = "#f0fdf4";
      c.actions.forEach((a, i) => { y = wrap(ctx, `${i + 1}. ${a}`, P, y, Wd - 2 * P, 40) + 14; });
    }
    if (rec.verdict && rec.verdict.recheck_days) {
      y += 10; ctx.fillStyle = "#fbbf24"; ctx.font = F(30, true);
      ctx.fillText(`⏰ ${w(lang, "next")}: ${fmtDate(recheckTs(rec), lang)}`, P, y); y += 56;
    }
    ctx.fillStyle = "#5a7a6c"; ctx.font = F(23); y = wrap(ctx, w(lang, "note"), P, y + 10, Wd - 2 * P, 30);
    ctx.fillText(location.host, P, y + 16); y += 50;
    const out = document.createElement("canvas"); out.width = Wd; out.height = y;
    out.getContext("2d").drawImage(cv, 0, 0);
    return out;
  }
  const card = (rec, lang) => (rec.card ? rec.card[lang] || rec.card.en : null);

  async function shareReport(rec, lang) {
    const canvas = await reportCanvas(rec, lang, await previousOf(rec));
    const blob = await new Promise((r) => canvas.toBlob(r, "image/png"));
    const name = `CoffeeGuard-report-${new Date(rec.ts).toISOString().slice(0, 10)}.png`;
    const file = new File([blob], name, { type: "image/png" });
    if (navigator.canShare && navigator.canShare({ files: [file] }) && /Android|iPhone|iPad/i.test(navigator.userAgent)) {
      try { await navigator.share({ files: [file], title: w(lang, "title") }); return "shared"; } catch (e) { if (e.name === "AbortError") return "cancelled"; }
    }
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    return "downloaded";
  }

  // ───────── PDF report ─────────
  // Builds a real PDF in the browser (no library, works offline): the report
  // image is embedded as a JPEG on an A4-width page. Because the text is part of
  // the image, Hindi / Kannada / Malayalam always display correctly.
  function canvasToPdf(canvas) {
    const jpeg = atob(canvas.toDataURL("image/jpeg", 0.92).split(",")[1]);
    const pw = 595.28, ph = +(pw * canvas.height / canvas.width).toFixed(2);   // A4 width in points
    const enc = new TextEncoder(), parts = [], offsets = [];
    let size = 0;
    const push = (x) => { const b = typeof x === "string" ? enc.encode(x) : x; parts.push(b); size += b.length; };
    const bin = new Uint8Array(jpeg.length);
    for (let i = 0; i < jpeg.length; i++) bin[i] = jpeg.charCodeAt(i);
    const content = `q ${pw} 0 0 ${ph} 0 0 cm /Im0 Do Q`;
    const objs = [
      "<< /Type /Catalog /Pages 2 0 R >>",
      "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${pw} ${ph}] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>`,
      null, // image, written below
      `<< /Length ${content.length} >>\nstream\n${content}\nendstream`,
    ];
    push("%PDF-1.4\n%âãÏÓ\n");
    objs.forEach((o, i) => {
      offsets.push(size);
      push(`${i + 1} 0 obj\n`);
      if (o === null) {
        push(`<< /Type /XObject /Subtype /Image /Width ${canvas.width} /Height ${canvas.height} /ColorSpace /DeviceRGB ` +
             `/BitsPerComponent 8 /Filter /DCTDecode /Length ${bin.length} >>\nstream\n`);
        push(bin); push("\nendstream");
      } else push(o);
      push("\nendobj\n");
    });
    const xref = size;
    push(`xref\n0 ${objs.length + 1}\n0000000000 65535 f \n` + offsets.map((o) => String(o).padStart(10, "0") + " 00000 n \n").join(""));
    push(`trailer\n<< /Size ${objs.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`);
    return new Blob(parts, { type: "application/pdf" });
  }

  async function downloadPdf(rec, lang) {
    const canvas = await reportCanvas(rec, lang, await previousOf(rec));
    const blob = canvasToPdf(canvas);
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
    a.download = `CoffeeGuard-report-${new Date(rec.ts).toISOString().slice(0, 10)}.pdf`;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    return "downloaded";
  }

  // ───────── re-check reminder (Google Calendar) ─────────
  function reminderUrl(rec, lang) {
    const d = new Date(recheckTs(rec)), d2 = new Date(d.getTime() + 86400000);
    const ymd = (x) => x.toISOString().slice(0, 10).replace(/-/g, "");
    const c = card(rec, lang);
    const text = `🌿 ${w(lang, "remind")}: ${rec.plant}`;
    const details = `${c ? c.name : rec.prediction} — ${sev(rec)}% (${fmtDate(rec.ts, lang)}). ${location.origin}/predict`;
    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(text)}&dates=${ymd(d)}/${ymd(d2)}&details=${encodeURIComponent(details)}`;
  }

  // ───────── export / import ─────────
  async function exportAll() {
    const blob = new Blob([JSON.stringify({ app: "CoffeeGuard", version: 1, scans: await all() })], { type: "application/json" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
    a.download = `CoffeeGuard-my-scans-${new Date().toISOString().slice(0, 10)}.json`; a.click();
  }
  async function importFile(file) {
    const data = JSON.parse(await file.text());
    if (!data || data.app !== "CoffeeGuard" || !Array.isArray(data.scans)) throw new Error("Not a CoffeeGuard backup file");
    const have = new Set((await all()).map((r) => r.ts + "|" + r.plant));
    let n = 0;
    for (const r of data.scans) { if (have.has(r.ts + "|" + r.plant)) continue; const { id, ...rest } = r; await save(rest); n++; }
    return n;
  }

  window.CGDiary = { save, put, get, del, all, clear, fromResult, trend, previousOf, groupKey, nextPlantName, reportCanvas, shareReport, downloadPdf,
                     reminderUrl, exportAll, importFile, recheckTs, fmtDate, w, sev, card };
})();
