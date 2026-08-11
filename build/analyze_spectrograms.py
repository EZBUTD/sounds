#!/usr/bin/env python3
"""
Precompute spectrograms + voice-onset-time segmentation for the word recordings,
and emit prototype/spectro.js for the Spectrograms page.

WHY PRECOMPUTE INSTEAD OF ANALYSING IN THE BROWSER
Safari only gained Ogg Vorbis support in 18.4, and older Safari cannot
decodeAudioData() an .ogg at all. Our <audio> playback degrades quietly there,
but an in-browser spectrogram would render an empty canvas with no explanation.
Precomputing means every visitor sees the same picture regardless of codec
support, and the page stays a static site with no runtime dependency.

WHAT IS MEASURED
Voice onset time (VOT): the gap between a stop's release burst and the onset of
voicing. It is the standard acoustic correlate of aspiration:
  - English word-initial /t/ ("top")  -> long VOT, ~50-90 ms   (aspirated [tʰ])
  - /t/ after /s/ ("stop")            -> short VOT, ~0-30 ms    (unaspirated [t])
This is a real measurement of the recordings we ship, not an assertion copied
from a textbook — which matters, because an earlier version of the allophones
page claimed an unreleased [t̚] in "cat" that the recording did not dependably
contain.

SEGMENTATION METHOD, AND THREE DETECTORS THAT FAILED FIRST
A stop is: [closure] -> [burst] -> [aspiration] -> [voicing]. The closure is the
anchor. Rejected approaches, recorded so they are not retried:
  1. "Sharpest energy rise" put the burst at the END of the aspiration (at the
     vowel), reporting VOT=5ms for "top" — i.e. no aspiration at all.
  2. High-frequency energy RATIO (hf/total) to find the noisy stretch: unstable
     in quiet frames, so the backward walk stopped early. VOT=0ms.
  3. ABSOLUTE high-frequency energy, walking back from the vowel: right for "top"
     (66ms) but for "stop" it walked back THROUGH the /s/ frication — also
     high-frequency noise — giving a nonsense 174ms.
Anchoring on the closure works with or without a preceding /s/, because the
closure always sits between the /s/ and the burst.

Verified against a frame-by-frame hand read of both files:
  top   closure 54ms, burst 86ms  (HF -16 -> +13 dB), vowel 156ms -> VOT 70ms
  stop  /s/ 160-290ms, closure 302ms, burst 306ms, vowel 332ms -> VOT 26ms
"""
import json

import numpy as np
import soundfile as sf

AUDIO_DIR = "prototype/audio/"
OUT = "prototype/spectro.js"

# Spectrogram render settings. 25ms window is the usual "wideband" choice for
# seeing formants and bursts; 4ms hop keeps the burst from being smeared away.
WIN_MS, HOP_MS = 25.0, 4.0
FMAX = 8000          # speech detail lives below this; above it is mostly hiss
N_BANDS = 96         # rows in the shipped matrix
DB_FLOOR = -70       # everything quieter renders as background

# Finer frames for segmentation than for display: a 25ms window is too coarse to
# place a burst, which can be a single 5ms event.
SEG_WIN_MS, SEG_HOP_MS = 10.0, 2.0

# The phoneme both words store. This is the whole point of the section — two
# allophones of ONE phoneme — so it ships as data rather than being written into
# the page, where it could drift away from the `allophone` values below.
PHONEME = "t"

WORDS = [
    {"word": "top", "file": "en-us-top.ogg", "allophone": "tʰ",
     "label": "aspirated", "phonetic": "[tʰɑp]",
     "note": "word-initial: the release is followed by a puff of air"},
    {"word": "stop", "file": "en-us-stop.ogg", "allophone": "t",
     "label": "unaspirated", "phonetic": "[stɑp]",
     "note": "after /s/: the puff is suppressed, voicing starts almost at once"},
]


def load(name):
    x, sr = sf.read(AUDIO_DIR + name)
    if x.ndim > 1:            # "stop" is stereo, the others mono
        x = x.mean(axis=1)
    x = x.astype(float)
    return x / (np.abs(x).max() + 1e-12), sr


def frame(x, sr, win_ms, hop_ms):
    win, hop = int(sr * win_ms / 1000), int(sr * hop_ms / 1000)
    n = 1 + max(0, (len(x) - win) // hop)
    return np.array([x[i * hop : i * hop + win] for i in range(n)]), win, hop


def features(x, sr):
    """Frame-level features used for segmentation (not for display)."""
    fr, win, _ = frame(x, sr, SEG_WIN_MS, SEG_HOP_MS)
    S = np.abs(np.fft.rfft(fr * np.hanning(win), axis=1)) ** 2
    f = np.fft.rfftfreq(win, 1 / sr)
    db = lambda v: 10 * np.log10(v + 1e-12)
    return dict(
        t=np.arange(len(fr)) * SEG_HOP_MS,
        rms=np.sqrt((fr ** 2).mean(axis=1) + 1e-12),
        hi=db(S[:, f > 3000].sum(axis=1)),
        lo=db(S[:, (f > 100) & (f < 1000)].sum(axis=1)),
        zcr=(np.diff(np.sign(fr), axis=1) != 0).mean(axis=1),
    )


def segment(a):
    """-> dict(closure, burst, voice) in ms, anchored on the closure."""
    t, rms, hi, lo, zcr = a["t"], a["rms"], a["hi"], a["lo"], a["zcr"]
    peak = rms.max()

    # vowel: loud, periodic, low-frequency dominated
    vowel = (rms > 0.45 * peak) & (zcr < 0.10) & (lo > hi + 6)
    idx = np.where(vowel)[0]
    if not len(idx):
        raise ValueError("no vowel found")
    v = idx[0]
    while v > 0 and rms[v - 1] > 0.15 * peak and zcr[v - 1] < 0.14 \
            and lo[v - 1] > hi[v - 1]:
        v -= 1

    # closure: quietest frame in the 120ms before voicing
    lo_i = max(0, v - int(120 / SEG_HOP_MS))
    if v - lo_i < 3:
        raise ValueError("not enough room before voicing to find a closure")
    c = lo_i + int(np.argmin(rms[lo_i:v]))

    # burst: first frame after the closure where HF energy jumps clear of it
    floor = hi[c]
    b = next((i for i in range(c + 1, v + 1) if hi[i] > floor + 8), c + 1)
    return {"closureMs": round(float(t[c]), 1),
            "burstMs": round(float(t[b]), 1),
            "voiceMs": round(float(t[v]), 1),
            "votMs": round(float(t[v] - t[b]), 1)}


def spectrogram(x, sr):
    """-> (matrix as uint8 rows of frequency bands, times_ms, freqs_hz)."""
    fr, win, hop = frame(x, sr, WIN_MS, HOP_MS)
    S = np.abs(np.fft.rfft(fr * np.hanning(win), axis=1)) ** 2
    f = np.fft.rfftfreq(win, 1 / sr)
    keep = f <= FMAX
    S, f = S[:, keep], f[keep]
    # pool linear FFT bins into N_BANDS equal-width bands (linear frequency: a
    # mel scale would hide the high-frequency aspiration this page is about)
    edges = np.linspace(0, len(f), N_BANDS + 1).astype(int)
    band = np.array([S[:, edges[i]:max(edges[i] + 1, edges[i + 1])].mean(axis=1)
                     for i in range(N_BANDS)])           # (bands, frames)
    db = 10 * np.log10(band + 1e-12)
    db -= db.max()                                        # 0 dB = loudest point
    q = np.clip((db - DB_FLOOR) / (0 - DB_FLOOR), 0, 1)   # -> 0..1
    return (q * 255).astype(np.uint8), \
        (np.arange(band.shape[1]) * HOP_MS), \
        np.linspace(0, FMAX, N_BANDS)


def main():
    out = {"settings": {"winMs": WIN_MS, "hopMs": HOP_MS, "fmax": FMAX,
                        "bands": N_BANDS, "dbFloor": DB_FLOOR},
           # the phoneme both allophones belong to; the page labels each card
           # /phoneme/ -> [allophone] from this
           "phoneme": PHONEME,
           "words": []}

    print(f"{'word':<8} {'dur':>7} {'closure':>8} {'burst':>7} {'voice':>7} "
          f"{'VOT':>7}  verdict")
    print("-" * 62)
    for w in WORDS:
        x, sr = load(w["file"])
        seg = segment(features(x, sr))
        mat, times, freqs = spectrogram(x, sr)
        vot = seg["votMs"]
        verdict = ("aspirated" if vot >= 40 else
                   "unaspirated" if vot <= 30 else "ambiguous")
        print(f"{w['word']:<8} {len(x)/sr*1000:>6.0f}ms {seg['closureMs']:>7.0f} "
              f"{seg['burstMs']:>6.0f} {seg['voiceMs']:>6.0f} {vot:>6.0f}  {verdict}")
        if verdict == "ambiguous":
            raise SystemExit(
                f"{w['word']}: VOT {vot}ms is neither clearly aspirated nor "
                f"unaspirated. Do not ship a card claiming either.")
        out["words"].append({
            **{k: w[k] for k in
               ("word", "file", "allophone", "label", "phonetic", "note")},
            "durationMs": round(len(x) / sr * 1000, 1),
            "sampleRate": sr,
            **seg,
            "verdict": verdict,
            # rows are frequency bands low->high, values 0..255
            "spectrogram": [row.tolist() for row in mat],
            "timesMs": [round(float(t), 1) for t in times],
        })

    # the contrast the page is built on must actually hold
    vots = {w["word"]: w["votMs"] for w in out["words"]}
    gap = vots["top"] - vots["stop"]
    out["votGapMs"] = round(gap, 1)
    print(f"\nVOT gap: top {vots['top']:.0f}ms - stop {vots['stop']:.0f}ms "
          f"= {gap:.0f}ms")
    if gap < 25:
        raise SystemExit("VOT gap under 25ms — the aspiration contrast is not "
                         "clear in these recordings. Pick a different pair.")

    # The page labels each card "/PHONEME/ -> [allophone]". That claim is only
    # true if every allophone really is a realisation of that one phoneme, so
    # check it here rather than trusting the hand-written table above. An
    # allophone of /t/ must be /t/ plus diacritics, or a documented substitution
    # of it — a bare symbol that is not t-based would mean the section is
    # comparing two phonemes and calling them allophones.
    T_ALLOPHONES = {"t", "tʰ", "t̚", "ɾ", "ʔ", "t̪", "ʈ"}
    for w in out["words"]:
        a = w["allophone"]
        if a not in T_ALLOPHONES and not a.startswith(PHONEME):
            raise SystemExit(
                f"{w['word']}: [{a}] is not a documented allophone of "
                f"/{PHONEME}/. The page presents these cards as two allophones "
                f"of one phoneme; shipping an unrelated segment would make that "
                f"label false.")
        if a == PHONEME and w["label"] == "aspirated":
            raise SystemExit(
                f"{w['word']}: labelled aspirated but the allophone symbol is "
                f"plain [{a}] with no aspiration diacritic.")
    allos = [w["allophone"] for w in out["words"]]
    if len(set(allos)) != len(allos):
        raise SystemExit(f"two cards claim the same allophone {allos}; the "
                         f"section is a CONTRAST between allophones.")
    print(f"phoneme /{PHONEME}/ -> allophones " +
          ", ".join(f"[{a}]" for a in allos) + "  (all t-based, all distinct)")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("const SPECTRO = ")
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    import os
    print(f"wrote {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
