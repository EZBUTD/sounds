#!/usr/bin/env python3
"""
Accounting audit: for every language, reconcile
  raw PHOIBLE phoneme count
    = displayed on-chart + displayed extras
    + MERGED (base-normalization collapses e.g. kʰ/k into one cell — by design)
    + TONES (excluded from extras by design, flagged in headline)
    + DROPPED (silently lost — should be ZERO / needs fixing)
"""
import csv
import unicodedata
from collections import defaultdict
from build_chart_data import LANG_INVENTORIES, norm, chart_symbols

TONE_CHARS = set("˥˦˧˨˩")


def is_tone(seg):
    return any(c in TONE_CHARS for c in seg)


def main():
    rows_by_inv = defaultdict(list)
    with open("data/phoible.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows_by_inv[row["InventoryID"]].append(row)

    onchart = chart_symbols()
    CLICKS = "ʘǀǃǂǁ"
    print(f"{'language':<20} {'raw':>4} {'chart':>5} {'extra':>5} {'merged':>6} {'tones':>5} {'DROP':>4}")
    total_dropped = {}
    for name, inv_id in LANG_INVENTORIES.items():
        rows = rows_by_inv.get(inv_id, [])
        raw_segs = [r["Phoneme"] for r in rows]

        base_map = defaultdict(list)   # base symbol -> raw segs mapping to it
        tones = []
        for seg in raw_segs:
            if is_tone(seg):
                tones.append(seg)
                continue
            base_map[norm(seg)].append(seg)

        display_chart = set()
        display_extras = set()
        dropped = []
        for base, sources in base_map.items():
            if base in onchart:
                display_chart.add(base)
            elif base and not any(unicodedata.category(c) in ("Sk",) for c in base):
                display_extras.add(base)
            else:
                dropped.extend(sources)
        # clicks credited from clusters count as chart coverage, not new raw segs
        n_merged = sum(len(v) - 1 for v in base_map.values())
        # extras cap in build is 24 — check overflow
        overflow = max(0, len(display_extras) - 24)
        if overflow:
            dropped.append(f"({overflow} extras over display cap)")
        n_drop = len(dropped)
        total_dropped[name] = dropped
        ok = "" if (len(raw_segs) == len(display_chart) + len(display_extras)
                    + n_merged + len(tones) + (n_drop if not overflow else 0)) else "  <-- MISMATCH"
        print(f"{name:<20} {len(raw_segs):>4} {len(display_chart):>5} {len(display_extras):>5} "
              f"{n_merged:>6} {len(tones):>5} {n_drop:>4}{ok}")

    print("\n--- dropped segments detail (should be empty) ---")
    for name, d in total_dropped.items():
        if d:
            print(f"  {name}: {d}")


if __name__ == "__main__":
    main()
