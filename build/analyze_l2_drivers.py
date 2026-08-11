#!/usr/bin/env python3
"""
Does sound difficulty deter learners?

Motivation: the main page argues sound distance is not a barrier to learning.
This tests that at map scale -- if unusual sounds deterred learners, languages
with rarer inventories should have fewer L2 speakers.

The naive answer is misleading, and the correction is the interesting part:

  rarity ~ log10(L2 speakers)                    r = +0.48   (significant)
  ... controlling for inventory SIZE             r = +0.20   (collapses)
  because rarity ~ inventory size                r = +0.82   (confound)

  lingua-franca status ~ log10(L2 speakers)      r = +0.71
  lingua-franca status ~ rarity                  r = +0.05   (independent)

So the raw positive correlation is mostly an artifact: `meanRarity` is the mean
rarity of a language's sounds, and languages with MORE sounds inevitably include
more unusual ones, so rarity partly just measures inventory size. What actually
predicts learner counts is whether a language became a regional lingua franca --
a matter of empire, trade, migration and state policy, not phonetics.

Conclusion for the page: there is no evidence that hard sounds deter learners.
Sound difficulty and learner numbers are effectively unrelated once you account
for inventory size; history dominates.

CAVEATS
  - n = 25 languages with published L2 estimates. Small, and not a random
    sample: it is skewed toward large, well-documented, politically prominent
    languages, which is exactly the population where lingua-franca status is
    common. Treat coefficients as descriptive of this roster, not the world.
  - Lingua-franca status is a hand-coded binary (documented below), which is a
    blunt instrument for a continuum. It is used only to show that a
    history-based variable outpredicts a phonetic one, not to quantify empire.
  - Correlation, not causation, in every direction here.
  - THE RARITY AXIS IS SEGMENTAL ONLY. It scores consonants and vowels. Tone is
    recorded separately by PHOIBLE and excluded from every figure here, so the
    seven tonal languages on the roster carry lexical contrasts this analysis
    cannot see. Cantonese scores near the BOTTOM of the rarity axis while having
    six tones English offers no equivalent for. Read a low score as "few unusual
    consonants and vowels", never as "easy".
  - Earlier revisions scored rarity over every symbol including diphthongs, which
    made the axis substantially a count of how many glides a source transcribed
    as single phonemes (r = +0.66 with multi-segment symbol count) and put
    English 2nd of 34. The figures above are the corrected, single-segment ones;
    the previous values were +0.56 / +0.16 / +0.88 / +0.71 / +0.02.
"""
import json
import math

GEO = "geo_analysis.json"

# Hand-coded: languages that function as a regional/official lingua franca well
# beyond their native-speaker community (colonial legacy, state policy, trade,
# or liturgical/formal register). Deliberately coarse -- see caveats.
LINGUA_FRANCA = {
    "English", "French", "Arabic (MSA)", "Swahili", "Portuguese", "Spanish",
    "Indonesian", "Hindi", "Tagalog", "Thai", "Amharic", "Hausa", "Russian",
}


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs)
    dy = sum((y - my) ** 2 for y in ys)
    return num / math.sqrt(dx * dy) if dx and dy else 0.0


def spearman(xs, ys):
    def ranks(a):
        order = sorted(range(len(a)), key=lambda i: a[i])
        r = [0.0] * len(a)
        for pos, i in enumerate(order):
            r[i] = float(pos)
        return r
    return pearson(ranks(xs), ranks(ys))


def partial(r_xy, r_xz, r_yz):
    """Correlation of x,y with z held constant."""
    den = math.sqrt((1 - r_xz ** 2) * (1 - r_yz ** 2))
    return (r_xy - r_xz * r_yz) / den if den else 0.0


def t_stat(r, n):
    return r * math.sqrt((n - 2) / (1 - r ** 2)) if abs(r) < 1 else float("inf")


def main():
    langs = json.load(open(GEO, encoding="utf-8"))["languages"]
    rows = [(n, d) for n, d in langs.items() if d.get("l2")]
    n = len(rows)

    rarity = [d["meanRarity"] for _, d in rows]
    l2 = [math.log10(d["l2"]) for _, d in rows]
    # Measure the size confound on the SAME unit the rarity score is built from.
    # meanRarity averages over single segments only, so pairing it with a phoneme
    # count that includes diphthongs would control for a slightly different
    # variable than the one generating the confound.
    size = [float(d["nSingleSegments"]) for _, d in rows]
    lf = [1.0 if name in LINGUA_FRANCA else 0.0 for name, _ in rows]

    r_rl = pearson(rarity, l2)
    r_rs = pearson(rarity, size)
    r_sl = pearson(size, l2)
    r_lfl = pearson(lf, l2)
    r_lfr = pearson(lf, rarity)

    print("=" * 74)
    print(f"DOES SOUND DIFFICULTY DETER LEARNERS?  (n = {n} languages with L2 data)")
    print("=" * 74)
    print(f"{'relationship':<52} {'r':>7} {'t':>7}")
    for label, r in [
        ("inventory rarity  ~  log10(L2 speakers)", r_rl),
        ("inventory rarity  ~  inventory size", r_rs),
        ("inventory size    ~  log10(L2 speakers)", r_sl),
        ("lingua-franca     ~  log10(L2 speakers)", r_lfl),
        ("lingua-franca     ~  inventory rarity", r_lfr),
    ]:
        print(f"{label:<52} {r:>+7.3f} {t_stat(r, n):>+7.2f}")
    print(f"\nspearman (rank) rarity ~ L2: {spearman(rarity, l2):+.3f} "
          f"(guards against outlier leverage)")
    print(f"|t| > {2.07:.2f} on {n-2} df is roughly p < 0.05")

    print("\n" + "-" * 74)
    print("CONTROLLING FOR CONFOUNDS (partial correlations)")
    print("-" * 74)
    p_size = partial(r_rl, r_rs, r_sl)
    p_lf = partial(r_rl, r_lfr, r_lfl)
    print(f"rarity ~ L2, holding inventory SIZE constant        : {p_size:+.3f}")
    print(f"rarity ~ L2, holding LINGUA-FRANCA status constant  : {p_lf:+.3f}")
    print(f"size   ~ L2, holding rarity constant                : "
          f"{partial(r_sl, r_rs, r_rl):+.3f}")

    # Read every figure from the computed values. These were hardcoded as +0.56
    # and 0.88, which silently went stale the moment the rarity metric was fixed.
    print(f"\nREADING: the raw {r_rl:+.2f} looks like 'rarer sounds attract learners',")
    print(f"but rarity and inventory size are {r_rs:.2f} correlated -- a language with")
    print("more sounds necessarily has more unusual ones. Hold size constant and")
    print(f"the effect collapses to {p_size:+.3f}. Meanwhile lingua-franca status")
    print(f"predicts learners at {r_lfl:+.3f} while being uncorrelated with rarity")
    print(f"({r_lfr:+.3f}). Learner numbers track history, not phonetics.")
    print("\nAnd none of this sees tone: the rarity axis is segmental only, so the")
    print("tonal languages on the roster carry contrasts it cannot measure.")

    print("\n" + "-" * 74)
    print("LINGUA FRANCA vs NOT — median learners")
    print("-" * 74)
    for flag, label in ((1.0, "lingua franca"), (0.0, "not")):
        grp = sorted(d["l2"] for (nm, d), f in zip(rows, lf) if f == flag)
        med = grp[len(grp) // 2]
        print(f"{label:<16} n={len(grp):<3} median L2 {med:>6.0f}M   "
              f"range {grp[0]:.0f}–{grp[-1]:.0f}M")

    out = {
        "n": n,
        # Stated in the payload so the page's axis label and caveats are driven by
        # the same source as the numbers.
        "rarityUnit": "single segments only (diphthongs, clusters and tone excluded)",
        "sizeUnit": "count of single segments",
        "rarityVsL2": round(r_rl, 4),
        "raritySpearman": round(spearman(rarity, l2), 4),
        "rarityVsSize": round(r_rs, 4),
        "sizeVsL2": round(r_sl, 4),
        "linguaFrancaVsL2": round(r_lfl, 4),
        "linguaFrancaVsRarity": round(r_lfr, 4),
        "partialRarityGivenSize": round(p_size, 4),
        "partialRarityGivenLingua": round(p_lf, 4),
        "tRarityVsL2": round(t_stat(r_rl, n), 3),
        "linguaFranca": sorted(LINGUA_FRANCA),
    }
    with open("l2_drivers.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nwrote l2_drivers.json")


if __name__ == "__main__":
    main()
