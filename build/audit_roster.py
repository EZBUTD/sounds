# Roster quality audit: find dialect/register pairs (mutually intelligible or
# same macrolanguage) and inventory quality flags across the 36 languages.
import json
from itertools import combinations

raw = open("prototype/data.js", encoding="utf-8").read()
D = json.loads(raw[len("const DATA = "):-2])
langs = {l["name"]: l for l in D["languages"]}

# 1. Pairs to inspect: same macrolanguage / register / high mutual intelligibility
SUSPECT_PAIRS = [
    ("Arabic (MSA)", "Egyptian Arabic",
     "same macrolanguage; MSA is a written/formal register, Egyptian a spoken dialect"),
    ("Hindi", "Urdu",
     "same spoken language (Hindustani) in different scripts/registers"),
    ("Indonesian", None,
     "Indonesian is a standardized register of Malay — no pair here, OK"),
    ("Mandarin Chinese", "Cantonese",
     "NOT dialects: mutually unintelligible, both worth keeping"),
    ("Russian", "Ukrainian",
     "distinct languages, partial intelligibility — defensible to keep both"),
    ("Punjabi", "Urdu",
     "distinct languages, same region — OK"),
]
print("=== Suspect same-language/register pairs ===")
for a, b, note in SUSPECT_PAIRS:
    if b and a in langs and b in langs:
        key = a + "|" + b if a < b else b + "|" + a
        sh, j = D["pairOverlap"].get(key, ("?", "?"))
        print(f"  {a} + {b}: overlap={j} — {note}")
    else:
        print(f"  {a}: {note}")

# 2. Quality flags per language
print("\n=== Inventory quality flags ===")
for name, l in sorted(langs.items()):
    flags = []
    if not l["allophoneData"]:
        flags.append("no allophone data (2-state only)")
    if l["soundCount"] >= 50:
        flags.append(f"large count {l['soundCount']} (verify vs textbook)")
    if l["soundCount"] <= 22:
        flags.append(f"small count {l['soundCount']} (verify vs textbook)")
    if l["mergedCount"] > l["phonemes"].__len__():
        flags.append("more merged variants than base cells")
    if flags:
        print(f"  {name:<20} {'; '.join(flags)}")

# 3. Languages whose top-2 neighbors are the same-macrolanguage partner
#    (their presence distorts each other's percentile panels)
print("\n=== Distortion check: does a register-pair dominate percentiles? ===")
for a, b in [("Arabic (MSA)", "Egyptian Arabic"), ("Hindi", "Urdu")]:
    rows = []
    for other in langs:
        if other == a:
            continue
        key = a + "|" + other if a < other else other + "|" + a
        rows.append((D["pairOverlap"][key][1], other))
    rows.sort(reverse=True)
    rank = [o for _, o in rows].index(b) + 1
    print(f"  {b} is {a}'s #{rank} nearest neighbor of {len(rows)}")
