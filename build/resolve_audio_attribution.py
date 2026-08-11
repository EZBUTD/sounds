#!/usr/bin/env python3
"""Fill in real author/licence data for every audio file, from the Commons API.

WHY: download_audio.py wrote the literal string "verify on Commons file page
before publishing" into every row's license_note. That was a to-do, not a
licence. CC BY-SA requires naming the author, so the project could not be
published with it. Nothing was wrong with the audio — the metadata simply was
never fetched.

The Commons filenames are already recorded in audio_manifest.csv, so this asks
the API for each one and records author, licence, licence URL and the file's
description page. Metadata is fetched, never hand-typed.

Uses curl because macOS system Python fails SSL verification against wikimedia
(same reason download_audio.py does).

Output: rewrites audio_manifest.csv in place with real columns, and prints a
summary of licences so anything unexpected is visible.
"""
import csv
import io
import json
import re
import subprocess
import sys
import time
import urllib.parse

MANIFEST = "audio_manifest.csv"
API = "https://commons.wikimedia.org/w/api.php"
UA = "SpokenSoundsAcrossTheWorld/1.0 (data-viz research; https://github.com/EZBUTD/sounds)"
# licences acceptable for this project; anything else is reported, not silently kept
OK_LICENCE = re.compile(r"CC[ -]BY(-SA)?|public domain|CC0", re.I)


def api(titles):
    """Batch metadata lookup: up to 50 File: titles per request."""
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "prop": "imageinfo",
        "iiprop": "url|user|extmetadata",
        "titles": "|".join(f"File:{t}" for t in titles),
    })
    r = subprocess.run(
        ["curl", "-sL", "--max-time", "45", "-A", UA, f"{API}?{q}"],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"curl failed: rc={r.returncode}")
    return json.loads(r.stdout)


def strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def main():
    rows = list(csv.DictReader(io.open(MANIFEST, encoding="utf-8")))
    print(f"{len(rows)} rows in {MANIFEST}")

    # the manifest records "Name.ogg (assumed, verify)" for files that were
    # downloaded from a guessed filename, and "(cached)" where the file already
    # existed locally. Recover the real Commons name from the local filename in
    # the second case by looking it up in download_audio.py's candidate table.
    from download_audio import F, slug
    by_file = {}
    for sym, cands in F.items():
        by_file[f"{slug(sym)}.ogg"] = cands[0]

    wanted = {}
    for r in rows:
        name = re.sub(r"\s*\(assumed, verify\)\s*$", "", r["commons_file"] or "")
        if not name or name == "(cached)":
            name = by_file.get(r["file"], "")
        if name:
            wanted[r["phoneme"]] = name

    print(f"resolved {len(wanted)} Commons filenames to query")

    info = {}
    names = sorted(set(wanted.values()))
    for i in range(0, len(names), 40):
        batch = names[i:i + 40]
        data = api(batch)
        for page in data.get("query", {}).get("pages", {}).values():
            title = page.get("title", "").replace("File:", "")
            if "missing" in page:
                info[title] = {"missing": True}
                continue
            ii = page["imageinfo"][0]
            em = ii.get("extmetadata", {})
            val = lambda k: strip_html(em.get(k, {}).get("value", ""))
            info[title] = {
                "author": val("Artist") or ii.get("user", ""),
                "uploader": ii.get("user", ""),
                "licence": val("LicenseShortName"),
                "licence_url": em.get("LicenseUrl", {}).get("value", ""),
                "page": f"https://commons.wikimedia.org/wiki/File:"
                        + urllib.parse.quote(title.replace(" ", "_")),
                "date": val("DateTimeOriginal"),
            }
        print(f"  queried {min(i+40, len(names))}/{len(names)}")
        time.sleep(1)

    out, problems, licences = [], [], {}
    for r in rows:
        name = wanted.get(r["phoneme"], "")
        m = info.get(name, {})
        if not name:
            problems.append(f"{r['phoneme']}: no Commons filename recorded")
        elif m.get("missing"):
            problems.append(f"{r['phoneme']}: File:{name} not found on Commons")
        elif not OK_LICENCE.search(m.get("licence", "")):
            problems.append(f"{r['phoneme']}: unexpected licence "
                            f"{m.get('licence')!r} on {name}")
        lic = m.get("licence", "UNKNOWN")
        licences[lic] = licences.get(lic, 0) + 1
        out.append({
            "phoneme": r["phoneme"],
            "file": r["file"],
            "audio_kind": r["audio_kind"],
            "commons_file": name,
            "commons_page": m.get("page", ""),
            "author": m.get("author", ""),
            "uploader": m.get("uploader", ""),
            "licence": lic,
            "licence_url": m.get("licence_url", ""),
            "date": m.get("date", ""),
        })

    with io.open(MANIFEST, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    print(f"\nwrote {MANIFEST}")
    print("\nlicences found:")
    for lic, n in sorted(licences.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>4}  {lic}")
    authors = {r["author"] for r in out if r["author"]}
    print(f"\ndistinct credited authors: {len(authors)}")
    if problems:
        print(f"\n{len(problems)} PROBLEMS:")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("\nall rows carry an author and an acceptable licence")


if __name__ == "__main__":
    main()
