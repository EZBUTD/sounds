#!/usr/bin/env python3
"""
Fetch the geography + speaker-population layer for the world-map view.

Two external sources, both cite-able:
  1. Glottolog 5.x CLDF `languages.csv` — Glottocode -> latitude/longitude,
     macroarea, countries. Joined to PHOIBLE on Glottocode (PHOIBLE ships one).
     CC BY 4.0.
  2. Wikipedia "List of languages by total number of speakers" (sourced from
     Ethnologue 2026) -> L1 / L2 / total speaker millions. Ethnologue itself is
     paywalled; the Wikipedia table is the standard citable proxy. CC BY-SA.

Both are cached to data/ so the build is reproducible offline.

CAVEAT that shapes the whole map: a language is not a point. Glottolog gives one
representative coordinate per language -- roughly the historical center of the
speech community -- which is a reasonable anchor for Zulu and badly misleading
for English or Spanish. The map therefore uses the point only as a
*primary-homeland marker* and shows L2 reach separately, never as territory.
"""
import csv
import json
import os
import re
import subprocess

GLOTTO_URL = ("https://raw.githubusercontent.com/glottolog/glottolog-cldf/"
              "master/cldf/languages.csv")
GLOTTO_CACHE = "data/glottolog_languages.csv"
WIKI_API = ("https://en.wikipedia.org/w/api.php?action=parse"
            "&page=List_of_languages_by_total_number_of_speakers"
            "&prop=wikitext&format=json&section=1")
SPEAKERS_CACHE = "data/speakers_ethnologue.json"
UA = "VizCon2026-sounds-research/1.0 (educational data viz)"


def curl(url):
    """macOS system Python fails SSL verification on these hosts (same gotcha the
    audio pipeline hit), so shell out to curl, which uses the system trust store."""
    return subprocess.run(
        ["curl", "-sL", "--max-time", "90", "-H", f"User-Agent: {UA}", url],
        capture_output=True, check=True).stdout


def fetch(url, dest):
    if os.path.exists(dest):
        print(f"cached: {dest}")
        return
    print(f"fetching: {url}")
    data = curl(url)
    with open(dest, "wb") as f:
        f.write(data)
    print(f"wrote {dest} ({len(data)} bytes)")


def parse_speakers():
    """Wikipedia/Ethnologue table -> {language name: {l1, l2, total}} in millions."""
    if os.path.exists(SPEAKERS_CACHE):
        print(f"cached: {SPEAKERS_CACHE}")
        return json.load(open(SPEAKERS_CACHE, encoding="utf-8"))
    wt = json.loads(curl(WIKI_API))["parse"]["wikitext"]["*"]

    def num(cell):
        # cells look like: 372   |  data-sort-value="1135 million" ! | 1,121
        cell = re.sub(r'data-sort-value="[^"]*"', "", cell)
        cell = cell.replace("!", "").strip()
        m = re.search(r"([\d,]+(?:\.\d+)?)", cell)
        return float(m.group(1).replace(",", "")) if m else None

    out, rows = {}, wt.split("\n|-")
    for row in rows:
        cells = [c.strip() for c in row.split("\n|")[1:]]
        if len(cells) < 6:
            continue
        m = re.search(r"\[\[(?:ISO 639:\w+\|)?([^\]|]+)(?:\|([^\]]+))?\]\]", cells[0])
        if not m:
            continue
        name = (m.group(2) or m.group(1)).strip()
        l1, l2, tot = num(cells[3]), num(cells[4]), num(cells[5])
        if l1 is None or tot is None:
            continue
        out[name] = {"l1": l1, "l2": l2 or 0.0, "total": tot}
    with open(SPEAKERS_CACHE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"wrote {SPEAKERS_CACHE}: {len(out)} languages")
    return out


def main():
    fetch(GLOTTO_URL, GLOTTO_CACHE)
    sp = parse_speakers()
    n_geo = sum(1 for r in csv.DictReader(open(GLOTTO_CACHE, encoding="utf-8"))
                if r["Latitude"])
    print(f"\nglottolog rows with coordinates: {n_geo}")
    print(f"speaker table entries: {len(sp)}")
    top = sorted(sp.items(), key=lambda kv: -kv[1]["total"])[:8]
    for n, d in top:
        share = d["l2"] / d["total"] if d["total"] else 0
        print(f"  {n:<20} L1 {d['l1']:>6.0f}M  L2 {d['l2']:>6.0f}M  "
              f"total {d['total']:>6.0f}M  ({share:.0%} L2)")


if __name__ == "__main__":
    main()
