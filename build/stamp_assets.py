#!/usr/bin/env python3
"""Cache-bust every local asset reference with a content hash.

WHY THIS EXISTS
The dendrogram appeared "not visible" to a reader while rendering correctly in a
fresh browser. Cause: their browser held a CACHED `analysis.js` from before the
tree data existed, so `ANALYSIS.tree` was undefined and the drawing block was
skipped. Because the page had no reference to compare against, it failed silently
— blank canvas, empty placeholders, nothing in the console.

Regenerating a data bundle without changing the filename is exactly the situation
browser caching handles badly: same URL, new contents, and `file://` pages get no
cache headers at all. Appending a content hash makes the URL change whenever the
bytes change, so a stale copy can never be served.

Run this after ANY script that regenerates a bundle (build_chart_data.py,
analyze_families.py, build_deep_data.py, build_map_data.py, build_rarity_data.py).
Idempotent: re-running with unchanged files is a no-op.
"""
import hashlib
import io
import os
import re

PROTO = "prototype"
# only local assets we generate or edit; skip external URLs
ASSET_RE = re.compile(
    r'(?P<attr>src|href)="(?P<file>[A-Za-z0-9_\-]+\.(?:js|css))(?:\?v=[0-9a-f]+)?"')


def digest(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:8]


def main():
    pages = sorted(p for p in os.listdir(PROTO) if p.endswith(".html"))
    hashes, changed = {}, 0

    for page in pages:
        path = os.path.join(PROTO, page)
        src = io.open(path, encoding="utf-8").read()

        def sub(m):
            fn = m.group("file")
            target = os.path.join(PROTO, fn)
            if not os.path.exists(target):
                return m.group(0)          # leave unknown refs alone
            if fn not in hashes:
                hashes[fn] = digest(target)
            return f'{m.group("attr")}="{fn}?v={hashes[fn]}"'

        out = ASSET_RE.sub(sub, src)
        if out != src:
            io.open(path, "w", encoding="utf-8").write(out)
            changed += 1
            print(f"stamped {page}")
        else:
            print(f"unchanged {page}")

    print(f"\n{changed} of {len(pages)} pages updated")
    for fn, h in sorted(hashes.items()):
        print(f"  {fn:<18} v={h}")


if __name__ == "__main__":
    main()
