#!/usr/bin/env python3
"""
Asymmetric difficulty: learning is a one-way street.

Overlap is symmetric -- English and Japanese share the same 16 sounds in either
direction. But LEARNING is not. What matters to a learner is the sounds in the
target language that their own language never gave them, and that count differs
sharply by direction:

    English speaker learning Japanese : Japanese has 4 sounds English lacks
    Japanese speaker learning English : English has 20 sounds Japanese lacks

Same pair, five times the phonetic workload one way versus the other. This is
the backlog's "hardest language pair / asymmetric gaps" item, and it reframes
the project's takeaway: when a language feels hard to English speakers, that is
often a small gap being felt from the easy side of a steep hill.

Two refinements over a raw missing-sound count:
  1. NEW-SOUND LOAD weights each missing sound by how rare it is worldwide, since
     a sound almost no language has is likely to be genuinely unfamiliar rather
     than merely absent from one inventory.
  2. BRIDGE CREDIT (from the allophone analysis) discounts missing sounds the
     learner's language already produces as a positional variant -- those are
     easier to acquire than sounds a speaker has never made at all.

CAVEATS
  - Phonetic workload is ONE component of difficulty, and not the largest.
    Grammar, writing system, vocabulary distance and available study material
    usually dominate. This measures the sound layer only, and says nothing about
    tone, prosody, syllable structure or phonotactics -- Japanese speakers find
    English consonant clusters hard even where every individual sound is shared.
  - Counts are at the base-symbol level, so aspiration and length contrasts are
    merged (see the main page's counting policy).
"""
import csv
import json
import math
from collections import defaultdict

from build_chart_data import LANG_INVENTORIES, norm

PHOIBLE = "data/phoible.csv"
GEO = "geo_analysis.json"
ALLO = "allophone_analysis.json"
TONE_CHARS = set("˥˦˧˨˩")


def main():
    rows_by_inv = defaultdict(list)
    for r in csv.DictReader(open(PHOIBLE, encoding="utf-8")):
        rows_by_inv[r["InventoryID"]].append(r)

    sets = {}
    for name, inv in LANG_INVENTORIES.items():
        sets[name] = {s for s in (norm(r["Phoneme"]) for r in rows_by_inv[inv])
                      if s and not any(c in TONE_CHARS for c in s)}

    geo = json.load(open(GEO, encoding="utf-8"))
    freq = geo["globalFreq"]
    allo = json.load(open(ALLO, encoding="utf-8"))["pairs"]

    def bridges_for(learner, target):
        """target-only sounds the learner already produces as an allophone."""
        p = allo.get(f"{learner}|{target}")
        if p:
            return set(p["aBridges"])          # learner is side A
        p = allo.get(f"{target}|{learner}")
        if p:
            return set(p["bBridges"])          # learner is side B
        return set()

    names = list(sets)
    rows = []
    for a in names:                             # a = learner's native language
        for b in names:                         # b = language being learned
            if a == b:
                continue
            new = sets[b] - sets[a]
            br = bridges_for(a, b) & new
            # rarity-weighted load: rarer sounds are likely genuinely unfamiliar;
            # bridge sounds count half since the learner can already produce them
            load = sum((1 - freq.get(s, 0)) * (0.5 if s in br else 1.0) for s in new)
            rows.append({
                "learner": a, "target": b,
                "newSounds": len(new), "bridged": len(br),
                "load": round(load, 3),
                "sounds": sorted(new),
            })

    by_pair = {}
    for r in rows:
        by_pair[(r["learner"], r["target"])] = r

    print("=" * 78)
    print("MOST LOPSIDED PAIRS (one direction far harder than the other)")
    print("=" * 78)
    seen, lop = set(), []
    for a in names:
        for b in names:
            if a == b or (b, a) in seen:
                continue
            seen.add((a, b))
            f, g = by_pair[(a, b)], by_pair[(b, a)]
            lop.append((abs(f["newSounds"] - g["newSounds"]), a, b, f, g))
    print(f"{'pair':<36} {'→ direction':<34} {'gap':>4}")
    for diff, a, b, f, g in sorted(lop, reverse=True)[:10]:
        easy, hard = (f, g) if f["newSounds"] < g["newSounds"] else (g, f)
        print(f"{a + ' / ' + b:<36} "
              f"{easy['learner']}→{easy['target']} {easy['newSounds']} new vs "
              f"{hard['learner']}→{hard['target']} {hard['newSounds']}   {diff:>4}")

    print("\n" + "=" * 78)
    print("FROM AN ENGLISH SPEAKER'S SIDE — sound workload, easiest first")
    print("=" * 78)
    eng = sorted((r for r in rows if r["learner"] == "English"),
                 key=lambda r: r["load"])
    print(f"{'target':<20} {'new sounds':>10} {'already make':>13} {'load':>7}  reverse")
    for r in eng[:8] + [None] + eng[-6:]:
        if r is None:
            print(f"{'…':<20}")
            continue
        rev = by_pair[(r["target"], "English")]
        print(f"{r['target']:<20} {r['newSounds']:>10} {r['bridged']:>13} "
              f"{r['load']:>7.1f}  (they need {rev['newSounds']} of ours)")

    print("\n" + "=" * 78)
    print("THE ENGLISH ADVANTAGE")
    print("=" * 78)
    out_load = [by_pair[("English", b)]["newSounds"] for b in names if b != "English"]
    in_load = [by_pair[(b, "English")]["newSounds"] for b in names if b != "English"]
    print(f"English speakers need on average {sum(out_load)/len(out_load):.1f} new sounds "
          f"to reach these languages")
    print(f"Their speakers need on average  {sum(in_load)/len(in_load):.1f} new sounds "
          f"to reach English")
    harder_in = sum(1 for b in names if b != "English"
                    and by_pair[(b, "English")]["newSounds"] >
                        by_pair[("English", b)]["newSounds"])
    print(f"English is the harder direction for {harder_in} of {len(names)-1} languages")

    # Sanity/honesty check: is this special to English, or just a big-inventory
    # effect? Rank every language by how lopsided its outward direction is.
    print("\nis this an English quirk, or just inventory size?")
    adv = []
    for a in names:
        out = [by_pair[(a, b)]["newSounds"] for b in names if b != a]
        inn = [by_pair[(b, a)]["newSounds"] for b in names if b != a]
        adv.append((sum(inn) / len(inn) - sum(out) / len(out), a, len(sets[a])))
    for d, a, sz in sorted(adv, reverse=True)[:6]:
        print(f"   {a:<18} {sz:>3} sounds   advantage {d:>+5.1f} "
              f"(others need that many more of its sounds than it needs of theirs)")
    big = sorted(adv, reverse=True)
    print(f"   -> the top of this list is simply the biggest inventories: "
          f"the more sounds a language has, the more its speakers already cover.")

    payload = {
        "pairs": {f"{r['learner']}|{r['target']}": {
            "newSounds": r["newSounds"], "bridged": r["bridged"],
            "load": r["load"], "sounds": r["sounds"][:14],
        } for r in rows},
        "englishOutMean": round(sum(out_load) / len(out_load), 2),
        "englishInMean": round(sum(in_load) / len(in_load), 2),
        "englishHarderForN": harder_in,
        "rosterSize": len(names),
        "mostLopsided": [{
            "a": a, "b": b, "gap": diff,
            "easyDir": f"{ (f if f['newSounds']<g['newSounds'] else g)['learner'] }→"
                       f"{ (f if f['newSounds']<g['newSounds'] else g)['target'] }",
            "easyN": min(f["newSounds"], g["newSounds"]),
            "hardDir": f"{ (g if f['newSounds']<g['newSounds'] else f)['learner'] }→"
                       f"{ (g if f['newSounds']<g['newSounds'] else f)['target'] }",
            "hardN": max(f["newSounds"], g["newSounds"]),
        } for diff, a, b, f, g in sorted(lop, reverse=True)[:12]],
    }
    with open("asymmetry_analysis.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f"\nwrote asymmetry_analysis.json ({len(rows)} directed pairs)")


if __name__ == "__main__":
    main()
