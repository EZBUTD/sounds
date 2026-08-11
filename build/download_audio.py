#!/usr/bin/env python3
"""
Download Wikimedia Commons audio for ALL IPA chart symbols used by the visual
(v2: full chart, base-normalized symbol keys).

- Uses curl (macOS system python urllib fails SSL on wikimedia).
- Commons 429-rate-limits bursts: retries with hard backoff + paces requests.
- Filenames on disk: audio/u<hex codepoints>.ogg (unambiguous, case-safe).
- Manifest: audio_manifest.csv (phoneme, file, commons_file, commons_url,
  resolved, audio_kind, license_note).
- English diphthongs (off-chart extras) keep word-example fallbacks.

Idempotent: cached files are skipped, so rerun until 100%.
"""
import csv
import os
import subprocess
import time
import urllib.parse

AUDIO_DIR = "audio"
MANIFEST = "audio_manifest.csv"
UA = "SpokenSoundsAcrossTheWorld/1.0 (data-viz research; https://github.com/EZBUTD/sounds)"

F = {
    # --- pulmonic consonants: plosives ---
    "p": ["Voiceless bilabial plosive.ogg"], "b": ["Voiced bilabial plosive.ogg"],
    "t": ["Voiceless alveolar plosive.ogg"], "d": ["Voiced alveolar plosive.ogg"],
    "ʈ": ["Voiceless retroflex stop.oga", "Voiceless retroflex plosive.ogg"],
    "ɖ": ["Voiced retroflex stop.oga", "Voiced retroflex plosive.ogg"],
    "c": ["Voiceless palatal plosive.ogg"], "ɟ": ["Voiced palatal plosive.ogg"],
    "k": ["Voiceless velar plosive.ogg"], "ɡ": ["Voiced velar plosive 02.ogg", "Voiced velar plosive.ogg"],
    "q": ["Voiceless uvular plosive.ogg"], "ɢ": ["Voiced uvular stop.oga", "Voiced uvular plosive.ogg"],
    "ʔ": ["Glottal stop.ogg"],
    # --- nasals ---
    "m": ["Bilabial nasal.ogg"], "ɱ": ["Labiodental nasal.ogg"],
    "n": ["Alveolar nasal.ogg"], "ɳ": ["Retroflex nasal.ogg"],
    "ɲ": ["Palatal nasal.ogg"], "ŋ": ["Velar nasal.ogg"], "ɴ": ["Uvular nasal.ogg"],
    # --- trills ---
    "ʙ": ["Bilabial trill.ogg"], "r": ["Alveolar trill.ogg"], "ʀ": ["Uvular trill.ogg"],
    # --- taps/flaps ---
    "ⱱ": ["Labiodental flap.ogg", "Labiodental flap.oga"],
    "ɾ": ["Alveolar tap.ogg"], "ɽ": ["Retroflex flap.ogg"],
    # --- fricatives ---
    "ɸ": ["Voiceless bilabial fricative.ogg"], "β": ["Voiced bilabial fricative.ogg"],
    "f": ["Voiceless labiodental fricative.ogg", "Voiceless labio-dental fricative.ogg"],
    "v": ["Voiced labiodental fricative.ogg", "Voiced labio-dental fricative.ogg"],
    "θ": ["Voiceless Dental Fricative.ogg", "Voiceless dental fricative.ogg"],
    "ð": ["Voiced dental fricative.ogg"],
    "s": ["Voiceless alveolar sibilant.ogg"], "z": ["Voiced alveolar sibilant.ogg"],
    "ʃ": ["Voiceless palato-alveolar sibilant.ogg"], "ʒ": ["Voiced palato-alveolar sibilant.ogg"],
    "ʂ": ["Voiceless retroflex sibilant.ogg", "Voiceless retroflex fricative.ogg"],
    "ʐ": ["Voiced retroflex sibilant.ogg", "Voiced retroflex fricative.ogg"],
    "ç": ["Voiceless palatal fricative.ogg"], "ʝ": ["Voiced palatal fricative.ogg"],
    "x": ["Voiceless velar fricative.ogg"], "ɣ": ["Voiced velar fricative.ogg"],
    "χ": ["Voiceless uvular fricative.ogg"], "ʁ": ["Voiced uvular fricative.ogg"],
    "ħ": ["Voiceless pharyngeal fricative.ogg"], "ʕ": ["Voiced pharyngeal fricative.ogg"],
    "h": ["Voiceless glottal fricative.ogg"], "ɦ": ["Voiced glottal fricative.ogg"],
    "ɬ": ["Voiceless alveolar lateral fricative.ogg"], "ɮ": ["Voiced alveolar lateral fricative.ogg"],
    # --- approximants ---
    "ʋ": ["Labiodental approximant.ogg"], "ɹ": ["Alveolar approximant.ogg"],
    "ɻ": ["Retroflex approximant.ogg"], "j": ["Palatal approximant.ogg"],
    "ɰ": ["Voiced velar approximant.ogg"],
    "l": ["Alveolar lateral approximant.ogg"], "ɭ": ["Retroflex lateral approximant.ogg"],
    "ʎ": ["Palatal lateral approximant.ogg"], "ʟ": ["Velar lateral approximant.ogg"],
    # --- co-articulated ---
    "w": ["Voiced labio-velar approximant.ogg"], "ʍ": ["Voiceless labio-velar fricative.ogg"],
    "ɥ": ["Voiced labialized post-palatal approximant.ogg", "Labial-palatal approximant.ogg"],
    "ɕ": ["Voiceless alveolo-palatal sibilant.ogg", "Voiceless alveolo-palatal fricative.ogg"],
    "ʑ": ["Voiced alveolo-palatal sibilant.ogg", "Voiced alveolo-palatal fricative.ogg"],
    "ɺ": ["Voiced alveolar lateral flap.wav", "Alveolar lateral flap.ogg"],
    # --- affricates ---
    "ts": ["Voiceless alveolar sibilant affricate.oga", "Voiceless alveolar affricate.ogg"],
    "dz": ["Voiced alveolar sibilant affricate.oga", "Voiced alveolar affricate.ogg"],
    "tʃ": ["Voiceless palato-alveolar affricate.ogg"], "dʒ": ["Voiced palato-alveolar affricate.ogg"],
    "tɕ": ["Voiceless alveolo-palatal affricate.oga", "Voiceless alveolo-palatal affricate.ogg"],
    "dʑ": ["Voiced alveolo-palatal affricate.oga", "Voiced alveolo-palatal affricate.ogg"],
    # --- clicks & implosives ---
    "ʘ": ["Clic bilabial sourd.oga", "Bilabial click.ogg"],
    "ǀ": ["Dental click.ogg"], "ǃ": ["Postalveolar click.ogg", "Alveolar click.oga"],
    "ǂ": ["Palatoalveolar click.ogg", "Palatal click.ogg"], "ǁ": ["Alveolar lateral click.ogg"],
    "ɓ": ["Voiced bilabial implosive.ogg"], "ɗ": ["Voiced alveolar implosive.ogg"],
    "ʄ": ["Voiced palatal implosive.ogg"], "ɠ": ["Voiced velar implosive.ogg"],
    "ʛ": ["Voiced uvular implosive.ogg"],
    # --- vowels ---
    "i": ["Close front unrounded vowel.ogg"], "y": ["Close front rounded vowel.ogg"],
    "ɨ": ["Close central unrounded vowel.ogg"], "ʉ": ["Close central rounded vowel.ogg"],
    "ɯ": ["Close back unrounded vowel.ogg"], "u": ["Close back rounded vowel.ogg"],
    "ɪ": ["Near-close near-front unrounded vowel.ogg"], "ʏ": ["Near-close near-front rounded vowel.ogg"],
    "ʊ": ["Near-close near-back rounded vowel.ogg"],
    "e": ["Close-mid front unrounded vowel.ogg"], "ø": ["Close-mid front rounded vowel.ogg"],
    "ɘ": ["Close-mid central unrounded vowel.ogg"], "ɵ": ["Close-mid central rounded vowel.ogg"],
    "ɤ": ["Close-mid back unrounded vowel.ogg"], "o": ["Close-mid back rounded vowel.ogg"],
    "ə": ["Mid-central vowel.ogg"],
    "ɛ": ["Open-mid front unrounded vowel.ogg"], "œ": ["Open-mid front rounded vowel.ogg"],
    "ɜ": ["Open-mid central unrounded vowel.ogg"], "ɞ": ["Open-mid central rounded vowel.ogg"],
    "ʌ": ["Open-mid back unrounded vowel.ogg"], "ɔ": ["Open-mid back rounded vowel.ogg"],
    "æ": ["Near-open front unrounded vowel.ogg"], "ɐ": ["Near-open central unrounded vowel.ogg"],
    "a": ["Open front unrounded vowel.ogg"], "ɶ": ["Open front rounded vowel.ogg"],
    "ɑ": ["Open back unrounded vowel.ogg"], "ɒ": ["Open back rounded vowel.ogg"],
    # --- English diphthongs (word-example fallbacks; off-chart extras) ---
    "aɪ": ["En-us-eye.ogg"], "aʊ": ["En-us-ow.ogg"], "eɪ": ["En-us-hey.ogg"],
    "əʊ": ["En-uk-oh.ogg"], "ɔɪ": ["En-us-boy.ogg"], "ɪə": ["En-uk-ear.ogg"],
    "eə": ["En-uk-air.ogg"], "ʊə": ["En-us-tour.ogg"],
}
WORD_BASED = {"aɪ", "aʊ", "eɪ", "əʊ", "ɔɪ", "ɪə", "eə", "ʊə"}


def slug(sym: str) -> str:
    return "u" + "_".join(f"{ord(c):04x}" for c in sym)


def try_download(commons_name, dest):
    url = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
           + urllib.parse.quote(commons_name))
    r = subprocess.run(
        ["curl", "-sL", "--max-time", "30", "-A", UA,
         "-o", dest, "-w", "%{http_code}", url],
        capture_output=True, text=True)
    code = r.stdout.strip()
    ok = (r.returncode == 0 and code == "200"
          and os.path.exists(dest) and os.path.getsize(dest) > 1000)
    if not ok and os.path.exists(dest):
        os.remove(dest)
    return ok, url, code


def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    manifest, missing = [], []
    for sym, candidates in F.items():
        dest = os.path.join(AUDIO_DIR, f"{slug(sym)}.ogg")
        resolved, used_name, used_url = False, "", ""
        if os.path.exists(dest) and os.path.getsize(dest) > 1000:
            resolved, used_name = True, "(cached)"
        else:
            for name in candidates:
                for attempt in range(4):
                    ok, url, code = try_download(name, dest)
                    if ok:
                        resolved, used_name, used_url = True, name, url
                        break
                    if code == "404":
                        break  # wrong filename; try next candidate, don't retry
                    time.sleep(5 * (attempt + 1))  # 429 backoff
                if resolved:
                    break
            time.sleep(1.5)
        manifest.append({
            "phoneme": sym, "file": f"{slug(sym)}.ogg" if resolved else "",
            "commons_file": used_name, "commons_url": used_url, "resolved": resolved,
            "audio_kind": "word_example" if sym in WORD_BASED else "isolated_phoneme",
            "license_note": "verify on Commons file page before publishing" if resolved else "",
        })
        print(f"  [{'ok ' if resolved else 'MISS'}] {sym:>3}  {used_name if resolved else candidates[0]}")
        if not resolved:
            missing.append(sym)

    with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
        w.writeheader(); w.writerows(manifest)
    n_ok = sum(1 for m in manifest if m["resolved"])
    print(f"\n{n_ok}/{len(manifest)} symbols resolved -> {MANIFEST}")
    if missing:
        print("Missing:", " ".join(missing))


if __name__ == "__main__":
    main()
