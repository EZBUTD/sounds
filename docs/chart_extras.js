// Sound Chart page: proportional Venn of the two selected languages, plus the
// rare-sounds material (moved here from the map page, since rarity is a fact
// about sounds rather than geography).
//
// The Venn is area-proportional on the horizontal axis only: circle radii scale
// with each inventory's size and the overlap distance is solved so the lens area
// matches the true shared count. A true 2-set area-proportional Venn is exactly
// solvable, so no approximation is needed -- but the SYMBOLS inside are laid out
// on a simple grid, not packed geometrically, because legibility of the IPA
// characters matters more than perfect containment.
(function () {
  const $ = id => document.getElementById(id);
  if (!$("vennWrap")) return;              // not on this page

  const byName = {};
  for (const l of DATA.languages) byName[l.name] = l;
  const freq = (typeof RARITY !== "undefined") ? RARITY.globalFreq : {};
  const pct = x => Math.round(100 * x);

  function rarityTier(sym) {
    const f = freq[sym];
    if (f == null) return null;
    if (f < 0.05) return "very-rare";
    if (f < 0.15) return "rare";
    if (f < 0.5) return "uncommon";
    return "common";
  }

  // Example word per (language, symbol). Curated entries carry a gloss; mined
  // ones are bare Wiktionary words and are labelled as such.
  function wordFor(sym, lang) {
    const e = DATA.examplesByLang && DATA.examplesByLang[`${lang}|${sym}`];
    return e ? { text: e.text, mined: e.mined } : null;
  }

  function rarityPhrase(sym) {
    const f = freq[sym];
    if (f == null) return "";
    return `in ${f < 0.01 ? "<1" : pct(f)}% of the world's languages`;
  }

  function chip(sym, cls, langs) {
    const tier = rarityTier(sym);
    const bits = [sym, rarityPhrase(sym)].filter(Boolean);
    for (const lg of langs || []) {
      const w = wordFor(sym, lg);
      if (w) bits.push(`${lg}: ${w.text}`);
    }
    const label = bits.join(" — ");
    return `<button class="vchip ${cls}${tier ? " t-" + tier : ""}" ` +
      `data-sym="${sym}" data-langs="${(langs || []).join("|")}" ` +
      `aria-label="${label.replace(/"/g, "&quot;")}. Click to hear.">${sym}</button>`;
  }

  // ---------- rich tooltip (mirrors the main chart's behaviour) ----------
  let tip = document.getElementById("vennTip");
  if (!tip) {
    tip = document.createElement("div");
    tip.id = "vennTip";
    tip.className = "tooltip";
    document.body.appendChild(tip);
  }
  function showTip(btn) {
    const sym = btn.dataset.sym;
    const langs = (btn.dataset.langs || "").split("|").filter(Boolean);
    const name = DATA.names[sym] ? `<span style="opacity:.8">${DATA.names[sym]}</span><br>` : "";
    const rare = rarityPhrase(sym);
    let html = `<strong class="ipa">${sym}</strong> ${name}` +
      (rare ? `<span style="opacity:.8">${rare}</span><br>` : "");
    const rows = [];
    for (const lg of langs) {
      const w = wordFor(sym, lg);
      if (w) rows.push(`<em>${lg}</em>: ${w.text}` +
        (w.mined ? ` <span style="opacity:.55">(via Wiktionary)</span>` : ""));
    }
    html += rows.length ? rows.join("<br>")
      : `<span style="opacity:.6">no example word recorded</span>`;
    html += `<br><span style="opacity:.55">Click to hear the sound.</span>`;
    tip.innerHTML = html;
    tip.classList.add("show");
  }
  function moveTip(e) {
    tip.style.left = Math.min(e.clientX + 14, window.innerWidth - 320) + "px";
    tip.style.top = (e.clientY + 16) + "px";
  }
  function hideTip() { tip.classList.remove("show"); }

  // ---------- render ----------
  function renderVenn(n1, n2) {
    const wrap = $("vennWrap");
    const L1 = byName[n1];
    if (!L1) return;
    const solo = !n2 || !byName[n2];
    const set1 = new Set(L1.phonemes);

    if (solo) {
      // single language: show its inventory ranked by global rarity
      const ranked = [...set1].sort((a, b) => (freq[a] ?? 1) - (freq[b] ?? 1));
      wrap.innerHTML =
        `<p class="sub" style="margin:0 0 .6rem">Pick a second language above to
         compare inventories. For now, here is <strong>${n1}</strong>'s
         ${set1.size} chart sounds, rarest in the world first.</p>` +
        `<div class="vgroup solo">${ranked.map(s => chip(s, "both", [n1])).join("")}</div>`;
      $("vennLegend").innerHTML = rarityLegend();
      bindChips();
      return;
    }

    const L2 = byName[n2], set2 = new Set(L2.phonemes);
    const shared = [...set1].filter(s => set2.has(s));
    const only1 = [...set1].filter(s => !set2.has(s));
    const only2 = [...set2].filter(s => !set1.has(s));
    const byRare = (a, b) => (freq[a] ?? 1) - (freq[b] ?? 1);
    only1.sort(byRare); only2.sort(byRare); shared.sort(byRare);

    // Three labelled groups, no circles. The counts + grouped chips carry the
    // point on their own; proportional circles were decoration on top of that.
    const total = set1.size + set2.size - shared.length;
    const share = n => Math.round(100 * n / total);
    wrap.innerHTML =
      `<div class="vcols">
         <div class="vcol">
           <h4 class="c1">Only ${n1} <span>${only1.length}</span></h4>
           <div class="vmeter"><i class="m1" style="width:${share(only1.length)}%"></i></div>
           <div class="vgroup">${only1.map(s => chip(s, "l1", [n1])).join("") || '<span class="vnone">none</span>'}</div>
         </div>
         <div class="vcol">
           <h4 class="cb">Shared <span>${shared.length}</span></h4>
           <div class="vmeter"><i class="mb" style="width:${share(shared.length)}%"></i></div>
           <div class="vgroup">${shared.map(s => chip(s, "both", [n1, n2])).join("") || '<span class="vnone">none</span>'}</div>
         </div>
         <div class="vcol">
           <h4 class="c2">Only ${n2} <span>${only2.length}</span></h4>
           <div class="vmeter"><i class="m2" style="width:${share(only2.length)}%"></i></div>
           <div class="vgroup">${only2.map(s => chip(s, "l2", [n2])).join("") || '<span class="vnone">none</span>'}</div>
         </div>
       </div>
       <p class="sub">Bars show each group as a share of the ${total} distinct
       sounds the two languages use between them. Hover a sound for an example
       word; click to hear it.</p>`;
    $("vennLegend").innerHTML = rarityLegend();

    // headline: the most unusual sound each language brings to the pair
    const star = arr => arr.find(s => (freq[s] ?? 1) < 0.15);
    const s1 = star(only1), s2 = star(only2);
    const bits = [];
    if (s1) bits.push(`<strong>${n1}</strong> brings <span class="ipa">${s1}</span>` +
      ` (in ${pct(freq[s1])}% of the world's languages)`);
    if (s2) bits.push(`<strong>${n2}</strong> brings <span class="ipa">${s2}</span>` +
      ` (${pct(freq[s2])}%)`);
    $("vennHeadline").innerHTML = bits.length
      ? "Rarest sound each one brings: " + bits.join("; ") + "."
      : "Neither language contributes a globally unusual sound to this pair.";
    bindChips();
  }

  function rarityLegend() {
    return `<span class="rl">Outline shows how rare a sound is worldwide:</span>` +
      `<span class="rkey"><i class="t-very-rare"></i>under 5%</span>` +
      `<span class="rkey"><i class="t-rare"></i>5–15%</span>` +
      `<span class="rkey"><i class="t-uncommon"></i>15–50%</span>` +
      `<span class="rkey"><i class="t-common"></i>over 50%</span>` +
      `<span class="rl">Click any sound to hear it.</span>`;
  }

  // reuse the chart's audio: clicking a chip plays that symbol
  function bindChips() {
    for (const b of document.querySelectorAll(".vchip")) {
      b.addEventListener("click", () => {
        if (typeof window.playSymbol === "function") window.playSymbol(b.dataset.sym);
      });
      b.addEventListener("mouseenter", () => showTip(b));
      b.addEventListener("mousemove", moveTip);
      b.addEventListener("mouseleave", hideTip);
      b.addEventListener("focus", () => {
        showTip(b);
        const r = b.getBoundingClientRect();
        moveTip({ clientX: r.left, clientY: r.bottom });
      });
      b.addEventListener("blur", hideTip);
    }
  }

  // ---------- rare sounds tables (moved from the map page) ----------
  function renderRarity() {
    if (typeof RARITY === "undefined") return;
    $("worldN").textContent = RARITY.worldLanguageCount.toLocaleString();

    // ---- rarest sounds, one row per language, capped ----
    const RARE_ROW_CAP = 10;
    const single = s => s.length === 1 || /[ʘǀǃǂǁ]/.test(s) ||
      ["ts","dz","tʃ","dʒ","tɕ","dʑ","tʂ","dʐ","ɡb","kp"].includes(s);

    // Which of our languages treat this sound as a signature? PHOIBLE writes
    // Zulu's clicks as clusters (kǀ, kǃ, kǁ), and the chart plus the audio set
    // key on the BARE click, so a lookup on the exact string finds nothing for
    // ǀ and everything for kǀ — which is why the old table had rows reading
    // "signature sound of —" next to the world's rarest sounds. Match a bare
    // click against the cluster forms too. (Same normalisation gap as the Zulu
    // rarity bug fixed earlier in analyze_geography.py.)
    const CLICKS = "ʘǀǃǂǁ";
    const ownersOf = sym => Object.entries(RARITY.signature)
      .filter(([, d]) => d.signature.some(g =>
        g.sym === sym || (CLICKS.includes(sym) && g.sym.includes(sym))))
      .map(([n]) => n);

    // Rank by rarity, then keep a row only if it introduces a language we
    // haven't shown yet: without that, five of the top rows are Zulu clicks and
    // the table reads as a list of one language's inventory. Prefer a symbol we
    // can actually play, so every row's button works.
    const byRarity = Object.entries(RARITY.globalFreq)
      .filter(([s]) => single(s))
      .sort((a, b) => a[1] - b[1]);
    const shown = new Set();
    const rareRows = [];
    for (const [sym, share] of byRarity) {
      if (!DATA.audio[sym]) continue;         // keep every row playable
      const owners = ownersOf(sym);
      const fresh = owners.filter(l => !shown.has(l));
      if (!fresh.length) continue;            // no owners, or all already shown
      fresh.forEach(l => shown.add(l));
      rareRows.push({ sym, share, owners: fresh });
      if (rareRows.length >= RARE_ROW_CAP) break;
    }

    $("raretable").innerHTML =
      `<table class="data"><thead><tr><th>Sound</th>` +
      `<th class="num">Share of world languages</th>` +
      `<th>A signature sound of…</th></tr></thead><tbody>` +
      rareRows.map(r =>
        `<tr><td class="sym">${chip(r.sym, "both", r.owners)}</td>` +
        `<td class="num">${r.share < 0.01 ? "<1" : pct(r.share)}%</td>` +
        `<td>${r.owners.join(", ")}</td></tr>`).join("") +
      `</tbody></table>` +
      `<p class="sub">Click a sound to hear it, or hover for an example word.
       Ranked rarest first, keeping one row per language so a single language's
       inventory doesn't fill the table.</p>`;
    bindChips();

    // English cards
    const WORD = { "θ": "think", "ð": "this", "ɹ": "red", "æ": "cat", "ʌ": "cup",
      "ɜ": "bird", "ɒ": "hot", "ɑ": "father", "ŋ": "sing", "ʒ": "vision",
      "w": "wet", "ʃ": "ship" };
    const withWord = RARITY.englishRarest.filter(d => WORD[d.sym]);
    const LEAD = ["θ", "ð", "ɹ"];
    const pick = [...withWord.filter(d => LEAD.includes(d.sym)),
                  ...withWord.filter(d => !LEAD.includes(d.sym))].slice(0, 4);
    $("engCards").innerHTML = pick.map(d =>
      `<div class="card"><h4><span class="ipa">${d.sym}</span> ` +
      `<span style="font-weight:400;color:#6b6459">as in “${WORD[d.sym]}”</span></h4>` +
      `<div class="big">${d.worldShare < 0.01 ? "<1" : pct(d.worldShare)}%</div>` +
      `<p>of the world's languages have this sound</p></div>`).join("");

    const ranked = Object.entries(RARITY.signature)
      .sort((a, b) => b[1].meanRarity - a[1].meanRarity).map(([n]) => n);
    const r = ranked.indexOf("English") + 1;
    $("engRank").textContent = r === 1 ? "single" : r === 2 ? "second" : r + "th";

    // rarity-weighted overlap
    const wp = Object.entries(RARITY.weightedPairs).map(([k, v]) => {
      const [a, b] = k.split("|");
      return { a, b, ...v, drop: v.plain - v.weighted };
    });
    const tbl = list => list.map(x =>
      `<tr><td>${x.a} + ${x.b}</td><td class="num">${pct(x.plain)}%</td>` +
      `<td class="num">${pct(x.weighted)}%</td>` +
      `<td class="num">−${pct(x.drop)}</td></tr>`).join("");
    // Ranked by the RARITY-WEIGHTED score itself, not by the drop. Sorting by
    // drop answered "who lost the most points", which is a different question
    // from "who is genuinely most alike" and made the ordering read as arbitrary
    // (a pair can have a small drop simply by starting low). The weighted column
    // is the one the section is about, so it is the one the rows are sorted on
    // and both blocks are sorted the same direction: high to low.
    const byWeighted = wp.slice().sort((x, y) => y.weighted - x.weighted);
    $("weightedtable").innerHTML =
      `<table class="data"><thead><tr><th>Pair</th><th class="num">Plain overlap</th>` +
      `<th class="num">Rarity-weighted</th><th class="num">Drop</th></tr></thead><tbody>` +
      `<tr><th colspan="4" style="padding-top:.6rem">Most alike once rare sounds count for more ` +
      `<span style="font-weight:400;color:#8a8275">— top 5 of ${wp.length} pairs</span></th></tr>` +
      tbl(byWeighted.slice(0, 5)) +
      `<tr><th colspan="4" style="padding-top:.6rem">Least alike ` +
      `<span style="font-weight:400;color:#8a8275">— bottom 5; their overlap was almost all universal sounds</span></th></tr>` +
      tbl(byWeighted.slice(-5)) +
      `</tbody></table>`;
  }

  renderRarity();
  window.renderVenn = renderVenn;          // chart page calls this on selection change
  // this file loads after the page's inline script, so trigger the first paint
  // ourselves now that renderVenn exists
  if (typeof window.__repaintAll === "function") window.__repaintAll();
})();
