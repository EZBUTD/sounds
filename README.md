# Spoken Sounds Across the World

An interactive look at speech sounds around the world — which broad sound
categories selected language descriptions share, which are rare, and what they
may mean for learners.
Built for VizCon 2026.

**Live site:** https://ezbutd.github.io/sounds/

## What's here

Seven pages, all static HTML:

| Page | What it shows |
|---|---|
| **Sound Chart** | An IPA reference grid comparing two of 34 selected language descriptions, with original source transcriptions available as detail |
| **World Map** | Where each language's speakers are, and how its sounds compare to its neighbours' |
| **Sound Variants** | Why matching broad IPA labels can still have different phonetic realizations |
| **Seeing Sounds** | Spectrograms — what these sounds look like as sound |
| **History of English** | A flow diagram of sounds entering and leaving English since 400 CE |
| **Language Learners** | Potentially unfamiliar broad sound areas, and why they do not amount to a difficulty score |
| **About & Sources** | Every dataset, licence, and known limitation |

## Data

Everything traces to public, citable sources. The full table with licences is on
the [About page](https://ezbutd.github.io/sounds/about.html); in short:

- **[PHOIBLE 2.0](https://phoible.org)** (CC BY-SA 3.0) — 3,020 inventories
  covering 2,186 distinct languages; the rarity layer uses PHOIBLE's 2,177-entry
  sample of one inventory per Glottocode
- **[Wikimedia Commons](https://commons.wikimedia.org)** — 117 sound-label
  recordings plus three whole-word examples, credited in the audio manifests
- **[WikiPron](https://github.com/CUNY-CL/wikipron)** (CC BY-SA) — an optional
  build input for candidate example words; no mined entries are in the public bundle
- **[Glottolog](https://glottolog.org)** (CC BY 4.0) — classification, coordinates
- **[Unicode CLDR](https://cldr.unicode.org/)**, US Census ACS, UK ONS, Statistics
  Canada, and others for speaker counts

Historical claims on the History of English page are **not** from PHOIBLE, which
records languages as spoken today. Those come from published histories, cited on
the page itself.

## What this can't tell you

PHOIBLE is a large convenience sample rather than a census of roughly 7,000
living languages, and its coverage is skewed toward languages that have received
sustained academic attention. One
inventory is used per language, so "English" here means one analysis of Received
Pronunciation rather than English in general. Where two sources disagree, the
seams are documented rather than smoothed over — see
[About & Sources](https://ezbutd.github.io/sounds/about.html) and `SCOPING.md`.
The overlap score counts each occupied broad IPA area once. That reduces false
differences caused by source transcription detail while retaining detailed labels
in the tooltips as qualitative information. It is
not a claim that two languages possess one cross-language phoneme or pronounce the
matching categories identically.

## Running it locally

No build step. Any static server works:

```bash
cd docs
python3 -m http.server 8000
# then open http://localhost:8000
```

Opening `docs/index.html` directly as a `file://` URL mostly works, but some
browsers block audio playback from the filesystem, so the local server is the
safer option.

The comparison invariant test requires only Node:

```bash
node tests/comparison_consistency.mjs
node tests/site_integrity.mjs
```

## Repository layout

```
docs/            the site itself — this is what GitHub Pages serves
  *.html         seven pages
  *.js           generated data bundles + page scripts
  audio/         117 IPA sound recordings (Wikimedia Commons)
  shared.css
build/           the Python that generates the data bundles in docs/
  *.py
SCOPING.md       design decisions, dead ends, and why things are the way they are
GENAI_LOG.md     how an LLM was used, and every error it made that had to be caught
audio_manifest.csv       per-file audio attribution and licence
```

The raw source data (PHOIBLE's 23 MB CSV, WikiPron's 69 MB of TSVs) is **not**
committed — it is downloadable from the links above, and the scripts in `build/`
expect it in a sibling `data/` directory.

## Licence

Code is MIT (see `LICENSE`). The **data and audio are not mine to relicense**:
PHOIBLE, WikiPron and most Commons recordings are CC BY-SA, so if you reuse the
derived data bundles in `docs/*.js`, the share-alike terms of the upstream
sources apply. Individual audio credits are in `audio_manifest.csv`.
