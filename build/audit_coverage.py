#!/usr/bin/env python3
"""
Systematic data-coverage audit across every layer the pages render.

Motivated by the Zulu-clicks bug: a symbol with NO frequency rendered identically
to a symbol that was merely common, so "we don't know" looked like "nothing
special". This script hunts for the same failure mode everywhere else — any place
a page can display an element whose backing value is missing, and any layer whose
coverage is so uneven that a cross-language comparison would measure
documentation rather than language.

Run after the build scripts. Exit code 1 if a BLOCKING gap is found.
"""
import csv
import json
from collections import defaultdict

from build_chart_data import LANG_INVENTORIES, norm

TONE_CHARS = set("˥˦˧˨˩")
CLICKS = set("ʘǀǃǂǁ")

problems = []      # (severity, layer, detail)


def load_js(path, var):
    s = open(path, encoding="utf-8").read()
    return json.loads(s.split("=", 1)[1].rstrip().rstrip(";"))


def main():
    DATA = load_js("prototype/data.js", "DATA")
    RARITY = load_js("prototype/rarity.js", "RARITY")
    DEEP = load_js("prototype/deep.js", "DEEP")
    MAP = load_js("prototype/mapdata.js", "MAPDATA")
    langs = {l["name"]: l for l in DATA["languages"]}
    names = list(langs)

    print("=" * 78)
    print("LAYER 1 — global sound rarity (the Zulu-clicks failure mode)")
    print("=" * 78)
    chart_syms = {s for l in DATA["languages"] for s in l["phonemes"]}
    missing = sorted(chart_syms - set(RARITY["globalFreq"]))
    print(f"chart symbols: {len(chart_syms)}   without a world frequency: {len(missing)}")
    if missing:
        problems.append(("BLOCKING", "rarity",
                         f"{len(missing)} chart symbols have no frequency: {missing}"))
    # also check the off-chart 'extras' chips, which the headline mentions
    extras = {e for l in DATA["languages"] for e in l.get("extras", [])}
    ex_missing = sorted(extras - set(RARITY["globalFreq"]))
    print(f"off-chart extras: {len(extras)}   without a frequency: {len(ex_missing)}")
    if ex_missing:
        problems.append(("INFO", "rarity",
                         f"{len(ex_missing)} extras lack frequency (diphthongs, by design): "
                         f"{ex_missing[:8]}"))

    print("\n" + "=" * 78)
    print("LAYER 2 — allophone records (per language)")
    print("=" * 78)
    rows_by_inv = defaultdict(list)
    for r in csv.DictReader(open("data/phoible.csv", encoding="utf-8")):
        rows_by_inv[r["InventoryID"]].append(r)
    # TWO different measures, and only the second one means anything:
    #   populated = the Allophones cell is non-empty
    #   real      = it lists at least one variant DIFFERENT from the phoneme
    # Nearly every inventory that records allophones at all fills the column for
    # every row, often just restating the phoneme, so `populated` reads ~100%
    # across the board and hides the true unevenness. An earlier version of this
    # audit reported only `populated` and wrongly concluded coverage was binary.
    cov, cov_pop = {}, {}
    for name, inv in LANG_INVENTORIES.items():
        rows = rows_by_inv[inv]
        n = len(rows) or 1
        cov_pop[name] = sum(1 for r in rows if r["Allophones"] not in ("", "NA")) / n
        cov[name] = sum(
            1 for r in rows
            if r["Allophones"] not in ("", "NA")
            and set(r["Allophones"].split()) - {r["Phoneme"]}) / n
    ranked = sorted(cov.items(), key=lambda kv: -kv[1])
    print(f"{'language':<20} {'cell populated':>15} {'REAL variation':>15}")
    for n, c in ranked:
        flag = "  <-- unusable" if c < 0.15 else ""
        print(f"{n:<20} {cov_pop[n]:>14.0%} {c:>15.0%}{flag}")
    zero = [n for n, c in cov.items() if c == 0]
    unusable = sorted((n for n, c in cov.items() if c < 0.15), key=lambda n: cov[n])

    # A 0% here is a fact about the ONE inventory we chart, not about the
    # language. Before reporting "no variation", check every other inventory
    # PHOIBLE has for that language — for English the charted RP inventory (2252)
    # records 0% while SPA inv 160 records 68%, and reporting the 0% unqualified
    # is what led four files to claim "English has no allophones". Only a language
    # with 0% across ALL its inventories genuinely lacks records.
    by_lang_all = defaultdict(list)
    for inv, rows in rows_by_inv.items():
        if not rows:
            continue
        n = len(rows)
        real = sum(1 for r in rows
                   if r["Allophones"] not in ("", "NA")
                   and set(r["Allophones"].split()) - {r["Phoneme"]}) / n
        by_lang_all[rows[0]["LanguageName"].split(" (")[0]].append((inv, real, n))
    elsewhere = {}
    for name in zero:
        alts = sorted((a for a in by_lang_all.get(name.split(" (")[0], [])
                       if a[0] != LANG_INVENTORIES[name] and a[1] > 0),
                      key=lambda a: -a[1])
        if alts:
            elsewhere[name] = alts[0]
    if elsewhere:
        print("\n0% in the charted inventory but documented elsewhere in PHOIBLE:")
        for name, (inv, real, n) in elsewhere.items():
            print(f"  {name}: charted inv {LANG_INVENTORIES[name]} 0%, "
                  f"but inv {inv} records variation on {real:.0%} of {n} rows "
                  f"-> say \"the inventory we chart records none\", NOT "
                  f"\"{name} has no allophones\"")
    truly_zero = [n for n in zero if n not in elsewhere]
    print(f"\nreal-variation spread: {ranked[0][0]} {ranked[0][1]:.0%} -> "
          f"{ranked[-1][0]} {ranked[-1][1]:.0%}")
    print(f"below the 15% usability floor ({len(unusable)}): " +
          ", ".join(f"{n} {cov[n]:.0%}" for n in unusable))
    problems.append(("WARN", "allophones",
                     f"real-variation coverage ranges {ranked[-1][1]:.0%}-{ranked[0][1]:.0%}; "
                     f"{len(unusable)} languages below 15% are gated out of divergence "
                     f"(kept for bridges, which can only undercount)"))
    if truly_zero:
        problems.append(("WARN", "allophones",
                         f"no allophone variation in ANY PHOIBLE inventory: {truly_zero}"))
    for name, (inv, real, _n) in elsewhere.items():
        problems.append(("INFO", "allophones",
                         f"{name}: charted inventory records 0% variation, but inv {inv} "
                         f"records {real:.0%} — page copy must blame the inventory, "
                         f"not the language"))

    # what the page actually renders: the English-Hindi card
    feat = DEEP["allophones"]["featured"]
    print(f"\nfeatured pairs rendered on the page: {len(feat)}")
    for f in feat:
        rows = f.get("examples", [])
        both = sum(1 for e in rows if e["aVariants"] and e["bVariants"])
        a_only = sum(1 for e in rows if e["aVariants"] and not e["bVariants"])
        b_only = sum(1 for e in rows if e["bVariants"] and not e["aVariants"])
        neither = sum(1 for e in rows if not e["aVariants"] and not e["bVariants"])
        print(f"  {f['a']} + {f['b']}: {len(rows)} example rows — "
              f"both sides documented {both}, only {f['a']} {a_only}, "
              f"only {f['b']} {b_only}, neither {neither}")
        if neither or (a_only + b_only) > both:
            problems.append(("BLOCKING", "allophone card",
                             f"{f['a']}+{f['b']}: {a_only + b_only + neither} of {len(rows)} "
                             f"rows are half-empty or empty — the table renders as blanks"))

    print("\n" + "=" * 78)
    print("LAYER 3 — example words per language")
    print("=" * 78)
    ebl = DATA["examplesByLang"]
    print(f"{'language':<20} {'sounds':>7} {'with a word':>12} {'coverage':>9}")
    weak = []
    for name in names:
        syms = langs[name]["phonemes"]
        have = sum(1 for s in syms if f"{name}|{s}" in ebl)
        c = have / len(syms) if syms else 0
        if c < 0.8:
            weak.append((name, c))
        print(f"{name:<20} {len(syms):>7} {have:>12} {c:>8.0%}")
    if weak:
        problems.append(("INFO", "example words",
                         "below 80% coverage: " +
                         ", ".join(f"{n} {c:.0%}" for n, c in weak)))

    print("\n" + "=" * 78)
    print("LAYER 4 — audio")
    print("=" * 78)
    audio = DATA["audio"]
    no_audio = sorted(chart_syms - set(audio))
    print(f"chart symbols: {len(chart_syms)}   with audio: {len(chart_syms) - len(no_audio)}")
    if no_audio:
        print(f"  without audio: {no_audio}")
        problems.append(("WARN", "audio",
                         f"{len(no_audio)} chart symbols have no recording: {no_audio}"))
    kinds = defaultdict(int)
    for a in audio.values():
        kinds[a.get("kind", "?")] += 1
    print(f"  by kind: {dict(kinds)}")

    print("\n" + "=" * 78)
    print("LAYER 5 — speaker + country data (map page)")
    print("=" * 78)
    L = MAP["languages"]
    no_l2 = [n for n in L if L[n].get("l2") is None]
    print(f"languages with L2 estimate: {len(L) - len(no_l2)}/{len(L)}")
    if no_l2:
        print(f"  without: {sorted(no_l2)}")
        problems.append(("INFO", "speakers",
                         f"{len(no_l2)} languages have no published L2 estimate "
                         f"(shown as unknown, not zero)"))
    CL = MAP["countryLayer"]
    thin = []
    for n, rows in CL.items():
        home = max(rows.items(), key=lambda kv: kv[1]["speakers"])[0]
        ab = len([c for c in rows if c != home])
        if ab < 5:
            thin.append((n, ab))
    print(f"languages with <5 documented abroad communities: {len(thin)}")
    for n, ab in sorted(thin, key=lambda t: t[1]):
        print(f"  {n}: {ab}")
    if thin:
        problems.append(("INFO", "country layer",
                         "still thin after augmentation: " +
                         ", ".join(f"{n}({ab})" for n, ab in sorted(thin, key=lambda t: t[1]))))

    # LAYER 6 was the merger model behind the "Lost in Translation" page. Both the
    # page and the model are gone; see build_deep_data.py for why. Guard against a
    # stale DEEP.mergers reappearing, since that would mean the payload and the
    # pages had drifted apart again.
    if "mergers" in DEEP:
        problems.append(("BLOCKING", "mergers",
                         "DEEP.mergers is back, but no page consumes it"))

    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    if not problems:
        print("no gaps found")
        return 0
    order = {"BLOCKING": 0, "WARN": 1, "INFO": 2}
    for sev, layer, detail in sorted(problems, key=lambda p: order[p[0]]):
        print(f"[{sev:<8}] {layer}: {detail}")
    blocking = [p for p in problems if p[0] == "BLOCKING"]
    print(f"\n{len(blocking)} blocking, "
          f"{sum(1 for p in problems if p[0] == 'WARN')} warnings, "
          f"{sum(1 for p in problems if p[0] == 'INFO')} informational")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
