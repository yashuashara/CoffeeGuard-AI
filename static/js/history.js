/* My Scans page: history grouped by plant, progress chart, re-check due,
   report in any language, backup/restore, labelled example plant. */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const D = window.CGDiary;
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const LANGS = { en: "English", hi: "हिन्दी", kn: "ಕನ್ನಡ", ml: "മലയാളം" };
  const T = {
    en: { scans: "scans", plants: "plants", due: "due for re-check", dueBadge: "⏰ Re-check due", next: "Next check",
          latest: "Latest", example: "EXAMPLE", report: "🖼️ Share report image", pdf: "📑 Download PDF", pdfOk: "✅ PDF saved — print it or send it to your KVK officer.", remind: "⏰ Remind me", del: "🗑️ Delete this scan",
          confirmClear: "Delete ALL saved scans from this phone?", confirmDel: "Delete this scan?", restored: "Restored {n} scan(s).",
          demoDone: "Example plant added (marked EXAMPLE). Tap a scan to see its report.", what: "What to do", conf: "confidence" },
    hi: { scans: "जाँचें", plants: "पौधे", due: "दोबारा जाँच बाकी", dueBadge: "⏰ दोबारा जाँच का समय", next: "अगली जाँच",
          latest: "नवीनतम", example: "उदाहरण", report: "🖼️ रिपोर्ट फ़ोटो भेजें", pdf: "📑 PDF डाउनलोड करें", pdfOk: "✅ PDF सेव हुई — प्रिंट करें या KVK अधिकारी को भेजें।", remind: "⏰ याद दिलाएँ", del: "🗑️ यह जाँच हटाएँ",
          confirmClear: "इस फ़ोन से सभी सेव जाँचें हटाएँ?", confirmDel: "यह जाँच हटाएँ?", restored: "{n} जाँच(ें) वापस लाई गईं।",
          demoDone: "उदाहरण पौधा जोड़ा गया (उदाहरण चिह्नित)।", what: "क्या करें", conf: "विश्वास" },
    kn: { scans: "ಪರೀಕ್ಷೆಗಳು", plants: "ಗಿಡಗಳು", due: "ಮರುಪರೀಕ್ಷೆ ಬಾಕಿ", dueBadge: "⏰ ಮರುಪರೀಕ್ಷೆಯ ಸಮಯ", next: "ಮುಂದಿನ ಪರೀಕ್ಷೆ",
          latest: "ಇತ್ತೀಚಿನದು", example: "ಉದಾಹರಣೆ", report: "🖼️ ವರದಿ ಚಿತ್ರ ಹಂಚಿಕೊಳ್ಳಿ", pdf: "📑 PDF ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ", pdfOk: "✅ PDF ಉಳಿಸಲಾಗಿದೆ — ಮುದ್ರಿಸಿ ಅಥವಾ KVK ಅಧಿಕಾರಿಗೆ ಕಳುಹಿಸಿ.", remind: "⏰ ನೆನಪಿಸಿ", del: "🗑️ ಈ ಪರೀಕ್ಷೆ ಅಳಿಸಿ",
          confirmClear: "ಈ ಫೋನ್‌ನಿಂದ ಎಲ್ಲಾ ಪರೀಕ್ಷೆಗಳನ್ನು ಅಳಿಸಬೇಕೇ?", confirmDel: "ಈ ಪರೀಕ್ಷೆ ಅಳಿಸಬೇಕೇ?", restored: "{n} ಪರೀಕ್ಷೆ(ಗಳು) ಮರುಸ್ಥಾಪಿಸಲಾಗಿದೆ.",
          demoDone: "ಉದಾಹರಣೆ ಗಿಡ ಸೇರಿಸಲಾಗಿದೆ (ಉದಾಹರಣೆ ಎಂದು ಗುರುತಿಸಲಾಗಿದೆ).", what: "ಏನು ಮಾಡಬೇಕು", conf: "ವಿಶ್ವಾಸ" },
    ml: { scans: "പരിശോധനകൾ", plants: "ചെടികൾ", due: "വീണ്ടും പരിശോധിക്കാനുണ്ട്", dueBadge: "⏰ വീണ്ടും പരിശോധിക്കാൻ സമയമായി", next: "അടുത്ത പരിശോധന",
          latest: "ഏറ്റവും പുതിയത്", example: "ഉദാഹരണം", report: "🖼️ റിപ്പോർട്ട് ചിത്രം പങ്കിടുക", pdf: "📑 PDF ഡൗൺലോഡ് ചെയ്യുക", pdfOk: "✅ PDF സേവ് ചെയ്തു — പ്രിന്റ് ചെയ്യുക അല്ലെങ്കിൽ KVK ഉദ്യോഗസ്ഥന് അയക്കുക.", remind: "⏰ ഓർമ്മിപ്പിക്കുക", del: "🗑️ ഈ പരിശോധന ഇല്ലാതാക്കുക",
          confirmClear: "ഈ ഫോണിൽ നിന്ന് എല്ലാ പരിശോധനകളും ഇല്ലാതാക്കണോ?", confirmDel: "ഈ പരിശോധന ഇല്ലാതാക്കണോ?", restored: "{n} പരിശോധന(കൾ) പുനഃസ്ഥാപിച്ചു.",
          demoDone: "ഉദാഹരണ ചെടി ചേർത്തു (ഉദാഹരണം എന്ന് അടയാളപ്പെടുത്തി).", what: "എന്ത് ചെയ്യണം", conf: "വിശ്വാസ്യത" },
  };
  let lang = "en";
  try { lang = localStorage.getItem("cg-lang") || "en"; } catch (e) {}
  if (!T[lang]) lang = "en";
  const t = (k, n) => ((T[lang] && T[lang][k]) || T.en[k]).replace("{n}", n);
  const nameOf = (r) => { const c = D.card(r, lang); return c ? c.name : r.prediction; };
  let open = null;

  function msg(text) { const m = $("h-msg"); m.hidden = !text; m.textContent = text || ""; }

  function langPills() {
    $("h-langs").innerHTML = "";
    Object.entries(LANGS).forEach(([code, label]) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "lang-pill" + (code === lang ? " active" : ""); b.textContent = label;
      b.onclick = () => { lang = code; try { localStorage.setItem("cg-lang", code); } catch (e) {} langPills(); render(); if (open) openScan(open.id); };
      $("h-langs").appendChild(b);
    });
  }

  // small SVG line chart of severity % over time
  function chart(scans) {
    if (scans.length < 2) return "";
    const W = 320, H = 110, P = 24, max = Math.max(10, ...scans.map(D.sev)) * 1.15;
    const t0 = scans[0].ts, t1 = scans[scans.length - 1].ts;
    // evenly spaced points, so scans taken minutes apart don't overlap
    const idx = new Map(scans.map((r, i) => [r, i]));
    const x = (r) => P + (idx.get(r) / (scans.length - 1)) * (W - 2 * P);
    const sameDay = new Date(t0).toDateString() === new Date(t1).toDateString();
    const lbl = (ts) => (sameDay ? new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : D.fmtDate(ts, lang));
    const y = (r) => H - P - (D.sev(r) / max) * (H - 2 * P);
    const pts = scans.map((r) => `${x(r).toFixed(1)},${y(r).toFixed(1)}`).join(" ");
    const dots = scans.map((r) => `<circle cx="${x(r).toFixed(1)}" cy="${y(r).toFixed(1)}" r="5" fill="${r.color || "#22c55e"}"/>
        <text x="${x(r).toFixed(1)}" y="${(y(r) - 10).toFixed(1)}" text-anchor="middle">${D.sev(r)}%</text>`).join("");
    return `<svg class="h-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Leaf area affected over time">
      <line x1="${P}" y1="${H - P}" x2="${W - P}" y2="${H - P}" class="h-axis"/>
      <polyline points="${pts}" fill="none" stroke="#4ade80" stroke-width="3" stroke-linejoin="round"/>${dots}
      <text x="${P}" y="${H - 6}">${esc(lbl(t0))}</text>
      <text x="${W - P}" y="${H - 6}" text-anchor="end">${esc(lbl(t1))}</text></svg>`;
  }

  async function render() {
    const scans = await D.all();
    const byPlant = {};
    scans.forEach((r) => { const k = D.groupKey(r); (byPlant[k] = byPlant[k] || []).push(r); });
    const now = Date.now();
    const due = Object.values(byPlant).filter((list) => { const l = list[list.length - 1]; return l.verdict && l.verdict.recheck_days && D.recheckTs(l) <= now; }).length;
    $("h-empty").hidden = scans.length > 0;
    $("h-summary").innerHTML = scans.length
      ? `<span><b>${scans.length}</b> ${esc(t("scans"))}</span><span><b>${Object.keys(byPlant).length}</b> ${esc(t("plants"))}</span>` +
        (due ? `<span class="due"><b>${due}</b> ${esc(t("due"))}</span>` : "") : "";
    const box = $("h-plants");
    box.innerHTML = "";
    Object.entries(byPlant).sort((a, b) => b[1][b[1].length - 1].ts - a[1][a[1].length - 1].ts).forEach(([plant, list]) => {
      const last = list[list.length - 1], prev = list.length > 1 ? list[list.length - 2] : null;
      const tr = D.trend(last, prev), isDue = last.verdict && last.verdict.recheck_days && D.recheckTs(last) <= now;
      const shown = plant.startsWith("My plant#") ? `Leaf scan · ${D.fmtDate(last.ts, lang)} ${new Date(last.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : plant;
      const el = document.createElement("article");
      el.className = "plant-group";
      el.innerHTML = `
        <header class="pg-head">
          <div><h3>🌱 ${esc(shown)} ${last.demo ? `<span class="demo-tag">${esc(t("example"))}</span>` : ""}</h3>
            <div class="pg-latest">${esc(t("latest"))}: <b style="color:${last.color}">${esc(nameOf(last))}</b> · ${D.sev(last)}%
              · <span style="color:${last.verdict ? last.verdict.color : "#9ca3af"}">${last.verdict ? esc(last.verdict.icon + " " + (last.verdict.text[lang] || last.verdict.text.en).title) : ""}</span></div></div>
          <div class="pg-badges">
            ${isDue ? `<span class="due-badge">${esc(t("dueBadge"))}</span>` : last.verdict && last.verdict.recheck_days ? `<span class="next-badge">${esc(t("next"))}: ${esc(D.fmtDate(D.recheckTs(last), lang))}</span>` : ""}
            <span class="trend-badge" style="--t:${tr.color}">${tr.icon} ${esc(D.w(lang, tr.key))}</span>
          </div>
        </header>
        ${chart(list)}
        <div class="pg-scans"></div>`;
      const sc = el.querySelector(".pg-scans");
      list.slice().reverse().forEach((r) => {
        const b = document.createElement("button");
        b.type = "button"; b.className = "pg-scan";
        b.innerHTML = `<img alt="" src="${r.overlay || r.original || ""}"><b>${esc(D.fmtDate(r.ts, lang))}</b>
          <span style="color:${r.color}">${esc(nameOf(r))}</span><small>${D.sev(r)}%${r.demo ? " · " + esc(t("example")) : ""}</small>`;
        b.onclick = () => openScan(r.id);
        sc.appendChild(b);
      });
      box.appendChild(el);
    });
  }

  async function openScan(id) {
    const r = await D.get(id);
    if (!r) return;
    open = r;
    const c = D.card(r, lang), v = r.verdict ? r.verdict.text[lang] || r.verdict.text.en : null;
    $("m-date").textContent = `${D.fmtDate(r.ts, lang)} · 🌱 ${r.plant}${r.demo ? " · " + t("example") : ""}`;
    $("m-title").textContent = nameOf(r);
    $("m-title").style.color = r.color;
    $("m-orig").src = r.original || ""; $("m-scan").src = r.overlay || "";
    const lvl = r.severity && c && c.severity ? c.severity[r.severity.level] : "";
    $("m-stats").innerHTML = `<span><b>${D.sev(r)}%</b> ${esc(c ? c.ui.area : "")}</span><span>${esc(lvl)}</span><span>${r.confidence}% ${esc(t("conf"))}</span>`;
    const mv = $("m-verdict");
    mv.hidden = !v;
    if (v) { mv.style.setProperty("--v", r.verdict.color); mv.innerHTML = `<div class="verdict-icon">${r.verdict.icon}</div><div class="verdict-body"><div class="verdict-title">${esc(v.title)}</div><div class="verdict-recheck">🗓️ ${esc(v.recheck)}</div></div>`; }
    const prev = await D.previousOf(r), mp = $("m-progress");
    if (prev) { const tr = D.trend(r, prev); mp.hidden = false; mp.style.setProperty("--t", tr.color);
      mp.innerHTML = `<div class="diary-trend">${tr.icon} ${esc(D.w(lang, tr.key))} <small>(${esc(D.fmtDate(prev.ts, lang))}: ${D.sev(prev)}% → ${D.sev(r)}%)</small></div>`; }
    else mp.hidden = true;
    $("m-what").textContent = t("what");
    $("m-steps").innerHTML = c ? c.actions.map((a) => `<li>${esc(a)}</li>`).join("") : "";
    $("m-report").textContent = t("report");
    $("m-pdf").textContent = t("pdf");
    $("m-remind").textContent = t("remind");
    $("m-remind").href = D.reminderUrl(r, lang);
    $("m-remind").hidden = !(r.verdict && r.verdict.recheck_days);
    $("m-delete").textContent = t("del");
    $("m-note").hidden = true;
    $("h-modal").hidden = false;
    document.body.style.overflow = "hidden";
  }
  function closeModal() { $("h-modal").hidden = true; document.body.style.overflow = ""; open = null; }
  $("m-close").onclick = closeModal;
  $("h-modal").addEventListener("click", (e) => { if (e.target === $("h-modal")) closeModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("h-modal").hidden) closeModal(); });
  $("m-report").onclick = async () => {
    const b = $("m-report"); b.disabled = true;
    try { const how = await D.shareReport(open, lang); if (how !== "cancelled") { $("m-note").hidden = false; $("m-note").textContent = "✅ " + t("report").replace("📄 ", ""); } }
    catch (e) { $("m-note").hidden = false; $("m-note").textContent = e.message; }
    b.disabled = false;
  };
  $("m-pdf").onclick = async () => {
    const b = $("m-pdf"); b.disabled = true;
    try { await D.downloadPdf(open, lang); $("m-note").hidden = false; $("m-note").textContent = t("pdfOk"); }
    catch (e) { $("m-note").hidden = false; $("m-note").textContent = e.message; }
    b.disabled = false;
  };
  $("m-delete").onclick = async () => { if (!confirm(t("confirmDel"))) return; await D.del(open.id); closeModal(); render(); };

  $("h-export").onclick = () => D.exportAll();
  $("h-import").onchange = async (e) => {
    const f = e.target.files[0]; if (!f) return;
    try { msg(t("restored", await D.importFile(f))); render(); } catch (err) { msg("⚠️ " + err.message); }
    e.target.value = "";
  };
  $("h-clear").onclick = async () => { if (!confirm(t("confirmClear"))) return; await D.clear(); msg(""); render(); };

  // Example plant for demonstrations: one REAL diagnosis of the sample rust leaf,
  // plus two earlier example points. Every record is flagged demo:true and shown as EXAMPLE.
  $("h-demo").onclick = async () => {
    const b = $("h-demo"); b.disabled = true; msg("…");
    try {
      const img = await (await fetch("/static/images/rust_sample.jpg")).blob();
      const fd = new FormData(); fd.append("file", img, "rust_sample.jpg");
      const data = await (await fetch("/api/predict", { method: "POST", body: fd })).json();
      if (data.error) throw new Error(data.message || data.error);
      const base = D.fromResult(data, "Example plant");
      const day = 86400000, now = Date.now(), real = base.severity ? base.severity.percent : 6;
      // same severity bands as the lesion scan (severity.py)
      const band = (p) => (p < 5 ? "minimal" : p < 15 ? "mild" : p < 35 ? "moderate" : "severe");
      const points = [[now - 20 * day, +(real * 2.6).toFixed(1)], [now - 10 * day, +(real * 1.5).toFixed(1)], [now, real]];
      for (const [ts, pct] of points) {
        await D.save({ ...base, ts, demo: true, severity: base.severity ? { ...base.severity, percent: pct, level: band(pct) } : null });
      }
      msg(t("demoDone"));
      render();
    } catch (e) { msg("⚠️ " + e.message); }
    b.disabled = false;
  };

  langPills();
  render();
})();
