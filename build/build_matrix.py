#!/usr/bin/env python3
"""
Build the 3-state phoneme matrix: English (PHOIBLE SPA inv 160) vs top-30 L1s.

States per (English phoneme, L1):
  FULL    - English phoneme is in L1's phoneme inventory
  VARIANT - not a phoneme, but appears in L1's Allophones column
  ABSENT  - neither
  (2-state languages: VARIANT impossible because source has no allophone data
   -> allophone_data=False flag emitted so the viz can annotate)

Matching: exact segment match after stripping length/tie marks for a base match,
reported alongside strict match. Headline counts use STRICT.

Output: matrix.csv (long format) + matrix_summary.csv + console sanity checks.
"""
import csv
import unicodedata
from collections import defaultdict

PHOIBLE = "data/phoible.csv"
# EA English (RP), 44 phonemes, standard transcription (diphthongs, ɹ).
# English allophone data not needed — variants only matter on the L1 side.
# (SPA inv 160 rejected: idiosyncratic vowels e̞/o̞ː/ɐ and marginal x/ʍ/ʔ.)
ENGLISH_INV = "2252"

# language name -> preferred InventoryID (best allophone coverage, from explore_inventories.py)
TOP_LANGS = {
    "Mandarin Chinese": "16",
    "Hindi": "2190",
    "Spanish": "2210",
    "French": "162",
    "Arabic (MSA)": "2157",
    "Egyptian Arabic": "132",
    "Bengali": "2162",
    "Russian": "166",
    "Portuguese": "163",
    "Indonesian": "1144",
    "German": "2184",
    "Japanese": "197",
    "Telugu": "8",
    "Turkish": "186",
    "Tamil": "1058",
    "Cantonese": "19",
    "Vietnamese": "2233",
    "Korean": "2197",
    "Italian": "2195",
    "Thai": "2215",
    "Polish": "1046",
    "Ukrainian": "1035",
    "Persian": "172",
    "Punjabi": "175",
    "Swahili": "823",
    "Tagalog": "37",
    "Dutch": "2173",
    "Greek": "2186",
    "Hebrew": "135",
    "Amharic": "2156",
    "Hausa": "2188",
    # 2-state (no allophone data in any source):
    "Urdu": "1797",
    "Marathi": "1766",
    "Yoruba": "636",
}

def norm(seg: str) -> str:
    """Base-segment normalization for cross-source comparison.
    Strips combining diacritics (Mn: dental, raised, voiceless...) AND modifier
    letters (Lm: aspiration, labialization, palatalization, length marks).
    Needed because sources differ in convention: English EA writes aspirated
    stops where most L1 sources write plain ones."""
    seg = unicodedata.normalize("NFD", seg)
    return "".join(c for c in seg if unicodedata.category(c) not in ("Mn", "Lm"))


def load_inventory(inv_id, rows_by_inv):
    rows = rows_by_inv[inv_id]
    phonemes = {r["Phoneme"] for r in rows}
    allophones = set()
    for r in rows:
        if r["Allophones"] not in ("", "NA"):
            for a in r["Allophones"].split():
                allophones.add(a)
    has_allo_data = any(r["Allophones"] not in ("", "NA") for r in rows)
    meta = rows[0]
    return phonemes, allophones, has_allo_data, meta


def classify(eng_seg, phonemes, allophones, has_allo_data):
    """Return (strict_state, base_state)."""
    def in_set(seg, s, use_norm):
        if not use_norm:
            return seg in s
        n = norm(seg)
        return any(norm(x) == n for x in s)

    def state(use_norm):
        if in_set(eng_seg, phonemes, use_norm):
            return "FULL"
        if has_allo_data and in_set(eng_seg, allophones, use_norm):
            return "VARIANT"
        return "ABSENT"

    return state(False), state(True)


def main():
    rows_by_inv = defaultdict(list)
    with open(PHOIBLE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows_by_inv[row["InventoryID"]].append(row)

    eng_phonemes, _, _, eng_meta = load_inventory(ENGLISH_INV, rows_by_inv)
    eng_sorted = sorted(eng_phonemes)
    print(f"English target: inv {ENGLISH_INV} ({eng_meta['Source']}), {len(eng_sorted)} phonemes")
    print("  " + " ".join(eng_sorted))

    out_rows, summary = [], []
    for lang, inv_id in TOP_LANGS.items():
        if inv_id not in rows_by_inv:
            print(f"!! inventory {inv_id} for {lang} not found, skipping")
            continue
        ph, allo, has_allo, meta = load_inventory(inv_id, rows_by_inv)
        counts = defaultdict(int)
        for seg in eng_sorted:
            strict, base = classify(seg, ph, allo, has_allo)
            counts[base] += 1  # headline counts use BASE match (see norm docstring)
            out_rows.append({
                "language": lang, "inventory_id": inv_id, "source": meta["Source"],
                "glottocode": meta["Glottocode"], "english_phoneme": seg,
                "state_strict": strict, "state_base": base,
                "allophone_data_available": has_allo,
            })
        summary.append({
            "language": lang, "inventory_id": inv_id, "source": meta["Source"],
            "l1_phoneme_count": len(ph),
            "full": counts["FULL"], "variant": counts["VARIANT"], "absent": counts["ABSENT"],
            "allophone_data_available": has_allo,
        })

    with open("matrix.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader(); w.writerows(out_rows)
    with open("matrix_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        w.writeheader(); w.writerows(summary)

    print(f"\nWrote matrix.csv ({len(out_rows)} rows) and matrix_summary.csv ({len(summary)} languages)")

    print("\n=== Missing-sound leaderboard (BASE-match ABSENT count) ===")
    for s in sorted(summary, key=lambda x: -x["absent"]):
        flag = "" if s["allophone_data_available"] else "  [no allophone data: 2-state]"
        print(f"  {s['language']:<18} absent={s['absent']:>2}  variant={s['variant']:>2}  full={s['full']:>2}{flag}")

    print("\n=== Sanity checks (famous cases) ===")
    checks = [  # expectations refer to BASE state
        ("Japanese", "f", "VARIANT"), ("Japanese", "l", "ABSENT"), ("Japanese", "θ", "ABSENT"),
        ("Spanish", "v", "ABSENT"), ("Spanish", "ð", "VARIANT"), ("Spanish", "z", None),
        ("Korean", "f", "ABSENT"), ("Egyptian Arabic", "pʰ", "ABSENT"), ("German", "w", "ABSENT"),
        ("French", "θ", "ABSENT"), ("Hindi", "θ", None), ("Russian", "θ", "ABSENT"),
        ("Japanese", "ɹ", "ABSENT"), ("Korean", "v", "ABSENT"), ("Mandarin Chinese", "v", None),
    ]
    idx = {(r["language"], r["english_phoneme"]): r for r in out_rows}
    for lang, seg, expect in checks:
        r = idx.get((lang, seg))
        if not r:
            print(f"  {lang} /{seg}/: English phoneme not in target set under this symbol")
            continue
        ok = "" if expect is None else (" ✓" if r["state_base"] == expect else f" ✗ expected {expect}")
        print(f"  {lang:<16} /{seg}/ -> strict={r['state_strict']:<8} base={r['state_base']:<8}{ok}")


if __name__ == "__main__":
    main()
