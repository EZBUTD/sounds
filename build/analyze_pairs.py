#!/usr/bin/env python3
"""
Pairwise overlap analysis across the selected languages.

Two metrics per pair (one occupied broad IPA area per language):
  shared  = number of broad areas occupied by both sources
  jaccard = shared / number of areas occupied by either source

This lets differently detailed source spellings share a broad area while keeping
the source entries as qualitative detail rather than inferring equivalent contrasts.

Prints: top/bottom pairs by jaccard, distribution stats, per-language
"best friend / stranger", and English's ranked list.
"""
import json
import statistics
from itertools import combinations

raw = open("docs/data.js", encoding="utf-8").read()
D = json.loads(raw[len("const DATA = "):-2])
langs = {l["name"]: l["comparisonGroups"] for l in D["languages"]}
names = sorted(langs)

pairs = []
for a, b in combinations(names, 2):
    keys = set(langs[a]) | set(langs[b])
    inter = len(set(langs[a]) & set(langs[b]))
    union = len(keys)
    pairs.append({"a": a, "b": b, "shared": inter, "jaccard": inter / union})

jac = [p["jaccard"] for p in pairs]
sh = [p["shared"] for p in pairs]
print(f"=== {len(pairs)} pairs ===")
print(f"shared:  min={min(sh)} median={statistics.median(sh)} max={max(sh)}")
print(f"jaccard: min={min(jac):.2f} median={statistics.median(jac):.2f} "
      f"max={max(jac):.2f} mean={statistics.mean(jac):.2f} stdev={statistics.stdev(jac):.2f}")

pairs.sort(key=lambda p: -p["jaccard"])
print("\n=== Top 10 most similar (jaccard) ===")
for p in pairs[:10]:
    print(f"  {p['a']:<18} + {p['b']:<18} shared={p['shared']:>2} jaccard={p['jaccard']:.2f}")
print("\n=== Bottom 10 least similar ===")
for p in pairs[-10:]:
    print(f"  {p['a']:<18} + {p['b']:<18} shared={p['shared']:>2} jaccard={p['jaccard']:.2f}")

# per-language best friend / total stranger
print("\n=== Best friend / stranger per language (jaccard) ===")
by_lang = {n: [] for n in names}
for p in pairs:
    by_lang[p["a"]].append((p["jaccard"], p["shared"], p["b"]))
    by_lang[p["b"]].append((p["jaccard"], p["shared"], p["a"]))
for n in names:
    fr = max(by_lang[n]); st = min(by_lang[n])
    print(f"  {n:<18} friend: {fr[2]:<18} ({fr[0]:.2f})   stranger: {st[2]:<18} ({st[0]:.2f})")

print("\n=== English's ranked neighbors ===")
for j, s, other in sorted(by_lang["English"], reverse=True):
    print(f"  {other:<18} shared={s:>2} jaccard={j:.2f}")
