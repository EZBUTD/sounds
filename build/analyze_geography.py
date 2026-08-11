#!/usr/bin/env python3
"""
World-map layer: where these languages are spoken, who learns them, and which
of their sounds are globally rare.

Three questions:
  1. WHERE — Glottolog coordinates + macroarea per language (homeland anchor).
  2. WHO LEARNS IT — L1 vs L2 speaker counts (Ethnologue via Wikipedia). The
     surprise: for several of these languages most speakers are LEARNERS.
  3. WHAT'S RARE — for each language, which of its sounds are unusual worldwide.

RARITY METRIC
  Computed over all 3,020 PHOIBLE inventories, deduplicated to one inventory per
  Glottocode so that heavily-documented languages (English has ~10 inventories)
  don't distort the global frequency. A sound's rarity = share of the world's
  languages that lack it. /m/ is in ~96% of languages (rarity ~0.04); the click
  /ǃ/ is in under 2% (rarity >0.98).

  A language's SIGNATURE SOUNDS = its phonemes ranked by global rarity. This
  also answers the backlog's "rarity-weighted overlap" item: sharing /m/ is
  trivial, sharing /ɬ/ is remarkable, so overlap is recomputed with each shared
  sound weighted by its rarity.

CAVEATS
  - A language is not a point. Glottolog gives one representative coordinate per
    language (roughly the historical center of the speech community). Fine for
    Zulu, badly misleading for English. Used only as a homeland marker; L2 reach
    is shown as a separate magnitude, never as territory.
  - PHOIBLE's 2,177 languages are a sample, not a census, and documentation is
    geographically uneven, so global frequencies are estimates. Dedup by
    Glottocode reduces but does not remove this bias.
  - Speaker counts are Ethnologue estimates via Wikipedia and are contested for
    languages where L1/L2 status is politically loaded (notably MSA, which is
    listed with ~0 L1 speakers because it is nobody's home register).
"""
import csv
import json
import unicodedata
from collections import defaultdict

from build_chart_data import LANG_INVENTORIES, norm

PHOIBLE = "data/phoible.csv"
GLOTTO = "data/glottolog_languages.csv"
SPEAKERS = "data/speakers_ethnologue.json"
TONE_CHARS = set("˥˦˧˨˩")
VOWEL_CHARS = set("iyɨʉɯuɪʏʊeøɘɵɤoəɛœɜɞʌɔæɐaɶɑɒ")
CLICK_CHARS = set("ʘǀǃǂǁ")

# Multi-character symbols that ARE single speech sounds, not sequences:
# affricates, co-articulated stops, prenasalized stops. Anything else with more
# than one character is treated as a cluster/diphthong and kept out of the
# "signature sound" ranking (see is_single_segment).
TRUE_MULTICHAR = {
    "ts", "dz", "tʃ", "dʒ", "tɕ", "dʑ", "tʂ", "dʐ", "pf", "kx", "cç",
    "ɡb", "kp", "ŋm",
}


def is_single_segment(sym: str) -> bool:
    """True if `sym` plausibly denotes ONE sound.

    Rarity is only meaningful for comparable units. PHOIBLE sources disagree
    about whether to list diphthongs and clusters as segments at all, so a
    diphthong like /əʊ/ scores as "0% of the world's languages" when the real
    story is that almost no source transcribes it that way. Excluding these
    keeps "signature sounds" about genuine articulatory rarity (clicks,
    pharyngeals, implosives) instead of transcription convention.
    """
    if len(sym) == 1:
        return True
    if sym in TRUE_MULTICHAR:
        return True
    if any(c in CLICK_CHARS for c in sym):
        return True          # PHOIBLE writes Zulu clicks as clusters (kǀ, kǁ)
    return False

# our display name -> the name used in the Wikipedia/Ethnologue speaker table
SPEAKER_NAME = {
    "Arabic (MSA)": "Modern Standard Arabic", "Mandarin Chinese": "Mandarin Chinese",
    "Cantonese": "Yue Chinese", "Punjabi": "Western Punjabi", "Zulu": "Zulu",
}
# PHOIBLE glottocodes are per-inventory; pin the language-level code we want
# where the inventory's own code is a dialect or is missing.
GLOTTO_PIN = {
    "English": "stan1293", "Mandarin Chinese": "mand1415", "Spanish": "stan1288",
    "Arabic (MSA)": "stan1318", "Hindi": "hind1269", "Bengali": "beng1280",
    "Portuguese": "port1283", "Russian": "russ1263", "Japanese": "nucl1643",
    "German": "stan1295", "Korean": "kore1280", "French": "stan1290",
    "Turkish": "nucl1301", "Vietnamese": "viet1252", "Italian": "ital1282",
    "Thai": "thai1261", "Polish": "poli1260", "Ukrainian": "ukra1253",
    "Persian": "west2369", "Punjabi": "east2295", "Swahili": "swah1253",
    "Tagalog": "taga1270", "Dutch": "dutc1256", "Greek": "mode1248",
    "Hebrew": "hebr1245", "Amharic": "amha1245", "Hausa": "haus1257",
    "Marathi": "mara1378", "Yoruba": "yoru1245", "Zulu": "zulu1248",
    "Telugu": "telu1262", "Tamil": "tami1289", "Cantonese": "yuec1235",
    "Indonesian": "indo1316",
}

# Homeland anchor overrides. Glottolog's coordinate is the historical center of
# a speech community, which for widely-transplanted languages points somewhere
# unhelpful (its English entry sits in the Netherlands region of the
# West-Germanic dialect continuum). For those we pin the conventional homeland
# and say plainly on the page that this marker is a simplification.
GEO_OVERRIDE = {
    "English": (52.0, -1.5, "Eurasia"),        # England
    "Spanish": (40.0, -4.0, "Eurasia"),        # central Spain
    "Portuguese": (39.5, -8.0, "Eurasia"),     # Portugal
    "Arabic (MSA)": (24.0, 45.0, "Eurasia"),   # Arabian peninsula
    "French": (47.0, 2.5, "Eurasia"),
}


def load_phoible():
    rows_by_inv = defaultdict(list)
    inv_glotto = {}
    for r in csv.DictReader(open(PHOIBLE, encoding="utf-8")):
        rows_by_inv[r["InventoryID"]].append(r)
        inv_glotto[r["InventoryID"]] = r["Glottocode"]
    return rows_by_inv, inv_glotto


def global_frequencies(rows_by_inv, inv_glotto):
    """base symbol -> share of world languages having it (dedup by Glottocode).

    CLICKS need special handling. PHOIBLE writes them as clusters with their
    accompaniment (Zulu has kǀ, kǁ, kǃ -- never a bare ǀ), but the chart credits
    the BARE click symbol to a language via substring match, so a chart chip
    labelled "ǀ" would find no frequency entry and silently render as "rarity
    unknown" -- i.e. visually unremarkable, when clicks are in fact among the
    rarest sounds on the chart (each under 1% of the world's languages).
    So bare click symbols get their own entry counted by substring, matching how
    the chart credits them.
    """
    # one inventory per glottocode: prefer the largest (best documented)
    best = {}
    for inv, rows in rows_by_inv.items():
        g = inv_glotto.get(inv) or f"_noglotto_{inv}"
        if g not in best or len(rows) > len(rows_by_inv[best[g]]):
            best[g] = inv
    counts = defaultdict(int)
    for g, inv in best.items():
        syms = set()
        raw = []
        for r in rows_by_inv[inv]:
            seg = r["Phoneme"]
            if any(c in seg for c in TONE_CHARS):
                continue
            raw.append(seg)
            s = norm(seg)
            if s:
                syms.add(s)
        # credit the bare click if it appears inside any segment of this language
        for click in CLICK_CHARS:
            if any(click in seg for seg in raw):
                syms.add(click)
        for s in syms:
            counts[s] += 1
    n = len(best)
    return {s: c / n for s, c in counts.items()}, n


def load_geo():
    geo = {}
    for r in csv.DictReader(open(GLOTTO, encoding="utf-8")):
        if r["Level"] != "language" or not r["Latitude"]:
            continue
        geo[r["Glottocode"]] = {
            "name": r["Name"], "lat": float(r["Latitude"]),
            "lon": float(r["Longitude"]), "macroarea": r["Macroarea"],
            "countries": r["Countries"],
        }
    return geo


def main():
    rows_by_inv, inv_glotto = load_phoible()
    freq, n_world = global_frequencies(rows_by_inv, inv_glotto)
    geo = load_geo()
    speakers = json.load(open(SPEAKERS, encoding="utf-8"))

    print("=" * 78)
    print(f"GLOBAL SOUND FREQUENCY (over {n_world} languages, one per Glottocode)")
    print("=" * 78)
    common = sorted(freq.items(), key=lambda kv: -kv[1])[:10]
    print("most universal: " + ", ".join(f"{s} {v:.0%}" for s, v in common))
    # symbols our 34 languages use. Includes BARE clicks as well as the cluster
    # forms PHOIBLE records, because the chart labels its cells with the bare
    # click -- if this set omits them, they get filtered out of the exported
    # frequencies and the chart shows "rarity unknown" for the rarest sounds on it.
    ours = set()
    for name, inv in LANG_INVENTORIES.items():
        for r in rows_by_inv[inv]:
            seg = r["Phoneme"]
            if any(c in seg for c in TONE_CHARS):
                continue
            s = norm(seg)
            if s:
                ours.add(s)
            for click in CLICK_CHARS:
                if click in seg:
                    ours.add(click)
    rare_ours = sorted((freq.get(s, 0), s) for s in ours
                       if is_single_segment(s))[:12]
    print("rarest single segments among our 34 languages: " +
          ", ".join(f"{s} {v:.1%}" for v, s in rare_ours))
    excluded = sorted((freq.get(s, 0), s) for s in ours
                      if not is_single_segment(s))[:6]
    print("excluded from rarity as clusters/diphthongs (notation artifacts): " +
          ", ".join(f"{s}" for _, s in excluded))

    # ---- per language ----
    out = {}
    missing_geo, missing_sp = [], []
    print("\n" + "=" * 78)
    print("PER LANGUAGE — homeland, speakers, and signature (globally rare) sounds")
    print("=" * 78)
    print(f"{'language':<18} {'area':<14} {'L1':>7} {'L2':>7} {'L2%':>5}  signature sounds")
    for name, inv in LANG_INVENTORIES.items():
        gcode = GLOTTO_PIN.get(name) or inv_glotto.get(inv)
        g = geo.get(gcode)
        if name in GEO_OVERRIDE:
            lat, lon, area = GEO_OVERRIDE[name]
            g = {"lat": lat, "lon": lon, "macroarea": area, "pinned": True}
        if not g:
            missing_geo.append(name)
        sp = speakers.get(SPEAKER_NAME.get(name, name))
        if not sp:
            missing_sp.append(name)

        syms = set()
        for r in rows_by_inv[inv]:
            s = norm(r["Phoneme"])
            if s and not any(c in TONE_CHARS for c in s):
                syms.add(s)
        # signature = rarest SINGLE segments (diphthongs/clusters excluded, see
        # is_single_segment) so this measures articulatory rarity, not notation
        sig_pool = [s for s in syms if is_single_segment(s)]
        ranked = sorted(sig_pool, key=lambda s: freq.get(s, 0))
        sig = [{"sym": s, "worldShare": round(freq.get(s, 0), 4),
                "isVowel": s[0] in VOWEL_CHARS} for s in ranked[:6]]

        out[name] = {
            "lat": g["lat"] if g else None, "lon": g["lon"] if g else None,
            "macroarea": g["macroarea"] if g else None,
            "pinnedHomeland": bool(g and g.get("pinned")),
            "glottocode": gcode,
            "l1": sp["l1"] if sp else None, "l2": sp["l2"] if sp else None,
            "total": sp["total"] if sp else None,
            "l2Share": round(sp["l2"] / sp["total"], 4) if sp and sp["total"] else None,
            "signature": sig,
            "nPhonemes": len(syms),
            # Mean rarity of a language's inventory: how unusual it is overall.
            #
            # Scored over SINGLE SEGMENTS ONLY, the same `sig_pool` the signature
            # ranking uses. An earlier version scored every symbol, which made
            # this metric substantially a count of how many diphthongs a source
            # chose to transcribe as units: /ʊə/ appears in 0.07% of PHOIBLE
            # inventories and /əʊ/ in 0.17%, not because those glides are rare
            # but because almost nobody writes them as one phoneme. That put
            # English 2nd of 34 on the "how unusual are its sounds" axis, and
            # correlated the axis with diphthong count at r = +0.66. On single
            # segments that drops to +0.13 and English sits 4th, effectively
            # tied with Zulu and Telugu.
            #
            # This is the SAME artifact `is_single_segment` was written to fix.
            # The guard was applied to the signature ranking and not here, so
            # one consumer of `freq` was corrected and the other was not. Both
            # now share `sig_pool`; audit_coverage.py asserts they agree.
            "meanRarity": round(
                sum(1 - freq.get(s, 0) for s in sig_pool) / len(sig_pool), 4),
            # kept so the size confound can be measured on the same unit as the
            # rarity score rather than against a count that includes diphthongs
            "nSingleSegments": len(sig_pool),
            "nMultiSegment": len(syms) - len(sig_pool),
        }
        l1 = f"{sp['l1']:.0f}M" if sp else "—"
        l2 = f"{sp['l2']:.0f}M" if sp else "—"
        l2p = f"{out[name]['l2Share']:.0%}" if out[name]["l2Share"] is not None else "—"
        print(f"{name:<18} {(g['macroarea'] if g else '?'):<14} {l1:>7} {l2:>7} {l2p:>5}  "
              + " ".join(f"{d['sym']}({d['worldShare']:.0%})" for d in sig[:4]))

    if missing_geo:
        print(f"\nWARNING no coordinates: {missing_geo}")
    if missing_sp:
        print(f"WARNING no speaker data: {missing_sp}")

    # ---- L2 story ----
    print("\n" + "=" * 78)
    print("LEARNED MORE THAN INHERITED (L2 share of total speakers)")
    print("=" * 78)
    wl = [(d["l2Share"], n, d) for n, d in out.items() if d["l2Share"] is not None]
    for s, n, d in sorted(wl, reverse=True)[:10]:
        print(f"{n:<20} {s:>5.0%} of its {d['total']:.0f}M speakers learned it "
              f"({d['l1']:.0f}M native, {d['l2']:.0f}M learners)")

    # ---- rarity-weighted overlap (backlog item) ----
    print("\n" + "=" * 78)
    print("RARITY-WEIGHTED OVERLAP vs plain overlap")
    print("(sharing /m/ is trivial; sharing a click is remarkable)")
    print("=" * 78)
    sets = {}
    for name, inv in LANG_INVENTORIES.items():
        sets[name] = {s for s in (norm(r["Phoneme"]) for r in rows_by_inv[inv])
                      if s and not any(c in TONE_CHARS for c in s)}
    names = list(sets)
    pairs = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            inter, union = sets[a] & sets[b], sets[a] | sets[b]
            plain = len(inter) / len(union)
            wi = sum(1 - freq.get(s, 0) for s in inter)
            wu = sum(1 - freq.get(s, 0) for s in union)
            pairs.append((a, b, plain, wi / wu if wu else 0))
    # NOTE: weighting can only LOWER the ratio -- every language shares the
    # universal sounds, so down-weighting them shrinks the numerator faster than
    # the union. So the informative signal is the SIZE of the drop, not its sign:
    # a big drop means the overlap was mostly generic sounds; a small drop means
    # the pair genuinely shares unusual ones.
    print(f"{'pair':<40} {'plain':>7} {'weighted':>9} {'drop':>7}")
    print("-- biggest drop: their overlap was almost all universal sounds --")
    for a, b, p, w in sorted(pairs, key=lambda t: t[3] - t[2])[:6]:
        print(f"{a + ' + ' + b:<40} {p:>7.0%} {w:>9.0%} {p - w:>7.0%}")
    print("-- smallest drop: they share genuinely rare sounds, not just easy ones --")
    for a, b, p, w in sorted(pairs, key=lambda t: t[2] - t[3])[:6]:
        print(f"{a + ' + ' + b:<40} {p:>7.0%} {w:>9.0%} {p - w:>7.0%}")

    # ---- reverse hook: English's own sounds are globally unusual ----
    print("\n" + "=" * 78)
    print("IS ENGLISH THE WEIRD ONE? English sounds by global frequency")
    print("=" * 78)
    eng = sets["English"]
    eng_single = sorted((freq.get(s, 0), s) for s in eng if is_single_segment(s))
    print("English's rarest sounds worldwide:")
    for v, s in eng_single[:8]:
        print(f"   /{s}/  in {v:.0%} of the world's languages")
    med_rarity = sorted(out[n]["meanRarity"] for n in out)
    eng_rank = sorted(out, key=lambda n: -out[n]["meanRarity"]).index("English") + 1
    print(f"\nEnglish inventory 'unusualness' rank: {eng_rank} of {len(out)} "
          f"(mean rarity {out['English']['meanRarity']:.2f}, "
          f"roster median {med_rarity[len(med_rarity)//2]:.2f})")
    most_unusual = sorted(out.items(), key=lambda kv: -kv[1]["meanRarity"])[:5]
    print("most unusual inventories on the roster: " +
          ", ".join(f"{n} {d['meanRarity']:.2f}" for n, d in most_unusual))
    print("(scored on single segments only; multi-segment symbols per language: " +
          ", ".join(f"{n} {out[n]['nMultiSegment']}"
                    for n in sorted(out, key=lambda n: -out[n]["nMultiSegment"])[:4])
          + ")")

    # ---- tone: counted separately, and NOT part of any rarity score ----
    # Mandarin and Cantonese carry their contrasts in pitch as much as in
    # segments, and PHOIBLE records tone as its own SegmentClass. Report the
    # split explicitly rather than letting the silence imply tone was included.
    print("\n" + "=" * 78)
    print("TONE — recorded separately by PHOIBLE, excluded from every score here")
    print("=" * 78)
    # Count the RAW phoneme strings: norm() strips tone marks to "" by design, so
    # counting normalised symbols reports 1 for every tonal language.
    tonal = []
    for name, inv in LANG_INVENTORIES.items():
        raw = {r["Phoneme"] for r in rows_by_inv[inv]
               if (r.get("SegmentClass") or "") == "tone"
               or any(c in TONE_CHARS for c in (r["Phoneme"] or ""))}
        if raw:
            tonal.append((name, sorted(raw), out[name]["meanRarity"]))
    print(f"{'language':<18} {'tones':>5}  {'segmental':>9}  tone phonemes as recorded")
    print(f"{'':<18} {'':>5}  {'rarity':>9}")
    for name, raw, rar in sorted(tonal, key=lambda t: -len(t[1])):
        print(f"{name:<18} {len(raw):>5}  {rar:>9.3f}  {' '.join(raw)}")
    print(f"\n{len(tonal)} of {len(LANG_INVENTORIES)} charted languages carry tone "
          f"rows. Every one of those rows is dropped before any figure on the site "
          f"is computed:")
    print("  - the chart grid has no axis for pitch, so tones have nowhere to sit")
    print("  - norm() reduces a tone mark to the empty string, so tone-bearing")
    print("    phonemes collapse onto their segmental base (norm('a˥') -> 'a')")
    print("  - phoneme COUNTS, pairwise overlap, and this rarity score are all")
    print("    computed after that filter, so they are segmental-only figures")
    print("\nConsequences worth stating on the page rather than leaving implicit:")
    ranked_low = sorted(out, key=lambda n: out[n]["meanRarity"])
    cant_rank = ranked_low.index("Cantonese") + 1
    print(f"  - Cantonese is {cant_rank}nd-least-unusual of {len(out)} "
          f"({out['Cantonese']['meanRarity']:.2f}) while carrying six lexical tones\n"
          f"    English has no equivalent for. Its low score is a fact about its "
          f"consonants\n    and vowels, not a statement about difficulty.")
    print(f"  - Thai is {ranked_low.index('Thai') + 1}th-least-unusual "
          f"({out['Thai']['meanRarity']:.2f}) with five tones. Mandarin sits higher "
          f"({out['Mandarin Chinese']['meanRarity']:.2f}),\n    but for its retroflex "
          f"and alveolo-palatal series rather than for anything tonal.")
    # Coverage gap, reported rather than silently absorbed: Yoruba is a
    # well-described three-tone language, and the inventory we chart lists none.
    no_tone_rows = [n for n in ("Yoruba", "Japanese")
                    if n in LANG_INVENTORIES and not any(
                        (r.get("SegmentClass") or "") == "tone"
                        for r in rows_by_inv[LANG_INVENTORIES[n]])]
    if no_tone_rows:
        print("  - Coverage is uneven even for tone itself: " +
              ", ".join(no_tone_rows) + " have no tone rows in the charted "
              "inventory.\n    Yoruba is a three-tone language, so that is a gap in "
              "the source, not a\n    property of the language. Japanese pitch accent "
              "is lexical too and is\n    not recorded as tone by PHOIBLE at all.")

    # Tone shipped as data so the page can name the tonal languages and their
    # tone counts without hardcoding either. `nTones` is the count of raw
    # tone-class rows in the charted inventory; `noToneRows` names languages that
    # are described as tonal in the literature but have none recorded here, so a
    # reader is not left to infer the absence means "not tonal".
    tone_out = {name: {"nTones": len(raw), "tones": raw,
                       "meanRarity": rar}
                for name, raw, rar in tonal}

    payload = {
        "worldLanguageCount": n_world,
        "rarityUnit": "single segments only; multi-segment symbols "
                      "(diphthongs, clusters) and tone are excluded",
        "tone": {
            "languages": tone_out,
            "nTonal": len(tone_out),
            "nCharted": len(LANG_INVENTORIES),
            "excludedFromAllMetrics": True,
            "noToneRows": no_tone_rows,
        },
        "englishRarest": [{"sym": s, "worldShare": round(v, 4)}
                          for v, s in eng_single[:10]],
        "languages": out,
        "globalFreq": {s: round(v, 5) for s, v in freq.items()
                       if s in ours},   # only symbols our languages use
        "weightedPairs": {f"{a}|{b}": {"plain": round(p, 4), "weighted": round(w, 4)}
                          for a, b, p, w in pairs},
    }
    with open("geo_analysis.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f"\nwrote geo_analysis.json "
          f"({len(out)} languages, {len(pairs)} weighted pairs)")


if __name__ == "__main__":
    main()
