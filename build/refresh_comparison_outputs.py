#!/usr/bin/env python3
"""Regenerate every output derived from the inventory-comparison universe.

Run after ``build_chart_data.py`` from the build directory.  This intentionally
does not rebuild geographic shapes, speaker estimates, or the chart-cell rarity
analysis.  It replaces only the fields whose unit is a one-to-one entry inside
the broad, length-collapsed segmental comparison groups:

* worldwide broad-category and additional-contrast frequencies;
* plain and rarity-weighted pair overlap; and
* directional learner inventory gaps.

Existing ``prototype/rarity.js`` and ``prototype/mapdata.js`` bundles are updated
in place so those large, independently sourced payloads do not require unavailable
geography inputs merely because the comparison policy changed.
"""
import csv
import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_chart_data import TONE_CHARS, comparison_groups, comparison_segment

PHOIBLE = Path("data/phoible.csv")
DATA_JS = Path("prototype/data.js")
RARITY_JS = Path("prototype/rarity.js")
MAPDATA_JS = Path("prototype/mapdata.js")
ANALYSIS_JSON = Path("comparison_analysis.json")

COMPARISON_UNIT = (
    "one-to-one inventory entries grouped inside broad IPA categories after "
    "length collapse; standalone tone rows excluded"
)


def group_units(groups):
    """Stable internal ids: one base category plus any additional contrasts."""
    units = set()
    for category, entries in groups.items():
        if not entries:
            continue
        units.add(category)
        for rank in range(2, len(entries) + 1):
            units.add(f"{category}#contrast{rank}")
    return units


def read_const(path, declaration):
    raw = path.read_text(encoding="utf-8")
    prefix = f"const {declaration} = "
    if not raw.startswith(prefix) or not raw.rstrip().endswith(";"):
        raise ValueError(f"unexpected JavaScript wrapper in {path}")
    return json.loads(raw[len(prefix):].rstrip()[:-1])


def write_const(path, declaration, value):
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"const {declaration} = {payload};\n", encoding="utf-8")


def worldwide_frequencies(selected_segments):
    """Frequency by Glottocode, taking its largest PHOIBLE inventory once."""
    rows_by_inventory = defaultdict(list)
    glottocode_by_inventory = {}
    with PHOIBLE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            inventory = row["InventoryID"]
            rows_by_inventory[inventory].append(row)
            if row.get("Glottocode"):
                glottocode_by_inventory[inventory] = row["Glottocode"]

    best_by_glottocode = {}
    for inventory, glottocode in glottocode_by_inventory.items():
        current = best_by_glottocode.get(glottocode)
        if current is None or len(rows_by_inventory[inventory]) > len(rows_by_inventory[current]):
            best_by_glottocode[glottocode] = inventory

    counts = defaultdict(int)
    for inventory in best_by_glottocode.values():
        inventory_segments = {
            comparison_segment(row["Phoneme"])
            for row in rows_by_inventory[inventory]
            if not any(mark in row["Phoneme"] for mark in TONE_CHARS)
        }
        for unit in group_units(comparison_groups(inventory_segments)):
            counts[unit] += 1

    world_n = len(best_by_glottocode)
    frequencies = {
        segment: round(counts.get(segment, 0) / world_n, 5)
        for segment in selected_segments
    }
    return frequencies, world_n


def pair_metrics(sets, frequencies):
    pairs = {}
    for a, b in combinations(sorted(sets), 2):
        shared, union = sets[a] & sets[b], sets[a] | sets[b]
        plain = len(shared) / len(union) if union else 0
        shared_weight = sum(1 - frequencies.get(s, 0) for s in shared)
        union_weight = sum(1 - frequencies.get(s, 0) for s in union)
        pairs[f"{a}|{b}"] = {
            "plain": round(plain, 4),
            "weighted": round(shared_weight / union_weight if union_weight else 0, 4),
        }
    return pairs


def asymmetry(sets, frequencies):
    rows = {}
    for learner in sorted(sets):
        for target in sorted(sets):
            if learner == target:
                continue
            new = sets[target] - sets[learner]
            rows[f"{learner}|{target}"] = {
                "newSounds": len(new),
                "load": round(sum(1 - frequencies.get(s, 0) for s in new), 3),
                "sounds": sorted(new)[:14],
            }

    names = sorted(sets)
    outward = [rows[f"English|{n}"]["newSounds"] for n in names if n != "English"]
    inward = [rows[f"{n}|English"]["newSounds"] for n in names if n != "English"]
    harder_for = sum(
        rows[f"{n}|English"]["newSounds"] > rows[f"English|{n}"]["newSounds"]
        for n in names if n != "English"
    )

    lopsided = []
    for a, b in combinations(names, 2):
        ab, ba = rows[f"{a}|{b}"], rows[f"{b}|{a}"]
        if ab["newSounds"] <= ba["newSounds"]:
            easy_a, easy_b, easy, hard = a, b, ab, ba
        else:
            easy_a, easy_b, easy, hard = b, a, ba, ab
        lopsided.append({
            "a": a, "b": b,
            "gap": abs(ab["newSounds"] - ba["newSounds"]),
            "easyDir": f"{easy_a}→{easy_b}", "easyN": easy["newSounds"],
            "hardDir": f"{easy_b}→{easy_a}", "hardN": hard["newSounds"],
        })
    lopsided.sort(key=lambda x: (x["gap"], x["a"], x["b"]), reverse=True)

    return {
        "pairs": rows,
        "englishOutMean": round(sum(outward) / len(outward), 2),
        "englishInMean": round(sum(inward) / len(inward), 2),
        "englishHarderForN": harder_for,
        "rosterSize": len(names),
        "mostLopsided": lopsided[:12],
    }


def main():
    data = read_const(DATA_JS, "DATA")
    sets = {
        language["name"]: group_units(language["comparisonGroups"])
        for language in data["languages"]
    }
    selected = set().union(*sets.values())
    frequencies, world_n = worldwide_frequencies(selected)
    weighted_pairs = pair_metrics(sets, frequencies)
    learner_gaps = asymmetry(sets, frequencies)

    comparison = {
        "worldLanguageCount": world_n,
        "comparisonUnit": COMPARISON_UNIT,
        "comparisonFreq": frequencies,
        "weightedPairs": weighted_pairs,
        "asymmetry": learner_gaps,
    }
    ANALYSIS_JSON.write_text(
        json.dumps(comparison, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )

    if RARITY_JS.exists():
        rarity = read_const(RARITY_JS, "RARITY")
        rarity.update({
            "comparisonUnit": COMPARISON_UNIT,
            "comparisonFreq": frequencies,
            "weightedPairs": weighted_pairs,
        })
        write_const(RARITY_JS, "RARITY", rarity)

    if MAPDATA_JS.exists():
        mapdata = read_const(MAPDATA_JS, "MAPDATA")
        mapdata.update({
            "comparisonUnit": COMPARISON_UNIT,
            "comparisonFreq": frequencies,
            "weightedPairs": weighted_pairs,
            "asymmetry": learner_gaps,
        })
        write_const(MAPDATA_JS, "MAPDATA", mapdata)

    print(
        f"comparison outputs: {len(sets)} languages, {len(weighted_pairs)} pairs, "
        f"{world_n} worldwide inventories"
    )


if __name__ == "__main__":
    main()
