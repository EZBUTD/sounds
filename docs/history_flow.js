// The English sound-flow diagram: one horizontal trunk (English) with branches
// arriving from donor languages and leaving toward the relatives that kept them.
//
// SVG, not CSS boxes. The previous version positioned lanes with percentage
// offsets inside a CSS grid, and three separate layout bugs followed from that
// (labels masking line ends, the axis drifting out of alignment with the track,
// per-row tags overlapping their own lanes). In SVG every element shares one
// coordinate system, so "the label is at the year it describes" is arithmetic
// rather than a CSS coincidence.
//
// Layout contract for future rendered-page checks:
//   * x is a single monotonic function of year, exported as window.__flowX
//   * the trunk is one horizontal line at y = TRUNK_Y
//   * an inflow leaves its donor row ABOVE and meets the trunk at its year
//   * an outflow leaves the trunk at its year and continues BELOW to the present
//   * no two labels overlap
(function () {
  const HOST = "flowChart";
  if (typeof HIST === "undefined" || typeof DATA === "undefined") return;
  const host = document.getElementById(HOST);
  if (!host) return;

  const NS = "http://www.w3.org/2000/svg";
  const el = (tag, attrs, text) => {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    return n;
  };

  // ------------------------------------------------------------- row packing
  // Branch labels are wide (250 viewBox units), and several sounds arrive within
  // a few decades of each other — v and z both land at 1200.
  //
  // Rows are ASSIGNED, not enumerated: walk the flows in time order and drop each
  // into the lowest row whose last label ends before this one starts, so flows
  // far enough apart horizontally SHARE a row. First-fit interval packing.
  //
  // What this buys is compactness, not correctness: one row per flow also avoids
  // overlaps (ROW exceeds a label's height) but makes the diagram about 300px
  // taller — 1025 vs 725 — for the same eight branches. On a page whose brief was
  // "less text, more visual", that vertical padding is the cost. Overlap is
  // prevented by ROW and TRUNK_GAP; a render test asserts both the absence of
  // overlaps AND that the diagram stays compact, so a regression to naive
  // stacking is caught as the bloat it is rather than passing silently.
  function packRows(flows, labelW) {
    const rowEnd = [];                       // right edge occupied per row
    const out = new Map();
    for (const f of [...flows].sort((a, b) => a.year - b.year)) {
      const x0 = f._x0, x1 = x0 + labelW;
      let r = 0;
      while (r < rowEnd.length && rowEnd[r] > x0 - 8) r++;
      rowEnd[r] = x1;
      out.set(f.sym, r);
    }
    return { row: out, count: Math.max(1, rowEnd.length) };
  }

  // ---------------------------------------------------------------- geometry
  const PAD = { l: 22, r: 22, t: 26, b: 22 };
  const W = 1180;
  const ROW = 104;           // vertical space per branch row (a label is ~95 tall)
  const ERA_H = 20;
  const AXIS_H = 20;
  const LABEL_W = 250;       // viewBox units; must match .flow-label width

  const Y0 = HIST.scale.from, Y1 = HIST.scale.to;
  const PLOT_L = PAD.l + 92;                 // room for the "English" trunk label
  const PLOT_R = W - PAD.r - 8;
  // ONE year -> x mapping. Everything on the diagram derives from this, and the
  // render test evaluates this exact function rather than restating the formula
  // (the dendrogram shipped inverted because its test hard-copied the math).
  const x = year => {
    const t = (Math.max(Y0, Math.min(Y1, year)) - Y0) / (Y1 - Y0);
    return PLOT_L + t * (PLOT_R - PLOT_L);
  };
  window.__flowX = x;

  // Where each branch's label starts, in viewBox units. An inflow label sits to
  // the LEFT of its junction (the sound is travelling rightward into the trunk);
  // an outflow label sits to the RIGHT (it is travelling away). Clamped so no
  // label runs off either edge.
  const ins = HIST.flows.filter(f => f.dir === "in");
  const outs = HIST.flows.filter(f => f.dir === "out");
  // Every branch descends in a vertical corridor 30 units from its junction (see
  // CORR where the paths are built). A label must not straddle any corridor but
  // its own, so its span is clipped to the gap between the neighbouring ones.
  // This replaces three rounds of hand-tuned x-offsets: the constraint is the
  // corridors, so deriving the label box from them is the fix that holds.
  // CORR_W is where the vertical corridor sits relative to the junction; CORR_BOX
  // is how wide the drawn curve's bounding box actually is, because the path also
  // contains the two quarter-bends at top and bottom. Reserving only CORR_W left a
  // 6px overlap that looked like a rounding error but was the bends. Measure the
  // drawn shape, not the idealised line.
  const CORR_W = 30;
  const CORR_BOX = 50;
  const inX = ins.map(f => x(f.year)).sort((a, b) => a - b);
  const outX = outs.map(f => x(f.year)).sort((a, b) => a - b);

  // A corridor passes through EVERY row between its own and the trunk, so a label
  // must clear the corridor of any branch further out than itself — not merely the
  // adjacent one. Checking only neighbours left dʒ's corridor (3 rows up) crossing
  // ʒ's label, and x-out's crossing y-out's. Row order is what decides this, so
  // the rows are packed first and the label boxes derived from them.
  const corridorsCrossing = (f, group, pack) => {
    const myRow = pack.row.get(f.sym);
    return group
      .filter(o => o !== f && pack.row.get(o.sym) > myRow)   // further from trunk
      .map(o => x(o.year));
  };

  // Provisional anchors, only so packRows has something to pack against. The real
  // label boxes are derived AFTER packing, because they depend on row order — a
  // corridor crosses every row between its branch and the trunk. Two passes, with
  // the dependency stated, rather than one pass that quietly uses a stale x.
  for (const f of ins)
    f._x0 = Math.max(PAD.l, Math.min(x(f.year) - LABEL_W - 12, W - PAD.l - LABEL_W));
  for (const f of outs)
    f._x0 = Math.max(PAD.l, Math.min(x(f.year) + 38, W - PAD.l - LABEL_W));

  const inPack = packRows(ins, LABEL_W);
  const outPack = packRows(outs, LABEL_W);

  for (const f of ins) {
    const xj = x(f.year);
    // The label hangs LEFT of the junction, so its right edge is fixed just clear
    // of its own corridor, and the left edge is LABEL_W back from that.
    //
    // Two constraints then narrow it, and BOTH must hold — trying to satisfy them
    // one at a time is what produced three broken layouts in a row (labels pinned
    // to the page pad, then ʒ landing on top of v):
    //   1. it must not cross a corridor belonging to a branch further from the
    //      trunk, because that corridor passes through this row
    //   2. it must not extend left past the corridor of the previous branch IN
    //      THIS ROW, or two labels sharing a row collide
    // Narrowing is always preferred to moving: a label stays beside its own
    // junction and gives up width instead.
    const myRow = inPack.row.get(f.sym);
    let right = xj - CORR_W - 6;
    let left = right - LABEL_W;

    for (const c of corridorsCrossing(f, ins, inPack)) {
      const boxL = c - CORR_W, boxR = boxL + CORR_BOX;
      if (boxL < right && boxR > left) {
        // the corridor cuts into this label's span: take whichever side survives
        if (boxR - left < right - boxL) left = boxR + 10;   // clip from the left
        else right = boxL - 8;                              // clip from the right
      }
    }
    // same-row predecessor: never reach back over its corridor
    for (const o of ins) {
      if (o === f || inPack.row.get(o.sym) !== myRow) continue;
      const oxj = x(o.year);
      if (oxj < xj) left = Math.max(left, oxj - CORR_W + CORR_BOX + 10);
    }
    f._x0 = Math.max(PAD.l, left);
    f._w = Math.max(120, Math.min(LABEL_W, right - f._x0));
  }
  for (const f of outs) {
    const xj = x(f.year);
    // Mirror image of the inflow case: the label hangs to the RIGHT, so its LEFT
    // edge is fixed just clear of its own corridor and only the right edge gives.
    let left = xj + CORR_W + 8;
    for (const c of corridorsCrossing(f, outs, outPack)) {
      const cx = c + CORR_W;              // an outflow corridor sits right of its junction
      // a corridor that crosses this row to the left of the label pushes it right
      if (cx > left - CORR_BOX && cx < left + LABEL_W)
        left = Math.max(left, c + CORR_BOX + 10);
    }
    let right = Math.min(PLOT_R, left + LABEL_W);
    for (const c of corridorsCrossing(f, outs, outPack)) {
      const cx = c + CORR_W;
      if (cx > left && cx < right) right = cx - 8;
    }
    f._x0 = Math.min(left, W - PAD.l - 140);
    f._w = Math.max(140, Math.min(LABEL_W, right - f._x0));
  }
  // Clearance above and below the trunk. Each side's row 0 label hangs back
  // toward the trunk, so this gap has to exceed the label height or an inflow
  // label collides with an outflow label across the line — which is exactly what
  // happened with ŋ (1600, above) and y (1300, below) at the first attempt.
  const TRUNK_GAP = 74;
  // Reserved strip just below the trunk for the year stamps. Nothing else may be
  // drawn in it, which is what keeps the stamps from colliding with branch text.
  const STAMP_DY = 17;
  const STAMP_STRIP = 24;
  // Clearance between the era band strip and the topmost branch label. Labels are
  // anchored by their BOTTOM edge and grow upward, so the top row needs a whole
  // label's height of headroom, and labels are NOT uniform — the tallest here
  // (tʃ, whose word list wraps to three lines) is ~113px against ~78px for the
  // shortest. Sizing this to the short ones let the tall one climb into the band
  // and sit on top of "Middle English", so it is set from the tallest, with a
  // margin. A render test asserts no text overlaps anywhere in the diagram.
  const ERA_CLEAR = 125;
  const TRUNK_Y = PAD.t + ERA_H + ERA_CLEAR + (inPack.count - 1) * ROW + TRUNK_GAP;
  // Outflow labels hang BELOW their run (see the .flow-label.out CSS note), so the
  // space under the last outflow row has to fit a whole label, not just the line.
  const OUT_CLEAR = 120;
  const H = TRUNK_Y + STAMP_STRIP + TRUNK_GAP +
            (outPack.count - 1) * ROW + OUT_CLEAR + AXIS_H + PAD.b;

  const svg = el("svg", {
    viewBox: `0 0 ${W} ${H}`, width: "100%", role: "img",
    "aria-label": "Diagram: sounds flowing into and out of English over time",
  });

  // ---------------------------------------------------------------- backdrop
  // era bands, so the reader can place a branch in Old / Middle / Modern English
  for (const era of HIST.scale.eras) {
    const x0 = x(era.from), x1 = x(era.to);
    svg.appendChild(el("rect", {
      x: x0, y: PAD.t, width: x1 - x0, height: ERA_H,
      fill: "#efe9df", rx: 3,
    }));
    const lab = el("text", {
      x: (x0 + x1) / 2, y: PAD.t + ERA_H - 6, "text-anchor": "middle",
      class: "flow-era",
    }, era.label);
    svg.appendChild(lab);
  }
  // faint century guides
  for (const t of HIST.scale.ticks)
    svg.appendChild(el("line", {
      x1: x(t), y1: PAD.t + ERA_H, x2: x(t), y2: H - PAD.b - AXIS_H,
      class: "flow-guide",
    }));

  // ---------------------------------------------------------------- the trunk
  svg.appendChild(el("line", {
    x1: PLOT_L - 78, y1: TRUNK_Y, x2: PLOT_R, y2: TRUNK_Y, class: "flow-trunk",
  }));
  svg.appendChild(el("text", {
    x: PLOT_L - 82, y: TRUNK_Y - 9, "text-anchor": "start", class: "flow-trunklab",
  }, "ENGLISH"));
  // arrowhead at the present end
  svg.appendChild(el("path", {
    d: `M${PLOT_R} ${TRUNK_Y} l-9 -5 l0 10 z`, class: "flow-arrowhead",
  }));

  // ---------------------------------------------------------------- branches
  // A branch is one path: donor row -> curve -> trunk (inflow), or trunk ->
  // curve -> survivor row (outflow). The curve is a cubic with horizontal
  // control points so it meets both lines tangentially.
  const chipOf = window.__flowChip;      // provided by the page (audio + tooltip)
  const groups = { in: [], out: [] };
  const yearStamps = [];

  for (const f of HIST.flows) {
    const isIn = f.dir === "in";
    const xj = x(f.year);                              // junction on the trunk
    const pack = isIn ? inPack : outPack;
    const row = pack.row.get(f.sym);
    // inflow rows count upward from the trunk (row 0 nearest it); outflow rows
    // count downward, so in both cases row 0 is closest to the line
    const yRow = isIn
      ? TRUNK_Y - TRUNK_GAP + 14 - row * ROW
      : TRUNK_Y + STAMP_STRIP + TRUNK_GAP - 14 + row * ROW;

    // Identity is (sym, dir), not sym: /x/ appears TWICE on this diagram —
    // leaving around 1500 and returning marginally around 1800 — so keying
    // elements on the symbol alone made the label lookup ambiguous and
    // attached the wrong label to the wrong branch.
    const bid = `${f.sym}-${f.dir}`;
    const g = el("g", { class: `flow-branch ${f.dir}`, "data-sym": f.sym,
                        "data-bid": bid });

    // The horizontal run sits under its own label, and the curve joins that run
    // to the trunk. An inflow runs left-to-right into the junction; an outflow
    // runs away from it toward the present.
    const runFrom = isIn ? f._x0 + 8 : xj;
    const runTo = isIn ? xj : Math.min(f._x0 + LABEL_W, PLOT_R);
    // Each branch's descent to the trunk runs in its OWN vertical corridor,
    // immediately right of its junction. Previously the curve swept from the row
    // all the way down to the trunk in one bend, so a branch two rows up crossed
    // every row between it and the line — z-in's curve covered y 560..717 while
    // v-in's label sat at 565..660 inside that band, printing "from Norman
    // French" across it. Nudging label x-offsets could not fix that; the curve had
    // to stop straddling other rows. Now: bend to vertical just past the junction,
    // drop straight down that corridor, then bend into the trunk.
    const CORR = 30;                       // corridor offset from the junction
    if (isIn) {
      const xc = xj - CORR;                // corridor sits LEFT of the junction
      // Meet the top edge of the junction dot instead of drawing the incoming
      // line and arrowhead through the centre of the English timeline.
      const joinY = TRUNK_Y - 5;
      const arrowBaseY = joinY - 8;
      g.appendChild(el("line", {
        x1: runFrom, y1: yRow, x2: Math.min(runTo, xc), y2: yRow,
        class: "flow-run in",
      }));
      g.appendChild(el("path", {
        d: `M${Math.min(runTo, xc)} ${yRow} ` +
           `Q${xc} ${yRow} ${xc} ${yRow + 18} ` +
           `L${xc} ${arrowBaseY - 18} ` +
           `Q${xc} ${arrowBaseY - 8} ${xj - 10} ${arrowBaseY - 8} ` +
           `Q${xj} ${arrowBaseY - 8} ${xj} ${arrowBaseY}`,
        class: "flow-curve in",
      }));
      // Point down into the timeline. The curve's short vertical ending meets
      // the centre of the arrowhead's flat top edge.
      g.appendChild(el("path", {
        d: `M${xj} ${joinY} l-4.5 -8 l9 0 z`, class: "flow-tip in",
      }));
    } else {
      // same corridor treatment, mirrored: leave the trunk, drop straight down
      // just right of the junction, then run out along the row
      const xc = xj + CORR;
      g.appendChild(el("path", {
        d: `M${xj} ${TRUNK_Y} Q${xc} ${TRUNK_Y} ${xc} ${TRUNK_Y + 18} ` +
           `L${xc} ${yRow - 18} ` +
           `Q${xc} ${yRow} ${Math.min(xc + 18, runTo)} ${yRow}`,
        class: "flow-curve out",
      }));
      g.appendChild(el("line", {
        x1: Math.min(xc + 18, runTo), y1: yRow, x2: runTo, y2: yRow,
        class: "flow-run out",
      }));
      g.appendChild(el("path", {
        d: `M${runTo} ${yRow} l-8 -4.5 l0 9 z`, class: "flow-tip out",
      }));
    }

    // junction dot on the trunk, at the year
    g.appendChild(el("circle", {
      cx: xj, cy: TRUNK_Y, r: 5, class: `flow-node ${f.dir}`,
    }));
    // The year stamp is drawn later, once per DISTINCT year: v and z both arrive
    // in 1200, so drawing it per branch stacked "1200" on itself at identical
    // coordinates — legible by luck, and doubled text at any other zoom.
    yearStamps.push({ year: f.year, x: xj, dir: f.dir });

    // a ✕ when the sound survives nowhere we can check
    if (!isIn && f.gone)
      g.appendChild(el("text", {
        x: runTo + 6, y: yRow + 5, class: "flow-gone", "aria-hidden": "true",
      }, "✕"));

    groups[f.dir].push({ f, yRow, xj, runFrom, runTo, g, row });
    svg.appendChild(g);
  }

  // -------------------------------------------------------- year stamps
  // One stamp per distinct year, drawn in a reserved strip immediately BELOW the
  // trunk. Two earlier arrangements failed:
  //   * one stamp per branch -> "1200" drawn twice at the same coordinates,
  //     because v and z both arrive then
  //   * stamp placed on the side opposite its branch -> an inflow's stamp landed
  //     under the trunk, in the same strip as the outflow labels, and collided
  //     with their "kept by" line
  // Keeping every stamp on one side, inside a strip nothing else occupies, means
  // collisions are impossible by construction rather than by luck.
  {
    const seen = new Map();
    for (const s of yearStamps)
      if (!seen.has(s.year)) seen.set(s.year, s.x);
    // nudge apart any two stamps closer than a label width
    // Walk RIGHT TO LEFT. Left-to-right, the minimum-spacing pass kept undoing the
    // outflow offset: 1300 was correctly moved to 694, then pushed back to 697 by
    // the spacing rule against 1250, landing on y-out's corridor at 697. Going
    // right to left, spacing gives way leftward — into empty space — instead of
    // shoving a stamp back onto the line it was moved off.
    const sorted = [...seen.entries()].sort((a, b) => b[1] - a[1]);
    let lastL = Infinity;
    const MIN_W = 30;
    // An OUTFLOW's corridor descends just right of its junction, through this same
    // strip, so a stamp centred on the junction lands on that line. Shift those
    // stamps left of their junction instead; inflow corridors run above the trunk
    // and never enter the strip, so those stamps stay centred.
    const outAt = new Set(yearStamps.filter(s => s.dir === "out")
      .map(s => Math.round(s.x)));
    for (const [year, xc] of sorted) {
      // Offset first, THEN apply the minimum spacing — doing it the other way
      // round let the shifted 1300 stamp slide back into 1250.
      // Clear the whole corridor BOX, not a guessed nudge: the drawn curve is
      // ~CORR_BOX wide (bends included), and it starts at the junction, so a stamp
      // has to sit a full half-stamp left of that. 22px left still clipped it.
      const want = outAt.has(Math.round(xc)) ? xc - 32 : xc;
      const x0 = Math.min(want, lastL - MIN_W);
      lastL = x0;
      svg.appendChild(el("text", {
        x: x0, y: TRUNK_Y + STAMP_DY, "text-anchor": "middle", class: "flow-year",
      }, year));
    }
  }

  // ---------------------------------------------------------------- axis
  const axisY = H - PAD.b - 4;
  svg.appendChild(el("line", {
    x1: PLOT_L, y1: axisY - AXIS_H + 4, x2: PLOT_R, y2: axisY - AXIS_H + 4,
    class: "flow-axis",
  }));
  for (const t of HIST.scale.ticks) {
    svg.appendChild(el("line", {
      x1: x(t), y1: axisY - AXIS_H + 4, x2: x(t), y2: axisY - AXIS_H + 9,
      class: "flow-axis",
    }));
    svg.appendChild(el("text", {
      x: x(t), y: axisY, "text-anchor": "middle", class: "flow-tick",
    }, t));
  }

  host.appendChild(svg);

  // ---------------------------------------------------------------- HTML labels
  // The sound chips and word lists are HTML, not SVG text: they must be real
  // buttons (audio + the shared tooltip) and must wrap. They are absolutely
  // positioned over the SVG using the SAME x() and row geometry, and the render
  // test checks each label actually sits at its own year.
  const overlay = document.createElement("div");
  overlay.className = "flow-overlay";
  host.appendChild(overlay);

  function pctX(px) { return (100 * px / W).toFixed(3) + "%"; }
  function pctY(py) { return (100 * py / H).toFixed(3) + "%"; }

  for (const dir of ["in", "out"]) {
    for (const b of groups[dir]) {
      const f = b.f;
      const box = document.createElement("div");
      box.className = `flow-label ${dir}`;
      box.dataset.sym = f.sym;
      box.dataset.bid = `${f.sym}-${f.dir}`;
      // Anchored at the same x used for the run below it, and sized in viewBox
      // units so the label scales with the SVG rather than drifting off its own
      // branch when the diagram is scaled.
      box.style.left = pctX(f._x0);
      // width is per-label now: it is clipped to the gap between neighbouring
      // corridors, so a crowded branch gets a narrower label rather than one that
      // reaches across someone else's line
      box.style.width = pctX(f._w || LABEL_W);
      box.style.top = pctY(b.yRow);
      // words: hand-entered cognates, each tagged with its language
      const words = (f.dir === "out" ? f.survives : f.words) || [];
      const wordHtml = words.map(([lang, word, gloss]) => {
        const unver = (HIST.unverifiedLangs || []).includes(lang);
        return `<span class="fw${unver ? " unver" : ""}">` +
          `<b>${lang}</b> <i lang="${langTag(lang)}">${word}</i>` +
          (gloss ? ` <em>${gloss}</em>` : "") + `</span>`;
      }).join("");
      const srcLine = f.dir === "in"
        ? `<span class="flow-src">from ${f.source}</span>`
        : `<span class="flow-src">kept by</span>`;
      box.innerHTML =
        `<span class="flow-head">${chipOf ? chipOf(f.sym) : f.sym}` +
        `<span class="flow-gloss">${f.label}</span></span>` +
        srcLine + `<span class="flow-words">${wordHtml}</span>`;
      overlay.appendChild(box);
    }
  }

  function langTag(name) {
    return { German: "de", Dutch: "nl", French: "fr", English: "en",
             Scots: "sco" }[name] || "";
  }

  // expose geometry for the render test to check against what it measures
  window.__flowGeom = {
    W, H, TRUNK_Y, PLOT_L, PLOT_R,
    junctions: HIST.flows.map(f => ({ sym: f.sym, dir: f.dir, year: f.year,
                                      x: x(f.year) })),
  };

  if (typeof window.__flowBind === "function") window.__flowBind(host);
})();
