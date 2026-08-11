#!/usr/bin/env python3
"""
Mine example words per (language, phoneme) from WikiPron (CC BY-SA,
github.com/CUNY-CL/wikipron): word + IPA transcription pairs from Wiktionary.

For each language and each of its on-chart base phonemes, pick a real word
whose transcription contains that phoneme. Preference: word-INITIAL sound,
then shortest word (easier for a general audience to hear the target sound).

Output: mined_examples.json {"Lang|symbol": {"word", "ipa", "source"}}.
Hand-curated EXAMPLES_BY_LANG in build_chart_data.py always wins over mined
entries; mined entries fill the gaps. Both flagged as Wiktionary-sourced in
methodology.
"""
import csv
import io
import json
import os
import subprocess
import time
import unicodedata
from collections import defaultdict

from build_chart_data import LANG_INVENTORIES, norm, chart_symbols

# language -> preferred WikiPron file (broad transcription when available;
# filtered = cleaned of loanword oddities, prefer it)
WIKIPRON = {
    "English": "eng_latn_uk_broad_filtered.tsv",
    "Mandarin Chinese": "cmn_hani_standard_broad.tsv",
    "Hindi": "hin_deva_broad_filtered.tsv",
    "Spanish": "spa_latn_ca_broad_filtered.tsv",
    "French": "fra_latn_broad_filtered.tsv",
    "Arabic (MSA)": "ara_arab_broad.tsv",

    "Bengali": "ben_beng_dhaka_broad_filtered.tsv",
    "Russian": "rus_cyrl_narrow.tsv",
    "Portuguese": "por_latn_bz_broad_filtered.tsv",
    "Indonesian": "ind_latn_broad.tsv",
    "German": "deu_latn_broad_filtered.tsv",
    "Japanese": "jpn_hira_narrow_filtered.tsv",
    "Telugu": "tel_telu_broad.tsv",
    "Turkish": "tur_latn_narrow_filtered.tsv",
    "Tamil": "tam_taml_broad.tsv",
    "Cantonese": "yue_hani_standard_broad.tsv",
    "Vietnamese": "vie_latn_hanoi_narrow_filtered.tsv",
    "Korean": "kor_hang_narrow_filtered.tsv",
    "Italian": "ita_latn_broad_filtered.tsv",
    "Thai": "tha_thai_broad.tsv",
    "Polish": "pol_latn_broad.tsv",
    "Ukrainian": "ukr_cyrl_narrow.tsv",
    "Persian": "fas_arab_broad.tsv",
    "Punjabi": "pan_guru_broad.tsv",
    "Swahili": "swa_latn_broad.tsv",
    "Tagalog": "tgl_latn_broad.tsv",
    "Dutch": "nld_latn_broad_filtered.tsv",
    "Greek": "ell_grek_broad_filtered.tsv",
    "Hebrew": "heb_hebr_broad.tsv",
    "Amharic": "amh_ethi_broad.tsv",
    "Hausa": "hau_latn_broad.tsv",

    "Marathi": "mar_deva_broad.tsv",
    "Yoruba": "yor_latn_broad.tsv",
    "Zulu": "zul_latn_broad.tsv",
}
BASE = "https://raw.githubusercontent.com/CUNY-CL/wikipron/master/data/scrape/tsv/"
CACHE = "data/wikipron"
UA = "SpokenSoundsAcrossTheWorld/1.0 (data-viz research; https://github.com/EZBUTD/sounds)"


def fetch(fname):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, fname)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    r = subprocess.run(["curl", "-sL", "--max-time", "120", "-A", UA,
                        "-o", path, "-w", "%{http_code}", BASE + fname],
                       capture_output=True, text=True)
    if r.stdout.strip() != "200" or os.path.getsize(path) < 1000:
        if os.path.exists(path):
            os.remove(path)
        return None
    time.sleep(0.5)
    return path


def tokenize_ipa(ipa):
    """WikiPron transcriptions are space-separated segments already."""
    return ipa.split()


def main():
    # per-language on-chart phoneme sets from PHOIBLE (same pipeline as build)
    rows_by_inv = defaultdict(list)
    with open("data/phoible.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows_by_inv[row["InventoryID"]].append(row)
    onchart = chart_symbols()

    mined = {}
    stats = []
    for lang, inv_id in LANG_INVENTORIES.items():
        fname = WIKIPRON.get(lang)
        if not fname:
            continue
        path = fetch(fname)
        if not path:
            stats.append((lang, "DOWNLOAD FAILED", 0, 0))
            continue

        targets = {norm(r["Phoneme"]) for r in rows_by_inv[inv_id]} & onchart

        # best candidate per target, ranked to look like a real word:
        #   1. skip 1-char words & 1-2 segment transcriptions (letter names!)
        #   2. prefer word-initial target sound
        #   3. prefer 3-6 char words (fallback up to 12)
        best = {}
        with io.open(path, encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) != 2:
                    continue
                word, ipa = parts
                if len(word) < 2 or len(word) > 12 or " " in word or "-" in word:
                    continue
                raw_segs = tokenize_ipa(ipa)
                if len(raw_segs) < 3:  # letter names / interjections
                    continue
                if any(c.isupper() for c in word) and word[:1].isupper():
                    continue  # proper nouns / initialisms
                segs = [norm(s) for s in raw_segs]
                lenscore = 0 if 3 <= len(word) <= 6 else 1
                for i, seg in enumerate(segs):
                    if seg in targets:
                        key = (i > 0, lenscore, len(word))
                        if seg not in best or key < best[seg][0]:
                            best[seg] = (key, word, ipa)
        for seg, (_, word, ipa) in best.items():
            mined[f"{lang}|{seg}"] = {"word": word, "ipa": ipa, "source": fname}
        stats.append((lang, fname, len(targets), len(best)))

    with open("mined_examples.json", "w", encoding="utf-8") as f:
        json.dump(mined, f, ensure_ascii=False, indent=1)

    print(f"{'language':<20} {'targets':>7} {'found':>6} {'coverage':>9}")
    for lang, fname, n_t, n_f in stats:
        pct = f"{100*n_f/n_t:.0f}%" if n_t else "-"
        print(f"{lang:<20} {n_t:>7} {n_f:>6} {pct:>9}")
    print(f"\ntotal mined: {len(mined)} -> mined_examples.json")


if __name__ == "__main__":
    main()
