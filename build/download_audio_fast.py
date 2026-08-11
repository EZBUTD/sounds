#!/usr/bin/env python3
"""
Fast path for the remaining Commons audio: batch-resolve file URLs via the
Commons API (50 titles per request), then download from upload.wikimedia.org
directly (separate, more generous rate pool than the Special:FilePath
redirector). Falls back gracefully; idempotent; rewrites audio_manifest.csv.

Reuses the F/WORD_BASED/slug definitions from download_audio.py.
"""
import csv
import json
import os
import subprocess
import time
import urllib.parse

from download_audio import F, WORD_BASED, slug, AUDIO_DIR, MANIFEST, UA


def api_resolve(names):
    """names: list of Commons filenames -> {name: direct_url}. Batches of 50."""
    out = {}
    for i in range(0, len(names), 50):
        batch = names[i:i + 50]
        titles = "|".join("File:" + n for n in batch)
        url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json"
               "&prop=imageinfo&iiprop=url&titles=" + urllib.parse.quote(titles))
        r = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, url],
                           capture_output=True, text=True)
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            time.sleep(10)
            continue
        norm_map = {}
        for n in (data.get("query", {}).get("normalized", []) or []):
            norm_map[n["to"]] = n["from"]
        for page in data.get("query", {}).get("pages", {}).values():
            title = page.get("title", "")
            orig = norm_map.get(title, title)
            name = orig.removeprefix("File:")
            ii = page.get("imageinfo")
            if ii:
                out[name] = ii[0]["url"]
        time.sleep(2)
    return out


def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # figure out what's still needed
    todo = {}
    for sym, candidates in F.items():
        dest = os.path.join(AUDIO_DIR, f"{slug(sym)}.ogg")
        if not (os.path.exists(dest) and os.path.getsize(dest) > 1000):
            todo[sym] = candidates
    print(f"{len(F) - len(todo)} cached, {len(todo)} to fetch")

    # resolve all candidate filenames in batches
    all_names = [n for cands in todo.values() for n in cands]
    resolved = api_resolve(all_names)
    print(f"API resolved {len(resolved)}/{len(set(all_names))} candidate filenames")

    used = {}  # sym -> (commons_name, url)
    for sym, candidates in todo.items():
        for name in candidates:
            if name in resolved:
                used[sym] = (name, resolved[name])
                break

    # download from upload.wikimedia.org
    failed = []
    for sym, (name, url) in used.items():
        dest = os.path.join(AUDIO_DIR, f"{slug(sym)}.ogg")
        ok = False
        for attempt in range(3):
            r = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA,
                                "-o", dest, "-w", "%{http_code}", url],
                               capture_output=True, text=True)
            if r.stdout.strip() == "200" and os.path.getsize(dest) > 1000:
                ok = True
                break
            time.sleep(8 * (attempt + 1))
        if not ok and os.path.exists(dest):
            os.remove(dest)
        print(f"  [{'ok ' if ok else 'MISS'}] {sym:>3}  {name}")
        if not ok:
            failed.append(sym)
        time.sleep(0.8)

    unresolved = [s for s in todo if s not in used]
    if unresolved:
        print("No candidate filename found on Commons for:", " ".join(unresolved))

    # rewrite manifest from disk state
    rows = []
    # keep previous commons attribution info if present
    prev = {}
    if os.path.exists(MANIFEST):
        for r in csv.DictReader(open(MANIFEST, encoding="utf-8")):
            prev[r["phoneme"]] = r
    for sym, candidates in F.items():
        dest = os.path.join(AUDIO_DIR, f"{slug(sym)}.ogg")
        have = os.path.exists(dest) and os.path.getsize(dest) > 1000
        commons_file = ""
        commons_url = ""
        if sym in used:
            commons_file, commons_url = used[sym]
        elif sym in prev and prev[sym].get("commons_file") not in ("", "(cached)"):
            commons_file = prev[sym]["commons_file"]
            commons_url = prev[sym].get("commons_url", "")
        elif have:
            commons_file = candidates[0] + " (assumed, verify)"
        rows.append({
            "phoneme": sym, "file": f"{slug(sym)}.ogg" if have else "",
            "commons_file": commons_file, "commons_url": commons_url,
            "resolved": have,
            "audio_kind": "word_example" if sym in WORD_BASED else "isolated_phoneme",
            "license_note": "verify on Commons file page before publishing" if have else "",
        })
    with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    n_ok = sum(1 for r in rows if r["resolved"])
    print(f"\n{n_ok}/{len(rows)} symbols have audio -> {MANIFEST}")
    missing = [r["phoneme"] for r in rows if not r["resolved"]]
    if missing:
        print("Still missing:", " ".join(missing))


if __name__ == "__main__":
    main()
