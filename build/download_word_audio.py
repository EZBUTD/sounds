#!/usr/bin/env python3
"""Download the English /t/ allophone WORD recordings from Wikimedia Commons.

Why words and not isolated IPA segments: the allophones page needs to demonstrate
one phoneme pronounced three ways, and the allophones only exist in context. The
tapped [ɾ] in "butter" is a positional allophone, not a segment an IPA reference
records as English, and the unaspirated [t] of "stop" is only unaspirated BECAUSE
of the preceding /s/. Playing an isolated /t/ file and labelling it would be a
fabricated comparison.

These files are unusually good for the purpose: same speaker (Dvortygirl), same
accent (General American), same licence (CC BY-SA 3.0), so the listener hears the
allophonic difference rather than three different voices. Verified against the
Commons API before download; metadata is fetched live, never hand-transcribed.

WORD SELECTION: prefer allophones that are OBLIGATORY in General American.
"cat" was originally used for the unreleased allophone [t̚], but word-final stop
release in English is OPTIONAL — a speaker's choice, not a rule — so the recording
did not reliably contain the allophone the card claimed (caught by listening to
it). It was replaced with "stop", where aspiration is suppressed after /s/ without
exception, so any competent recording demonstrates it. Applying the same test:
  - aspiration word-initially (top)          -> obligatory, keep
  - suppression after /s/ (stop)             -> obligatory, added
  - flapping between vowels (butter)         -> near-obligatory in GA, keep
  - unreleased word-finally (cat)            -> OPTIONAL, removed
"top" and "stop" are also a near-minimal pair, which makes the aspiration
contrast unusually easy to hear.

Phonetic transcriptions come from Wiktionary and are recorded in the manifest so
the page can show what to listen for.
"""
import csv
import io
import json
import os
import subprocess
import urllib.parse

# macOS system Python fails SSL verification against wikimedia (no local issuer
# cert), so shell out to curl exactly as download_audio.py already does. Do not
# switch this back to urllib.request.
UA = "SpokenSoundsAcrossTheWorld/1.0 (data-viz research; https://github.com/EZBUTD/sounds)"
OUT_DIR = "audio"
MANIFEST = "audio_manifest_words.csv"
API = "https://commons.wikimedia.org/w/api.php"

# word -> (Commons file, local name, broad phonemic, narrow phonetic, what to hear)
WORDS = {
    "top": ("En-us-top.ogg", "en-us-top.ogg", "/tɑp/", "[tʰɑp]",
            "word-initial: released with an audible puff of air"),
    "stop": ("En-us-stop.ogg", "en-us-stop.ogg", "/stɑp/", "[stɑp]",
             "after /s/: the puff of air is suppressed"),
    "butter": ("En-us-butter.ogg", "en-us-butter.ogg", "/ˈbʌtəɹ/", "[ˈbʌɾɚ]",
               "between vowels: a single quick tap of the tongue"),
}


def fetch(url, dest=None):
    """curl the URL. With dest, save to disk and return the byte count."""
    cmd = ["curl", "-sL", "--max-time", "30", "-A", UA]
    if dest:
        cmd += ["-o", dest, "-w", "%{http_code}", url]
    else:
        cmd += [url]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"curl failed for {url}: rc={r.returncode}")
    if dest:
        code = r.stdout.strip()
        if code != "200":
            raise SystemExit(f"{url} returned HTTP {code}")
        return os.path.getsize(dest)
    return r.stdout


def commons_info(title):
    """Live metadata so licence/author are never hand-transcribed."""
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "prop": "imageinfo",
        "iiprop": "url|user|extmetadata", "titles": f"File:{title}",
    })
    data = json.loads(fetch(f"{API}?{q}"))
    page = next(iter(data["query"]["pages"].values()))
    if "missing" in page:
        raise SystemExit(f"Commons file not found: {title}")
    ii = page["imageinfo"][0]
    em = ii.get("extmetadata", {})
    val = lambda k: em.get(k, {}).get("value", "")
    return {
        "url": ii["url"].split("?")[0],
        "author": ii.get("user", ""),
        "license": val("LicenseShortName"),
        "date": val("DateTimeOriginal"),
        "terms": val("UsageTerms"),
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    for word, (title, local, phonemic, phonetic, hear) in WORDS.items():
        info = commons_info(title)
        if "BY-SA" not in info["license"] and "BY" not in info["license"]:
            raise SystemExit(f"{title}: unexpected licence {info['license']!r}")
        dest = os.path.join(OUT_DIR, local)
        nbytes = fetch(info["url"], dest=dest)
        print(f"{word:8} {local:22} {nbytes:>7,}B  {info['license']}  "
              f"by {info['author']} ({info['date']})")
        rows.append({
            "word": word, "file": local, "phonemic": phonemic,
            "phonetic": phonetic, "listen_for": hear,
            "commons_file": title, "commons_url": info["url"],
            "author": info["author"], "license": info["license"],
            "date": info["date"], "usage_terms": info["terms"],
            "transcription_source": "Wiktionary",
        })

    with io.open(MANIFEST, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {MANIFEST} ({len(rows)} rows)")
    speakers = {r["author"] for r in rows}
    print(f"speakers: {', '.join(speakers)} "
          f"({'single speaker — good' if len(speakers) == 1 else 'MIXED'})")


if __name__ == "__main__":
    main()
