#!/usr/bin/env python3
"""
Country-level language layer for the map rework: for each of our 34 languages,
which countries it is spoken in and by roughly how many people.

Source: Unicode CLDR supplementalData.xml `languagePopulation` — per territory,
the share of the population that speaks each language, with official status.
This is the dataset behind every OS's locale defaults; it counts SPEAKERS
(native or not) per country, which is exactly the "where does the language
actually live" layer the homeland dot could not show.

Output feeds a choropleth-on-highlight: select a language -> countries shade by
speaker count, arcs optionally flow homeland -> major speaker countries.

CAVEATS
  - CLDR percentages mix L1 and L2 without a consistent split, and small
    percentages for big countries are still huge numbers (1% of India = 14M).
    Treat country values as magnitude estimates, not census figures.
  - CLDR under-reports diaspora and learner populations for some languages
    (its Japanese row for the US, say, reflects communities, not classrooms).
    So the page copy must say "speaks", not "learns", for the country shading;
    the L1/L2 split stays sourced from Ethnologue at language level.
  - Languages are ISO 639-1/3 codes in CLDR; our display names are mapped by
    hand below, including the MSA quirk (CLDR uses `ar` for Arabic generally).
"""
import json
import re
import subprocess
import os

CLDR_URL = ("https://raw.githubusercontent.com/unicode-org/cldr/main/common/"
            "supplemental/supplementalData.xml")
CLDR_CACHE = "data/cldr_supplemental.xml"
OUT = "country_language_layer.json"

# our display name -> CLDR language code
CLDR_CODE = {
    "English": "en", "Mandarin Chinese": "zh", "Hindi": "hi", "Spanish": "es",
    "French": "fr", "Arabic (MSA)": "ar", "Bengali": "bn", "Russian": "ru",
    "Portuguese": "pt", "Indonesian": "id", "German": "de", "Japanese": "ja",
    "Telugu": "te", "Turkish": "tr", "Tamil": "ta", "Cantonese": "yue",
    "Vietnamese": "vi", "Korean": "ko", "Italian": "it", "Thai": "th",
    "Polish": "pl", "Ukrainian": "uk", "Persian": "fa", "Punjabi": "pa",
    "Swahili": "sw", "Tagalog": "fil", "Dutch": "nl", "Greek": "el",
    "Hebrew": "he", "Amharic": "am", "Hausa": "ha", "Marathi": "mr",
    "Yoruba": "yo", "Zulu": "zu",
}
# Threshold checked empirically (2026-08-10): lowering 100k -> 10k recovers 75
# real rows (Thai in SG, Zulu in SZ/MW, Turkish in CA...) and no junk, so keep
# it low. NOTE the bigger issue is CLDR's own coverage, not this filter: CLDR
# documents languages relevant to locale support per territory, NOT diaspora.
# It has no row at all for Thai in the US (~300k speakers per US Census) or
# Japanese in the US (~460k). Surfaced honestly in the page caveat.
MIN_SPEAKERS = 10_000


def ensure_cldr():
    if not os.path.exists(CLDR_CACHE):
        data = subprocess.run(["curl", "-sL", "--max-time", "90", CLDR_URL],
                              capture_output=True, check=True).stdout
        with open(CLDR_CACHE, "wb") as f:
            f.write(data)
    return open(CLDR_CACHE, encoding="utf-8").read()


def main():
    xml = ensure_cldr()
    wanted = {v: k for k, v in CLDR_CODE.items()}

    # parse territory blocks with a tolerant regex (structure is flat + stable)
    terr_re = re.compile(
        r'<territory type="([A-Z]{2})"[^>]*population="(\d+)"[^>]*>(.*?)</territory>',
        re.S)
    lang_re = re.compile(
        r'<languagePopulation type="([a-zA-Z_]+)"[^>]*?populationPercent="([\d.E-]+)"'
        r'(?:[^>]*?officialStatus="([a-z_]+)")?')

    by_lang = {name: {} for name in CLDR_CODE}
    n_terr = 0
    for tcode, pop, body in terr_re.findall(xml):
        pop = int(pop)
        if pop == 0:
            continue
        n_terr += 1
        for lcode, pcts, status in lang_re.findall(body):
            base = lcode.split("_")[0]
            name = wanted.get(lcode) or wanted.get(base)
            if not name:
                continue
            speakers = pop * float(pcts) / 100.0
            if speakers < MIN_SPEAKERS:
                continue
            cur = by_lang[name].get(tcode)
            entry = {
                "speakers": round(speakers / 1e6, 3),   # millions
                "pct": round(float(pcts), 2),
                "official": status or "",
            }
            # keep the larger row if a language appears twice (e.g. zh + zh_Hant)
            if cur is None or entry["speakers"] > cur["speakers"]:
                by_lang[name][tcode] = entry

    print(f"parsed {n_terr} territories")
    print(f"{'language':<20} {'countries':>9} {'top countries by speakers'}")
    for name in CLDR_CODE:
        rows = by_lang[name]
        top = sorted(rows.items(), key=lambda kv: -kv[1]["speakers"])[:4]
        tops = ", ".join(f"{c} {v['speakers']:.0f}M" for c, v in top)
        print(f"{name:<20} {len(rows):>9}   {tops}")

    empty = [n for n, r in by_lang.items() if not r]
    if empty:
        print(f"\nWARNING languages with no CLDR rows: {empty}")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(by_lang, f, ensure_ascii=False, indent=1)
    total_rows = sum(len(r) for r in by_lang.values())
    print(f"\nwrote {OUT}: {total_rows} (language, country) rows")


if __name__ == "__main__":
    main()
