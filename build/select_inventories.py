#!/usr/bin/env python3
"""
Systematic inventory selection per language (replaces "most allophone rows"
rule that biased toward maximalist analyses, e.g. Italian 70-phoneme inv).

Rule per language:
  1. Compute each candidate inventory's LENGTH-COLLAPSED phoneme count
     (the textbook-comparable layer from the counting policy).
  2. Prefer inventories WITH allophone data (needed for variant badges).
  3. Among preferred, pick the one closest to the MEDIAN collapsed count of
     all candidates (the "typical" analysis); tie-break = more allophone rows.
Outputs a proposed LANG_INVENTORIES dict + before/after comparison with
sanity checks (Japanese ɸ-variant must survive, Zulu clicks, etc.).
"""
import csv
import statistics
import unicodedata
from collections import defaultdict

TONE_CHARS = set("˥˦˧˨˩")

# language name variants in PHOIBLE per our 36 display names
NAME_MAP = {
    "English": ["english"], "Mandarin Chinese": ["mandarin chinese"],
    "Hindi": ["hindi"], "Spanish": ["spanish"], "French": ["french"],
    "Arabic (MSA)": ["arabic"], "Egyptian Arabic": ["egyptian arabic"],
    "Bengali": ["bengali"], "Russian": ["russian"], "Portuguese": ["portuguese"],
    "Indonesian": ["indonesian"], "German": ["german"], "Japanese": ["japanese"],
    "Telugu": ["telugu"], "Turkish": ["turkish"], "Tamil": ["tamil"],
    "Cantonese": ["cantonese", "yue chinese"], "Vietnamese": ["vietnamese"],
    "Korean": ["korean"], "Italian": ["italian"], "Thai": ["thai"],
    "Polish": ["polish"], "Ukrainian": ["ukrainian"], "Persian": ["persian", "farsi"],
    "Punjabi": ["punjabi", "eastern panjabi"], "Swahili": ["swahili"],
    "Tagalog": ["tagalog"], "Dutch": ["dutch"], "Greek": ["greek", "modern greek"],
    "Hebrew": ["hebrew", "modern hebrew"], "Amharic": ["amharic"],
    "Hausa": ["hausa"], "Urdu": ["urdu"], "Marathi": ["marathi"],
    "Yoruba": ["yoruba"], "Zulu": ["zulu"],
}

OLD = {  # current choices, for comparison
    "English": "2252", "Mandarin Chinese": "16", "Hindi": "2190", "Spanish": "2210",
    "French": "162", "Arabic (MSA)": "2157", "Egyptian Arabic": "132",
    "Bengali": "2162", "Russian": "166", "Portuguese": "163", "Indonesian": "1144",
    "German": "2184", "Japanese": "197", "Telugu": "8", "Turkish": "186",
    "Tamil": "1058", "Cantonese": "19", "Vietnamese": "2233", "Korean": "2197",
    "Italian": "2195", "Thai": "2215", "Polish": "1046", "Ukrainian": "1035",
    "Persian": "172", "Punjabi": "175", "Swahili": "823", "Tagalog": "37",
    "Dutch": "2173", "Greek": "2186", "Hebrew": "135", "Amharic": "2156",
    "Hausa": "2188", "Urdu": "1797", "Marathi": "1766", "Yoruba": "636",
    "Zulu": "147",
}


def collapse(seg):
    s = unicodedata.normalize("NFD", seg)
    out = "".join(c for c in s if c not in "ːˑ")
    return out[0] if len(out) == 2 and out[0] == out[1] else out


def main():
    by_lang_inv = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open("data/phoible.csv", encoding="utf-8")):
        by_lang_inv[r["LanguageName"].lower()][r["InventoryID"]].append(r)

    picks = {}
    print(f"{'language':<18} {'old inv (n)':<14} {'new inv (n)':<14} note")
    for lang, name_keys in NAME_MAP.items():
        cands = []
        for key in name_keys:
            for inv_id, rows in by_lang_inv.get(key, {}).items():
                segs = [r["Phoneme"] for r in rows]
                nontone = [s for s in segs if not any(c in TONE_CHARS for c in s)]
                collapsed = len({collapse(s) for s in nontone})
                has_allo = any(r["Allophones"] not in ("", "NA") for r in rows)
                n_allo = sum(1 for r in rows if r["Allophones"] not in ("", "NA"))
                cands.append((inv_id, collapsed, has_allo, n_allo, rows[0]["Source"]))
        if not cands:
            print(f"{lang:<18} NOT FOUND"); continue
        med = statistics.median(c[1] for c in cands)
        pool = [c for c in cands if c[2]] or cands
        best = min(pool, key=lambda c: (abs(c[1] - med), -c[3]))
        picks[lang] = best[0]
        old_id = OLD[lang]
        old = next((c for c in cands if c[0] == old_id), None)
        note = "unchanged" if best[0] == old_id else \
            f"CHANGED (candidates: {sorted((c[1]) for c in cands)})"
        print(f"{lang:<18} {old_id:>5} ({old[1] if old else '?':>3})    "
              f"{best[0]:>5} ({best[1]:>3})    {note}")

    # sanity checks on new picks
    print("\n=== sanity on new picks ===")
    def inv_rows(inv_id):
        for rows_by_inv in by_lang_inv.values():
            if inv_id in rows_by_inv:
                return rows_by_inv[inv_id]
    ja = inv_rows(picks["Japanese"])
    allo = " ".join(r["Allophones"] for r in ja if r["Allophones"] not in ("", "NA"))
    print(f"Japanese inv {picks['Japanese']}: ɸ in allophones: {'ɸ' in allo}")
    zu = inv_rows(picks["Zulu"])
    print(f"Zulu inv {picks['Zulu']}: clicks in phonemes: "
          f"{any(c in ''.join(r['Phoneme'] for r in zu) for c in 'ǀǃǁʘǂ')}")
    en = inv_rows(picks["English"])
    print(f"English inv {picks['English']}: {len(en)} phonemes")

    print("\nLANG_INVENTORIES = {")
    for lang, inv in picks.items():
        print(f'    "{lang}": "{inv}",')
    print("}")


if __name__ == "__main__":
    main()
