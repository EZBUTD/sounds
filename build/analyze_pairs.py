#!/usr/bin/env python3
"""
Pairwise overlap analysis across all 36 languages (630 pairs).

Two metrics per pair (one-to-one matches inside broad IPA categories):
  shared  = sum(min(entriesA, entriesB))
  jaccard = shared / sum(max(entriesA, entriesB))

This lets differently detailed source spellings match without discarding extra
contrastive entries when a language records more than one in the same category.

Prints: top/bottom pairs by jaccard, distribution stats, per-language
"best friend / stranger", and English's ranked list.
"""
import json
import statistics
from itertools import combinations

raw = open("prototype/data.js", encoding="utf-8").read()
D = json.loads(raw[len("const DATA = "):-2])
langs = {l["name"]: l["comparisonGroups"] for l in D["languages"]}
names = sorted(langs)

pairs = []
for a, b in combinations(names, 2):
    keys = set(langs[a]) | set(langs[b])
    inter = sum(min(len(langs[a].get(k, ())), len(langs[b].get(k, ())))
                for k in keys)
    union = sum(max(len(langs[a].get(k, ())), len(langs[b].get(k, ())))
                for k in keys)
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
