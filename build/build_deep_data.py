#!/usr/bin/env python3
"""
Emit docs/deep.js — the data behind the Sound Variants page:

  DEEP.allophones : why same-inventory languages still sound different

Run analyze_allophones.py first (this reads its JSON).

DEEP.mergers is gone. It fed the "Lost in Translation" page, which predicted
which English word pairs collapse into a homophone when borrowed. The page was
removed after a Japanese reader checked its output and found most of the words it
produced were not Japanese; four separate defects, the largest being that the
shared symbol normaliser strips vowel length, which is phonemic in Japanese, so
the model manufactured mergers out of the contrast it had discarded. The full
account is on the About page under "What got cut, and why". Do not reintroduce a
predicted-collision layer without ground truth to validate it against: the nine
documented mergers it did reproduce were compatible with being wrong everywhere
else.
"""
import json

ALLO_IN = "allophone_analysis.json"
OUT = "docs/deep.js"

def main():
    allo = json.load(open(ALLO_IN, encoding="utf-8"))

    # The overlap-vs-divergence scatter and the ranked bridge table are both
    # retired. The scatter's y-axis was documentation density in disguise; the
    # bridge ranking rewarded whichever languages happen to have the fullest
    # allophone records, which is not a fact about their speakers.

    out = {
        "allophones": {
            "coverage": allo["coverage"],
        },
    }
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("const DEEP = ")
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"wrote {OUT}: coverage metadata only; listening examples are curated")


if __name__ == "__main__":
    main()
