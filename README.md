# Spoken Sounds Across the World

An interactive look at the sounds human languages use — which ones they share,
which are rare, and what happens to a learner caught between two inventories.
Built for VizCon 2026.

**Live site:** https://ezbutd.github.io/sounds/

## What's here

Seven pages, all static HTML:

| Page | What it shows |
|---|---|
| **Sound Chart** | An IPA grid for any two of 34 languages side by side, with 117 playable recordings |
| **World Map** | Where each language's speakers are, and how its sounds compare to its neighbours' |
| **Allophones** | Why two languages can "share" a sound and still sound different |
| **Seeing Sounds** | Spectrograms — what these sounds look like as sound |
| **History of English** | A flow diagram of sounds entering and leaving English since 400 CE |
| **Difficulty in Learning** | Whether an unfamiliar sound inventory predicts how many people learn a language (mostly, it doesn't) |
| **About & Sources** | Every dataset, licence, and known limitation |

## Data

Everything traces to public, citable sources. The full table with licences is on
the [About page](https://ezbutd.github.io/sounds/about.html); in short:

- **[PHOIBLE 2.0](https://phoible.org)** (CC BY-SA 3.0) — sound inventories for
  2,177 languages, the backbone of every count and comparison here
- **[Wikimedia Commons](https://commons.wikimedia.org)** — all 117 audio
  recordings, each credited to its author in `audio_manifest.csv`
- **[WikiPron](https://github.com/CUNY-CL/wikipron)** (CC BY-SA) — example words
- **[Glottolog](https://glottolog.org)** (CC BY 4.0) — classification, coordinates
- **[Unicode CLDR](https://cldr.unicode.org/)**, US Census ACS, UK ONS, Statistics
  Canada, and others for speaker counts

Historical claims on the History of English page are **not** from PHOIBLE, which
records languages as spoken today. Those come from published histories, cited on
the page itself.

## What this can't tell you

PHOIBLE covers 2,177 of roughly 7,000 living languages, and its coverage is
skewed toward languages that have received sustained academic attention. One
inventory is used per language, so "English" here means one analysis of Received
Pronunciation rather than English in general. Where two sources disagree, the
seams are documented rather than smoothed over — see
[About & Sources](https://ezbutd.github.io/sounds/about.html) and `SCOPING.md`.

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

## Repository layout

```
docs/            the site itself — this is what GitHub Pages serves
  *.html         seven pages
  *.js           generated data bundles + page scripts
  audio/         117 phoneme recordings (Wikimedia Commons)
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
