#!/usr/bin/env python3
"""
Directional broad sound-area gaps for learners.

Overlap is symmetric, but potentially unfamiliar areas depend on the direction
of learning. The target source can occupy broad areas absent from the learner's
source, and that count can differ by direction.

This is a descriptive starting point, not a workload or difficulty score. A
learner may already produce a related pronunciation variant, and an inventory
does not measure individual perception or control.

CAVEATS
  - This measures one part of the sound layer only. Grammar, writing system,
    vocabulary distance, study access, tone, prosody, syllable structure and
    phonotactics can all change a learner's experience.
  - Counts use the same one-occupied-area rule as the main comparison. Detailed
    source entries remain qualitative information; length follows the declared
    broad display policy.
"""
import csv
import json
from collections import defaultdict

from build_chart_data import (LANG_INVENTORIES, TONE_CHARS, comparison_groups,
                              comparison_segment)

PHOIBLE = "data/phoible.csv"
COMPARISON = "comparison_analysis.json"


def group_units(groups):
    return {category for category, entries in groups.items() if entries}


def main():
    rows_by_inv = defaultdict(list)
    for r in csv.DictReader(open(PHOIBLE, encoding="utf-8")):
        rows_by_inv[r["InventoryID"]].append(r)

    sets = {}
    for name, inv in LANG_INVENTORIES.items():
        segments = {
            comparison_segment(r["Phoneme"])
            for r in rows_by_inv[inv]
            if not any(c in r["Phoneme"] for c in TONE_CHARS)
        }
        sets[name] = group_units(comparison_groups(segments))

    comparison = json.load(open(COMPARISON, encoding="utf-8"))
    freq = comparison["comparisonFreq"]
    names = list(sets)
    rows = []
    for a in names:                             # a = learner's native language
        for b in names:                         # b = language being learned
            if a == b:
                continue
            new = sets[b] - sets[a]
            # Rarity is only a descriptive weighting; allophone entries do not
            # discount the score because they do not establish learner ability.
            load = sum(1 - freq.get(s, 0) for s in new)
            rows.append({
                "learner": a, "target": b,
                "newSounds": len(new),
                "load": round(load, 3),
                "sounds": sorted(new),
            })

    by_pair = {}
    for r in rows:
        by_pair[(r["learner"], r["target"])] = r

    print("=" * 78)
    print("MOST LOPSIDED PAIRS (one direction has a larger broad-area gap)")
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
        smaller, larger = (f, g) if f["newSounds"] < g["newSounds"] else (g, f)
        print(f"{a + ' / ' + b:<36} "
              f"{smaller['learner']}→{smaller['target']} {smaller['newSounds']} areas vs "
              f"{larger['learner']}→{larger['target']} {larger['newSounds']}   {diff:>4}")

    print("\n" + "=" * 78)
    print("FROM THE ENGLISH SOURCE — FEWEST POTENTIALLY UNFAMILIAR AREAS FIRST")
    print("=" * 78)
    eng = sorted((r for r in rows if r["learner"] == "English"),
                 key=lambda r: r["load"])
    print(f"{'target':<20} {'new areas':>10} {'rarity weight':>13}  reverse")
    for r in eng[:8] + [None] + eng[-6:]:
        if r is None:
            print(f"{'…':<20}")
            continue
        rev = by_pair[(r["target"], "English")]
        print(f"{r['target']:<20} {r['newSounds']:>10} "
              f"{r['load']:>13.1f}  (reverse gap {rev['newSounds']})")

    print("\n" + "=" * 78)
    print("THE ENGLISH SOURCE OCCUPIES MANY BROAD AREAS")
    print("=" * 78)
    out_load = [by_pair[("English", b)]["newSounds"] for b in names if b != "English"]
    in_load = [by_pair[(b, "English")]["newSounds"] for b in names if b != "English"]
    print(f"Targets add an average {sum(out_load)/len(out_load):.1f} areas absent from "
          f"the selected English source")
    print(f"English adds an average {sum(in_load)/len(in_load):.1f} areas absent from "
          f"the selected target source")
    harder_in = sum(1 for b in names if b != "English"
                    and by_pair[(b, "English")]["newSounds"] >
                        by_pair[("English", b)]["newSounds"])
    print(f"English is the larger source gap for {harder_in} of {len(names)-1} languages")

    # Sanity/honesty check: is this special to English, or just a big-inventory
    # effect? Rank every language by how lopsided its outward direction is.
    print("\nis this an English quirk, or just inventory size?")
    adv = []
    for a in names:
        out = [by_pair[(a, b)]["newSounds"] for b in names if b != a]
        inn = [by_pair[(b, a)]["newSounds"] for b in names if b != a]
        adv.append((sum(inn) / len(inn) - sum(out) / len(out), a, len(sets[a])))
    for d, a, sz in sorted(adv, reverse=True)[:6]:
        print(f"   {a:<18} {sz:>3} areas   directional difference {d:>+5.1f}")
    big = sorted(adv, reverse=True)
    print("   -> larger selected inventories tend to occupy more comparison areas; "
          "this is a source-coverage pattern, not a learner advantage score.")

    payload = {
        "pairs": {f"{r['learner']}|{r['target']}": {
            "newSounds": r["newSounds"],
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
