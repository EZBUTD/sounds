#!/usr/bin/env python3
"""
Allophone-layer analysis: WHY don't same-inventory languages sound the same?

The phoneme chart says English and Hindi share 27 sounds. They still sound
nothing alike. This script quantifies three reasons, all from PHOIBLE's
`Allophones` column (which the phoneme-only analysis throws away):

  1. REALIZATION DIVERGENCE — a phoneme both languages "have" is physically
     produced differently (different allophone sets). Same chart cell, different
     mouth. This is the main answer to the user's question.
  2. BRIDGES — a sound that is a full phoneme in L2 exists in L1 only as a
     positional variant. L1 speakers CAN make it but don't hear it as separate,
     so they can't use it to tell words apart.
  3. ALLOPHONE LOAD — how much variation a language piles onto each phoneme.
     High load = one letter, many realizations = harder to map by ear.

CAVEATS (kept honest, surfaced in output):
  - English's pinned chart inventory (EA RP 2252) carries NO allophone data. This
    is a fact about that inventory, not about English: PHOIBLE's SPA inv 160
    records differing variants for 68% of its 40 English phonemes, and the PH
    inventories land between (Australian 52%, British 42%, American 26%). We
    supplement English allophones from inv 160, which agrees with 2252 on 32 of 51
    base phonemes. Flagged in output; English rows marked (mixed). Never state
    that "English has no allophones" — say the charted inventory records none.
  - Marathi and Yoruba have no allophone data in ANY PHOIBLE inventory, so
    they are excluded from allophone metrics (still present on the chart).
  - Allophones are recorded per-source and are not exhaustive: absence of an
    allophone is NOT proof a language lacks that variant. Counts are
    lower bounds, comparable across languages only in the loose sense.

COVERAGE HANDLING (added after review, 2026-08)
  Allophone documentation density varies enormously by source: Spanish records
  variants for 80% of its phonemes, Punjabi for 1%. Two consequences drove a
  scope cut:

    a) DIVERGENCE IS ONE-SIDED-SAFE NOW. Previously a shared phoneme counted as
       "realized differently" whenever the two variant sets differed — including
       when one side simply had no record. That made Hindi+Punjabi read 100%
       diverged purely because Punjabi has no allophone data. A phoneme is now
       classified diverged/identical ONLY when both sides have a record;
       one-sided phonemes join `undocumented`.
    b) THIN LANGUAGES ARE EXCLUDED. Any language documenting variants for fewer
       than MIN_COVERAGE of its phonemes is dropped from pairwise divergence
       (it stays in bridge counts, which are one-directional and therefore only
       ever undercount).

  Even with (a) and (b), cross-pair divergence RATES remain sensitive to source
  density and should not be ranked against each other. The published page no
  longer shows them; they are retained here for analysis only.
"""
import csv
import json
import unicodedata
from collections import defaultdict

from build_chart_data import LANG_INVENTORIES, norm

PHOIBLE = "data/phoible.csv"

# The English inventory pinned for the chart (RP, inv 2252) records no allophones.
# This is a property of that inventory, NOT of English: PHOIBLE's SPA inv 160
# documents differing variants for 68% of its 40 English phonemes. Borrow from 160.
ALLOPHONE_SUPPLEMENT = {"English": "160"}
NO_ALLOPHONE_DATA = {"Marathi", "Yoruba"}

# Minimum share of a language's phonemes that must carry allophone records
# before we trust it in a pairwise divergence comparison. Below this the
# "variants differ" signal is dominated by missing data, not phonetics.
MIN_COVERAGE = 0.15


def load_rows():
    rows_by_inv = defaultdict(list)
    for r in csv.DictReader(open(PHOIBLE, encoding="utf-8")):
        rows_by_inv[r["InventoryID"]].append(r)
    return rows_by_inv


def raw_allophones(row):
    """Allophones of a row, excluding the phoneme's own faithful realization."""
    if row["Allophones"] in ("", "NA"):
        return set()
    return {a for a in row["Allophones"].split() if a and a != row["Phoneme"]}


def build_language(name, rows_by_inv):
    """-> dict with phoneme set, per-phoneme allophones (base + raw), load."""
    rows = rows_by_inv[LANG_INVENTORIES[name]]
    phonemes = set()
    for r in rows:
        p = norm(r["Phoneme"])
        if p:
            phonemes.add(p)

    # allophones may come from a different (supplement) inventory
    allo_rows = rows_by_inv[ALLOPHONE_SUPPLEMENT[name]] if name in ALLOPHONE_SUPPLEMENT else rows

    by_base = defaultdict(set)   # base phoneme -> base-normalized variants
    raw_by_base = defaultdict(set)  # base phoneme -> raw variants (diacritics kept)
    for r in allo_rows:
        base = norm(r["Phoneme"])
        if not base:
            continue
        for a in raw_allophones(r):
            raw_by_base[base].add(a)
            nb = norm(a)
            if nb:
                by_base[base].add(nb)

    all_variants = {v for s in by_base.values() for v in s}
    # coverage = share of this language's phonemes that carry any allophone record
    documented = sum(1 for p in phonemes if by_base.get(p))
    coverage = documented / max(len(phonemes), 1)
    return {
        "name": name,
        "phonemes": phonemes,
        "variants": all_variants,          # base-normalized, chart-comparable
        "by_base": dict(by_base),
        "raw_by_base": dict(raw_by_base),
        "coverage": coverage,
        "has_allo": name not in NO_ALLOPHONE_DATA,
        # trustworthy enough for a pairwise divergence comparison?
        "div_ok": name not in NO_ALLOPHONE_DATA and coverage >= MIN_COVERAGE,
        "mixed": name in ALLOPHONE_SUPPLEMENT,
    }


def pair_report(a, b):
    """Allophone-layer comparison of two language dicts."""
    shared = a["phonemes"] & b["phonemes"]
    a_only = a["phonemes"] - b["phonemes"]
    b_only = b["phonemes"] - a["phonemes"]

    # 1. realization divergence among SHARED phonemes.
    #    A phoneme only counts as diverged/identical when BOTH languages have a
    #    record for it. One-sided documentation is missing data, not evidence of
    #    a different realization — counting it as divergence is what produced the
    #    bogus Hindi+Punjabi "100% realized differently".
    diverged, identical, undocumented = [], [], []
    for p in sorted(shared):
        va, vb = a["by_base"].get(p, set()), b["by_base"].get(p, set())
        if not va or not vb:
            undocumented.append(p)
        elif va == vb:
            identical.append(p)
        else:
            diverged.append({
                "phoneme": p,
                "a_variants": sorted(a["raw_by_base"].get(p, set())),
                "b_variants": sorted(b["raw_by_base"].get(p, set())),
            })

    # 2. bridges: other language's exclusive phoneme present here as a variant
    a_bridges = sorted(b_only & a["variants"])   # B's phoneme, A has as variant
    b_bridges = sorted(a_only & b["variants"])
    documented = len(shared) - len(undocumented)

    return {
        "shared": len(shared),
        "a_only": len(a_only), "b_only": len(b_only),
        "jaccard": len(shared) / len(a["phonemes"] | b["phonemes"]),
        "diverged": diverged,
        "n_diverged": len(diverged),
        "n_identical": len(identical),
        "n_undocumented": len(undocumented),
        # share of shared phonemes that are actually realized differently
        "divergence_rate": (len(diverged) / documented) if documented else None,
        "a_bridges": a_bridges, "b_bridges": b_bridges,
    }


def main():
    rows_by_inv = load_rows()
    langs = {n: build_language(n, rows_by_inv) for n in LANG_INVENTORIES}
    usable = [n for n, d in langs.items() if d["has_allo"]]
    div_ok = [n for n, d in langs.items() if d["div_ok"]]
    thin = sorted(n for n, d in langs.items()
                  if d["has_allo"] and not d["div_ok"])

    print("=" * 72)
    print("ALLOPHONE COVERAGE")
    print("=" * 72)
    print(f"languages on chart: {len(langs)}   with allophone data: {len(usable)}")
    print(f"excluded (no allophone data anywhere): {sorted(NO_ALLOPHONE_DATA)}")
    print(f"allophones supplemented from another inventory: {ALLOPHONE_SUPPLEMENT}")
    print(f"\ntrusted for pairwise divergence (coverage >= {MIN_COVERAGE:.0%}): "
          f"{len(div_ok)} of {len(langs)}")
    thin_desc = ", ".join(f"{n} {langs[n]['coverage']:.0%}" for n in thin)
    print(f"too thin for divergence, kept for bridges: {thin_desc}")
    print("\nper-language coverage (share of phonemes with any variant recorded):")
    for n, d in sorted(langs.items(), key=lambda kv: -kv[1]["coverage"]):
        flag = "" if d["div_ok"] else "  <-- excluded from divergence"
        print(f"  {n:<20} {d['coverage']:>5.0%}{flag}")

    print("\n" + "=" * 72)
    print("ALLOPHONE LOAD (how much hidden variation per language)")
    print("=" * 72)
    print(f"{'language':<20} {'phonemes':>8} {'variants':>8} {'load':>6}  {'note':<8}")
    load = []
    for n in usable:
        d = langs[n]
        nv = sum(len(v) for v in d["raw_by_base"].values())
        load.append((nv / max(len(d["phonemes"]), 1), n, len(d["phonemes"]), nv))
    for ld, n, npho, nv in sorted(load, reverse=True):
        note = "(mixed)" if langs[n]["mixed"] else ""
        print(f"{n:<20} {npho:>8} {nv:>8} {ld:>6.2f}  {note:<8}")

    # ---- headline pair: English vs Hindi ----
    print("\n" + "=" * 72)
    print("CASE STUDY: English vs Hindi — same 27 sounds, different mouths")
    print("=" * 72)
    rep = pair_report(langs["English"], langs["Hindi"])
    print(f"shared phonemes: {rep['shared']}   phoneme-only overlap: {rep['jaccard']:.0%}")
    print(f"of {rep['shared']} shared, allophone data on both sides for "
          f"{rep['shared'] - rep['n_undocumented']}:")
    print(f"  realized DIFFERENTLY: {rep['n_diverged']}"
          f"   identical: {rep['n_identical']}   no data: {rep['n_undocumented']}")
    if rep["divergence_rate"] is not None:
        print(f"  divergence rate: {rep['divergence_rate']:.0%} of documented shared phonemes")
    print(f"\nbridges — Hindi phonemes English has only as a variant: {rep['b_bridges']}")
    print(f"bridges — English phonemes Hindi has only as a variant:  {rep['a_bridges']}")
    print("bridge candidates are qualitative only; they receive no overlap or "
          "learner difficulty score")
    print("\nsample realization splits (same phoneme, different variants):")
    for d in rep["diverged"][:12]:
        print(f"  /{d['phoneme']}/  English: {' '.join(d['a_variants']) or '—':<22}"
              f"  Hindi: {' '.join(d['b_variants']) or '—'}")

    # Build all pairs for the coverage-gated descriptive output. Bridge lists are
    # retained as qualitative examples, never ranked or converted into a score.
    # bridges are computed over every language with any allophone data (missing
    # data can only undercount a bridge). Divergence is gated on coverage and is
    # suppressed for thin pairs via divergenceRate = None.
    pairs = []
    for i, n1 in enumerate(usable):
        for n2 in usable[i + 1:]:
            r = pair_report(langs[n1], langs[n2])
            if not (langs[n1]["div_ok"] and langs[n2]["div_ok"]):
                r["divergence_rate"] = None
            pairs.append((n1, n2, r))

    print("\n" + "=" * 72)
    print("SIMILAR ON PAPER, DIVERGENT IN THE MOUTH")
    print("(high base-cell overlap BUT high realization divergence)")
    print("=" * 72)
    cand = [t for t in pairs if t[2]["jaccard"] >= 0.5
            and t[2]["divergence_rate"] is not None
            and t[2]["shared"] - t[2]["n_undocumented"] >= 8]
    print(f"{'pair':<38} {'overlap':>7} {'divergence':>11} {'shared':>7}")
    for n1, n2, r in sorted(cand, key=lambda t: -t[2]["divergence_rate"])[:12]:
        print(f"{n1 + ' + ' + n2:<38} {r['jaccard']:>7.0%} "
              f"{r['divergence_rate']:>11.0%} {r['shared']:>7}")

    # ---- emit for the deployed static site ----
    out = {
        "coverage": {
            "total": len(langs), "with_allophones": len(usable),
            "excluded": sorted(NO_ALLOPHONE_DATA),
            "supplemented": ALLOPHONE_SUPPLEMENT,
            "minCoverage": MIN_COVERAGE,
            "divergenceTrusted": sorted(div_ok),
            "tooThinForDivergence": thin,
            "perLanguage": {n: round(d["coverage"], 3) for n, d in langs.items()},
        },
        "load": {n: {"phonemes": npho, "variants": nv, "load": round(ld, 3)}
                 for ld, n, npho, nv in load},
        "pairs": {f"{n1}|{n2}": {
            "shared": r["shared"], "jaccard": round(r["jaccard"], 4),
            "aBridges": r["a_bridges"], "bBridges": r["b_bridges"],
            "nDiverged": r["n_diverged"], "nIdentical": r["n_identical"],
            "nUndocumented": r["n_undocumented"],
            "divergenceRate": round(r["divergence_rate"], 4) if r["divergence_rate"] is not None else None,
            "diverged": r["diverged"][:20],
        } for n1, n2, r in pairs},
    }
    with open("allophone_analysis.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\nwrote allophone_analysis.json ({len(pairs)} pairs)")


if __name__ == "__main__":
    main()
