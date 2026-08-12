#!/usr/bin/env python3
"""
Emit docs/rarity.js — the global sound-rarity layer for the Sound Chart page.

The rare-sounds material moved from the map page to the Sound Chart (it is a fact
about sounds, not geography), but the chart page must not pay for the ~200 KB map
bundle to get it. This carves out just the rarity fields from geo_analysis.json:
global frequency per symbol, English's rarest sounds, each language's signature
sounds, and the rarity-weighted pair overlaps. Result is a few KB.

Run analyze_geography.py first.
"""
import json

GEO_IN = "geo_analysis.json"
OUT = "docs/rarity.js"


def main():
    geo = json.load(open(GEO_IN, encoding="utf-8"))
    # GUARD: every symbol the chart can display must have a frequency, or it
    # renders as "rarity unknown" -- which reads as unremarkable and silently
    # understates the rarest sounds. This exact bug hid Zulu's clicks (each in
    # <1% of the world's languages) behind a default gray outline.
    import re
    js = open("docs/data.js", encoding="utf-8").read()
    data = json.loads(js.split("=", 1)[1].rstrip().rstrip(";"))
    chart_syms = {s for l in data["languages"] for s in l["phonemes"]}
    missing = sorted(chart_syms - set(geo["globalFreq"]))
    if missing:
        raise SystemExit(
            f"ERROR: {len(missing)} chart symbols have no global frequency: "
            f"{missing}\nFix analyze_geography.py (see the CLICK_CHARS handling) "
            f"rather than shipping unknown-rarity chips.")

    payload = {
        "worldLanguageCount": geo["worldLanguageCount"],
        "globalFreq": geo["globalFreq"],
        "englishRarest": geo["englishRarest"],
        # What `meanRarity` is scored over, carried alongside the number so a
        # page cannot label the axis in a way the metric does not support.
        "rarityUnit": geo["rarityUnit"],
        # per language: signature sounds + how unusual the inventory is overall
        "signature": {n: {"signature": d["signature"],
                          "meanRarity": d["meanRarity"],
                          "nPhonemes": d["nPhonemes"],
                          # scored unit vs charted unit: meanRarity uses
                          # nSingleSegments, not nPhonemes
                          "nSingleSegments": d["nSingleSegments"],
                          "nMultiSegment": d["nMultiSegment"]}
                      for n, d in geo["languages"].items()},
        # Tone is recorded by PHOIBLE and excluded from every metric here. Ship
        # it so any page that plots rarity can say which languages carry
        # contrasts the axis cannot see.
        "tone": geo["tone"],
        "weightedPairs": geo["weightedPairs"],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("const RARITY = ")
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    import os
    print(f"wrote {OUT} ({os.path.getsize(OUT)/1024:.0f}KB): "
          f"{len(payload['globalFreq'])} symbol frequencies, "
          f"{len(payload['signature'])} languages, "
          f"{len(payload['weightedPairs'])} weighted pairs")


if __name__ == "__main__":
    main()
