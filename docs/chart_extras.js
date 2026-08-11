// Sound Chart page: grouped comparison of the two selected inventories, plus the
// rare-sounds material (moved here from the map page, since rarity is a fact
// about sounds rather than geography).
(function () {
  const $ = id => document.getElementById(id);
  if (!$("vennWrap")) return;              // not on this page

  const byName = {};
  for (const l of DATA.languages) byName[l.name] = l;
  // globalFreq describes broad reference categories on the chart;
  // comparisonFreq remains available for source labels that have no chart cell.
  const chartFreq = (typeof RARITY !== "undefined") ? RARITY.globalFreq : {};
  const comparisonFreq = (typeof RARITY !== "undefined" && RARITY.comparisonFreq)
    ? RARITY.comparisonFreq : chartFreq;
  const pct = x => Math.round(100 * x);

  function rarityTier(sym, freqMap) {
    const f = freqMap[sym];
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

  function rarityPhrase(sym, freqMap) {
    const f = freqMap[sym];
    if (f == null) return "";
    return `in ${f < 0.01 ? "<1" : pct(f)}% of the world's languages`;
  }

  function chip(sym, cls, langs, freqMap = comparisonFreq, freqKind = "comparison") {
    const tier = rarityTier(sym, freqMap);
    const hasAudio = !!DATA.audio[sym];
    const bits = [sym, rarityPhrase(sym, freqMap)].filter(Boolean);
    if ((langs || []).length > 1) bits.push(`listed by both ${langs.join(" and ")}`);
    else if ((langs || []).length === 1) bits.push(`listed by ${langs[0]}`);
    for (const lg of langs || []) {
      const w = wordFor(sym, lg);
      if (w) bits.push(`${lg}: ${w.text}`);
    }
    const label = bits.join(" — ");
    return `<button class="vchip ${cls}${tier ? " t-" + tier : ""}${hasAudio ? "" : " no-audio"}" ` +
      `data-sym="${sym}" data-langs="${(langs || []).join("|")}" ` +
      `data-audio="${hasAudio ? 1 : 0}" data-freq-kind="${freqKind}" ` +
      `aria-label="${label.replace(/"/g, "&quot;")}. ${hasAudio ? "Click to hear." : "No exact recording available."}">${sym}</button>`;
  }

  function groupChip(group, cls, langs, count, kind) {
    const sym = group.key;
    const freqMap = chartFreq[sym] == null ? comparisonFreq : chartFreq;
    const freqKind = freqMap === chartFreq ? "chart" : "comparison";
    const tier = rarityTier(sym, freqMap);
    const hasAudio = !!DATA.audio[sym];
    const existsOnBothSides = group.source1.length && group.source2.length;
    let suffix = "";
    if (kind !== "shared" && existsOnBothSides) {
      suffix = `<span class="mult">+${count} contrast${count === 1 ? "" : "s"}</span>`;
    } else if (count > 1) {
      suffix = `<span class="mult">×${count}</span>`;
    }
    const description = kind === "shared"
      ? `${count} source ${count === 1 ? "entry matches" : "entries match"} one-for-one under broad /${sym}/`
      : existsOnBothSides
        ? `${count} additional ${count === 1 ? "contrast" : "contrasts"} in ${kind === "only1" ? langs[0] : langs[1]} under broad /${sym}/`
        : `broad /${sym}/ recorded only for ${kind === "only1" ? langs[0] : langs[1]}`;
    return `<button class="vchip ${cls}${tier ? " t-" + tier : ""}${hasAudio ? "" : " no-audio"}" ` +
      `data-sym="${sym}" data-langs="${langs.join("|")}" data-group-chip="1" ` +
      `data-count-kind="${kind}" data-count="${count}" ` +
      `data-audio="${hasAudio ? 1 : 0}" data-freq-kind="${freqKind}" ` +
      `aria-label="${description}. ${hasAudio ? "Click to hear the broad reference sound." : "No reference recording available."}">` +
      `${sym}${suffix}</button>`;
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
    if (btn.dataset.groupChip === "1") {
      const freqMap = btn.dataset.freqKind === "chart" ? chartFreq : comparisonFreq;
      const rare = rarityPhrase(sym, freqMap);
      let html = `<strong class="ipa">/${sym}/</strong> ` +
        `<span style="opacity:.8">broad comparison category</span><br>` +
        (rare ? `<span style="opacity:.8">${rare}</span><br>` : "");
      for (const languageName of langs) {
        const language = byName[languageName];
        const entries = language && window.SOUND_COMPARISON.groupsFor(language)[sym];
        if (!entries || !entries.length) continue;
        html += `<em>${languageName}</em> source ${entries.length === 1 ? "entry" : "entries"}: ` +
          `<span class="ipa">${entries.join(" ")}</span><br>`;
        const note = window.SOUND_COMPARISON.noteFor(languageName, sym);
        if (note) html += `${note}<br>`;
        const word = wordFor(sym, languageName);
        if (word) html += `${languageName} example: ${word.text}` +
          (word.mined ? ` <span style="opacity:.55">(via Wiktionary)</span>` : "") + `<br>`;
      }
      if (btn.dataset.countKind !== "shared") {
        const ownerIndex = btn.dataset.countKind === "only1" ? 0 : 1;
        const owner = langs[ownerIndex];
        const other = langs[1 - ownerIndex];
        const otherHasCategory = !!(byName[other] &&
          window.SOUND_COMPARISON.groupsFor(byName[other])[sym]);
        html += otherHasCategory
          ? `<span style="opacity:.75">${owner}'s source records ${btn.dataset.count} additional contrast${btn.dataset.count === "1" ? "" : "s"} inside this broad category.</span><br>`
          : `<span style="opacity:.75">This broad category is not recorded for ${other}.</span><br>`;
      }
      html += btn.dataset.audio === "1"
        ? `<span style="opacity:.55">Click to hear the broad reference sound.</span>`
        : `<span style="opacity:.55">No reference recording is available.</span>`;
      tip.innerHTML = html;
      tip.classList.add("show");
      return;
    }
    const name = DATA.names[sym] ? `<span style="opacity:.8">${DATA.names[sym]}</span><br>` : "";
    const freqMap = btn.dataset.freqKind === "chart" ? chartFreq : comparisonFreq;
    const rare = rarityPhrase(sym, freqMap);
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
    html += btn.dataset.audio === "1"
      ? `<br><span style="opacity:.55">Click to hear this sound.</span>`
      : `<br><span style="opacity:.55">No exact recording is available for this sound label.</span>`;
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
    const groups1 = window.SOUND_COMPARISON.groupsFor(L1);

    if (solo) {
      const ranked = Object.entries(groups1).map(([key, entries]) => ({
        key, source1: entries, source2: [], shared: entries.length,
        only1: 0, only2: 0
      })).sort((a, b) =>
        ((chartFreq[a.key] ?? comparisonFreq[a.key]) ?? 1) -
        ((chartFreq[b.key] ?? comparisonFreq[b.key]) ?? 1));
      const units = ranked.reduce((sum, group) => sum + group.source1.length, 0);
      wrap.innerHTML =
        `<p class="sub" style="margin:0 0 .6rem">Pick a second language above to
         compare inventories. For now, here is <strong>${n1}</strong>'s
         ${units} recorded categories and contrasts, grouped into ${ranked.length}
         broad positions and ordered rarest first.</p>` +
        `<div class="vgroup solo">${ranked.map(group =>
          groupChip(group, "l1", [n1], group.source1.length, "shared")).join("")}</div>`;
      $("vennLegend").innerHTML = rarityLegend();
      bindChips();
      return;
    }

    const L2 = byName[n2];
    const result = window.SOUND_COMPARISON.pairSummary(L1, L2);
    const shared = result.groups.filter(group => group.shared);
    const only1 = result.groups.filter(group => group.only1);
    const only2 = result.groups.filter(group => group.only2);
    const frequency = key => (chartFreq[key] ?? comparisonFreq[key]) ?? 1;
    const byRare = (a, b) => frequency(a.key) - frequency(b.key);
    only1.sort(byRare); only2.sort(byRare); shared.sort(byRare);

    // Three labelled groups, no circles. The counts + grouped chips carry the
    // point on their own; proportional circles were decoration on top of that.
    const total = result.union;
    const share = n => Math.round(100 * n / total);
    wrap.innerHTML =
      `<div class="vcols">
         <div class="vcol">
           <h4 class="c1">Additional in ${n1} <span>${result.only1}</span></h4>
           <div class="vmeter"><i class="m1" style="width:${share(result.only1)}%"></i></div>
           <div class="vgroup">${only1.map(group =>
             groupChip(group, "l1", [n1, n2], group.only1, "only1")).join("") || '<span class="vnone">none</span>'}</div>
         </div>
         <div class="vcol">
           <h4 class="cb">Broadly shared <span>${result.shared}</span></h4>
           <div class="vmeter"><i class="mb" style="width:${share(result.shared)}%"></i></div>
           <div class="vgroup">${shared.map(group =>
             groupChip(group, "both", [n1, n2], group.shared, "shared")).join("") || '<span class="vnone">none</span>'}</div>
         </div>
         <div class="vcol">
           <h4 class="c2">Additional in ${n2} <span>${result.only2}</span></h4>
           <div class="vmeter"><i class="m2" style="width:${share(result.only2)}%"></i></div>
           <div class="vgroup">${only2.map(group =>
             groupChip(group, "l2", [n1, n2], group.only2, "only2")).join("") || '<span class="vnone">none</span>'}</div>
         </div>
       </div>
       <p class="sub">Bars show each group as a share of the ${total} distinct
       broad categories and contrastive distinctions the two sources have between
       them. Hover a category to see each source's original transcription.</p>`;
    $("vennLegend").innerHTML = rarityLegend();

    bindChips();
  }

  function rarityLegend() {
    return `<span class="rl">Outline shows how rare the broad category is worldwide:</span>` +
      `<span class="rkey"><i class="t-very-rare"></i>under 5%</span>` +
      `<span class="rkey"><i class="t-rare"></i>5–15%</span>` +
      `<span class="rkey"><i class="t-uncommon"></i>15–50%</span>` +
      `<span class="rkey"><i class="t-common"></i>over 50%</span>` +
      `<span class="rl">Playable entries have an exact recording.</span>`;
  }

  // reuse the chart's audio: clicking a chip plays that symbol
  function bindChips() {
    for (const b of document.querySelectorAll(".vchip")) {
      // Venn chips are recreated whenever a language changes, while the rarity
      // table and English cards persist. Mark bound buttons so repainting the
      // comparison never stacks duplicate click and tooltip listeners on them.
      if (b.dataset.soundChipBound === "1") continue;
      b.dataset.soundChipBound = "1";
      if (b.dataset.audio === "1") b.addEventListener("click", () => {
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
        // This table is global, not a statement about the selected pair. Keep
        // the fill neutral; the outline alone carries the rarity tier.
        `<tr><td class="sym">${chip(r.sym, "neutral", r.owners, chartFreq, "chart")}</td>` +
        `<td class="num">${r.share < 0.01 ? "<1" : pct(r.share)}%</td>` +
        `<td>${r.owners.join(", ")}</td></tr>`).join("") +
      `</tbody></table>` +
      `<p class="sub">Click a sound to hear it, or hover for an example word.
       Ranked rarest first, keeping one row per language so a single language's
       inventory doesn't fill the table.</p>`;
    // English cards
    const WORD = { "θ": "think", "ð": "this", "ɹ": "red", "æ": "cat", "ʌ": "cup",
      "ɜ": "bird", "ɒ": "hot", "ɑ": "father", "ŋ": "sing", "ʒ": "vision",
      "w": "wet", "ʃ": "ship" };
    const withWord = RARITY.englishRarest.filter(d => WORD[d.sym]);
    const LEAD = ["θ", "ð", "ɹ"];
    const pick = [...withWord.filter(d => LEAD.includes(d.sym)),
                  ...withWord.filter(d => !LEAD.includes(d.sym))].slice(0, 4);
    $("engCards").innerHTML = pick.map(d =>
      `<div class="card"><h4>${chip(d.sym, "neutral", ["English"], chartFreq, "chart")} ` +
      `<span style="font-weight:400;color:#6b6459">as in “${WORD[d.sym]}”</span></h4>` +
      `<div class="big">${d.worldShare < 0.01 ? "<1" : pct(d.worldShare)}%</div>` +
      `<p>of the world's languages have this sound</p></div>`).join("");

    const ranked = Object.entries(RARITY.signature)
      .sort((a, b) => b[1].meanRarity - a[1].meanRarity).map(([n]) => n);
    const r = ranked.indexOf("English") + 1;
    $("engRank").textContent = r === 1 ? "single" : r === 2 ? "second" : r + "th";

    // Give readers the endpoints of the ordinary overlap measure. The previous
    // table added a rarity-weighted score, but it changed little in the ordering
    // and made the simple closest/furthest question harder to answer.
    const pairs = Object.entries(DATA.pairOverlap).map(([k, v]) => {
      const [a, b] = k.split("|");
      return { a, b, shared: v[0], overlap: v[1] };
    });
    const tbl = list => list.map(x =>
      `<tr><td>${x.a} + ${x.b}</td><td class="num">${x.shared}</td>` +
      `<td class="num"><strong>${pct(x.overlap)}%</strong></td></tr>`).join("");
    const byOverlap = pairs.slice().sort((x, y) =>
      y.overlap - x.overlap || y.shared - x.shared ||
      `${x.a}|${x.b}`.localeCompare(`${y.a}|${y.b}`));
    $("overlaptable").innerHTML =
      `<table class="data"><thead><tr><th>Pair</th>` +
       `<th class="num">Broad matches</th><th class="num">Overlap</th></tr></thead><tbody>` +
      `<tr><th colspan="3" style="padding-top:.6rem">Highest overlap ` +
      `<span style="font-weight:400;color:#8a8275">— top 5 of ${pairs.length} pairs</span></th></tr>` +
      tbl(byOverlap.slice(0, 5)) +
      `<tr><th colspan="3" style="padding-top:.6rem">Lowest overlap ` +
      `<span style="font-weight:400;color:#8a8275">— bottom 5</span></th></tr>` +
      tbl(byOverlap.slice(-5).reverse()) +
      `</tbody></table>`;
    bindChips();
  }

  renderRarity();
  window.renderVenn = renderVenn;          // chart page calls this on selection change
  // this file loads after the page's inline script, so trigger the first paint
  // ourselves now that renderVenn exists
  if (typeof window.__repaintAll === "function") window.__repaintAll();
})();
