#!/usr/bin/env python3
"""Show what PHOIBLE actually contains for Japanese: phonemes + Allophones column."""
import csv
from collections import defaultdict

inventories = defaultdict(list)
with open("data/phoible.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["LanguageName"].lower() == "japanese":
            inventories[(row["InventoryID"], row["Source"])].append(row)

for (inv_id, source), rows in sorted(inventories.items()):
    n_with_allo = sum(1 for r in rows if r["Allophones"] not in ("", "NA"))
    print(f"\n=== InventoryID {inv_id} | source={source} | {len(rows)} phonemes | {n_with_allo} rows with allophone data ===")

# Detail: pick the inventory with the most allophone data
best = max(inventories.items(),
           key=lambda kv: sum(1 for r in kv[1] if r["Allophones"] not in ("", "NA")))
(inv_id, source), rows = best
print(f"\n--- Detail for InventoryID {inv_id} ({source}): phoneme -> allophones ---")
for r in sorted(rows, key=lambda r: r["Phoneme"]):
    allo = r["Allophones"]
    if allo not in ("", "NA") and allo != r["Phoneme"]:
        print(f"  /{r['Phoneme']}/  ->  [{allo}]")

# The actual 3-state check for a few famous English phonemes
print("\n--- Mechanical 3-state check vs English phonemes ---")
phonemes = {r["Phoneme"] for r in rows}
allophones = set()
for r in rows:
    if r["Allophones"] not in ("", "NA"):
        allophones.update(r["Allophones"].split())

for eng, label in [("f", "/f/"), ("ɸ", "[ɸ] (f-like)"), ("ʃ", "/ʃ/ (sh)"), ("ɕ", "[ɕ] (sh-like)"),
                   ("v", "/v/"), ("θ", "/θ/ (th)"), ("l", "/l/"), ("ŋ", "/ŋ/ (ng)"),
                   ("t̠ʃ", "/tʃ/ (ch)"), ("tɕ", "[tɕ] (ch-like)")]:
    if eng in phonemes:
        state = "FULL (phoneme)"
    elif eng in allophones:
        state = "HALF-FILL (allophone/variant)"
    else:
        state = "EMPTY (absent)"
    print(f"  {label:22s} -> {state}")
