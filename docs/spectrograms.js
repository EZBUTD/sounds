/* Spectrograms page.
 *
 * Two halves, deliberately different in provenance:
 *
 * 1. PRECOMPUTED reference spectrograms (SPECTRO from spectro.js). Analysed
 *    offline by analyze_spectrograms.py so every visitor sees the same picture.
 *    Safari could not decodeAudioData() an .ogg before 18.4, so computing these
 *    in-browser would render an empty canvas for some readers with no
 *    explanation — the same class of silent failure as the tofu-box diacritic.
 *
 * 2. LIVE microphone analysis, which must run in-browser by definition. Audio
 *    stays local: no upload, no recording kept.
 *
 * NO MATCH SCORE. A similarity number between a microphone signal and a
 * reference recording is dominated by pitch, vocal tract length, mic and room
 * rather than by articulation. It would look authoritative and measure the wrong
 * thing — the exact failure this project already had once, with the allophone
 * "divergence rate" that turned out to be tracking documentation density. F1/F2
 * are reported instead because each corresponds to a checkable articulatory fact.
 */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);

  // ---------- shared colour ramp ----------
  // Light parchment -> deep ink, matching the site's heatmap treatment. Values
  // arrive as 0..255 where 255 is the loudest point in that recording.
  function ramp(v) {
    const t = v / 255;
    const l = 97 - 82 * t;                 // lightness %
    const s = 8 + 30 * t;                  // saturation %
    return `hsl(28, ${s}%, ${l}%)`;
  }

  // ================= 1. precomputed reference spectrograms =================
  const cards = [];          // {word, canvas, base, geom} for playhead redraws

  function renderCards() {
    const host = $("spec-cards");
    if (!host || typeof SPECTRO === "undefined") return;
    const S = SPECTRO;
    // The phoneme both cards realise, from the data rather than written into the
    // page: the section's claim is that these are two allophones of ONE phoneme,
    // and analyze_spectrograms.py checks each allophone really belongs to it.
    const PHONEME = S.phoneme;
    // one shared time scale so the two cards are visually comparable: a wider
    // aspiration really does look wider, rather than being normalised away
    const maxMs = Math.max(...S.words.map((w) => w.durationMs));

    for (const w of S.words) {
      const card = document.createElement("div");
      card.className = "spec-card";
      // Header states the relationship rather than implying it. A reader asked
      // whether this section compares two allophones of one phoneme — it does,
      // and the only cue was a pair of square brackets. So each card now spells
      // out /phoneme/ -> [allophone] and captions the arrow, which is the same
      // vocabulary the Allophones page establishes.
      card.innerHTML =
        `<div class="spec-head">` +
        `<span class="w">${w.word}</span>` +
        `<span class="deriv">` +
          `<span class="ipa ph">/${PHONEME}/</span>` +
          `<span class="arrow" aria-hidden="true">\u2192</span>` +
          `<span class="allo ipa">[${w.allophone}]</span>` +
        `</span>` +
        `<span class="lab">${w.label}</span>` +
        `<span class="vot">voice onset time <b>${Math.round(w.votMs)} ms</b></span>` +
        `</div>` +
        `<p class="spec-derivcap">the phoneme <span class="ipa">/${PHONEME}/</span> ` +
        `is pronounced <span class="ipa">[${w.allophone}]</span> here \u2014 ` +
        `${w.label}</p>` +
        `<p class="spec-note">${w.note}</p>`;

      const btn = document.createElement("button");
      btn.className = "play";
      btn.type = "button";
      btn.innerHTML = `<span aria-hidden="true">\u25B6</span> play`;
      btn.setAttribute("aria-label", `Play the recording of ${w.word}`);
      card.appendChild(btn);

      const cv = document.createElement("canvas");
      cv.className = "spec-canvas";
      cv.width = 900;
      cv.height = 260;
      cv.setAttribute("role", "img");
      cv.setAttribute("aria-label",
        `Spectrogram of "${w.word}", in which the phoneme ${PHONEME} is ` +
        `pronounced as the allophone ${w.allophone}. The stop is released at ` +
        `${Math.round(w.burstMs)} milliseconds and voicing begins at ` +
        `${Math.round(w.voiceMs)}, a voice onset time of ` +
        `${Math.round(w.votMs)} milliseconds (${w.label}).`);
      card.appendChild(cv);

      const legend = document.createElement("div");
      legend.className = "spec-legend";
      legend.innerHTML =
        `<span class="k"><span class="sw burst"></span>release</span>` +
        `<span class="k"><span class="sw voice"></span>voicing starts</span>` +
        `<span class="k"><span class="sw asp"></span>aspiration (the gap between)</span>` +
        `<span class="k">0\u20138 kHz, ${S.settings.winMs} ms window</span>`;
      card.appendChild(legend);

      host.appendChild(card);
      // Render once into an offscreen copy, then blit + overlay the playhead each
      // frame. Redrawing ~20k spectrogram cells per animation frame would be
      // wasteful and visibly janky.
      const base = document.createElement("canvas");
      base.width = cv.width;
      base.height = cv.height;
      drawSpectrogram(base, w, S.settings, maxMs);
      const geom = { L: 46, R: 12, T: 10, B: 30, maxMs };
      cv.getContext("2d").drawImage(base, 0, 0);
      cards.push({ word: w, canvas: cv, base, geom });
      btn.addEventListener("click", () => play(w, cv, base, geom, btn));
    }

    const gap = S.votGapMs;
    const sum = $("spec-summary");
    if (sum) {
      const [a, b] = S.words;
      sum.innerHTML =
        `<strong>Measured from these two files:</strong> voicing starts ` +
        `<strong>${Math.round(gap)} ms</strong> later after the release in ` +
        `<em>${a.word}</em> than in <em>${b.word}</em>. That interval is the ` +
        `aspiration, and it is the whole difference between ` +
        `<span class="ipa">[${a.allophone}]</span> and ` +
        `<span class="ipa">[${b.allophone}]</span> — the two allophones of ` +
        `<span class="ipa">/${PHONEME}/</span> shown above. Swap one for the ` +
        `other and the word is still the same word, which is what makes this a ` +
        `difference between allophones rather than between phonemes.`;
    }
  }

  function drawSpectrogram(cv, w, cfg, maxMs) {
    const ctx = cv.getContext("2d");
    const L = 46, R = 12, T = 10, B = 30;
    const pw = cv.width - L - R, ph = cv.height - T - B;
    ctx.clearRect(0, 0, cv.width, cv.height);

    const mat = w.spectrogram;             // [band][frame], band 0 = lowest
    const bands = mat.length, frames = mat[0].length;
    // x maps onto the SHARED scale, so cards are comparable to each other
    const msToX = (ms) => L + (ms / maxMs) * pw;
    const cellW = Math.max(1, (cfg.hopMs / maxMs) * pw + 0.6);
    const cellH = ph / bands;

    for (let b = 0; b < bands; b++) {
      const y = T + ph - (b + 1) * cellH;   // low frequencies at the bottom
      for (let f = 0; f < frames; f++) {
        const v = mat[b][f];
        if (v < 8) continue;                // skip near-silence: keeps it crisp
        ctx.fillStyle = ramp(v);
        ctx.fillRect(msToX(f * cfg.hopMs), y, cellW, cellH + 0.6);
      }
    }

    // aspiration band: release -> voicing
    const x1 = msToX(w.burstMs), x2 = msToX(w.voiceMs);
    ctx.fillStyle = "rgba(193,85,58,.16)";
    ctx.fillRect(x1, T, x2 - x1, ph);
    for (const [x, col, label] of [[x1, "#c1553a", "release"],
                                   [x2, "#1a7f6b", "voicing"]]) {
      ctx.strokeStyle = col;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x, T);
      ctx.lineTo(x, T + ph);
      ctx.stroke();
      ctx.fillStyle = col;
      ctx.font = "600 11px system-ui, sans-serif";
      ctx.textAlign = x > L + pw * 0.75 ? "right" : "left";
      ctx.fillText(label, x + (ctx.textAlign === "right" ? -4 : 4), T + 12);
    }
    // VOT span annotation
    ctx.strokeStyle = "#8f4224";
    ctx.lineWidth = 1;
    const yv = T + ph - 14;
    ctx.beginPath(); ctx.moveTo(x1, yv); ctx.lineTo(x2, yv); ctx.stroke();
    ctx.fillStyle = "#8f4224";
    ctx.font = "600 11px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(`${Math.round(w.votMs)} ms`, (x1 + x2) / 2, yv - 4);

    // axes
    ctx.strokeStyle = "#ddd6c8";
    ctx.lineWidth = 1;
    ctx.strokeRect(L, T, pw, ph);
    ctx.fillStyle = "#8a8275";
    ctx.font = "10px system-ui, sans-serif";
    ctx.textAlign = "right";
    for (let k = 0; k <= cfg.fmax; k += 2000) {
      const y = T + ph - (k / cfg.fmax) * ph;
      ctx.fillText(`${k / 1000}k`, L - 6, y + 3);
    }
    ctx.textAlign = "center";
    const step = maxMs > 700 ? 200 : 100;
    for (let ms = 0; ms <= maxMs; ms += step) {
      ctx.fillText(`${ms}`, msToX(ms), T + ph + 14);
    }
    ctx.fillText("milliseconds", L + pw / 2, T + ph + 26);
  }

  /* Playback with a moving playhead, so what you HEAR lines up with where you
   * are LOOKING. Position comes from audio.currentTime rather than a timer, so
   * it stays correct if decoding stalls or the tab is throttled.
   *
   * The playhead is drawn by blitting the pre-rendered spectrogram and stroking
   * one line on top; the spectrogram itself is never recomputed per frame. */
  let current = null;

  function drawPlayhead(cv, base, geom, ms) {
    const ctx = cv.getContext("2d");
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.drawImage(base, 0, 0);
    if (ms == null) return;
    const { L, R, T, B } = geom;
    const pw = cv.width - L - R, ph = cv.height - T - B;
    const x = playheadX(ms, geom, cv.width);
    // a soft trailing wash makes the direction of travel obvious
    const g = ctx.createLinearGradient(Math.max(L, x - 40), 0, x, 0);
    g.addColorStop(0, "rgba(255,255,255,0)");
    g.addColorStop(1, "rgba(255,255,255,.34)");
    ctx.fillStyle = g;
    ctx.fillRect(Math.max(L, x - 40), T, Math.min(40, x - L), ph);
    ctx.strokeStyle = "#2b2620";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x, T - 4);
    ctx.lineTo(x, T + ph + 4);
    ctx.stroke();
    // a small cap so the line reads as a cursor rather than a gridline
    ctx.fillStyle = "#2b2620";
    ctx.beginPath();
    ctx.moveTo(x - 4, T - 4);
    ctx.lineTo(x + 4, T - 4);
    ctx.lineTo(x, T + 3);
    ctx.closePath();
    ctx.fill();
  }

  function stopPlayback() {
    if (!current) return;
    const { a, btn, cv, base, geom, raf } = current;
    if (raf) cancelAnimationFrame(raf);
    a.pause();
    btn.classList.remove("playing");
    drawPlayhead(cv, base, geom, null);        // clear the cursor
    current = null;
  }

  function play(word, cv, base, geom, btn) {
    const wasThis = current && current.btn === btn;
    stopPlayback();
    if (wasThis) return;                       // second click = stop

    const a = new Audio("audio/" + word.file.replace(/^audio\//, ""));
    current = { a, btn, cv, base, geom, raf: null };
    btn.classList.add("playing");

    const tick = () => {
      if (!current || current.a !== a) return;
      drawPlayhead(cv, base, geom, a.currentTime * 1000);
      current.raf = requestAnimationFrame(tick);
    };
    a.addEventListener("ended", () => {
      // hold the cursor at the end briefly, then clear it
      drawPlayhead(cv, base, geom, word.durationMs);
      setTimeout(() => { if (current && current.a === a) stopPlayback(); }, 260);
    });
    a.addEventListener("error", stopPlayback);
    a.play().then(tick).catch(stopPlayback);
  }

  // ================= 2. live microphone =================
  // Reference vowel positions come from DATA.vowels, the same x/y used to lay out
  // the Sound Chart trapezoid, so "your dot" and the chart share one coordinate
  // system. Only the corner-ish monophthongs are labelled: plotting all 28 makes
  // the panel unreadable and implies more precision than formant estimation has.
  const SHOW_VOWELS = ["i", "e", "\u025B", "a", "\u0251", "\u0254", "o", "u",
                       "\u026A", "\u028A", "\u0259", "\u028C", "\u00E6"];

  // F1/F2 ranges for the axes. Wide enough for most adult voices; a reader whose
  // vowel falls outside is clamped to the edge rather than silently dropped.
  const F1_MIN = 200, F1_MAX = 1000;     // vertical: openness
  const F2_MIN = 600, F2_MAX = 2800;     // horizontal: frontness

  const mic = {
    ctx: null, stream: null, analyser: null, raf: null,
    gain: null, noise: null, frames: 0,
    hist: [],           // recent [f1, f2] for smoothing
    spec: [],           // scrolling live spectrogram columns
  };

  // Clickable reference vowels. Hit targets are recorded BY THE DRAW CODE so the
  // two can never disagree; VOWEL_R is the drawn radius and the hit radius.
  const VOWEL_R = 14;
  const vowelHits = [];
  let hoverVowel = null;
  let playingVowel = null;
  // The chart is redrawn on hover and on vowel playback, and those redraws must
  // not erase the reader's own live dot, so the most recent formant reading is
  // kept here rather than living only in frameLoop's local scope.
  let lastLive = null;
  function redrawVowelChart() { drawVowelChart(lastLive); }

  function vowelRefs() {
    if (typeof DATA === "undefined" || !DATA.vowels) return [];
    return DATA.vowels.filter((v) => SHOW_VOWELS.includes(v.symbol));
  }

  function drawVowelChart(live) {
    const cv = $("vowelCanvas");
    if (!cv) return;
    const ctx = cv.getContext("2d");
    const L = 54, R = 22, T = 26, B = 40;
    const pw = cv.width - L - R, ph = cv.height - T - B;
    ctx.clearRect(0, 0, cv.width, cv.height);

    // F2 decreases left->right (front vowels have HIGH F2 and sit at the front
    // of the mouth, i.e. chart-left), F1 increases downward.
    const x = (f2) => L + (1 - (clamp(f2, F2_MIN, F2_MAX) - F2_MIN) /
                                (F2_MAX - F2_MIN)) * pw;
    const y = (f1) => T + ((clamp(f1, F1_MIN, F1_MAX) - F1_MIN) /
                           (F1_MAX - F1_MIN)) * ph;

    ctx.strokeStyle = "#e4ded2";
    ctx.lineWidth = 1;
    ctx.strokeRect(L, T, pw, ph);
    ctx.fillStyle = "#8a8275";
    ctx.font = "10px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("\u2190 tongue further forward (F2, Hz) ", L + pw / 2, T - 10);
    ctx.fillText("front", L + 24, T + ph + 26);
    ctx.fillText("back", L + pw - 24, T + ph + 26);
    ctx.save();
    ctx.translate(14, T + ph / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText("mouth more open (F1, Hz) \u2192", 0, 0);
    ctx.restore();
    ctx.textAlign = "right";
    for (let f = 200; f <= F1_MAX; f += 200) {
      ctx.fillText(String(f), L - 6, y(f) + 3);
    }
    ctx.textAlign = "center";
    for (let f = 800; f <= F2_MAX; f += 400) {
      ctx.fillText(String(f), x(f), T + ph + 14);
    }

    // Reference vowels: chart x/y are percentages of the trapezoid, which map
    // linearly onto the F2/F1 ranges closely enough for orientation. Positions
    // are cached so the click hit-test uses exactly the drawn geometry rather
    // than a second, possibly drifting, copy of the same maths.
    vowelHits.length = 0;
    for (const v of vowelRefs()) {
      const vx = L + (v.x / 100) * pw;
      const vy = T + (v.y / 100) * ph;
      vowelHits.push({ symbol: v.symbol, x: vx, y: vy, r: VOWEL_R });
      const hot = hoverVowel === v.symbol;
      const lit = playingVowel === v.symbol;
      ctx.fillStyle = lit ? "#c1553a" : hot ? "#eaf0f7" : "#fff";
      ctx.strokeStyle = lit ? "#8f4224" : hot ? "#23558c" : "#bfb7a8";
      ctx.lineWidth = hot || lit ? 2.5 : 1.5;
      ctx.beginPath();
      ctx.arc(vx, vy, VOWEL_R, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = lit ? "#fff" : "#6b6459";
      ctx.font = "600 15px " + ipaStack();
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(v.symbol, vx, vy + 1);
      // a small speaker hint on hover, so it reads as playable
      if (hot && !lit) {
        ctx.fillStyle = "#23558c";
        ctx.font = "600 9px system-ui, sans-serif";
        ctx.fillText("\u25B6", vx, vy + VOWEL_R + 7);
      }
    }
    ctx.textBaseline = "alphabetic";

    if (live) {
      // trail of recent positions, so a held vowel reads as a cluster
      mic.hist.forEach((p, i) => {
        const a = (i + 1) / mic.hist.length;
        ctx.fillStyle = `rgba(193,85,58,${0.10 + 0.25 * a})`;
        ctx.beginPath();
        ctx.arc(x(p[1]), y(p[0]), 5 + 3 * a, 0, 2 * Math.PI);
        ctx.fill();
      });
      ctx.fillStyle = "#c1553a";
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.arc(x(live[1]), y(live[0]), 9, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
    }
  }

  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

  /* IPA font stack for canvas text.
   *
   * A canvas font is NOT a CSS declaration: `ctx.font = "15px var(--ipa-font)"`
   * is an invalid font shorthand, so the assignment is silently DISCARDED and the
   * label falls back to the canvas default (10px sans-serif). Nothing throws and
   * nothing logs — the same class of quiet failure as the tofu-box diacritic.
   * The stack therefore has to be spelled out here. It is read from the
   * stylesheet at runtime where possible so the canvas and the DOM cannot drift
   * apart, with the literal below as the fallback. */
  const IPA_STACK_FALLBACK =
    '"Doulos SIL", "Charis SIL", "Gentium Plus", "Arial Unicode MS", ' +
    '"Times New Roman", serif';

  const ipaStack = (function () {
    let cached = null;
    return function () {
      if (cached) return cached;
      cached = IPA_STACK_FALLBACK;
      try {
        const v = getComputedStyle(document.documentElement)
          .getPropertyValue("--ipa-font").trim();
        if (v) cached = v;
      } catch (e) { /* no DOM (test harness): keep the literal */ }
      return cached;
    };
  })();

  /* Estimate F1 and F2 from a magnitude spectrum.
   *
   * Deliberately simple: smooth the spectrum, then take the two strongest peaks
   * inside the plausible F1 and F2 bands. This is NOT LPC formant tracking, and
   * on a high-pitched voice a harmonic can be mistaken for a formant. That
   * limitation is stated on the page rather than hidden behind a tidy number. */
  function estimateFormants(mag, sr, fftSize) {
    const binHz = sr / fftSize;
    // smooth over ~150 Hz to suppress individual harmonics
    const w = Math.max(2, Math.round(75 / binHz));
    const sm = new Float32Array(mag.length);
    for (let i = 0; i < mag.length; i++) {
      let s = 0, n = 0;
      for (let k = -w; k <= w; k++) {
        const j = i + k;
        if (j >= 0 && j < mag.length) { s += mag[j]; n++; }
      }
      sm[i] = s / n;
    }
    const peakIn = (loHz, hiHz) => {
      const lo = Math.max(1, Math.floor(loHz / binHz));
      const hi = Math.min(sm.length - 2, Math.ceil(hiHz / binHz));
      let best = -1, bv = -Infinity;
      for (let i = lo; i <= hi; i++) {
        if (sm[i] > sm[i - 1] && sm[i] >= sm[i + 1] && sm[i] > bv) {
          bv = sm[i]; best = i;
        }
      }
      if (best < 0) return null;
      // parabolic interpolation for sub-bin precision
      const d = 0.5 * (sm[best - 1] - sm[best + 1]) /
                (sm[best - 1] - 2 * sm[best] + sm[best + 1] || 1);
      return (best + (isFinite(d) ? d : 0)) * binHz;
    };
    const f1 = peakIn(250, 950);
    if (!f1) return null;
    // F2 must sit above F1, but for back rounded vowels it can be as low as
    // ~700 Hz — close behind F1. An earlier version searched from
    // max(900, F1+250), which is ABOVE the real F2 of [u] (~800 Hz), so "oo"
    // silently returned nothing. Search from just above F1 instead.
    const f2 = peakIn(f1 + 150, 2700);
    return f2 ? [f1, f2] : null;
  }

  function drawLiveSpec() {
    const cv = $("liveSpec");
    if (!cv) return;
    const ctx = cv.getContext("2d");
    const cols = mic.spec.length;
    ctx.clearRect(0, 0, cv.width, cv.height);
    if (!cols) return;
    const cw = cv.width / 160;             // fixed window of history
    mic.spec.forEach((col, i) => {
      const x = cv.width - (cols - i) * cw;
      const ch = cv.height / col.length;
      for (let b = 0; b < col.length; b++) {
        const v = col[b];
        if (v < 8) continue;
        ctx.fillStyle = ramp(v);
        ctx.fillRect(x, cv.height - (b + 1) * ch, cw + 0.6, ch + 0.6);
      }
    });
  }

  function frameLoop() {
    const an = mic.analyser;
    if (!an) return;
    const bins = new Float32Array(an.frequencyBinCount);
    an.getFloatFrequencyData(bins);           // dB, -Infinity..0

    // to linear magnitude for peak-picking
    const mag = new Float32Array(bins.length);
    let loud = -Infinity;
    for (let i = 0; i < bins.length; i++) {
      mag[i] = Math.pow(10, bins[i] / 20);
      if (bins[i] > loud) loud = bins[i];
    }

    const sr = mic.ctx.sampleRate;

    // Adaptive voicing gate. A FIXED threshold (-55 dB) was the second reason
    // the mic appeared dead: it is meaningless without knowing the device's own
    // noise floor, which varies by tens of dB between a laptop mic and a headset.
    // Instead, learn the floor from the first ~30 frames (roughly half a second,
    // while the user is still reading) and require a clear margin above it.
    mic.frames++;
    if (mic.frames <= 30) {
      mic.noise = mic.noise === null ? loud : Math.max(mic.noise, loud);
    }
    const floor = mic.noise === null ? -60 : mic.noise;
    const voiced = loud > floor + 8 && loud > -75;
    let f = null;
    if (voiced) {
      f = estimateFormants(mag, sr, an.fftSize);
      if (f) {
        mic.hist.push(f);
        if (mic.hist.length > 14) mic.hist.shift();
      }
    } else {
      mic.hist.length = 0;
    }
    // Remember the latest reading. The chart is also redrawn on hover and on
    // vowel playback, which call drawVowelChart(lastLive) — without this the
    // reader's own dot would blink out the moment they moused over a reference
    // vowel, i.e. exactly when they are trying to compare the two.
    lastLive = f;

    // live spectrogram column, same 0-8kHz range as the reference cards
    const nb = 96, fmax = 8000;
    const maxBin = Math.min(bins.length - 1,
      Math.floor(fmax / (sr / an.fftSize)));
    const col = new Uint8Array(nb);
    for (let b = 0; b < nb; b++) {
      const lo = Math.floor((b / nb) * maxBin);
      const hi = Math.max(lo + 1, Math.floor(((b + 1) / nb) * maxBin));
      let m = -Infinity;
      for (let i = lo; i < hi; i++) m = Math.max(m, bins[i]);
      col[b] = Math.round(clamp((m + 90) / 90, 0, 1) * 255);
    }
    mic.spec.push(col);
    if (mic.spec.length > 160) mic.spec.shift();

    drawVowelChart(f);
    drawLiveSpec();

    // Input level meter. Without this there was no way to tell "the microphone
    // is not working" apart from "the vowel detector is not firing" — the whole
    // reason the dead mic was hard to diagnose.
    const meter = $("micMeter");
    if (meter) {
      const pct = Math.round(clamp((loud + 90) / 80, 0, 1) * 100);
      meter.style.width = pct + "%";
      meter.className = "meter-fill" + (voiced ? " live" : "");
    }

    const ro = $("vowelReadout");
    if (ro) {
      if (f) {
        const near = nearestVowel(f);
        ro.innerHTML =
          `F1 <b>${Math.round(f[0])} Hz</b> \u00B7 F2 <b>${Math.round(f[1])} Hz</b>` +
          (near ? ` \u00B7 closest reference vowel on the chart: ` +
                  `<span class="ipa">${near}</span>` : "");
      } else if (voiced) {
        ro.innerHTML = `<span class="dim">Sound detected, but no clear vowel ` +
          `resonance \u2014 hold a steady "ee" or "ah" for about a second.</span>`;
      } else if (mic.frames <= 30) {
        ro.innerHTML = `<span class="dim">Measuring background noise\u2026 ` +
          `stay quiet for a moment.</span>`;
      } else {
        ro.innerHTML = `<span class="dim">Listening \u2014 speak or hold a ` +
          `vowel. If the level bar stays flat, check which input your browser ` +
          `is using.</span>`;
      }
    }
    mic.raf = requestAnimationFrame(frameLoop);
  }

  /* Nearest reference vowel BY CHART POSITION, described as "closest" and never
   * as a match or a score. Comparing chart geometry rather than raw Hz keeps it
   * honest about being an orientation aid: the reference positions are idealised
   * IPA chart coordinates, not one speaker's measured formants. */
  function nearestVowel(f) {
    const refs = vowelRefs();
    if (!refs.length) return null;
    const px = (1 - (clamp(f[1], F2_MIN, F2_MAX) - F2_MIN) / (F2_MAX - F2_MIN)) * 100;
    const py = ((clamp(f[0], F1_MIN, F1_MAX) - F1_MIN) / (F1_MAX - F1_MIN)) * 100;
    let best = null, bd = Infinity;
    for (const v of refs) {
      const d = (v.x - px) ** 2 + (v.y - py) ** 2;
      if (d < bd) { bd = d; best = v.symbol; }
    }
    return bd < 900 ? best : null;          // too far from any vowel: say nothing
  }

  async function startMic() {
    const status = $("micStatus"), btn = $("micBtn");
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      status.textContent = "This browser does not expose microphone access.";
      status.classList.add("err");
      btn.disabled = true;
      return;
    }
    try {
      status.classList.remove("err");
      status.textContent = "Requesting permission\u2026";
      // Leave the browser's own processing ON. An earlier version disabled
      // autoGainControl to get a "cleaner" signal, which in practice made a
      // normal speaking voice too quiet to register at all on built-in mics.
      // Gain control costs nothing here: F1/F2 are frequency positions, and
      // scaling amplitude does not move them.
      mic.stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: false, noiseSuppression: false },
      });
      const AC = window.AudioContext || window.webkitAudioContext;
      mic.ctx = new AC();
      // An AudioContext often starts "suspended" until a user gesture. Without
      // this the analyser returns silence forever and the page looks broken with
      // no error — which is exactly what happened.
      if (mic.ctx.state === "suspended") await mic.ctx.resume();

      const src = mic.ctx.createMediaStreamSource(mic.stream);
      mic.analyser = mic.ctx.createAnalyser();
      mic.analyser.fftSize = 2048;
      mic.analyser.smoothingTimeConstant = 0.3;
      mic.analyser.minDecibels = -100;      // default -100, stated for clarity
      mic.analyser.maxDecibels = -10;
      // A gain stage so quiet microphones still reach the voicing threshold.
      mic.gain = mic.ctx.createGain();
      mic.gain.gain.value = 4;
      src.connect(mic.gain).connect(mic.analyser);
      // NOT connected to ctx.destination: routing the mic to the speakers would
      // cause feedback. The analyser is a sink, so this is intentional.
      mic.noise = null;                     // measured on the first frames
      mic.frames = 0;
      btn.textContent = "Stop microphone";
      btn.setAttribute("aria-pressed", "true");
      status.textContent = "Listening. Audio stays in your browser.";
      frameLoop();
    } catch (err) {
      status.classList.add("err");
      status.textContent = err && err.name === "NotAllowedError"
        ? "Permission denied \u2014 nothing was recorded."
        : "Could not start the microphone: " + (err && err.name || "unknown error");
    }
  }

  function stopMic() {
    if (mic.raf) cancelAnimationFrame(mic.raf);
    mic.raf = null;
    if (mic.stream) mic.stream.getTracks().forEach((t) => t.stop());
    if (mic.ctx) mic.ctx.close();
    mic.ctx = mic.stream = mic.analyser = mic.gain = null;
    mic.noise = null;
    mic.frames = 0;
    mic.hist.length = 0;
    mic.spec.length = 0;
    lastLive = null;
    const meter = $("micMeter");
    if (meter) { meter.style.width = "0%"; meter.className = "meter-fill"; }
    const btn = $("micBtn");
    btn.textContent = "Start microphone";
    btn.setAttribute("aria-pressed", "false");
    $("micStatus").textContent = "Microphone off.";
    $("micStatus").classList.remove("err");
    drawVowelChart(null);
    drawLiveSpec();
    const ro = $("vowelReadout");
    if (ro) ro.innerHTML = `<span class="dim">No signal yet.</span>`;
  }

  // ---------- notes, generated so they cannot drift from the data ----------
  function renderNotes() {
    const el = $("spec-notes");
    if (!el || typeof SPECTRO === "undefined") return;
    const s = SPECTRO.settings;
    const w = SPECTRO.words;
    el.innerHTML =
      `<strong>Method.</strong> The two reference spectrograms are computed ` +
      `offline by <code>analyze_spectrograms.py</code> and shipped as data, not ` +
      `analysed in your browser: Safari could not decode Ogg Vorbis audio before ` +
      `version 18.4, and an in-browser version would show some readers an empty ` +
      `canvas with no explanation. Settings are a ${s.winMs} ms window, ` +
      `${s.hopMs} ms hop, ${s.bands} linear frequency bands from 0 to ` +
      `${s.fmax / 1000} kHz, floored at ${s.dbFloor} dB below each recording's ` +
      `loudest point. Frequency is spaced linearly rather than on a mel scale ` +
      `precisely because the aspiration this page is about lives in the high ` +
      `bands that a mel scale compresses. ` +
      `Release and voicing onset are measured by locating the vowel, stepping ` +
      `back to the stop closure, and taking the release as the first frame whose ` +
      `energy above 3 kHz rises clear of that closure; three earlier detectors ` +
      `that failed are documented in the script. Measured here: ` +
      w.map((x) => `<em>${x.word}</em> ${Math.round(x.votMs)} ms`).join(", ") +
      `. Recordings are the same speaker as the Allophones page ` +
      `(<a href="https://commons.wikimedia.org/wiki/User:Dvortygirl">Dvortygirl</a>, ` +
      `General American, CC BY-SA 3.0). ` +
      `<strong>Microphone.</strong> Live analysis runs entirely in your browser ` +
      `through the Web Audio API. Nothing is uploaded, and no audio is retained ` +
      `after you stop. Formants are estimated by smoothing the spectrum and ` +
      `taking the strongest peak in the F1 and F2 regions, which is simpler than ` +
      `the LPC analysis phonetics software uses \u2014 on a high-pitched voice an ` +
      `individual harmonic can be misread as a formant, so treat the position as ` +
      `an approximation. Reference vowel positions are idealised IPA chart ` +
      `coordinates, not a single speaker's measurements.`;
  }

  // ---------- clickable reference vowels ----------
  // Reuses DATA.audio, the same isolated-IPA recordings the Sound Chart plays, so
  // a reader hears the identical sound in both places.
  let vowelAudio = null;

  function playVowel(symbol) {
    const entry = typeof DATA !== "undefined" && DATA.audio
      ? DATA.audio[symbol] : null;
    if (!entry) return false;
    if (vowelAudio) vowelAudio.pause();
    vowelAudio = new Audio(entry.file);
    playingVowel = symbol;
    redrawVowelChart();
    const clear = () => {
      if (playingVowel === symbol) {
        playingVowel = null;
        redrawVowelChart();
      }
    };
    vowelAudio.addEventListener("ended", clear);
    vowelAudio.addEventListener("error", clear);
    vowelAudio.play().catch(clear);
    return true;
  }

  function canvasPoint(cv, ev) {
    const r = cv.getBoundingClientRect();
    return [(ev.clientX - r.left) * (cv.width / r.width),
            (ev.clientY - r.top) * (cv.height / r.height)];
  }

  function hitVowel(cv, ev) {
    const [mx, my] = canvasPoint(cv, ev);
    for (const h of vowelHits) {
      if ((mx - h.x) ** 2 + (my - h.y) ** 2 <= (h.r + 3) ** 2) return h.symbol;
    }
    return null;
  }

  function initVowelInteraction() {
    const cv = $("vowelCanvas");
    if (!cv) return;
    cv.addEventListener("mousemove", (ev) => {
      const hit = hitVowel(cv, ev);
      cv.style.cursor = hit ? "pointer" : "default";
      if (hit !== hoverVowel) { hoverVowel = hit; redrawVowelChart(); }
    });
    cv.addEventListener("mouseleave", () => {
      if (hoverVowel) { hoverVowel = null; redrawVowelChart(); }
      cv.style.cursor = "default";
    });
    cv.addEventListener("click", (ev) => {
      const hit = hitVowel(cv, ev);
      if (hit) playVowel(hit);
    });
    // Keyboard access: a canvas click target is otherwise unreachable without a
    // mouse. Left/right step through the vowels, Enter/Space plays the current.
    let kbIndex = -1;
    cv.addEventListener("keydown", (ev) => {
      if (!vowelHits.length) return;
      if (ev.key === "ArrowRight" || ev.key === "ArrowLeft") {
        const d = ev.key === "ArrowRight" ? 1 : -1;
        kbIndex = (kbIndex + d + vowelHits.length) % vowelHits.length;
        hoverVowel = vowelHits[kbIndex].symbol;
        redrawVowelChart();
        ev.preventDefault();
      } else if (ev.key === "Enter" || ev.key === " ") {
        if (hoverVowel) { playVowel(hoverVowel); ev.preventDefault(); }
      }
    });
    cv.addEventListener("blur", () => {
      if (hoverVowel) { hoverVowel = null; redrawVowelChart(); }
    });
  }

  // ---------- init ----------
  renderCards();
  renderNotes();
  drawVowelChart(null);
  initVowelInteraction();
  const btn = $("micBtn");
  if (btn) {
    btn.addEventListener("click", () => {
      if (mic.stream) stopMic(); else startMic();
    });
  }
  window.addEventListener("pagehide", () => { if (mic.stream) stopMic(); });

  // Playhead x position for a given time, in canvas pixels. Extracted so the
  // smoke test can check the mapping without a canvas: a cursor that drifts out
  // of sync with the audio would make the whole feature misleading.
  function playheadX(ms, geom, canvasWidth) {
    const { L, R, maxMs } = geom;
    return L + clamp(ms / maxMs, 0, 1) * (canvasWidth - L - R);
  }

  // exposed for the smoke test
  window.__SPEC_TEST__ = {
    estimateFormants, nearestVowel, ramp, vowelRefs, playheadX, cards,
    ipaStack,
    // The clickable-vowel surface. `hits` is the LIVE array the renderer fills,
    // not a copy, so a test cannot pass against a stale snapshot of the geometry.
    chart: {
      hits: vowelHits,
      radius: VOWEL_R,
      draw: drawVowelChart,
      redraw: redrawVowelChart,
      setHover(sym) { hoverVowel = sym; },
      // Deliberately NO setter for the live reading. An earlier test hook had
      // one, and it let a broken frameLoop pass: the test set the value itself,
      // and the source-scan guard matched the setter's own `lastLive = f`. The
      // only way to populate it is now to actually run a frame.
      getLive() { return lastLive; },
    },
    // The real analysis loop plus its state, so a test can feed a synthetic
    // spectrum through the actual code path rather than assert on source text.
    micState: mic,
    frameLoop,
  };
})();
