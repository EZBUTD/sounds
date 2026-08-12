#!/usr/bin/env python3
"""Build docs/history_data.js — the English sound-flow diagram + timeline.

THE DIAGRAM
-----------
One horizontal trunk = English, running 400 -> 2000. Branches flow IN (a sound
English acquired) and OUT (a sound it lost). An outflow does not just stop: where
the sound survives in a relative, its path continues to the present under that
language's name, which is the "how gh continues on in German" reading.

WHY THIS IS A BUILD SCRIPT
--------------------------
Every other page here is generated from PHOIBLE, so its claims are checkable by
construction. This page is not: PHOIBLE records languages as spoken today and has
no Old or Middle English, so dates and sound changes are hand-authored from
published histories linked on the page.

But each branch END is a claim about the PRESENT — "English has /ʒ/ today",
"German and Dutch still have /x/", "French itself later lost /dʒ/" — and a
hand-authored claim about the present can silently contradict the inventories the
rest of the site charts. So this script does not take those on trust:

    inflow            -> English MUST list the sound today
    outflow           -> English must NOT, and every named survivor MUST
    donor "has"/"lost"-> checked against that donor's inventory

It exits non-zero on any disagreement, and refuses a symbol with no audio (a
control that looks clickable and plays nothing).

Run:  python3 build_history_data.py     (then python3 stamp_assets.py)
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT.parent / "docs" / "history_data.js"

# ---------------------------------------------------------------- year scale
SCALE = {
    "from": 400,
    "to": 2000,
    "ticks": [500, 800, 1100, 1400, 1700, 2000],
    "eras": [
        {"from": 450, "to": 1150, "label": "Old English"},
        {"from": 1150, "to": 1500, "label": "Middle English"},
        {"from": 1500, "to": 2000, "label": "Modern English"},
    ],
}

# ---------------------------------------------------------------- the flows
# dir "in"  : a sound English acquired.
#   source   display label for where it came from ("Norman French", "inside English")
#   srcRoster roster language to verify a present-day claim about, or None
#   srcFate  "has" | "lost" — verified against srcRoster's inventory today
#   words    [[language, word, gloss], ...] hand-entered cognates, never mined
# dir "out" : a sound English lost.
#   survives [[language, word, gloss], ...] — each language verified to have it
#   gone     True when it survives nowhere in the roster (draws a ✕)
FLOWS = [
    {
        "sym": "tʃ",
        "dir": "in",
        "year": 700,
        "label": "the ch of church",
        "source": "inside English",
        "srcRoster": None,
        "srcFate": None,
        "how": "Old English softened an inherited {{k}} before front vowels. "
               "German and Dutch kept the {{k}}, which is why the same word is "
               "<em lang=\"de\">Kirche</em> and <em lang=\"nl\">kerk</em>.",
        "words": [["English", "church", ""],
                  ["German", "Kirche", "kept the k"],
                  ["Dutch", "kerk", "kept the k"]],
    },
    {
        "sym": "v",
        "dir": "in",
        "year": 1200,
        "label": "the v of veal",
        "source": "Norman French",
        "srcRoster": "French",
        "srcFate": "has",
        "how": "English already made a {{v}} sound, but only between voiced "
               "sounds — never at the start of a word. French loans put it "
               "there, and <em>fine</em>/<em>vine</em> came to differ by that "
               "alone.",
        "words": [["English", "veal", "from Old French"],
                  ["French", "veau", "calf"]],
    },
    {
        "sym": "z",
        "dir": "in",
        "year": 1200,
        "label": "the z of zeal",
        "source": "Norman French",
        "srcRoster": "French",
        "srcFate": "has",
        "how": "The same promotion as {{v}}: an in-between-vowels variant of "
               "{{s}} became a sound in its own right as French words carried it "
               "into new positions.",
        "words": [["English", "zeal", "from Old French"],
                  ["French", "zèle", "zeal"]],
    },
    {
        "sym": "dʒ",
        "dir": "in",
        "year": 1250,
        "label": "the j of judge",
        "source": "Norman French",
        "srcRoster": "French",
        "srcFate": "lost",
        "how": "English had the makings of this sound already, but the flood of "
               "French words carrying it is why it settled as a sound of its own. "
               "French then changed: it now says {{ʒ}} where it once said {{dʒ}}, "
               "so English keeps a sound its donor gave up.",
        "words": [["English", "judge", "from Old French juge"],
                  ["French", "juge", "now said with ʒ"]],
    },
    {
        "sym": "ʒ",
        "dir": "in",
        "year": 1650,
        "label": "the middle of measure",
        "source": "French",
        "srcRoster": "French",
        "srcFate": "has",
        "how": "English gained this sound through more than one route. French "
               "vocabulary supplied words in which it later appeared, while "
               "{{z}} and {{j}} also ran together inside English, as in some "
               "pronunciations of <em>as you</em>. It never got a letter of its own.",
        "words": [["English", "measure", ""],
                  ["French", "jour", "day"]],
    },
    {
        "sym": "y",
        "dir": "out",
        "year": 1300,
        "label": "the vowel of über",
        "how": "Old English <em>mȳs</em> had a rounded front vowel. English "
               "unrounded it, and the word became <em>mice</em> — before the "
               "Great Vowel Shift, which then moved the result again.",
        "survives": [["German", "über", "over"],
                     ["Dutch", "vuur", "fire"],
                     ["French", "tu", "you"]],
        "gone": False,
    },
    {
        "sym": "x",
        "dir": "out",
        "year": 1500,
        "label": "the ⟨gh⟩ of knight",
        "how": "An ordinary English sound, written ⟨gh⟩ in <em>knight</em> and "
               "<em>thought</em>. It left the language but not the spelling — "
               "sometimes hardening to {{f}} instead, which is why "
               "<em>enough</em> and <em>laugh</em> end as they do while "
               "<em>though</em> ends in nothing.",
        "survives": [["German", "Nacht", "night"],
                     ["Dutch", "nacht", "night"]],
        "gone": False,
    },
]

# Languages named in a `survives` list that are NOT in the roster cannot be
# verified, so they must be marked as such in the copy and skipped by the check.
# Currently empty: Scots was the only such language and it left with the /x/ rows.
# The mechanism stays, because the moment a flow names an uncharted language again
# the checks below force it to disclose that in its own gloss.
UNVERIFIED_LANGS: set[str] = set()

# ---------------------------------------------------------------- timeline copy
CLUSTERS = {"sk": "sk", "kn": "kn", "gn": "gn", "zj": "zj"}

EVENTS = [
    {
        "when": "about 450 to 1050",
        "kind": "gained",
        "title": "Old English",
        "body": "West Germanic dialects arrive in Britain. Before certain vowels "
                "{{sk}} softens to {{ʃ}} (<em>ship</em>, written ⟨sc⟩ then), and "
                "a parallel change gives {{tʃ}} in <em>church</em>.",
    },
    {
        "when": "about 793 to 1050",
        "kind": "shifted",
        "title": "Old Norse brings sk back",
        "body": "Norse had not undergone that softening, so its {{sk}} arrived "
                "intact and English kept both outcomes of one original word: "
                "<em>shirt</em> from the English line, <em>skirt</em> from the "
                "Norse — likewise <em>shell</em>/<em>skull</em>.",
    },
    {
        "when": "from 1066",
        "kind": "gained",
        "title": "The Norman Conquest",
        "body": "French becomes the language of court, and a large layer of "
                "vocabulary follows. French loans help {{v}}, {{z}} and {{dʒ}} "
                "appear in more positions and become firmly established as "
                "separate English sounds; changes inside English also contributed.",
    },
    {
        "when": "about 1400 to 1700",
        "kind": "shifted",
        "title": "The Great Vowel Shift",
        "body": "English's long vowels move in a chain. <em>Name</em> once had a "
                "more open, ah-like vowel, while <em>mine</em> had an ee-like one. "
                "The highest vowels broke into gliding vowels, helping produce "
                "today's <em>mine</em> and <em>house</em>.",
    },
    {
        "when": "from 1476",
        "kind": "shifted",
        "title": "Printing helps spelling settle",
        "body": "Caxton sets up England's first press at Westminster. Spelling "
                "settles toward its modern form over the next two centuries — "
                "while the vowels were still moving and ⟨gh⟩ was still being "
                "lost. Printing helped spread and stabilize conventions, but the "
                "process was gradual rather than one moment when spelling froze.",
    },
    {
        "when": "about 1600 to 1700",
        "kind": "lost",
        "title": "kn becomes n",
        "body": "The {{k}} in <em>knight</em> and <em>knee</em> stops being "
                "pronounced, with the {{ɡ}} of <em>gnaw</em>. Neither sound left "
                "the language — the cluster did. The letters stayed.",
    },
    {
        "when": "1600s to now",
        "kind": "shifted",
        "title": "Global spread",
        "body": "English is now learned as an additional language by more people "
                "than speak it first, and every accent has its own inventory — "
                "so \"English sounds\" is a family, not a list. The Sound Chart "
                "plots one variety, Received Pronunciation.",
    },
]

COGNATES = [
    ["knight", "Knecht", "German sense shifted to “servant, farmhand”"],
    ["night", "Nacht", "same meaning"],
    ["light", "Licht", "same meaning"],
    ["eight", "acht", "same meaning"],
    ["thought", "gedacht", "German is the past participle, “thought”"],
    ["enough", "genug", "here the English ⟨gh⟩ hardened to f"],
]


def load_data_js():
    src = (ROOT.parent / "docs" / "data.js").read_text(encoding="utf-8")
    m = re.search(r"const DATA\s*=\s*(\{.*\});?\s*$", src.strip(), re.S)
    if not m:
        m = re.search(r"=\s*(\{.*\})\s*;?\s*$", src.strip(), re.S)
    if not m:
        sys.exit("build_history_data: could not parse docs/data.js")
    data = json.loads(m.group(1))
    inv = {l["name"]: set(l["phonemes"]) for l in data["languages"]}
    return inv, set(data["audio"].keys()), len(data["languages"])


def verify(inv, audio):
    problems = []
    english = inv["English"]
    for f in FLOWS:
        sym, d = f["sym"], f["dir"]
        if sym not in audio:
            problems.append(f"{sym}: no audio, so it cannot be a playable chip")
        if len(sym) > 1 and sym not in ("tʃ", "dʒ"):
            problems.append(f"{sym}: multi-segment symbol on the trunk")
        if not (SCALE["from"] <= f["year"] <= SCALE["to"]):
            problems.append(f"{sym}: year {f['year']} is outside the scale")
        if not f.get("words") and not f.get("survives"):
            problems.append(f"{sym}: no example words")

        if d == "in":
            if sym not in english:
                problems.append(
                    f"{sym}: drawn flowing INTO English, but English does not "
                    f"list it today")
            # a donor claim about the present must hold
            if f.get("srcRoster"):
                if f["srcRoster"] not in inv:
                    problems.append(f"{sym}: unknown donor {f['srcRoster']}")
                else:
                    present = sym in inv[f["srcRoster"]]
                    if f["srcFate"] == "has" and not present:
                        problems.append(
                            f"{sym}: donor {f['srcRoster']} is marked as still "
                            f"having it, but does not list it today")
                    if f["srcFate"] == "lost" and present:
                        problems.append(
                            f"{sym}: donor {f['srcRoster']} is marked as having "
                            f"lost it, but lists it today")
            elif f.get("srcFate"):
                problems.append(f"{sym}: srcFate set with no roster language to "
                                f"check it against")
        elif d == "out":
            if sym in english:
                problems.append(
                    f"{sym}: drawn flowing OUT of English, but English lists it "
                    f"today")
            named = [w[0] for w in f.get("survives", [])]
            checkable = [n for n in named if n not in UNVERIFIED_LANGS]
            if not checkable and not f.get("gone"):
                problems.append(f"{sym}: no verifiable survivor and not marked gone")
            for lang in checkable:
                if lang not in inv:
                    problems.append(f"{sym}: survivor {lang} is not in the roster "
                                    f"and is not flagged unverified")
                elif sym not in inv[lang]:
                    problems.append(
                        f"{sym}: drawn surviving in {lang}, which does not list "
                        f"it today")
            if f.get("gone") and checkable:
                problems.append(f"{sym}: marked gone but names survivors")
            # an unverifiable survivor must say so in its gloss
            for lang, _word, gloss in f.get("survives", []):
                if lang in UNVERIFIED_LANGS and "not charted" not in gloss:
                    problems.append(
                        f"{sym}: {lang} is not in the roster, so its gloss must "
                        f"say the claim is not checked against the data")
        else:
            problems.append(f"{sym}: unknown direction {d!r}")

    # every embedded token must be a real symbol with audio, or a declared cluster
    bodies = [e["body"] for e in EVENTS] + [f["how"] for f in FLOWS]
    for text in bodies:
        for tok in re.findall(r"\{\{([^}]+)\}\}", text):
            if tok in CLUSTERS:
                continue
            if tok not in audio:
                problems.append(f"token {{{{{tok}}}}} has no audio file")
    return problems


def main():
    inv, audio, n_langs = load_data_js()
    problems = verify(inv, audio)
    if problems:
        print("build_history_data: verification FAILED", file=sys.stderr)
        for p in problems:
            print("  -", p, file=sys.stderr)
        sys.exit(1)

    payload = {
        "scale": SCALE,
        "flows": FLOWS,
        "unverifiedLangs": sorted(UNVERIFIED_LANGS),
        "events": EVENTS,
        "clusters": CLUSTERS,
        "cognates": COGNATES,
    }
    OUT.write_text(
        "// GENERATED by build_history_data.py — do not edit by hand.\n"
        "// Every branch end is verified against docs/data.js at build time.\n"
        "const HIST = " + json.dumps(payload, ensure_ascii=False,
                                     separators=(",", ":")) + ";\n",
        encoding="utf-8")

    ins = [f for f in FLOWS if f["dir"] == "in"]
    outs = [f for f in FLOWS if f["dir"] == "out"]
    # every direction gets reported: an earlier version listed only in/out, so the
    # "back" flow was silently absent from the build summary even though it was
    # generated and verified
    if len(ins) + len(outs) != len(FLOWS):
        sys.exit("build_history_data: a flow has an unreported direction")
    print(f"wrote {OUT.relative_to(ROOT)}  "
          f"({len(ins)} inflows, {len(outs)} outflows, {len(EVENTS)} events)")
    print(f"  verified against {n_langs} charted inventories")
    for f in ins:
        src = f["source"]
        fate = f" ({f['srcRoster']} {f['srcFate']} it today)" if f.get("srcRoster") else ""
        print(f"  IN   {f['sym']:<3} {f['year']:>4}  from {src}{fate}")
    for f in outs:
        who = ", ".join(w[0] for w in f["survives"])
        print(f"  OUT  {f['sym']:<3} {f['year']:>4}  survives in {who}")


if __name__ == "__main__":
    main()
