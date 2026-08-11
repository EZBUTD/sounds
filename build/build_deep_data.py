#!/usr/bin/env python3
"""
Emit prototype/deep.js — the data behind the Allophones page:

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
OUT = "prototype/deep.js"

# Pairs kept in the payload. Only English+Hindi is actually rendered now — the
# page uses it for the bridge half-credit lift ("overlap rises from X% to Y%"),
# which depends only on English's own allophone records and so is safe under
# sparse data. The per-pair "realized differently" cards and the overlap-vs-
# divergence scatter were removed: PHOIBLE allophone coverage is all-or-nothing
# per inventory (31 of 34 languages at 100% of phoneme rows; English, Marathi and
# Yoruba at 0%), so cross-pair rates tracked which analyses recorded allophones
# rather than phonetics. Listening examples now live in prototype/demos.js.
FEATURED_PAIRS = [
    ("English", "Hindi"),
]


def pair_lookup(pairs, a, b):
    return pairs.get(f"{a}|{b}") or pairs.get(f"{b}|{a}")


def main():
    allo = json.load(open(ALLO_IN, encoding="utf-8"))

    # --- allophone section ---
    pairs = allo["pairs"]
    featured = []
    for a, b in FEATURED_PAIRS:
        p = pair_lookup(pairs, a, b)
        if not p:
            continue
        flip = f"{a}|{b}" not in pairs      # stored order may be reversed
        featured.append({
            "a": a, "b": b,
            "shared": p["shared"],
            "jaccard": p["jaccard"],
            "bridgedJaccard": p["bridgedJaccard"],
            "divergenceRate": p["divergenceRate"],
            "nDiverged": p["nDiverged"], "nIdentical": p["nIdentical"],
            "nUndocumented": p["nUndocumented"],
            "aBridges": p["bBridges"] if flip else p["aBridges"],
            "bBridges": p["aBridges"] if flip else p["bBridges"],
            "examples": [{
                "phoneme": d["phoneme"],
                "aVariants": (d["b_variants"] if flip else d["a_variants"])[:5],
                "bVariants": (d["a_variants"] if flip else d["b_variants"])[:5],
            } for d in p["diverged"][:8]],
        })

    # The overlap-vs-divergence scatter and the ranked bridge table are both
    # retired. The scatter's y-axis was documentation density in disguise; the
    # bridge ranking rewarded whichever languages happen to have the fullest
    # allophone records, which is not a fact about their speakers.

    out = {
        "allophones": {
            "coverage": allo["coverage"],
            "featured": featured,
        },
    }
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("const DEEP = ")
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"wrote {OUT}: {len(featured)} featured pair(s)")


if __name__ == "__main__":
    main()
