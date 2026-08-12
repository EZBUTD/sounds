#!/usr/bin/env python3
"""
Build docs/data.js for the full IPA-style interactive visual.

Design (v3): the IPA chart supplies reference-phone cells; every language
projects its selected phoneme inventory onto those cells. Two selectable
languages -> pair states computed client-side:
  BOTH / L1-only / L2-only / NEITHER (+ "variant" badge when a language has
  the sound only as an allophone).

Data emitted:
  - consonant table layout (place x manner, voiceless/voiced pairs, impossible cells)
  - vowel trapezoid coords
  - other-symbols sections (co-articulated, affricates, clicks & implosives)
  - per-language source inventories, broad comparison groups, projected chart
    cells, allophone cells, and source segments represented by each chart cell
  - audio file per symbol (from audio_manifest.csv) + articulatory names
  - English anchor words + hand-written stories
"""
import csv
import json
import os
import unicodedata
from collections import defaultdict

PHOIBLE = "data/phoible.csv"

# Inventory selection (see select_inventories.py): among a language's PHOIBLE
# inventories, prefer allophone-bearing ones, then pick the one whose
# length-collapsed phoneme count is closest to the median of all candidates.
# This is a repeatable source-selection rule, not evidence that the chosen
# doculect is the language's single "typical" analysis. It fixes Italian (was a
# 70-phoneme diphthong-splitting analysis -> now 30, matching textbooks),
# Spanish (38->25), Korean (40->32), Japanese (27->21), French, Greek.
# EXCEPTION — English pinned to EA RP inv 2252 (44): matches the famous
# "44 phonemes" figure and uses standard transcription; the median rule would
# pick SPA inv 160 whose vowel symbols (e̞ o̞ː ɐ) are nonstandard on the chart.
LANG_INVENTORIES = {
    "English": "2252",   # pinned (see above)
    "Mandarin Chinese": "16", "Hindi": "2190", "Spanish": "164", "French": "2182",
    # ROSTER NOTE (audit_roster.py): Egyptian Arabic and Urdu REMOVED.
    # Both were register-pairs of kept languages (MSA / Hindi-Hindustani),
    # were each other's #1 percentile neighbor (distorting the dist panel),
    # and confused counts. Kept: Arabic (MSA), Hindi.
    # Mandarin+Cantonese and Russian+Ukrainian KEPT: distinct languages.
    "Arabic (MSA)": "2157", "Bengali": "2162",
    "Russian": "166", "Portuguese": "163", "Indonesian": "1144", "German": "2184",
    "Japanese": "2196", "Telugu": "8", "Turkish": "186", "Tamil": "1058",
    "Cantonese": "19", "Vietnamese": "2233", "Korean": "1", "Italian": "1145",
    "Thai": "2215", "Polish": "1046", "Ukrainian": "1035", "Persian": "172",
    "Punjabi": "175", "Swahili": "823", "Tagalog": "37", "Dutch": "2173",
    "Greek": "170", "Hebrew": "135", "Amharic": "2156", "Hausa": "2188",
    "Marathi": "1766", "Yoruba": "636",
    # Zulu: clicks! great "sounds not in English" story
    "Zulu": "147",
}

# English's allophones from PHOIBLE inventory 160 are deliberately not imported
# into this chart. Inv 160 documents variants for 68% of its phonemes, but it is
# a different inventory analysis from the RP inventory used here. Earlier code
# also exposed a normalization bug by turning `ç` into the palatal stop `c`; exact
# chart-symbol matching now prevents that error everywhere.
#   - 96 of the inventory's 121 allophone entries simply restate their own
#     phoneme, and counting those as variants added /x/, /ʍ/, /ʔ/ and /ɐ/.
#   - `ɪi` and `ʊu` are two-segment sequences with no single chart cell.
# Each is fixable, but the chart's job is phoneme comparison; per-language variant
# realisation is the Allophones page's job, and that page already uses inv 160
# with the transcriptions written out longhand where they render legibly.
# The "*" marker was removed from the picker instead (see index.html), since what
# it actually flagged — one inventory's missing column — is not a fact about the
# language and was being read as one.

# ---------------- IPA chart layout (2020 revision, pulmonic) ----------------
PLACES = ["Bilabial", "Labiodental", "Dental", "Alveolar", "Postalveolar",
          "Retroflex", "Palatal", "Velar", "Uvular", "Pharyngeal", "Glottal"]
MANNERS = ["Plosive", "Nasal", "Trill", "Tap or Flap", "Fricative",
           "Lateral fricative", "Approximant", "Lateral approximant"]

# cells[manner][place] = (voiceless, voiced); None = no symbol; "X" = impossible
C = {m: {p: None for p in PLACES} for m in MANNERS}
C["Plosive"].update({"Bilabial": ("p", "b"), "Alveolar": ("t", "d"),
                     "Retroflex": ("ʈ", "ɖ"), "Palatal": ("c", "ɟ"),
                     "Velar": ("k", "ɡ"), "Uvular": ("q", "ɢ"),
                     "Glottal": ("ʔ", None)})
C["Nasal"].update({"Bilabial": (None, "m"), "Labiodental": (None, "ɱ"),
                   "Alveolar": (None, "n"), "Retroflex": (None, "ɳ"),
                   "Palatal": (None, "ɲ"), "Velar": (None, "ŋ"), "Uvular": (None, "ɴ")})
C["Trill"].update({"Bilabial": (None, "ʙ"), "Alveolar": (None, "r"), "Uvular": (None, "ʀ")})
C["Tap or Flap"].update({"Labiodental": (None, "ⱱ"), "Alveolar": (None, "ɾ"),
                         "Retroflex": (None, "ɽ")})
C["Fricative"].update({"Bilabial": ("ɸ", "β"), "Labiodental": ("f", "v"),
                       "Dental": ("θ", "ð"), "Alveolar": ("s", "z"),
                       "Postalveolar": ("ʃ", "ʒ"), "Retroflex": ("ʂ", "ʐ"),
                       "Palatal": ("ç", "ʝ"), "Velar": ("x", "ɣ"),
                       "Uvular": ("χ", "ʁ"), "Pharyngeal": ("ħ", "ʕ"),
                       "Glottal": ("h", "ɦ")})
C["Lateral fricative"].update({"Alveolar": ("ɬ", "ɮ")})
C["Approximant"].update({"Labiodental": (None, "ʋ"), "Alveolar": (None, "ɹ"),
                         "Retroflex": (None, "ɻ"), "Palatal": (None, "j"),
                         "Velar": (None, "ɰ")})
C["Lateral approximant"].update({"Alveolar": (None, "l"), "Retroflex": (None, "ɭ"),
                                 "Palatal": (None, "ʎ"), "Velar": (None, "ʟ")})

IMPOSSIBLE = [  # shaded on the official chart
    ("Plosive", "Pharyngeal"), ("Nasal", "Pharyngeal"), ("Nasal", "Glottal"),
    ("Trill", "Pharyngeal"), ("Trill", "Glottal"), ("Tap or Flap", "Glottal"),
    ("Lateral fricative", "Bilabial"), ("Lateral fricative", "Labiodental"),
    ("Lateral fricative", "Pharyngeal"), ("Lateral fricative", "Glottal"),
    ("Approximant", "Pharyngeal"), ("Approximant", "Glottal"),
    ("Lateral approximant", "Bilabial"), ("Lateral approximant", "Labiodental"),
    ("Lateral approximant", "Pharyngeal"), ("Lateral approximant", "Glottal"),
]

OTHER_SECTIONS = [
    ("Other symbols", ["w", "ʍ", "ɥ", "ɕ", "ʑ", "ɺ"]),
    ("Affricates", ["ts", "dz", "tʃ", "dʒ", "tɕ", "dʑ"]),
    ("Clicks & implosives", ["ʘ", "ǀ", "ǃ", "ǂ", "ǁ", "ɓ", "ɗ", "ʄ", "ɠ", "ʛ"]),
]

VOWELS = [  # (symbol, x%, y%) on the trapezoid
    ("i", 8, 5), ("y", 16, 5), ("ɨ", 42, 5), ("ʉ", 50, 5), ("ɯ", 74, 5), ("u", 82, 5),
    ("ɪ", 22, 18), ("ʏ", 30, 18), ("ʊ", 68, 18),
    ("e", 16, 32), ("ø", 24, 32), ("ɘ", 46, 32), ("ɵ", 54, 32), ("ɤ", 74, 32), ("o", 82, 32),
    ("ə", 50, 45),
    ("ɛ", 24, 58), ("œ", 32, 58), ("ɜ", 48, 58), ("ɞ", 56, 58), ("ʌ", 74, 58), ("ɔ", 82, 58),
    ("æ", 30, 71), ("ɐ", 52, 71),
    ("a", 34, 84), ("ɶ", 42, 84), ("ɑ", 74, 84), ("ɒ", 82, 84),
]

# English anchor words (base-normalized symbols only where English has the sound)
EXAMPLES = {
    "p": "pen", "b": "bad", "t": "tea", "d": "dog", "k": "cat", "ɡ": "go",
    "tʃ": "chair", "dʒ": "jump", "f": "fan", "v": "van", "θ": "think", "ð": "this",
    "s": "sun", "z": "zoo", "ʃ": "ship", "ʒ": "vision", "h": "hat",
    "m": "man", "n": "no", "ŋ": "sing", "l": "leg", "ɹ": "red", "j": "yes", "w": "wet",
    "i": "see", "ɪ": "sit", "e": "bed", "æ": "cat", "ɑ": "father", "ɒ": "hot",
    "ɔ": "law", "ʊ": "put", "u": "food", "ʌ": "cup", "ɜ": "bird", "ə": "about",
    "aɪ": "my", "aʊ": "now", "eɪ": "day", "əʊ": "go", "ɔɪ": "boy",
    "ɪə": "ear", "eə": "hair", "ʊə": "tour",
}

# Plain-language definitions for chart terminology (hover tooltips)
GLOSSARY = {
    # places of articulation (columns) — where in the mouth
    "Bilabial": "Made with both lips pressed together — like p, b, m.",
    "Labiodental": "Lower lip against the upper teeth — like f, v.",
    "Dental": "Tongue tip against the teeth — like th.",
    "Alveolar": "Tongue against the ridge just behind the upper teeth — like t, d, s, n.",
    "Postalveolar": "Tongue just behind that ridge — like sh.",
    "Retroflex": "Tongue tip curled up and back — common in Hindi and other South Asian languages.",
    "Palatal": "Middle of the tongue against the roof of the mouth — like the y in 'yes'.",
    "Velar": "Back of the tongue against the soft rear roof of the mouth — like k, g.",
    "Uvular": "Very back of the tongue, near the dangling uvula — like the French r.",
    "Pharyngeal": "Squeezed in the throat itself — famous in Arabic.",
    "Glottal": "Made at the vocal folds — like h, or the catch in 'uh-oh'.",
    # manners (rows) — how the air moves
    "Plosive": "Block the air completely, then release it with a little pop — p, t, k, b, d, g.",
    "Nasal": "Air flows out through the nose — m, n, ng.",
    "Trill": "A part of the mouth vibrates rapidly — the rolled r of Spanish 'perro'.",
    "Tap or Flap": "One single quick tap of the tongue — the r in Spanish 'pero', or the tt in American 'butter'.",
    "Fricative": "Squeeze air through a narrow gap so it hisses — f, s, sh, th.",
    "Lateral fricative": "Hiss the air over the sides of the tongue — the Welsh ll, Zulu hl.",
    "Approximant": "Narrow the mouth, but not enough to hiss — w, y, the English r.",
    "Lateral approximant": "Air flows smoothly around the sides of the tongue — l.",
    # vowel axes
    "Close": "Mouth nearly closed, tongue high — the 'ee' position.",
    "Close-mid": "Tongue fairly high — like the vowel in 'day' (first half).",
    "Open-mid": "Tongue fairly low — like the vowel in 'bed'.",
    "Open": "Mouth wide open, tongue low — the 'ah' position.",
    "Front": "The tongue's high point is toward the front of the mouth ('ee').",
    "Central": "The tongue's high point is in the middle — like the lazy 'uh' of 'about'.",
    "Back": "The tongue's high point is toward the back ('oo').",
    # other sections
    "Other symbols": "A selection from the IPA's Other Symbols panel. Some are co-articulated (w, ʍ, ɥ); ɕ and ʑ are alveolo-palatal fricatives, and ɺ is a lateral flap.",
    "Affricates": "A stop and a hiss glued together — like ch (t + sh) or j (d + zh).",
    "Clicks & implosives": "Clicks use a tongue-made pressure pocket; implosives combine an oral closure with a lowering glottis. They are ordinary consonants in languages such as Zulu.",
    "Consonants": "Sounds made by obstructing airflow somewhere in the mouth. Columns = where; rows = how.",
    "Vowels": "Sounds made with an open mouth. Position on the chart = where your tongue sits.",
}

# Hand-curated example words in the languages themselves (spotlight set).
# Key: "Language|symbol" -> "word (romanization) 'meaning'".
# Sources: standard dictionaries / phonology references; verify before publish.
EXAMPLES_BY_LANG = {
    # Japanese
    "Japanese|ɸ": "富士 (Fuji) — the mountain",
    "Japanese|ɾ": "から (kara) 'from'",
    "Japanese|ts": "つなみ (tsunami)",
    "Japanese|k": "川 (kawa) 'river'",
    "Japanese|s": "酒 (sake) 'rice wine'",
    "Japanese|ɯ": "海 (umi) 'sea'",
    "Japanese|o": "音 (oto) 'sound'",
    "Japanese|a": "朝 (asa) 'morning'",
    "Japanese|i": "犬 (inu) 'dog'",
    "Japanese|e": "円 (en) 'yen'",
    # Spanish
    "Spanish|r": "perro 'dog' — the rolled r",
    "Spanish|ɾ": "pero 'but' — single tap; perro/pero differ only here!",
    "Spanish|ð": "nada 'nothing'",
    "Spanish|β": "cabo 'cape'",
    "Spanish|ɣ": "lago 'lake'",
    "Spanish|x": "jamón 'ham'",
    "Spanish|ɲ": "niño 'child'",
    "Spanish|tʃ": "chico 'boy'",
    # French
    "French|ʁ": "rouge 'red'",
    "French|y": "tu 'you'",
    "French|ø": "peu 'few'",
    "French|œ": "sœur 'sister'",
    "French|ɥ": "huit 'eight'",
    "French|ɲ": "agneau 'lamb'",
    "French|ʒ": "jour 'day'",
    # German
    "German|x": "Bach — the composer",
    "German|ç": "ich 'I' — the soft ch",
    "German|ʁ": "rot 'red'",
    "German|y": "über 'over'",
    "German|ø": "schön 'beautiful'",
    # Mandarin
    "Mandarin Chinese|χ": "好 (hǎo) 'good'",
    "Mandarin Chinese|ʂ": "山 (shān) 'mountain'",
    "Mandarin Chinese|ʐ": "日 (rì) 'sun'",
    "Mandarin Chinese|y": "鱼 (yú) 'fish'",
    "Mandarin Chinese|ɤ": "喝 (hē) 'to drink'",
    # Korean
    "Korean|ɾ": "사람 (saram) 'person'",
    "Korean|tʃ": "자 (ja) 'sleep'",
    "Korean|ɯ": "은 (eun) — topic particle",
    # Russian
    "Russian|x": "хорошо (khorosho) 'good'",
    "Russian|r": "рука (ruka) 'hand'",
    "Russian|ɨ": "ты (ty) 'you'",
    "Russian|ʒ": "жук (zhuk) 'beetle'",
    "Russian|ʃ": "шум (shum) 'noise'",
    "Russian|ts": "цирк (tsirk) 'circus'",
    # Arabic (MSA)
    "Arabic (MSA)|ħ": "حال (ḥāl) 'condition'",
    "Arabic (MSA)|ʕ": "عين (ʿayn) 'eye'",
    "Arabic (MSA)|q": "قلب (qalb) 'heart'",
    "Arabic (MSA)|ɣ": "غرب (gharb) 'west'",
    # Hindi
    "Hindi|ʈ": "टमाटर (ṭamāṭar) 'tomato'",
    "Hindi|ɖ": "डर (ḍar) 'fear'",
    "Hindi|ɳ": "बाण (bāṇ) 'arrow'",
    # Zulu
    "Zulu|ǀ": "icici 'earring' — the c is a dental click",
    "Zulu|ǃ": "iqanda 'egg' — the q is a loud click",
    "Zulu|ǁ": "ixoxo 'frog' — the x is a side click",
    "Zulu|ɓ": "ubaba 'father' — a gulped b",
    "Zulu|ɬ": "hlala 'sit' — the famous hl",
    # Italian
    "Italian|ʎ": "figlio 'son'",
    "Italian|ɲ": "gnocchi",
    "Italian|ts": "pizza",
    "Italian|dz": "zero",
    "Italian|tʃ": "ciao",
    # Portuguese
    "Portuguese|ʀ": "rio 'river' — trilled in this variety",
    "Portuguese|ɲ": "banho 'bath'",
    "Portuguese|ʎ": "filho 'son'",
    "Portuguese|ʃ": "chá 'tea'",
}

STORIES = {
    "Japanese|f": "Japanese /h/ is often pronounced [ɸ] before /ɯ/. English loanwords are reshaped by several Japanese sound patterns, which can make 'food' and 'hood' converge as fūdo.",
    "Japanese|l": "English /l/ and /r/ are often adapted toward the Japanese tap /ɾ/ in loanwords. That is a language pattern, not a claim that individual listeners cannot hear a difference.",
    "Japanese|ɹ": "English /l/ and /r/ are often adapted toward the Japanese tap /ɾ/ in loanwords. That is a language pattern, not a claim that individual listeners cannot hear a difference.",
    "Japanese|θ": "English /θ/ is often adapted toward /s/ in Japanese loanwords. Individual learners' pronunciations vary.",
    "Japanese|ð": "English /ð/ is often adapted toward /z/ or /d/ in Japanese loanwords. Individual learners' pronunciations vary.",
    "Spanish|ð": "In many varieties, d can have a [ð]-like pronunciation between vowels, as in nada. Sources differ in how they label the underlying category and its variants.",
    "Spanish|v": "Many Spanish varieties do not use an English-style /b/ versus /v/ contrast, even though both letters occur in spelling.",
    "Korean|f": "English /f/ is often adapted with a Korean p sound in loanwords, as in keopi for 'coffee'. Individual learners can learn a different pronunciation.",
    "French|θ": "Some French-accented English uses /s/ or /f/ where English has /θ/. Individual speakers vary.",
    "French|h": "French usually does not pronounce written h in native words, so English /h/ can be an unfamiliar contrast for some learners.",
    "German|w": "The German letter w usually represents /v/. That spelling difference can shape some learners' first attempts at English w.",
    "Russian|θ": "Some Russian-accented English uses /s/ or /t/ where English has /θ/. Individual speakers vary.",
    "Hindi|θ": "Hindi dental /t̪ʰ/ is made near English /θ/, but it stops the airflow instead of letting it continue.",
    "Mandarin Chinese|v": "The selected source records [v] as a pronunciation variant rather than a separate category. Mandarin varieties and speakers differ.",
    "Zulu|ǃ": "A click — made with the tongue like the 'tsk' or horse-clop sound. Zulu uses clicks as ordinary consonants in everyday words.",
}


TONE_CHARS = set("˥˦˧˨˩")
LENGTH_MARKS = set("ːˑ")
CLICK_SYMBOLS = "ʘǀǃǂǁ"


def comparison_segment(seg: str) -> str:
    """Return the segment used for inventory comparison.

    Length/gemination is deliberately collapsed because the public comparison
    focuses on broad consonant and vowel qualities. This is a display choice,
    not a claim that length is meaningless; it can distinguish words. Every other feature
    written by the selected source is preserved: aspiration, nasalization,
    dentality, breathy voice, palatalization, and so on. NFC keeps precomposed
    IPA bases such as ç intact.
    """
    decomposed = unicodedata.normalize("NFD", seg)
    out = unicodedata.normalize(
        "NFC", "".join(c for c in decomposed if c not in LENGTH_MARKS)
    )
    # Some inventories double the complete segment instead of writing ː.
    if len(out) % 2 == 0 and out[:len(out) // 2] == out[len(out) // 2:]:
        out = out[:len(out) // 2]
    return out


def norm(seg: str) -> str:
    """Project one PHOIBLE segment onto the nearest base chart symbol.

    This is only for coloring the finite chart and attaching reference audio. It
    is not used for overlap. Exact chart symbols are checked first so a base such
    as ç never decomposes into, and gets confused with, the different symbol c.
    """
    seg = comparison_segment(seg)
    if seg in chart_symbols():
        return seg
    decomposed = unicodedata.normalize("NFD", seg)
    out = unicodedata.normalize(
        "NFC",
        "".join(c for c in decomposed
                if unicodedata.category(c) not in ("Mn", "Lm", "Sk")),
    )
    if len(out) % 2 == 0 and out[:len(out) // 2] == out[len(out) // 2:]:
        out = out[:len(out) // 2]
    return out


def merged_examples():
    """Hand-curated EXAMPLES_BY_LANG wins; WikiPron-mined entries fill gaps.
    Mined values are marked so the UI can attribute them to Wiktionary."""
    merged = {}
    if os.path.exists("mined_examples.json"):
        mined = json.load(open("mined_examples.json", encoding="utf-8"))
        for key, m in mined.items():
            merged[key] = {"text": m["word"], "mined": True}
    for key, text in EXAMPLES_BY_LANG.items():
        merged[key] = {"text": text, "mined": False}
    return merged


def chart_symbols():
    syms = set()
    for m in MANNERS:
        for p in PLACES:
            cell = C[m][p]
            if cell:
                syms.update(s for s in cell if s)
    for _, ss in OTHER_SECTIONS:
        syms.update(ss)
    syms.update(v[0] for v in VOWELS)
    return syms


def comparison_key(seg: str, onchart=None) -> str:
    """Return the broad category used for cross-language matching.

    Source transcriptions that project to the same IPA reference square share a
    key. Click clusters such as Zulu kǀ use the bare click square. Entries that
    have no square (for example diphthongs) retain their source label.
    """
    onchart = onchart or chart_symbols()
    base = norm(seg)
    if base in onchart:
        return base
    for click in CLICK_SYMBOLS:
        if click in seg:
            return click
    return seg


def comparison_groups(segments, onchart=None):
    """Group source entries by broad key while retaining source detail."""
    onchart = onchart or chart_symbols()
    groups = defaultdict(set)
    for segment in segments:
        groups[comparison_key(segment, onchart)].add(segment)
    return {key: sorted(values) for key, values in groups.items()}


def broad_pair_metrics(groups_a, groups_b):
    """Count each occupied broad sound area once."""
    occupied_a, occupied_b = set(groups_a), set(groups_b)
    shared = len(occupied_a & occupied_b)
    union = len(occupied_a | occupied_b)
    return shared, (shared / union if union else 0)


def main():
    rows_by_inv = defaultdict(list)
    with open(PHOIBLE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows_by_inv[row["InventoryID"]].append(row)

    onchart = chart_symbols()
    languages = []
    for name, inv_id in LANG_INVENTORIES.items():
        rows = rows_by_inv.get(inv_id)
        if not rows:
            print(f"!! inventory {inv_id} ({name}) not found, skipping")
            continue
        comparison_phonemes, phonemes, allophones = set(), set(), set()
        cell_phonemes = defaultdict(set)
        # Chart cell -> the source phoneme rows that list that phone as an
        # allophone. This lets the UI say "recorded variant of /x/" rather than
        # making the unsupported language-wide claim "exists only as an
        # allophone". PHOIBLE's coverage remains explicitly source-bound.
        allophone_of = defaultdict(set)
        for r in rows:
            raw = r["Phoneme"]
            if any(c in raw for c in TONE_CHARS):
                continue
            exact = comparison_segment(raw)
            comparison_phonemes.add(exact)
            seg = norm(exact)
            if seg:
                phonemes.add(seg)
                if seg in onchart:
                    cell_phonemes[seg].add(exact)
            # PHOIBLE writes clicks as clusters (Zulu kǀ, kǃ...) — credit the bare click
            for c in CLICK_SYMBOLS:
                if c in exact:
                    phonemes.add(c)
                    cell_phonemes[c].add(exact)
            if r["Allophones"] not in ("", "NA"):
                for a in r["Allophones"].split():
                    a_cell = norm(a)
                    if a_cell:
                        allophones.add(a_cell)
                        if a_cell in onchart:
                            allophone_of[a_cell].add(exact)
        has_allo = any(r["Allophones"] not in ("", "NA") for r in rows)

        # A phone already represented by a phoneme row is not marked V even if it
        # also appears in an Allophones cell. Do not supplement from a different
        # inventory: the UI wording deliberately reports only what this selected
        # source records, because allophone coverage varies sharply across sources.
        allophones -= phonemes
        allophone_of = {
            s: sorted(parents) for s, parents in allophone_of.items()
            if s in allophones
        }
        # ---- headline accounting (see SCOPING.md "counting policy") ----
        # PHOIBLE sources differ in whether they list long/geminate consonants
        # (bː kʰː) as separate phonemes. Textbook counts ("Hindi has ~46
        # phonemes") do NOT count length twice. For cross-language consistency
        # the headline uses the LENGTH-COLLAPSED count; the raw source count is
        # reported alongside. Allophones are NEVER included in any count.
        raw_segs = [r["Phoneme"] for r in rows]
        n_tones = sum(1 for s in raw_segs if any(c in TONE_CHARS for c in s))
        nontone = [s for s in raw_segs if not any(c in TONE_CHARS for c in s)]

        length_collapsed = {comparison_segment(s) for s in nontone}
        n_length_variants = len(nontone) - len(length_collapsed)
        # distinctions beyond length that the base cells still merge
        # (aspiration, breathy voice, palatalization...)
        base_set = {norm(s) for s in nontone}
        n_merged = len(length_collapsed) - len(base_set)
        extras = sorted(s for s in comparison_phonemes
                        if norm(s) not in onchart and s)
        modified = sorted(s for s in comparison_phonemes
                          if norm(s) in onchart and s != norm(s))
        broad_groups = comparison_groups(comparison_phonemes, onchart)
        languages.append({
            "name": name,
            "allophoneData": has_allo,
            # Exact, length-collapsed source strings retained for provenance and
            # tooltips. Phoneme categories themselves remain language-specific.
            "comparisonPhonemes": sorted(comparison_phonemes),
            # Source spellings grouped into broad comparison categories. Pair
            # overlap counts an occupied area once, so English pʰ can share /p/
            # with Spanish p. Multiple source distinctions stay in the tooltip
            # as qualitative detail rather than becoming inferred matches.
            "comparisonGroups": broad_groups,
            # Coarse projections used only to light up the fixed chart cells.
            "chartPhonemes": sorted(phonemes & onchart),
            "phonemes": sorted(phonemes & onchart),
            "allophones": sorted(allophones & onchart),
            "allophoneOf": allophone_of,
            "cellPhonemes": {s: sorted(v) for s, v in cell_phonemes.items()},
            "modifiedPhonemes": modified,
            "extras": extras,
            "rawCount": len(raw_segs),
            "soundCount": len(length_collapsed),      # headline number
            "lengthVariantCount": n_length_variants,  # long/doubled forms in source
            "mergedCount": n_merged,                  # aspiration/breathy/etc. merges
            "toneCount": n_tones,
            "tones": n_tones > 0,
            "inventoryId": inv_id,
            "source": rows[0]["Source"],
        })

    # audio manifest (symbol keys are base-normalized by the downloader v2)
    audio = {}
    if os.path.exists("audio_manifest.csv"):
        for r in csv.DictReader(open("audio_manifest.csv", encoding="utf-8")):
            if r.get("file"):
                audio[r["phoneme"]] = {"file": "audio/" + r["file"],
                                       "kind": r.get("audio_kind", "")}

    names = {}  # articulatory names for tooltips (fallback for non-English sounds)
    if os.path.exists("audio_manifest.csv"):
        for r in csv.DictReader(open("audio_manifest.csv", encoding="utf-8")):
            if r.get("commons_file") and r["commons_file"] != "(cached)":
                names[r["phoneme"]] = r["commons_file"].rsplit(".", 1)[0]

    # Pairwise overlap counts each occupied broad IPA area once. A spelling
    # difference alone cannot create an exclusive category; multiple source
    # entries remain available as qualitative detail.
    lang_groups = {l["name"]: l["comparisonGroups"] for l in languages}
    pair_overlap = {}
    lang_names_sorted = sorted(lang_groups)
    for i, a in enumerate(lang_names_sorted):
        for b in lang_names_sorted[i + 1:]:
            shared, jaccard = broad_pair_metrics(lang_groups[a], lang_groups[b])
            pair_overlap[f"{a}|{b}"] = [shared, round(jaccard, 3)]

    data = {
        "places": PLACES, "manners": MANNERS,
        "consonants": {m: {p: (list(C[m][p]) if C[m][p] else None) for p in PLACES} for m in MANNERS},
        "impossible": [[m, p] for m, p in IMPOSSIBLE],
        "otherSections": [{"name": n, "symbols": s} for n, s in OTHER_SECTIONS],
        "vowels": [{"symbol": s, "x": x, "y": y} for s, x, y in VOWELS],
        "languages": languages,
        "audio": audio,
        "names": names,
        "examples": EXAMPLES,
        "examplesByLang": merged_examples(),
        "glossary": GLOSSARY,
        "stories": STORIES,
        "pairOverlap": pair_overlap,  # occupied broad areas -> [shared, jaccard]
    }

    # validate curated example keys map to sounds the language actually has
    lang_lookup = {l["name"]: l for l in languages}
    bad_examples = []
    for key in EXAMPLES_BY_LANG:
        lname, sym = key.split("|")
        L = lang_lookup.get(lname)
        if not L or (sym not in L["phonemes"] and sym not in L["allophones"]
                     and sym not in L["extras"]):
            bad_examples.append(key)
    if bad_examples:
        print("!! EXAMPLES_BY_LANG keys not matching language data:", bad_examples)

    os.makedirs("docs", exist_ok=True)
    with open("docs/data.js", "w", encoding="utf-8") as f:
        f.write("const DATA = ")
        json.dump(data, f, ensure_ascii=False)
        f.write(";\n")

    n_chart = len(onchart)
    eng = next(l for l in languages if l["name"] == "English")
    print(f"data.js: {n_chart} chart symbols, {len(languages)} languages")
    print(f"English on-chart phonemes: {len(eng['phonemes'])}, extras (off-chart, incl diphthongs): {eng['extras']}")
    zulu = next((l for l in languages if l["name"] == "Zulu"), None)
    if zulu:
        clicks = [s for s in zulu["phonemes"] if s in "ʘǀǃǂǁ"]
        print(f"Zulu clicks detected: {clicks}")
    cov = len([s for s in audio if s in onchart])
    print(f"audio coverage: {cov}/{n_chart} chart symbols have audio")


if __name__ == "__main__":
    main()
