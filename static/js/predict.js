/* CoffeeGuard AI — Predict page
 * Single-leaf + whole-plant diagnosis, lesion scan, action verdict,
 * voice read-aloud, data-saver compression, offline queue, WhatsApp
 * share and opt-in outbreak map.
 */
(function () {
  "use strict";

  // ───────────── helpers ─────────────
  const $ = (id) => document.getElementById(id);
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
  };
  const kb = (n) => (n / 1024 < 1024 ? Math.round(n / 1024) + " KB" : (n / 1048576).toFixed(1) + " MB");
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const UI = {
    en: { listen: "Listen", stop: "Stop", noVoice: "This phone has no {L} voice installed — showing text only. You can add it in phone Settings → Text-to-speech.",
          affected: "{a} of {n} leaves affected", avg: "Avg {s}% of leaf area", worst: "Worst leaf {s}%", leaf: "Leaf",
          offlineSaved: "📴 No signal — photo saved. It will be diagnosed automatically when you're back online.",
          pending: "📥 {n} saved photo(s) waiting for diagnosis.", share: "CoffeeGuard AI result", sev: "of leaf affected",
          steps: "What to do", plantRes: "Whole plant", mapAsk: "Share only the disease, severity and your approximate location (~1 km)? No photo is shared.",
          mapOk: "✅ Added to the outbreak map (location rounded to ~1 km).", mapFail: "Couldn't get your location — allow location access and try again.",
          fromOffline: "Diagnosed from your offline queue" },
    hi: { listen: "सुनें", stop: "रोकें", noVoice: "इस फ़ोन में {L} आवाज़ इंस्टॉल नहीं है — केवल टेक्स्ट दिखाया जा रहा है।",
          affected: "{n} में से {a} पत्तियाँ प्रभावित", avg: "औसत {s}% पत्ती प्रभावित", worst: "सबसे ज़्यादा {s}%", leaf: "पत्ती",
          offlineSaved: "📴 नेटवर्क नहीं — फ़ोटो सेव हो गई। नेटवर्क आने पर अपने-आप जाँच होगी।",
          pending: "📥 {n} सेव फ़ोटो जाँच का इंतज़ार कर रही हैं।", share: "CoffeeGuard AI परिणाम", sev: "पत्ती प्रभावित",
          steps: "क्या करें", plantRes: "पूरा पौधा", mapAsk: "केवल रोग, गंभीरता और आपकी अनुमानित जगह (~1 किमी) साझा करें? कोई फ़ोटो साझा नहीं होगी।",
          mapOk: "✅ प्रकोप मानचित्र में जोड़ा गया (जगह ~1 किमी तक गोल की गई)।", mapFail: "आपकी जगह नहीं मिली — लोकेशन की अनुमति दें और फिर कोशिश करें।",
          fromOffline: "ऑफ़लाइन कतार से जाँचा गया" },
    kn: { listen: "ಕೇಳಿ", stop: "ನಿಲ್ಲಿಸಿ", noVoice: "ಈ ಫೋನ್‌ನಲ್ಲಿ {L} ಧ್ವನಿ ಇನ್‌ಸ್ಟಾಲ್ ಆಗಿಲ್ಲ — ಪಠ್ಯ ಮಾತ್ರ ತೋರಿಸಲಾಗುತ್ತಿದೆ.",
          affected: "{n} ರಲ್ಲಿ {a} ಎಲೆಗಳು ಬಾಧಿತ", avg: "ಸರಾಸರಿ {s}% ಎಲೆ ಬಾಧಿತ", worst: "ಅತಿ ಹೆಚ್ಚು {s}%", leaf: "ಎಲೆ",
          offlineSaved: "📴 ನೆಟ್‌ವರ್ಕ್ ಇಲ್ಲ — ಫೋಟೋ ಉಳಿಸಲಾಗಿದೆ. ನೆಟ್‌ವರ್ಕ್ ಬಂದಾಗ ತಾನಾಗಿಯೇ ಪರೀಕ್ಷೆ ಆಗುತ್ತದೆ.",
          pending: "📥 {n} ಉಳಿಸಿದ ಫೋಟೋ(ಗಳು) ಪರೀಕ್ಷೆಗಾಗಿ ಕಾಯುತ್ತಿವೆ.", share: "CoffeeGuard AI ಫಲಿತಾಂಶ", sev: "ಎಲೆ ಬಾಧಿತ",
          steps: "ಏನು ಮಾಡಬೇಕು", plantRes: "ಇಡೀ ಗಿಡ", mapAsk: "ರೋಗ, ತೀವ್ರತೆ ಮತ್ತು ನಿಮ್ಮ ಅಂದಾಜು ಸ್ಥಳ (~1 ಕಿಮೀ) ಮಾತ್ರ ಹಂಚಿಕೊಳ್ಳಬೇಕೇ? ಫೋಟೋ ಹಂಚಿಕೊಳ್ಳುವುದಿಲ್ಲ.",
          mapOk: "✅ ರೋಗ ನಕ್ಷೆಗೆ ಸೇರಿಸಲಾಗಿದೆ (ಸ್ಥಳ ~1 ಕಿಮೀ ವರೆಗೆ ಅಂದಾಜು).", mapFail: "ನಿಮ್ಮ ಸ್ಥಳ ಸಿಗಲಿಲ್ಲ — ಲೊಕೇಶನ್ ಅನುಮತಿ ನೀಡಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
          fromOffline: "ಆಫ್‌ಲೈನ್ ಸರತಿಯಿಂದ ಪರೀಕ್ಷಿಸಲಾಗಿದೆ" },
    ml: { listen: "കേൾക്കുക", stop: "നിർത്തുക", noVoice: "ഈ ഫോണിൽ {L} ശബ്ദം ഇൻസ്റ്റാൾ ചെയ്തിട്ടില്ല — ടെക്സ്റ്റ് മാത്രം കാണിക്കുന്നു.",
          affected: "{n} ഇലകളിൽ {a} എണ്ണം ബാധിച്ചു", avg: "ശരാശരി {s}% ഇല ബാധിച്ചു", worst: "ഏറ്റവും കൂടുതൽ {s}%", leaf: "ഇല",
          offlineSaved: "📴 നെറ്റ്‌വർക്ക് ഇല്ല — ഫോട്ടോ സേവ് ചെയ്തു. നെറ്റ്‌വർക്ക് വരുമ്പോൾ തനിയെ പരിശോധിക്കും.",
          pending: "📥 {n} സേവ് ചെയ്ത ഫോട്ടോ(കൾ) പരിശോധനയ്ക്കായി കാത്തിരിക്കുന്നു.", share: "CoffeeGuard AI ഫലം", sev: "ഇല ബാധിച്ചു",
          steps: "എന്ത് ചെയ്യണം", plantRes: "മുഴുവൻ ചെടി", mapAsk: "രോഗം, തീവ്രത, നിങ്ങളുടെ ഏകദേശ സ്ഥലം (~1 കി.മീ) മാത്രം പങ്കിടണോ? ഫോട്ടോ പങ്കിടില്ല.",
          mapOk: "✅ രോഗ ഭൂപടത്തിൽ ചേർത്തു (സ്ഥലം ~1 കി.മീ വരെ ഏകദേശം).", mapFail: "നിങ്ങളുടെ സ്ഥലം കിട്ടിയില്ല — ലൊക്കേഷൻ അനുമതി നൽകി വീണ്ടും ശ്രമിക്കുക.",
          fromOffline: "ഓഫ്‌ലൈൻ ക്യൂവിൽ നിന്ന് പരിശോധിച്ചു" },
  };
  const LANG_NAME = { en: "English", hi: "Hindi", kn: "Kannada", ml: "Malayalam" };
  const SPEECH_LANG = { en: "en-IN", hi: "hi-IN", kn: "kn-IN", ml: "ml-IN" };
  const ICONS = { Healthy: "✅", Miner: "🟡", Phoma: "🔴", Rust: "🟠", Cercospora: "🟣", Uncertain: "❓" };
  const RANK = { retake: 0, none: 1, watch: 2, act_soon: 3, act_now: 4 };
  const t = (key, vars) => {
    let s = (UI[lang] && UI[lang][key]) || UI.en[key] || key;
    Object.entries(vars || {}).forEach(([k, v]) => (s = s.replace("{" + k + "}", v)));
    return s;
  };

  let lang = store.get("cg-lang", "en");
  if (!UI[lang]) lang = "en";
  let mode = "single";
  let singleFile = null;
  let plantFiles = [];
  let current = null;          // result currently shown in the detail card
  let plantResults = [];

  // ───────────── data saver: compress in the browser ─────────────
  async function compress(file, maxSide = 1280, quality = 0.85) {
    try {
      const bmp = await createImageBitmap(file);
      const s = Math.min(1, maxSide / Math.max(bmp.width, bmp.height));
      if (s === 1 && file.size < 400 * 1024) return file;
      const c = document.createElement("canvas");
      c.width = Math.round(bmp.width * s);
      c.height = Math.round(bmp.height * s);
      c.getContext("2d").drawImage(bmp, 0, 0, c.width, c.height);
      const blob = await new Promise((r) => c.toBlob(r, "image/jpeg", quality));
      return blob && blob.size < file.size ? blob : file;
    } catch (e) {
      return file;
    }
  }

  // ───────────── offline queue (IndexedDB) ─────────────
  const DB = "coffeeguard", STORE = "pending";
  function idb() {
    return new Promise((res, rej) => {
      const r = indexedDB.open(DB, 1);
      r.onupgradeneeded = () => r.result.createObjectStore(STORE, { keyPath: "id", autoIncrement: true });
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error);
    });
  }
  async function qOp(fn, mode_ = "readonly") {
    const db = await idb();
    return new Promise((res, rej) => {
      const tx = db.transaction(STORE, mode_);
      const out = fn(tx.objectStore(STORE));
      tx.oncomplete = () => res(out && out.result !== undefined ? out.result : out);
      tx.onerror = () => rej(tx.error);
    });
  }
  const qAdd = (item) => qOp((s) => s.add(item), "readwrite");
  const qAll = () => qOp((s) => s.getAll());
  const qDel = (id) => qOp((s) => s.delete(id), "readwrite");

  async function refreshPending() {
    let items = [];
    try { items = await qAll(); } catch (e) {}
    $("pending-banner").hidden = !items.length;
    if (items.length) $("pending-text").textContent = t("pending", { n: items.length });
    return items;
  }

  async function runQueue() {
    if (!navigator.onLine) return;
    const items = await refreshPending();
    if (!items.length) return;
    const done = [];
    for (const it of items) {
      try {
        const data = await diagnose(it.blob, it.name);
        await qDel(it.id);
        done.push({ data, blob: it.blob, name: it.name });
      } catch (e) {
        if (e.offline) break;
        await qDel(it.id);
      }
    }
    await refreshPending();
    if (done.length === 1) showSingle(done[0].data, t("fromOffline"));
    else if (done.length > 1) showPlant(done.map((d) => d.data), done.map((d) => d.blob), t("fromOffline"));
  }

  function updateOnline() {
    $("offline-banner").hidden = navigator.onLine;
    if (navigator.onLine) runQueue();
  }
  window.addEventListener("online", updateOnline);
  window.addEventListener("offline", updateOnline);

  // ───────────── API ─────────────
  async function diagnose(blob, name) {
    const fd = new FormData();
    fd.append("file", blob, name || "leaf.jpg");
    let res;
    try {
      res = await fetch("/api/predict", { method: "POST", body: fd });
    } catch (e) {
      const err = new Error("offline");
      err.offline = true;
      throw err;
    }
    const ct = res.headers.get("content-type") || "";
    if (!ct.includes("application/json")) {
      // Render free tier may return an HTML page while waking up
      const err = new Error("The server is waking up — please try again in a few seconds.");
      throw err;
    }
    const data = await res.json();
    data._ok = res.ok && !data.error;
    return data;
  }

  // ───────────── mode toggle ─────────────
  function setMode(m) {
    mode = m;
    $("mode-single").classList.toggle("active", m === "single");
    $("mode-plant").classList.toggle("active", m === "plant");
    $("mode-single").setAttribute("aria-selected", m === "single");
    $("mode-plant").setAttribute("aria-selected", m === "plant");
    $("main-file-input").multiple = m === "plant";
    $("upload-title").textContent = m === "plant" ? "Select 3–5 leaves from one plant" : "Select Leaf Image";
    resetView();
  }
  $("mode-single").onclick = () => setMode("single");
  $("mode-plant").onclick = () => setMode("plant");

  function resetView() {
    singleFile = null;
    plantFiles = [];
    $("main-upload-zone").style.display = "";
    $("main-preview").classList.remove("active");
    $("plant-preview").hidden = true;
    $("plant-summary").hidden = true;
    $("main-result").classList.remove("active");
    $("data-saver").hidden = true;
    $("plant-data-saver").hidden = true;
  }

  // ───────────── file selection ─────────────
  const input = $("main-file-input");
  input.addEventListener("change", (e) => takeFiles([...e.target.files]));
  const zone = $("main-upload-zone");
  zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("drag-over"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    takeFiles([...e.dataTransfer.files].filter((f) => f.type.startsWith("image/")));
  });
  $("change-photo").onclick = () => { resetView(); input.value = ""; input.click(); };
  $("plant-add").onclick = () => { input.value = ""; input.click(); };

  function takeFiles(files) {
    if (!files.length) return;
    if (mode === "single") {
      singleFile = files[0];
      $("main-preview-img").src = URL.createObjectURL(singleFile);
      $("main-filename").textContent = singleFile.name;
      $("main-filesize").textContent = kb(singleFile.size);
      $("main-preview").classList.add("active");
      $("main-result").classList.remove("active");
      zone.style.display = "none";
    } else {
      plantFiles = plantFiles.concat(files).slice(0, 5);
      renderPlantThumbs();
      $("plant-preview").hidden = false;
      $("plant-summary").hidden = true;
      $("main-result").classList.remove("active");
      zone.style.display = "none";
    }
  }

  function renderPlantThumbs() {
    const box = $("plant-thumbs");
    box.innerHTML = "";
    plantFiles.forEach((f, i) => {
      const d = document.createElement("div");
      d.className = "plant-thumb";
      d.innerHTML = `<img alt="Leaf ${i + 1}"><button type="button" aria-label="Remove leaf ${i + 1}">×</button><span>${i + 1}</span>`;
      d.querySelector("img").src = URL.createObjectURL(f);
      d.querySelector("button").onclick = () => {
        plantFiles.splice(i, 1);
        if (!plantFiles.length) resetView(); else renderPlantThumbs();
      };
      box.appendChild(d);
    });
    $("plant-add").hidden = plantFiles.length >= 5;
    $("plant-predict-btn").disabled = plantFiles.length < 1;
    $("plant-predict-btn").textContent = plantFiles.length < 3
      ? `🔬 Check ${plantFiles.length} leaf${plantFiles.length > 1 ? "ves" : ""} (3–5 recommended)`
      : `🔬 Check whole plant (${plantFiles.length} leaves)`;
  }

  function busy(on, text) {
    $("main-spinner").classList.toggle("active", on);
    if (text) $("spinner-text").textContent = text;
    const thumb = document.querySelector("#main-preview .preview-thumb");
    if (thumb) thumb.classList.toggle("scanning", on && mode === "single");
    document.querySelectorAll(".plant-thumb").forEach((el) => el.classList.toggle("scanning", on));
    $("main-predict-btn").disabled = on;
    $("plant-predict-btn").disabled = on;
  }

  function showSaver(el, orig, sent) {
    if (sent >= orig * 0.95) { el.hidden = true; return; }
    el.hidden = false;
    el.innerHTML = `📶 Data saver: sent <b>${kb(sent)}</b> instead of ${kb(orig)} (−${Math.round((1 - sent / orig) * 100)}%)`;
  }

  // ───────────── single leaf ─────────────
  $("main-predict-btn").onclick = async () => {
    if (!singleFile) return;
    const blob = await compress(singleFile);
    showSaver($("data-saver"), singleFile.size, blob.size);
    if (!navigator.onLine) return saveOffline([blob], [singleFile.name]);
    busy(true, "Checking photo quality, finding the leaf, running the AI model…");
    try {
      const data = await diagnose(blob, singleFile.name);
      showSingle(data);
    } catch (e) {
      if (e.offline) return saveOffline([blob], [singleFile.name]);
      notice("❌", "Something went wrong", "#ef4444", e.message, "Please try again in a moment.");
    } finally {
      busy(false);
      $("main-predict-btn").textContent = "🔬 Re-analyze leaf";
    }
  };

  async function saveOffline(blobs, names) {
    for (let i = 0; i < blobs.length; i++) await qAdd({ blob: blobs[i], name: names[i], ts: Date.now() });
    busy(false);
    notice("📴", "Saved offline", "#9ca3af", t("offlineSaved"), "");
    refreshPending();
  }
  $("pending-run").onclick = runQueue;

  // ───────────── whole plant ─────────────
  $("plant-predict-btn").onclick = async () => {
    if (!plantFiles.length) return;
    const blobs = [];
    for (const f of plantFiles) blobs.push(await compress(f));
    const orig = plantFiles.reduce((a, f) => a + f.size, 0);
    showSaver($("plant-data-saver"), orig, blobs.reduce((a, b) => a + b.size, 0));
    if (!navigator.onLine) return saveOffline(blobs, plantFiles.map((f) => f.name));
    const results = [];
    try {
      for (let i = 0; i < blobs.length; i++) {
        busy(true, `Scanning leaf ${i + 1} of ${blobs.length}…`);
        results.push(await diagnose(blobs[i], plantFiles[i].name));
      }
      showPlant(results, blobs);
    } catch (e) {
      if (e.offline) return saveOffline(blobs.slice(results.length), plantFiles.slice(results.length).map((f) => f.name));
      notice("❌", "Something went wrong", "#ef4444", e.message, "Please try again in a moment.");
    } finally {
      busy(false);
    }
  };

  function showPlant(results, blobs, label) {
    plantResults = results;
    const ok = results.filter((r) => r._ok && r.prediction !== "Uncertain");
    $("plant-summary").hidden = false;
    $("plant-preview").hidden = mode !== "plant";
    if (!ok.length) {
      $("plant-name").textContent = "Not sure";
      $("plant-name").style.color = "#9ca3af";
      $("plant-stats").innerHTML = "Retake clearer photos of 3–5 leaves.";
    } else {
      // plant diagnosis = disease with the highest summed probability across leaves
      const sum = {};
      ok.forEach((r) => Object.entries(r.probabilities).forEach(([k, v]) => (sum[k] = (sum[k] || 0) + v)));
      const sick = ok.filter((r) => r.prediction !== "Healthy");
      // every disease actually found on a leaf, most frequent (then highest probability mass) first
      const found = [...new Set(sick.map((r) => r.prediction))].sort((a, b) =>
        sick.filter((r) => r.prediction === b).length - sick.filter((r) => r.prediction === a).length || sum[b] - sum[a]);
      const plantDisease = found.length ? found[0] : "Healthy";
      const sevs = ok.map((r) => (r.severity ? r.severity.percent : 0));
      const avg = sevs.reduce((a, b) => a + b, 0) / sevs.length;
      const worst = ok.reduce((a, r) => (RANK[r.verdict.level] > RANK[a.verdict.level] ? r : a), ok[0]);
      const color = (ok.find((r) => r.prediction === plantDisease) || ok[0]).color;
      $("plant-name").textContent = found.length
        ? found.map((d) => (ICONS[d] || "🍃") + " " + d).join(" + ")
        : (ICONS.Healthy + " Healthy");
      $("plant-name").style.color = color;
      $("plant-stats").innerHTML = [
        t("affected", { a: sick.length, n: ok.length }),
        t("avg", { s: avg.toFixed(1) }),
        t("worst", { s: Math.max(...sevs).toFixed(1) }),
      ].map((x) => `<span>${esc(x)}</span>`).join("");
      // detail card shows the worst leaf, so the plant verdict is the most urgent one
      showSingle(worst, label || t("plantRes"));
    }
    const box = $("plant-leaves");
    box.innerHTML = "";
    results.forEach((r, i) => {
      const d = document.createElement("button");
      d.type = "button";
      d.className = "plant-leaf";
      const img = r.severity ? r.severity.overlay : (blobs && blobs[i] ? URL.createObjectURL(blobs[i]) : "");
      const name = r._ok ? r.prediction : (r.error === "bad_photo" ? "📷 Retake" : "Not a leaf");
      const sev = r._ok && r.severity ? r.severity.percent + "%" : "";
      d.innerHTML = `<img alt="">${""}<b>${esc(t("leaf"))} ${i + 1}</b><span style="color:${r.color || "#9ca3af"}">${esc(name)}</span><small>${esc(sev)}</small>`;
      d.querySelector("img").src = img;
      d.onclick = () => (r._ok ? showSingle(r, `${t("leaf")} ${i + 1}`) : showError(r));
      box.appendChild(d);
    });
  }

  // ───────────── render a single result ─────────────
  function showSingle(data, label) {
    if (!data._ok) return showError(data);
    current = data;
    const result = $("main-result");
    $("main-result-label").textContent = label || "Diagnosis";
    $("main-result-icon").textContent = ICONS[data.prediction] || "🍃";
    $("main-result-icon").style.background = data.color + "22";
    $("main-result-name").textContent = data.prediction;
    $("main-result-name").style.color = data.color;
    $("confidence-block").style.display = "";
    $("main-confidence-val").textContent = data.confidence + "%";
    $("main-confidence-bar").style.width = data.confidence + "%";
    $("main-confidence-bar").style.background = data.color;
    $("model-badge").textContent = data.model ? "🧠 Model: " + data.model : "";
    $("main-result-desc").textContent = data.description;
    $("main-result-rec").textContent = data.recommendation;
    $("prob-heading").style.display = "";
    const pb = $("main-prob-bars");
    pb.style.display = "";
    pb.innerHTML = Object.entries(data.probabilities).map(([k, v]) => `
      <div class="prob-item"><span class="prob-label">${esc(k)}</span>
      <div class="prob-bar"><div class="prob-fill ${esc(k.toLowerCase())}" style="width:${v}%"></div></div>
      <span class="prob-value">${v}%</span></div>`).join("");
    renderScan(data.severity);
    renderFarmerCard(data);
    $("result-actions").hidden = false;
    $("map-btn").hidden = data.prediction === "Uncertain";
    $("map-note").hidden = true;
    result.classList.add("active");
    stopVoice();
  }

  function showError(data) {
    if (data.error === "bad_photo" && data.quality) {
      const tip = data.quality.tips[lang] || data.quality.tips.en;
      return notice("📷", tip.title, "#f59e0b", tip.tip, "CoffeeGuard checks every photo before diagnosis so you never get advice from a bad picture.");
    }
    notice("⚠️", "Image Not Recognized", "#f59e0b",
      data.message || "Something went wrong while analyzing this image.",
      "Please upload a clear, close-up photo of a single coffee leaf.");
  }

  function notice(icon, title, color, description, recommendation) {
    current = null;
    $("main-result-label").textContent = "Notice";
    $("main-result-icon").textContent = icon;
    $("main-result-icon").style.background = color + "22";
    $("main-result-name").textContent = title;
    $("main-result-name").style.color = color;
    $("main-result-desc").textContent = description;
    $("main-result-rec").textContent = recommendation;
    $("confidence-block").style.display = "none";
    $("model-badge").textContent = "";
    $("main-prob-bars").style.display = "none";
    $("prob-heading").style.display = "none";
    $("scan-section").style.display = "none";
    $("farmer-card").style.display = "none";
    $("verdict").hidden = true;
    $("voice-note").hidden = true;
    $("result-actions").hidden = true;
    $("map-note").hidden = true;
    $("main-result").classList.add("active");
  }

  // ───────────── lesion scan + gauge ─────────────
  function renderScan(sev) {
    const section = $("scan-section");
    if (!sev) { section.style.display = "none"; return; }
    section.style.display = "";
    const compare = $("compare");
    $("scan-original").src = sev.original;
    $("scan-overlay").src = sev.overlay;
    compare.style.setProperty("--pos", "35%");
    compare.classList.remove("reveal"); void compare.offsetWidth; compare.classList.add("reveal");
    const fill = $("gauge-fill"), C = 314.16, pct = Math.min(sev.percent, 100);
    fill.style.stroke = sev.color; fill.style.color = sev.color;
    fill.style.strokeDashoffset = C;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      fill.style.strokeDashoffset = C * (1 - Math.max(pct, 1.5) / 100);
    }));
    const valEl = $("gauge-value"), start = performance.now();
    (function tick(now) {
      const k = Math.min((now - start) / 1400, 1), e = 1 - Math.pow(1 - k, 3);
      valEl.textContent = (pct * e).toFixed(1) + "%";
      if (k < 1) requestAnimationFrame(tick);
    })(start);
    const badge = $("severity-badge");
    badge.style.background = sev.color + "22";
    badge.style.color = sev.color;
    badge.style.border = "1px solid " + sev.color + "66";
  }

  (function initCompare() {
    const compare = $("compare");
    let dragging = false;
    const move = (x) => {
      const r = compare.getBoundingClientRect();
      compare.classList.remove("reveal");
      compare.style.setProperty("--pos", Math.min(Math.max((x - r.left) / r.width, 0), 1) * 100 + "%");
    };
    compare.addEventListener("pointerdown", (e) => { dragging = true; compare.setPointerCapture(e.pointerId); move(e.clientX); });
    compare.addEventListener("pointermove", (e) => dragging && move(e.clientX));
    compare.addEventListener("pointerup", () => (dragging = false));
    compare.addEventListener("pointercancel", () => (dragging = false));
  })();

  // ───────────── farmer card + verdict (4 languages) ─────────────
  function renderFarmerCard(data) {
    const box = $("farmer-card");
    if (!data.farmer_card) { box.style.display = "none"; return; }
    const pills = $("lang-pills");
    pills.innerHTML = "";
    Object.entries(data.languages).forEach(([code, name]) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "lang-pill" + (code === lang ? " active" : "");
      b.textContent = name;
      b.onclick = () => setLang(code);
      pills.appendChild(b);
    });
    box.style.display = "";
    paint();
  }

  function setLang(code) {
    lang = code;
    store.set("cg-lang", code);
    document.querySelectorAll(".lang-pill").forEach((b) => b.classList.toggle("active", b.textContent === current.languages[code]));
    stopVoice();
    paint();
    if (plantResults.length && !$("plant-summary").hidden) refreshPlantStats();
  }

  function refreshPlantStats() {
    const ok = plantResults.filter((r) => r._ok && r.prediction !== "Uncertain");
    if (!ok.length) return;
    const sevs = ok.map((r) => (r.severity ? r.severity.percent : 0));
    const sick = ok.filter((r) => r.prediction !== "Healthy");
    $("plant-stats").innerHTML = [t("affected", { a: sick.length, n: ok.length }),
      t("avg", { s: (sevs.reduce((a, b) => a + b, 0) / sevs.length).toFixed(1) }),
      t("worst", { s: Math.max(...sevs).toFixed(1) })].map((x) => `<span>${esc(x)}</span>`).join("");
  }

  function paint() {
    if (!current) return;
    const c = current.farmer_card[lang];
    $("farmer-card-title").textContent = "👨‍🌾 " + c.ui.card;
    $("farmer-card-name").textContent = c.name;
    $("farmer-steps").innerHTML = c.actions.map((a) => `<li>${esc(a)}</li>`).join("");
    $("farmer-dose").textContent = "ℹ️ " + c.ui.dose;
    const sev = current.severity;
    if (sev) {
      $("gauge-sub").textContent = c.ui.area;
      $("severity-badge").textContent = c.ui.severity + ": " + c.severity[sev.level];
      $("severity-meta").textContent = sev.lesion_count + " " + c.ui.spots;
    }
    const v = current.verdict;
    if (v) {
      const vt = v.text[lang];
      $("verdict").hidden = false;
      $("verdict").style.setProperty("--v", v.color);
      $("verdict-icon").textContent = v.icon;
      $("verdict-title").textContent = vt.title;
      $("verdict-recheck").textContent = "🗓️ " + vt.recheck;
      $("verdict-call").textContent = vt.call ? "📞 " + vt.call : "";
      $("verdict-call").hidden = !vt.call;
    }
    $("voice-label").textContent = speaking ? t("stop") : t("listen");
  }

  // ───────────── voice read-aloud ─────────────
  let speaking = false;
  function adviceText() {
    const c = current.farmer_card[lang], v = current.verdict.text[lang];
    const sev = current.severity ? `${current.severity.percent}% ${t("sev")}. ` : "";
    return `${c.name}. ${sev}${v.title}. ${v.call ? v.call + ". " : ""}${c.actions.map((a, i) => `${i + 1}. ${a}`).join(" ")} ${v.recheck}.`;
  }
  function stopVoice() {
    if ("speechSynthesis" in window) speechSynthesis.cancel();
    speaking = false;
    $("voice-label").textContent = t("listen");
  }
  $("voice-btn").onclick = () => {
    const note = $("voice-note");
    if (!("speechSynthesis" in window)) { note.hidden = false; note.textContent = t("noVoice", { L: LANG_NAME[lang] }); return; }
    if (speaking) return stopVoice();
    const u = new SpeechSynthesisUtterance(adviceText());
    u.lang = SPEECH_LANG[lang];
    u.rate = 0.9;
    const voices = speechSynthesis.getVoices();
    const voice = voices.find((v) => v.lang && v.lang.toLowerCase().startsWith(lang));
    note.hidden = !!voice || lang === "en";
    if (!voice && lang !== "en") note.textContent = t("noVoice", { L: LANG_NAME[lang] });
    if (voice) u.voice = voice;
    u.onend = u.onerror = () => { speaking = false; $("voice-label").textContent = t("listen"); };
    speaking = true;
    $("voice-label").textContent = t("stop");
    speechSynthesis.speak(u);
  };
  if ("speechSynthesis" in window) speechSynthesis.getVoices(); // warm up voice list

  // ───────────── WhatsApp share ─────────────
  $("share-btn").onclick = async () => {
    if (!current) return;
    const c = current.farmer_card[lang], v = current.verdict.text[lang];
    const sev = current.severity ? ` — ${current.severity.percent}% ${t("sev")}` : "";
    const plant = !$("plant-summary").hidden ? `\n${t("plantRes")}: ${$("plant-name").textContent} · ${[...$("plant-stats").children].map((s) => s.textContent).join(" · ")}` : "";
    const text = `🌿 ${t("share")}\n${c.name}${sev} (${current.confidence}%)${plant}\n\n${current.verdict.icon} ${v.title}\n${v.recheck}\n\n${t("steps")}:\n${c.actions.map((a, i) => `${i + 1}. ${a}`).join("\n")}\n\n${location.origin}`;
    if (navigator.share && /Android|iPhone|iPad/i.test(navigator.userAgent)) {
      try { await navigator.share({ text }); return; } catch (e) { /* fall through to WhatsApp link */ }
    }
    window.open("https://wa.me/?text=" + encodeURIComponent(text), "_blank", "noopener");
  };

  // ───────────── opt-in outbreak map ─────────────
  $("map-btn").onclick = () => {
    if (!current) return;
    const note = $("map-note");
    if (!window.confirm(t("mapAsk"))) return;
    if (!navigator.geolocation) { note.hidden = false; note.textContent = t("mapFail"); return; }
    navigator.geolocation.getCurrentPosition(async (pos) => {
      try {
        const r = await fetch("/api/report", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ disease: current.prediction, severity: current.severity ? current.severity.percent : 0,
                                 level: current.verdict.level, lat: pos.coords.latitude, lon: pos.coords.longitude }),
        });
        note.hidden = false;
        note.innerHTML = r.ok ? `${esc(t("mapOk"))} <a href="/map">Open map →</a>` : esc(t("mapFail"));
        if (r.ok) $("map-btn").disabled = true;
      } catch (e) { note.hidden = false; note.textContent = t("mapFail"); }
    }, () => { note.hidden = false; note.textContent = t("mapFail"); }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 });
  };

  // ───────────── start ─────────────
  updateOnline();
  refreshPending();
})();
