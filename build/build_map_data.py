#!/usr/bin/env python3
"""
Emit docs/mapdata.js — world basemap + per-language geography/rarity layer
for the "More to explore" page.

The Natural Earth 110m countries file is ~840 KB, far too heavy to inline in a
self-contained page. Since the map renders small and is only a backdrop for
language markers, coarse outlines are plenty, so polygons are simplified with
Ramer-Douglas-Peucker and coordinates rounded to 2 decimals (~1 km, well below
one screen pixel at this scale). Typical result: ~90% smaller.

Reads geo_analysis.json (run analyze_geography.py first).
"""
import json
import math
import os
import subprocess

WORLD_URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
             "master/geojson/ne_110m_admin_0_countries.geojson")
WORLD_CACHE = "data/ne_110m_countries.geojson"
GEO_IN = "geo_analysis.json"
DRIVERS_IN = "l2_drivers.json"
ASYM_IN = "asymmetry_analysis.json"
COUNTRY_IN = "country_language_layer.json"
OUT = "docs/mapdata.js"
EPSILON = 0.55        # simplification tolerance in degrees
MIN_AREA = 1.1        # drop islands smaller than this (deg^2 bounding box)


def ensure_world():
    if not os.path.exists(WORLD_CACHE):
        print(f"fetching {WORLD_URL}")
        data = subprocess.run(["curl", "-sL", "--max-time", "120", WORLD_URL],
                              capture_output=True, check=True).stdout
        with open(WORLD_CACHE, "wb") as f:
            f.write(data)
    return json.load(open(WORLD_CACHE, encoding="utf-8"))


def perp_dist(p, a, b):
    if a == b:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    num = abs((b[0] - a[0]) * (a[1] - p[1]) - (a[0] - p[0]) * (b[1] - a[1]))
    return num / math.hypot(b[0] - a[0], b[1] - a[1])


def rdp(pts, eps):
    """Ramer-Douglas-Peucker, iterative to avoid deep recursion on long rings."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        worst, wi = -1.0, None
        for k in range(i + 1, j):
            d = perp_dist(pts[k], pts[i], pts[j])
            if d > worst:
                worst, wi = d, k
        if worst > eps and wi is not None:
            keep[wi] = True
            stack.append((i, wi))
            stack.append((wi, j))
    return [p for p, k in zip(pts, keep) if k]


def simplify_ring(ring):
    pts = rdp([(round(x, 2), round(y, 2)) for x, y in ring], EPSILON)
    # drop consecutive duplicates left by rounding
    out = [pts[0]]
    for p in pts[1:]:
        if p != out[-1]:
            out.append(p)
    return out if len(out) >= 4 else None


def bbox_area(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def trim_asymmetry(asym):
    """Drop the per-pair `sounds` lists from the shipped bundle.

    All 1,122 directed pairs carry the actual list of missing IPA symbols, which
    is ~140 KB and more than half the payload, but the page only ever renders the
    counts. The full lists stay in asymmetry_analysis.json for analysis.
    """
    asym["pairs"] = {k: {kk: vv for kk, vv in v.items() if kk != "sounds"}
                     for k, v in asym["pairs"].items()}
    return asym


def iso2(props):
    """Natural Earth leaves ISO_A2 = -99 for a few countries (France, Norway,
    Kosovo...); ISO_A2_EH carries the usable code for most of them."""
    for k in ("ISO_A2", "ISO_A2_EH"):
        v = props.get(k)
        if v and v != "-99":
            return v
    return None


def main():
    world = ensure_world()
    # shapes tagged with country code + a label point so the front-end can shade
    # countries per selected language and anchor flow arcs
    shapes = []
    for feat in world["features"]:
        g = feat["geometry"]
        if not g:
            continue
        code = iso2(feat["properties"])
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            outer = poly[0]                     # ignore holes; invisible at this size
            if bbox_area(outer) < MIN_AREA:
                continue
            s = simplify_ring(outer)
            if s:
                shapes.append({"c": code, "pts": s})

    # one anchor point per country = centroid of its largest ring (arc endpoint)
    anchors = {}
    for sh in shapes:
        if not sh["c"]:
            continue
        n = len(sh["pts"])
        if sh["c"] not in anchors or n > anchors[sh["c"]][2]:
            cx = sum(p[0] for p in sh["pts"]) / n
            cy = sum(p[1] for p in sh["pts"]) / n
            anchors[sh["c"]] = [round(cx, 2), round(cy, 2), n]
    anchors = {c: v[:2] for c, v in anchors.items()}
    # hand-fix anchors where the centroid of the largest ring is misleading
    # (US largest ring includes Alaska pulling it north; FR ring is metropolitan)
    anchors.update({"US": [-98.0, 39.0], "RU": [50.0, 58.0], "CA": [-102.0, 56.0],
                    "NO": [9.0, 61.0], "CL": [-71.0, -33.0]})

    countries = json.load(open(COUNTRY_IN, encoding="utf-8"))

    geo = json.load(open(GEO_IN, encoding="utf-8"))
    payload = {
        "shapes": shapes,
        "countryAnchors": anchors,
        "countryLayer": countries,
        "worldLanguageCount": geo["worldLanguageCount"],
        "languages": geo["languages"],
        "englishRarest": geo["englishRarest"],
        "globalFreq": geo["globalFreq"],
        # What meanRarity is scored over, and which languages carry tone
        # contrasts it cannot see. Both travel with the numbers so a page cannot
        # label the rarity axis as more than it measures.
        "rarityUnit": geo["rarityUnit"],
        "tone": geo["tone"],
        "weightedPairs": geo["weightedPairs"],
        "l2Drivers": json.load(open(DRIVERS_IN, encoding="utf-8")),
        "asymmetry": trim_asymmetry(json.load(open(ASYM_IN, encoding="utf-8"))),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("const MAPDATA = ")
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    raw = os.path.getsize(WORLD_CACHE)
    got = os.path.getsize(OUT)
    npts = sum(len(s["pts"]) for s in shapes)
    print(f"wrote {OUT}: {len(shapes)} polygons, {npts} points, "
          f"{len(anchors)} country anchors, "
          f"{sum(len(r) for r in countries.values())} country-language rows")
    print(f"basemap {raw/1024:.0f}KB -> bundle {got/1024:.0f}KB "
          f"({100*(1-got/raw):.0f}% smaller)")


if __name__ == "__main__":
    main()
