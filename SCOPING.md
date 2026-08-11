# "Spoken Sounds Across the World" — Scoping

> Renamed 2026-08-10 from "The Sounds Your Language Never Gave You".
> The original framed the subject as a deficit in the reader's language;
> the new title describes what the project actually shows.

Core viz: matrix of English phonemes × top ~30 native languages, showing which
English sounds don't exist in each L1 — the raw material of every accent.
Stretch: accent-similarity map from Speech Accent Archive embeddings (idea #1).

## Datasets

### Backbone (symbolic, no audio)
- **PHOIBLE 2.0** — https://phoible.org | CSV: https://github.com/phoible/dev (data/phoible.csv)
  - 3,020 inventories, 2,186 languages, IPA segments + 37 distinctive features
  - License: CC-BY-SA 3.0
  - ⚠️ Multiple inventories per language (English has ~10). Dedup rule needed:
    prefer source = "SPA" or "UZ", or largest inventory, or majority-vote segments.
- **English target inventory**: use PHOIBLE's English (choose GenAm) ~39-40 phonemes.

### Per-phoneme audio (matrix cell click → sound)
- **Wikimedia Commons IPA recordings** — files behind:
  - https://en.wikipedia.org/wiki/IPA_consonant_chart_with_audio
  - https://en.wikipedia.org/wiki/IPA_vowel_chart_with_audio
  - Freely licensed .ogg, predictable names (e.g. Voiced_dental_fricative.ogg)
- ❌ IPA Handbook audio (internationalphoneticassociation.org): license forbids
  embedding in another product. Do not use.

### Words demonstrating phonemes across languages (depth layer)
- **UCLA Phonetics Lab Archive** — http://archive.phonetics.ucla.edu
  - Scholarly word-list recordings for 100s of languages, WAV/MP3 + transcriptions
- **Lingua Libre** — https://lingualibre.org — ~1M crowdsourced word recordings,
  150+ languages, CC BY-SA, bulk download
- **WikiPron** — https://github.com/CUNY-CL/wikipron — word→IPA pairs scraped
  from Wiktionary; use to FIND words containing a target phoneme, then link
  Commons audio where it exists
- **Common Voice** — sentence-level, 100+ languages, CC0 (only if needed)

### Allophone / "variant" state data
- **PHOIBLE `Allophones` column** (in main phoible.csv) — each phoneme row lists
  documented allophones in IPA. Core mechanic: English phoneme X appears in
  language Y's Allophones (but not Phonemes) → "variant" state.
  ⚠️ Coverage varies by source: SPA/PH/AA/EA document allophones; UPSID does NOT.
  Dedup rule must prefer allophone-bearing sources for top-30 languages.
- **AlloPhoible** — https://github.com/Aariciah/allophoible — normalized PHOIBLE
  allophones + distinctive-feature vectors per allophone
- **PanPhon** — https://github.com/dmort27/panphon — IPA segment → 24-dim
  articulatory feature vector; gives similarity distance between any two sounds.
  Use for "nearest sound your language DOES have" tooltip (predicted accent
  substitution, e.g. English /ɹ/ → Japanese /ɾ/). Not a cell state.

### Loanword adaptation examples (coffee→koohii genre)
- **WOLD (World Loanword Database)** — https://wold.clld.org | CSV: github.com/clld/wold2
  - 41 recipient languages, source word → borrowed form pairs + donor language,
    CC-BY. Japanese vocabulary included (~500 loans).
  - ⚠️ Organized by borrowed MEANINGS; phoneme substitutions visible but NOT
    annotated — must extract by aligning source/target forms.
- **JMdict** (CC-BY-SA) — `lsource` tags on every gairaigo entry give source
  language + source word. Richest source for the Japanese column specifically.
- **NO cross-linguistic DB of loanword pairs annotated with phoneme
  substitutions exists.**
- 📝 TODO (later, not now): generation pipeline — WOLD/JMdict pairs → G2P both
  forms → align → extract substitution patterns → LLM-curate story examples →
  **hand-verify every example that ships** (most-quoted part of the viz =
  highest error embarrassment).

### DECIDED: variant-cell visual = diagonal half-fill (split cell)
- Full solid = core in both | diagonal split (English half filled, other half
  outlined) = core in Eng, variant in L2 | outline/empty = English-only
- Split direction encodes the asymmetry (whose sound it fully is)
- NOT opacity (fails low-vision) / NOT hatching (reads as "disabled")
- Legend badge + tooltip text so fill is never the only channel (a11y rubric)
- Variant-cell click: play phoneme audio, then context ("only before u — Fuji")

### English↔Japanese variant cells — VERIFIED against phoible.csv (2026-08-09)
Data architecture (answering "where does half-fill data come from"):
- **Cell states = phoible.csv ONLY** (mechanical: Eng phoneme in L2 Phoneme col
  → FULL; in L2 Allophones col → HALF; neither → EMPTY). No wiki scraping.
  Scales to all languages with allophone-bearing sources.
- **Wikipedia/Vance 2008 = tooltip prose only** (conditioning environments like
  "before u" are not structured in PHOIBLE; hand-write for ~15 spotlight langs;
  chart works without them).

Verified from data (Japanese SPA inventory #197, 40 phonemes, allophones on all
rows). PHOIBLE /h/ row: Allophones = [ɸ h ç ɸː fː hʲ f] ✓
| Eng phoneme | Mechanical state | Story |
|---|---|---|
| /f/ | HALF (in /h/ allophones) | Fuji, koohii, fuudo |
| /v/ | EMPTY | violin→baiorin (b!) |
| /ʃ/ | **FULL** (SPA treats as phoneme) | shefu "chef" earned it status |
| /tʃ/ | **FULL** (SPA: t̠ʃ phoneme) | |
| /ŋ/ | **FULL** (SPA: phoneme, ga-gyō) | |
| /ts/ | HALF (in /t/ allophones) | two→tsuu |
| /θ/ /ð/ /l/ | EMPTY | th→s/z; l,r→/ɾ/ (most famous) |

⚠️ Lesson: analyses differ (some linguists call [ɕ] an allophone of /s/; SPA
grants ʃ/tʃ/ŋ phoneme status partly due to loanwords). DEFER TO THE DATASET —
hand-tables are sketches. Note the analysis-dependence in methodology section.
✅ DECIDED: include a footnote in the viz that linguists disagree on phoneme
analyses per language; link PHOIBLE FAQ (https://phoible.org/faq) which openly
documents why inventories differ across sources, as the criticism reference.
⚠️ Japanese has 3 PHOIBLE inventories: SPA(40, full allo), PH(21, full allo),
UPSID(20, ZERO allo). Dedup rule = pick max allophone-bearing inventory, else
variant cells silently vanish.
Reverse direction (JA core, Eng absent — include for fairness): geminates っ
(kite/kitte), phonemic vowel length (obasan/obaasan), pitch accent (hashi×3),
moraic /ɴ/

### Anchor story: /f/ vs [ɸ] (Japanese) — use in intro/tooltip
- [ɸ] in Japanese = automatic variant of /h/ before /u/; NO minimal pair exists
  within Japanese (that's what makes it an allophone; swapping [ɸ]/[h] can never
  change a Japanese word's meaning)
- Meaning collisions appear only at the language boundary:
  - "coffee" → コーヒー koohii (f→h! because [ɸ] only available before /u/)
  - "food" and "hood" → BOTH フード fuudo (genuine merger in borrowing)
  - /h/+/u/ → [ɸ] means "who'd" can sound like "food" in Japanese-accented English
- One-line framing: "Your language has the sound — it just never taught you to
  hear it as different."

### Substitution stories (manual curation, top ~15 L1s)
- Speech Accent Archive "generalizations" pages per language: http://accent.gmu.edu
- Contrastive analysis literature (cite per language)
- Examples: ja /θ/→/s/ (think→sink), es /ʃ/→/tʃ/, ar /p/→/b/, ko /f/→/p/,
  hi /w-v/ merger, fr /h/→∅, ru final devoicing

### Stretch (idea #1 bridge)
- **Speech Accent Archive** — 2,100+ speakers, 214 L1s, same paragraph
  - Kaggle mirror: rtatman/speech-accent-archive
- lang2vec / URIEL for precomputed language distances: https://github.com/antonisa/lang2vec

## Build plan

1. [x] Download PHOIBLE csv (data/phoible.csv, 23MB), pick dedup rule, extract
       English inventory — build_matrix.py
       - English target = **EA inv 2252 (RP), 44 phonemes** (standard
         transcription w/ diphthongs + /ɹ/). SPA inv 160 rejected:
         idiosyncratic vowels (e̞ o̞ː ɐ) + marginal x/ʍ/ʔ.
       - Dedup rule = per language, inventory with most allophone-bearing rows.
       - Matching = BASE match (strip Mn diacritics + Lm modifiers via unicodedata)
         because sources differ in convention (EA writes /pʰ/, L1 sources /p/).
         Strict match kept as a column for methodology.
2. [x] Top-30+ L1 list picked (34 langs; Urdu/Marathi/Yoruba flagged 2-state,
       no allophone data in any source)
3. [x] matrix.csv (1,496 rows) + matrix_summary.csv generated
4. [x] Sanity checks pass: ja /f/=VARIANT ✓ /l/ /ɹ/ /θ/=ABSENT ✓, es /ð/=VARIANT ✓
       /v/=ABSENT ✓, ko /f/ /v/=ABSENT ✓, de /w/=ABSENT ✓, fr+ru /θ/=ABSENT ✓
       - Egyptian Arabic /p/=FULL is *correct per SPA source* (loanword /p/ in
         Cairene); use MSA (no p anywhere) for the "Arabic has no p" story.
       - Fun finds: Mandarin has 13 VARIANT cells (most of any lang) — huge
         half-fill story; Hindi is the closest inventory to English (14 absent).
5. [x] Commons IPA audio downloaded — download_audio.py → audio/ (44 files) +
       audio_manifest.csv (per-file Commons URL for attribution)
       - 36/44 = isolated-phoneme recordings (canonical Commons articulatory files)
       - 8/8 diphthongs = word-example fallbacks (Commons has no systematic
         isolated diphthong recordings): eye/ow/hey/oh/boy/ear/air/tour.
         Flagged audio_kind=word_example in manifest; arguably BETTER for a
         general audience (real word > lab sound). Optionally self-record later.
       - Gotchas hit: (1) macOS system python urllib fails SSL on wikimedia →
         use curl; (2) Commons 429-rate-limits bursts → 5s+ backoff, 2s pacing;
         (3) macOS case-insensitive FS: slugs V.ogg/v.ogg collided → renamed.
       - PhoneticFlashCards repo (github.com/joshstephenson/PhoneticFlashCards)
         evaluated as alternative: same Commons files (CC BY-SA 3.0), only ~50
         of them, mp3 re-encodes, missing 6 of our consonants + all diphthongs,
         2nd-hand attribution chain. Our direct pipeline is strictly better;
         repo useful only as filename cross-reference.
       - TODO before publish: fetch per-file author/license from Commons API
         into manifest (license_note column is the placeholder).
6. [ ] Curate substitution stories for top 15 L1s with citations
7. [x] Prototype v0 built — prototype/index.html (self-contained; data via
       data.js global so file:// works; audio/ symlinked)
       - build_chart_data.py regenerates prototype/data.js from matrix.csv +
         audio_manifest.csv; includes IPA-chart layout (7 groups), plain-language
         labels + anchor words per phoneme, and hand-written VARIANT_STORIES /
         ABSENT_STORIES dicts (extend these per spotlight language)
       - Interactions: click-to-play, hover/focus tooltip w/ state + story,
         language dropdown, live headline ("X is missing N of English's 44
         sounds, and has M more only as variants"), 2-state languages get a
         data-coverage warning banner + * in dropdown
       - Visual: split-cell (135deg gradient) for VARIANT per decided design,
         ◐ badge as non-color channel, keyboard focusable buttons, aria-labels,
         aria-live headline, prefers-reduced-motion honored
       - Verified: node smoke_test.mjs (DOM-stub run of the inline script:
         data coverage, script executes, Japanese=23 absent/2 variant headline,
         Urdu triggers warning). Serve with: python3 -m http.server in prototype/
8. [x] **v2 REDESIGN — full IPA chart as the universe** (user decision):
       chart = all human speech sounds; every language (English included) is
       just a subset lighting up cells. Two language selectors; pair states
       BOTH / L1-only / L2-only / NEITHER + ◐ variant badge.
       - build_chart_data.py v2: official IPA 2020 layout (place×manner
         consonant table w/ impossible cells, vowel trapezoid coords, other
         sections: co-articulated/affricates/clicks+implosives); emits
         per-language phoneme/allophone sets (base-normalized incl Sk rhotic
         strip + geminate collapse); off-chart "extras" chips (Eng diphthongs,
         Mandarin ʈʂ, Zulu click clusters); tones flag.
       - Zulu added (inv 147 SPA) for the clicks story. PHOIBLE writes Zulu
         clicks as clusters (kǀ kǁ kǃ) → bare click credited via substring.
       - download_audio.py v2: full 117-symbol candidate map, hex-codepoint
         slugs (case-safe). download_audio_fast.py: batch-resolves via Commons
         API then hits upload.wikimedia.org directly (separate rate pool).
       - Commons rate limiting is BRUTAL on bursts: trickle_audio.sh reran
         every 20min until complete. ✅ 117/117 symbols resolved (109/109
         chart symbols + 8 diphthong word-examples); all files verified as
         valid audio. Last two stragglers had different Commons names:
         ɥ = "Voiced labialized post-palatal approximant.ogg",
         ɺ = "Voiced alveolar lateral flap.wav" (found via Commons API search).
       - index.html v2: consonant table + SVG vowel trapezoid + strips,
         2 selectors, pair headline ("English and Japanese share 19 sounds...\"),
         extras chips, stories in tooltips, a11y (aria-labels, focus, ◐ badge).
       - smoke_test.mjs v2 passes: Eng th/r/w ✓ Zulu clicks ✓ ja ɸ-variant ✓
         ja-no-l ✓; English=36 on-chart, Eng∩JA=19, JA-only=7.
       - v3 TODO: mobile layout, rank view, per-file Commons attribution,
         diphthong self-record

## EXAMPLE WORDS — data provenance (user asked: database or generated?)

Two layers, merged in build_chart_data.merged_examples():
1. **Hand-curated (65)** — EXAMPLES_BY_LANG in build_chart_data.py, written by
   Kiro from language knowledge, validated against language data, flagged
   "verify before publish". These WIN over mined entries. Story-quality
   (perro/pero minimal pair, iqanda click, etc.)
2. **WikiPron-mined (~920)** — mine_examples.py mines word+IPA pairs from
   WikiPron (CC BY-SA, github.com/CUNY-CL/wikipron = Wiktionary scrape; the
   dataset already noted in original scoping). For each (language, on-chart
   phoneme): prefer word-initial target sound, 3-6 char words, skip 1-2
   segment entries (letter names!), hyphens, proper nouns. ~92% avg coverage
   across all 36 languages. UI labels these "(via Wiktionary)".
   TSVs cached in data/wikipron/ (gitignore-able, ~re-downloadable).
- Remaining gaps (~8%): sounds documented in PHOIBLE but absent from that
  language's Wiktionary transcription conventions. Tooltip simply omits the
  example line. Could hand-fill spotlight-language gaps later.
- ⚠️ Mined examples are REAL words with REAL transcriptions (not generated),
  but Wiktionary transcription conventions ≠ PHOIBLE conventions in places;
  spot-check quality confirmed reasonable, full audit not done. Methodology
  note should say: examples sourced from Wiktionary via WikiPron.

## INVENTORY SELECTION POLICY (user caught Italian 55 — should be ~30)

Old rule "pick inventory with most allophone rows" biased toward MAXIMALIST
analyses: Italian inv 2195 = 70 phonemes because it treats every diphthong
(ai̯ ei̯ ua ui...) and geminate as separate phonemes → collapsed 55, textbooks
say ~30. Fixed with select_inventories.py:
- Rule: among a language's inventories, prefer allophone-bearing → pick the
  one whose LENGTH-COLLAPSED count is closest to the MEDIAN of all candidates
  (the "typical" analysis); tie-break = more allophone rows.
- Changes: Italian 55→30, Spanish 38→25, Korean 40→32, Japanese 27→21,
  French 39→36, Greek 28→26. English PINNED to EA RP 2252 (44) — median rule
  would pick SPA inv w/ nonstandard vowel symbols (e̞ o̞ː); pin documented.
- Sanity preserved: Japanese ɸ-variant ✓ Zulu clicks ✓ example validation
  caught + fixed 3 curated keys (ja ɔ→o ɛ→e, ko tɕ→tʃ).
- Wikipedia "List of languages by number of phonemes" considered as external
  anchor: REJECTED as data source (page itself warns "counts differ radically
  between sources... no precise inclusion criteria"; would break single-
  source consistency + phoneme sets must match PHOIBLE for the chart).
  Use only as spot-check: Italian ~30 ✓ Spanish ~25 ✓ English 44 ✓.
- Remaining outliers (Urdu 52, Punjabi 51, Marathi 51, Bengali 50): these are
  genuinely large inventories (aspiration series counted as distinct, which
  IS the textbook treatment for South Asian languages) — verified reasonable.

## PAIRWISE OVERLAP ANALYSIS (analysis phase, 2026-08, updated post-reselection)

Data: analyze_pairs.py over all 630 pairs (36 langs); build emits pairOverlap
into data.js; index.html renders a strip-plot percentile panel under the
headline when 2 languages are selected ("Japanese is less similar to English
than most languages here — more overlap than 35% of the 35 other languages").
Metrics: shared count (headline) + Jaccard |A∩B|/|A∪B| (fair, size-normalized
— big inventories share more with everyone in raw counts).

Key findings (jaccard, post inventory-reselection):
- Distribution: min 0.26, median 0.47, max 0.90, mean 0.48, σ 0.10
- Most similar pair: Amharic+Indonesian 0.90 (!!) — unrelated families,
  near-identical "average" inventories. Convergence, not kinship. STORY.
  (Survived the reselection — robust finding.)
- Runners-up: Russian+Ukrainian 0.77 (siblings), Indonesian+Persian 0.76,
  Dutch+German 0.76, French+German 0.74
- Least similar: Greek+Korean 0.26, Urdu+Zulu 0.27, Mandarin+Tamil 0.28
- English's best friend = HINDI (0.61, 27 shared) — not German (0.54)!
  Survived reselection. "I had no idea" candidate.
- Family ≠ similarity repeatedly: sound inventories converge/diverge
  independent of ancestry. THE analytical insight of the piece.
- ⚠️ Individual pair numbers moved when inventories were reselected (e.g.
  Eng-JA 19→16 shared) — headline findings robust, but re-run analyze_pairs
  after ANY inventory change before quoting numbers.

## ROSTER AUDIT — removed Egyptian Arabic + Urdu (user request + audit_roster.py)

Systematic sweep for dialect/register/quality issues across the roster:
- **REMOVED Egyptian Arabic** (user: confusing counts vs MSA): same
  macrolanguage, MSA = written/formal register vs spoken dialect. Was MSA's
  #1 percentile neighbor — distorted the dist panel.
- **REMOVED Urdu** (audit found same pattern): Hindi+Urdu = one spoken
  language (Hindustani) in two scripts/registers; 0.67 overlap, each other's
  #1 neighbor; Urdu also had no allophone data. Kept Hindi.
- **KEPT after inspection**: Mandarin+Cantonese (mutually unintelligible,
  distinct languages), Russian+Ukrainian (0.77 — distinct, defensible),
  Indonesian (register of Malay but no Malay in roster), Punjabi.
- Remaining quality flags (acceptable, documented): English EA source has no
  allophone data (fine — variants only matter on the L2 side); Marathi+Yoruba
  2-state; Bengali/Punjabi/Marathi large counts = genuine aspiration series.
- Roster now **34 languages, 561 pairs**. Smoke test derives counts from data
  (no more hardcoded 36/630).
- Post-removal findings SHIFTED: only 9/34 languages have closest relative
  in own family (was 13/36 — removing the two register-pairs made the thesis
  STRONGER, since those were 2 of the 13). Same-fam median 50% vs cross 46%,
  35% cross beat same-median. Amharic+Indonesian 0.90 still #1.

## FINDINGS SECTION (built 2026-08, on page below chart)

analyze_families.py → prototype/analysis.js: family metadata (11 top-level
families for the 36 langs), family-vs-similarity stats, UPGMA leaf order for
the heatmap, sound clusters at 0.60 jaccard cut.

Headline numbers (VERIFIED from data, quoted in the section):
- Only **13/36 languages** have their closest sound-relative in their OWN
  family. English's is Hindi (fine, both IE) but e.g. Japanese→Indonesian,
  Spanish→Swahili, Greek→Swahili, Zulu→Ukrainian, Hebrew→Tagalog.
- Same-family median overlap 50% vs cross-family 46% — barely different;
  **34% of cross-family pairs beat the same-family median.**
- UPGMA sound clusters @0.60 mix families freely: [Amharic Hausa Indonesian
  Persian Tagalog] (3 families!), [Italian Portuguese Russian Swahili
  Ukrainian] (2), [Korean Thai Vietnamese] (3), [Dutch French German],
  [Hindi Punjabi Telugu Urdu] (IE+Dravidian — the South Asia Sprachbund,
  textbook contact-convergence case)
- English–Spanish overlap 36% — near the bottom of English's list — yet
  Spanish = most-studied L2 for English speakers. THE takeaway datapoint.

Page section "What the data says" (5 findings blocks):
1. Thesis: families don't predict sound pools (stats above, live-filled)
2. Heatmap: 630-pair canvas, UPGMA-ordered, family color strip on edges
   (colors scatter = ancestry doesn't cluster), hover = pair details
3. Convergence explained: chance + shared articulatory physics + contact
   (Sprachbund, clicks into Zulu, retroflex South Asia zone)
4. Why relatives diverge: sound = fastest-changing layer; Eng/Spanish vs
   Eng/Hindi contrast
5. Takeaway (user's): sound distance ≠ learnability barrier; Eng-Spa 36%
   overlap yet most-studied + succeeded-at L2. "Gaps aren't walls."

Remaining future ideas:
- [x] Rarity-weighted overlap → analyze_geography.py (see GEOGRAPHY section)
- [x] "Hardest language pair" asymmetric gaps (A→B vs B→A) → analyze_asymmetry.py
- [ ] Dendrogram render of the UPGMA tree (data already in analyze_families)
- [ ] Mobile layout pass (both pages currently assume ≥900px for side-by-side)
- [ ] Per-file Commons author/license into audio_manifest (license_note is a
      placeholder — REQUIRED before publish for CC BY-SA compliance)

## ALLOPHONE LAYER + LOST IN TRANSLATION (built 2026-08-10)

analyze_allophones.py → why same-inventory languages still sound different.
- **English–Hindi share 27 phonemes but 92% are realized differently.** That
  divergence, not the inventory gap, is what an accent mostly is.
- Hindi+Punjabi: 65% phoneme overlap, **100%** realization divergence.
- Overlap does NOT predict divergence (scatter is flat) — 465 usable pairs.
- **Bridges**: sounds that are phonemes in L2 but allophones in L1 → the learner
  already produces them. Eng–Hindi overlap 52%→61% crediting bridges at half.
- Coverage: 32/34 languages have allophone data. Marathi+Yoruba have none in ANY
  PHOIBLE inventory (excluded from these metrics, still on chart). English's
  pinned inv 2252 has none → supplemented from SPA inv 160 (agrees on 32/51).
  All three facts surfaced in the page's method notes.

analyze_mergers.py → "Lost in translation", generalizing food/hood → フード.

> **❌ CUT 2026-08-11 — page, model and all its data deleted.** Kept below as a
> record of what was built and why it was dropped; do not rebuild from this.
> A user checked the Japanese output and found most of it was not Japanese
> (ハスト for *fast*). Four defects: (1) `norm()` strips vowel length, which
> Japanese contrasts phonemically, so fast/first fused on the contrast the model
> had discarded — this inflated every rate, not just the examples; (2) 4 of 8
> examples existed only via a non-primary pronunciation variant; (3) the pinned
> /f/→/h/ fired outside its /_u context, giving ハスト not ファスト; (4) the /ŋ/→ング
> fix sat downstream of the model that had already rewritten ŋ→ɴ.
> The transliterator's own suite passed 8/8 on hand-written inputs the pipeline
> never produces — end to end *food* became フド, not the フード the test asserted.
> Removed rather than repaired: predicted collisions have no external ground
> truth, and 9 passing anchors proved compatible with being wrong across 11,792
> words. Full account in GENAI_LOG.md and on the About page.
> Deleted: `analyze_mergers.py`, `build_native_script.py`,
> `test_native_script.py`, `merger_analysis.json`, `prototype/translation.html`,
> `prototype/nativescript.js`, `DEEP.mergers`. `smoke_pages.mjs` fails if any of
> them returns.

- Model: map each English phoneme to nearest sound the target HAS (38 PHOIBLE
  features, weighted Hamming, class-guarded) → apply to 11.8k common English
  words (wordfreq Zipf ≥3.4) → collect collisions.
- **Validates 9/9 documented mergers** (food/hood, right/light, glass/grass,
  bus/bath, bat/vat, ship/chip, pool/full, coat/goat, thin/sin).
- Merger pressure ranking: Cantonese 28% of common words collide (18 sounds) →
  Telugu 10% (38 sounds). Also a map of predictable accents.
- ⚠️ FOUR modeling errors found and fixed by the validation suite (1/7 → 9/9):
  1. **Allophones must NOT be substitution targets** — an allophone changes
     realization, not contrast. Crediting Korean's allophonic [ɡ] invented a
     coat/goat contrast Korean lacks. Targets = phonemes only.
  2. Sparse inventories break naive mapping: Japanese inv 2196 lists no flap
     /ɾ/, Spanish inv 164 lists /β/ but no /b/ → pinned via OVERRIDES.
  3. Pure feature distance is wrong for loanwords (Eng /v/ → JA /b/, not the
     closer /w/) — conventional substitutions are pinned and labelled.
  4. My own validation anchor was wrong: Mandarin /θ/→/s/ so thin collides with
     **sin**, not din. The test was wrong, not the code.
- Function words excluded from EXAMPLES (the=there is true but dull); still
  counted in rates.

## GEOGRAPHY / RARITY / L2 — "More to explore" page (built 2026-08-10)

New companion page prototype/explore.html for material that's interesting but
off the main narrative spine. Linked from the end of the findings section.

Data added: Glottolog CLDF languages.csv (coords, CC BY), Ethnologue-2026
speaker counts via Wikipedia (L1/L2/total, CC BY-SA), Natural Earth 110m
countries (public domain). NOTE: macOS system Python fails SSL on these hosts —
same gotcha as the audio pipeline; fetch_geo_speakers.py shells out to curl.

- **World map**: 34 languages at homeland coords, marker size = speakers
  (switchable total/L1/L2), color = inventory rarity, hover = signature sounds.
  Basemap simplified with RDP (819KB → 158KB bundle, 81% smaller).
  ⚠️ Explicit caveat on the page: a language is not a dot. Markers are homeland
  anchors, NOT territory. Glottolog's English coordinate sits in the West-Germanic
  dialect continuum, so English/Spanish/Portuguese/French/MSA homelands are
  pinned by hand (flagged `pinnedHomeland`).
- **Signature sounds** = rarest phonemes per language, computed over 2,177
  languages (one inventory per Glottocode to avoid over-weighting well-studied
  languages). Zulu clicks kǁ kǃ kǀ, MSA pharyngeals ʕ ħ, Hausa implosives ɓ ɗ,
  Yoruba co-articulated ɡb kp.
  ⚠️ Diphthongs/clusters EXCLUDED from rarity: sources disagree whether to list
  them at all, so including them ranked English /əʊ/ among the world's rarest
  sounds — a notation artifact, not articulation.
- **English is the weird one** (old backlog item, now built): /θ/ 4% of world
  languages, /ð/ 6%, /ɹ/ 6%; English has the 2nd-most-unusual inventory of 34.
- **Rarity-weighted overlap**: weighting can only LOWER a pair's score (everyone
  shares the universals), so the signal is the SIZE of the drop. Japanese+Korean
  48%→16% (overlap was all common sounds); Russian+Ukrainian 77%→69% (they
  genuinely share rare ones).
- **L2 story**: English 75% learners, MSA ~100% (no native register), Swahili 96%.
- ⚠️ **A wrong claim I made and then had to retract**: drafted "no correlation
  between sound rarity and learner counts." Actual r = +0.56, significant
  (t=3.24). analyze_l2_drivers.py resolves it: rarity correlates 0.88 with
  inventory SIZE (more sounds ⇒ more unusual ones), and controlling for size the
  effect collapses to 0.16. Meanwhile lingua-franca status predicts learners at
  0.71 while being uncorrelated with rarity (0.02); median 77M learners vs 8M.
  Honest conclusion: **sound difficulty doesn't predict learner numbers; history
  does.** Smoke test now FAILS if the copy ever says "no correlation" again.

## ASYMMETRIC DIFFICULTY (analyze_asymmetry.py, 2026-08-10)

Overlap is symmetric; learning is not. Strongest finding of the session:
- Eng speaker → Japanese: **4** new sounds. Japanese speaker → English: **28**.
- Averaged over the roster: English speakers meet **9.5** new sounds going out,
  speakers coming toward English meet **23.3**. English is the harder direction
  for **32 of 33** languages.
- ⚠️ Checked whether this is English exceptionalism: it is NOT. Rank by this
  advantage and you get inventory size in order — Dutch (46) beats English (44),
  then Bengali, Telugu, German. Framed on the page as arithmetic, not prestige.
- Refinements: rarity-weighted load, plus bridge credit (half weight for sounds
  the learner already produces as a variant).
- ⚠️ Caveat on page: sound count is a small part of difficulty. Cantonese needs
  just 1 new sound from English yet is hard (tone); Japanese speakers struggle
  with English clusters where every sound is shared.

## NAVIGATION RESTRUCTURE — shared nav (2026-08-10; now 7 pages)

User asked for a top nav bar and content grouped into categories. Result:
prototype/{index,map,allophones,translation,history,difficulty,about}.html,
each loading only
the data it needs (chart page no longer pays for the 200KB map bundle).

- `nav.js` — single source of truth for the link list; each page sets
  `data-nav` on <body> and the script marks the current item (`aria-current`).
- `shared.css` — theme vars + nav + shared blocks/tables/tooltip, so the pages
  can't drift apart visually.
- `build_rarity_data.py` → `prototype/rarity.js` (43KB): carves just the rarity
  fields out of geo_analysis so the chart page gets rare-sounds material
  without the map bundle.
- Grouping: Sound Chart (chart + Venn/groups + RARE SOUNDS, moved here per
  user + heatmap/sound map/family findings) · World Map (choropleth + L2 table)
  · Allophones · Seeing Sounds · History of English · Difficulty · About.
  (Lost in Translation had its own section until it was cut on 2026-08-11.)

### Comparison visual: circles removed (user call)
Built an area-proportional 2-set Venn (exact lens-area solve), then the user
judged the circles redundant against the grouped chips. Removed; kept three
labelled groups (only-L1 / shared / only-L2) with slim share bars. Simpler and
the chips were always the part carrying the information.
- Chips: rarity encoded as BORDER treatment (not fill) so it doesn't collide
  with the L1/L2/both fill colours and never relies on colour alone.
- Chips now hover-tooltip an EXAMPLE WORD in each relevant language (curated
  entries carry a gloss, mined ones labelled "via Wiktionary"), plus the
  global-rarity phrase; click still plays the phoneme audio.

## HISTORY OF ENGLISH — 7th page (user request, 2026-08-10)

User asked for "a timeline in a new page documenting a brief history of the
english language… some interesting items could be split from german, and what
are phonemes that were lost in english that are included in german, like x in
knight (I think?)".

**The user's /x/ hunch was right, and was checked against the data before any
prose was written.** A throwaway probe confirmed: English does not list
<x>, German and Dutch both do, and audio exists for it. That probe also caught
something worth not getting wrong — **PHOIBLE's German inventory has no /ç/**,
only /x/. Writing "German has the ich-Laut and the ach-Laut" from memory would
have contradicted the very inventory the rest of the site charts. The page
instead states which analysis it follows and notes the question is contested.

`prototype/history.html`, slotted between Lost in Translation and Difficulty.

**This is the only page not backed by PHOIBLE, and that changes its obligations.**
PHOIBLE records languages as spoken now; it has no Old or Middle English entry.
So the timeline is compiled from published histories (Wikipedia's phonological
history of English + companions, Britannica, U. Toronto's Middle English
phonology notes, Wiktionary doublets) and each is cited on the page. The page
says so in its own prose, up top, because every other page here IS
PHOIBLE-backed and a reader will otherwise assume this one is too. The
present-day comparisons (English vs German columns, "x in 11 of 34 languages")
are PHOIBLE and are read from `data.js` at render time rather than typed in.

Timeline covers, each tagged gained / lost / shifted so the spine is scannable:
West Germanic split · Old English sc→/ʃ/ · Old Norse reintroducing /sk/
(shirt/skirt doublets) · 1066 and the French layer promoting /v z ð/ from
allophones to phonemes · the Great Vowel Shift · loss of /x/ (the ⟨gh⟩ of
*knight*) · Caxton 1476 freezing spelling mid-change · kn→n · /ʒ/ arriving late
· global spread. Sounds are playable chips reusing the Sound Chart's
chip/tooltip pattern.

### Clusters are spelled, never charted
First draft aliased the `{{sk}}` template token to the symbol `"s"`, which
rendered **a playable button reading "s" inside a sentence about sk** — a wrong
label on a control that plays a real sound. /sk/ and /kn/ are two segments; the
chart and the audio set are keyed on single segments, so there is no one cell
or recording for them. Now `CLUSTERS` renders them as italic spellings. Same
rule as the native-script transliterations: emit nothing rather than something
approximate. This is the third instance of the same failure mode in this
project (ç→c collapse, Zulu clicks, this) — **a symbol that looks close enough
is not the same symbol.**

Dates are all hedged ("about 1400 to 1700", "from 1066"). A bare range claims a
start and end for something that spread through a population over generations,
and the page's own caveat says as much — so a test enforces it.

### Two rejected visuals, then the flow diagram (2026-08-10)

The page went through three versions of its main visual. Recording all three,
because the reasons for the rejections are the useful part.

**v1 — prose timeline.** User: *"I want a more visual timeline, there's a lot of
text right now."*

**v2 — parallel lineage rows.** One row per sound, two lanes (English above,
German+Dutch below), on a shared year axis. User: *"I don't like this timeline
visual, it's hard to read, and doesn't seem to display gained phonemes from other
languages."* Both criticisms were fair and the second was structural: the two-lane
form could only express **English vs its siblings**, so every sound English got
from *contact* had to be drawn as "arrived from inside English" or omitted. A
diagram about a language shaped by borrowing could not show borrowing.

**v3 — one trunk, branches in and out.** User: *"unify it into one horizontal
timeline with branches flowing in and out of the main line, which represents
english. we can denote the phonemes in those branches that are gained and lost, as
well as the words associated with them, including the german, dutch, french."*

`prototype/history_flow.js` draws exactly that: English is a single horizontal
line from 400 to now, with era bands (Old / Middle / Modern English) behind it.
Branches **above** arrive, branches **below** leave, each meeting the trunk at its
year with an arrowhead for direction. Every branch carries its sound as a playable
chip plus the hand-checked cognates on both ends.

| | sound | year | other end |
|---|---|---|---|
| in | `tʃ` church | ~700 | inside English — German *Kirche*, Dutch *kerk* kept the k |
| in | `v` veal | ~1200 | Norman French *veau* |
| in | `z` zeal | ~1200 | Norman French *zèle* |
| in | `dʒ` judge | ~1250 | French *juge* — **French later lost it** |
| in | `ŋ` sing | ~1600 | inside English |
| in | `ʒ` measure | ~1650 | French *jour* |
| out | `y` über | ~1300 | German *über*, Dutch *vuur*, French *tu* |
| out | `x` knight | ~1500 | German *Nacht*, Dutch *nacht*, Scots *loch* |

The `dʒ` row is the one the two-lane version could not express: French handed
English that sound and then changed, so **English now keeps a sound its donor gave
up.** That is checkable — French is in the roster — and a test asserts it.

Text is down to 1,241 chars of timeline + 1,425 of branch detail + 2,693 of page
prose, from 2,812 + 3,605 at v1, with the diagram carrying the narrative.

### The branch ends are verified, not asserted
`build_history_data.py` → `prototype/history_data.js`. The dates are editorial
(published histories, cited on the page) but each branch END is a claim about the
PRESENT, and a hand-authored claim about the present can silently contradict the
inventories the rest of the site charts. So the build script checks all of them
against `data.js`:

- an **inflow** → English must list that sound today
- an **outflow** → English must NOT, and every named survivor MUST
- a **donor** marked `has`/`lost` → checked against that donor's inventory

It exits non-zero on disagreement, refuses a symbol with no audio, and requires
any language outside the roster (Scots) to be marked unverifiable in its own gloss
— the page renders those with a dotted underline and says why.
`smoke_pages.mjs` re-checks the same claims independently, since a data rebuild
after the build script ran would otherwise go unnoticed. It also rejects the mined
Wiktionary example words, which offered "vab" for /v/ and "tanh" for /θ/.

Confirmed by tampering: a false "English kept it", a false donor state, an
unaudited symbol, a missing date, and a mined word are all rejected.

## ⚠️ DATA BUG FOUND BY USER — Zulu clicks showed as "not rare" (FIXED)

User: "zulu clicks/implosives are marked as not very rare, is this true?" It was
not. Root cause chain:
- PHOIBLE writes Zulu clicks as CLUSTERS with their accompaniment: `kǀ kǁ kǃ`,
  never a bare `ǀ`.
- `build_chart_data.py` credits the BARE click to the chart via substring match
  (correct — the chart cell is the bare click).
- but `analyze_geography.py` keyed `globalFreq` on the normalized cluster, so
  the chart chip `ǀ` found NO frequency entry → fell through to the default gray
  border → read as unremarkable.
- Truth: each click is in **under 1% of the world's languages** (ǀ 0.73%,
  ǃ 0.69%, ǁ 0.46%, ǂ 0.23%, ʘ 0.09%) — among the very rarest sounds on the chart.
- Fix: `global_frequencies()` and the `ours` export filter both credit bare
  clicks by substring, matching how the chart credits them. 139 → 142 symbols.
- **Regression guard**: `build_rarity_data.py` now HARD FAILS if any chart symbol
  lacks a frequency, rather than shipping silent "unknown rarity" chips.
  smoke_chart.mjs also asserts clicks are <5% and k/m/i are >90%.
- Lesson worth keeping: "no data" rendered identically to "nothing special".
  Absent values in a visual encoding need to look absent, or be impossible.

## WORD AUDIO — investigated, NOT available (answer to user question)

User asked whether the example words could have audio. Checked: our 117 audio
files are all isolated-phoneme (or diphthong word-example) recordings for IPA
SYMBOLS. For per-language WORDS:
- Commons category `Lingua_Libre_pronunciation-zul` → **0 members**. Lingua Libre
  has ~1M word recordings but coverage is concentrated in French/English/etc.;
  our roster's rarer languages (Zulu, Telugu, Amharic, Marathi) are essentially
  unrecorded, which is exactly where the interesting sounds are.
- So audio would be available for the languages that need it least → asymmetric
  coverage would imply "these sounds are more real than those". Not shipped.
- Words still appear as TEXT in the chip tooltip; the phoneme audio still plays.
- If revisited: UCLA Phonetics Lab Archive has scholarly word-list recordings for
  100s of languages and is the better source, but needs per-language licence
  checks and manual alignment to our example words.

## SYSTEMATIC COVERAGE AUDIT (audit_coverage.py, 2026-08-10)

User asked whether the Zulu-clicks failure mode ("no data" rendering identically
to "nothing special") exists anywhere else. Built a 6-layer audit; exits 1 on any
BLOCKING gap. Result: **0 blocking, 2 warnings, 4 informational.**
- Layer 1 rarity: 92/92 chart symbols have a frequency ✓ (1 off-chart diphthong
  extra `ʊə` lacks one — by design, diphthongs are excluded from rarity).
- Layer 2 allophones: ⚠️ **the audit itself was wrong the first time.** v1 counted
  rows where the `Allophones` CELL was populated → reads ~100% for 31 of 34
  languages → I wrongly concluded coverage was "binary" and began rewriting
  correct prose to match it. Caught by cross-checking ALLOPHONE_REVIEW.md, which
  disagreed. The cell is usually populated even when it merely restates the
  phoneme; the metric that matters is rows listing a variant that DIFFERS from
  its phoneme: Russian 74%, Zulu 47%, Hindi 39% … Swahili 3%, Punjabi 1%,
  Marathi/Yoruba/English 0%. The original "very uneven" framing was right all
  along, and the 15% usability gate in analyze_allophones.py is well-founded.
  Audit now prints BOTH columns so the distinction can't be lost again.
  Lesson: when a fresh measurement contradicts an existing documented finding,
  suspect the measurement first.
- Layer 3 example words: 100%→74%; weakest Korean 74%, Telugu 76%, Greek 77%.
- Layer 4 audio: 92/92 chart symbols have a recording ✓
- Layer 5 speakers: 25/34 have L2 estimates; 5 languages still <5 abroad.
- Layer 6 mergers: removed 2026-08-11 (see the CUT note above). The audit now
  only checks that `DEEP.mergers` has not come back.

## ALLOPHONE PAGE REBUILT — audio demos, not a variant table (user call)

User reported the English+Hindi allophone table "not rendering correctly".
Diagnosed: **not a data bug** — all 8 rows are fully populated both sides. The
problem is the IPA itself: PHOIBLE's variants are stacked combining diacritics
(`b̚`, `d̪̤̚`, `t̪̚ʰ`) that most system fonts render as tofu/misaligned marks.
Inherent to displaying that level of phonetic detail in a browser.
- Per user's suggestion, replaced with a brief explanation + **audio contrasts**
  from `prototype/demos.js` (6 curated cards: b/β, ɹ/r, h/ɸ, s/ɕ, ʈ/t, ɾ/t).
  Every card = 2 genuinely different Commons recordings, both verified present in
  DATA.audio by smoke_pages.mjs.
- Page now leads with a plain-language phoneme-vs-allophone explanation (the
  /t/ in top / cat / butter), which is the concept the whole page depends on and
  was previously assumed.
- Kept: the bridge overlap lift (52%→61%), which depends only on English's own
  records and so is safe under uneven coverage.
- Dropped: the per-pair "% realized differently" figure. It was computed from
  documentation depth as much as phonetics, and with English at 0% coverage the
  English side came from a substituted inventory anyway.

## ABOUT & SOURCES PAGE (about.html) — 6th nav item

User asked for a tab documenting references, methodology, competition info, and
their motivation. Contains:
- **Why I made this** — user's own words: Chinese-American in Japan, hearing the
  same language handled differently across communities, conversations with other
  learners, and the Japanese loanword homophone pattern (food/hood → フード) that
  started the whole investigation.
- **The competition** — VizCon 2026 theme + the "I had no idea" claim.
- **Data sources** — 10-row table: every dataset, what it provides, its licence.
- **How it was built** — 6 numbered methodology steps in plain language.
- **What this can't tell you** — 7 explicit limits, styled as a warning block.
- **Tools** — Python + vanilla JS/canvas, Kiro, pointer to GENAI_LOG.md.
Also shortened the nav label "Allophones: Variations on Sounds" → "Allophones"
(it wrapped on narrow screens) and HTML-escaped the `&` in "About &amp; Sources".

## TESTS + GENAI LOG

- Four suites after the page split, all passing:
  `smoke_test.mjs` (chart interactions, counting policy, examples),
  `smoke_chart.mjs` (NEW — rarity coverage guard, click tiers, comparison groups,
  chip tooltips/labels), `smoke_map.mjs` (was smoke_explore; geo + diaspora
  augmentation + map controls), `smoke_pages.mjs` (NEW — nav wiring on all 5
  pages + allophones/translation/difficulty inline scripts).
- ⚠️ Process note: rewriting `smoke_explore.mjs` by line-filtering out moved
  assertions broke it twice (orphaned refs, then broken syntax). Rewriting the
  file cleanly took less time than the second patch attempt. Don't surgically
  edit a test whose subject moved — restate it.
- smoke_test.mjs extended to ~30 more assertions for the allophone/merger
  sections. Assertions encode PROSE CLAIMS, so a finding going stale fails a test.
- GENAI_LOG.md — required for the Best Use of GenAI category. Documents what the
  model wrote, the 8 factual errors caught (incl. the two the model caught in its
  own output via its own tests), rejected data sources, and the repro pipeline.
- ⚠️ Tests cover data + logic, NOT visual rendering. Layout needs a browser pass.

## COUNTING POLICY (user challenge: "online says Hindi 44-49, we showed 74")

What goes into each number — consistent across ALL languages:
- **Allophones: NEVER counted.** They only drive the ◐ variant badge. All
  counts below use the Phoneme column only.
- **Raw source count** = rows in the chosen PHOIBLE inventory. Sources differ
  in whether they list long/geminate consonants (bː, kʰː) as separate
  phonemes — the Hindi "ph" source does (74 rows), textbooks don't (44-49).
- **Headline "distinct sounds" (soundCount)** = raw minus long/doubled forms
  (length marks ː ˑ stripped, geminates collapsed), tones excluded. This is
  the textbook-comparable number: Hindi 46 ✓ (online 44-49), English 44 ✓.
- **Base cells on chart** = soundCount minus aspiration/breathy/palatalization
  distinctions (merged into base cells, reported as "modified versions").
- **Tones** counted separately, flagged in headline.
- Residual differences vs. any particular textbook = source analysis choices
  (already footnoted via PHOIBLE FAQ link).
- Headline copy: "Hindi has 46 distinct sounds — 35 base sounds on this chart,
  11 modified versions (aspirated, breathy…) shown merged into their base
  cells. This source also lists 28 long/doubled forms, not counted here."

9. [x] **Phoneme-count accounting audit** (user caught "English 44 vs chart 36"):
       audit_accounting.py reconciles per language:
       raw PHOIBLE count = on-chart + extras + merged + tones + dropped.
       ✅ DROPPED = 0 for all 36 languages — nothing silently lost.
       The gap sources: (a) diphthongs/combination sounds → extras chips
       (Eng 44 = 36 chart + 8 extras); (b) base-normalization MERGES
       aspiration/length/palatalization distinctions into one cell — huge for
       South Asian langs (Hindi 74 raw → 35 cells + 39 merged; Punjabi 73;
       Amharic 68) — this is a DESIGN CHOICE (chart shows base articulations),
       not data loss; (c) tones counted separately (Cantonese 5, Vietnamese 8).
       Headline now shows honest full accounting: "Hindi distinguishes 74
       sounds in this source — 35 base sounds on this chart, 39 variations
       (aspiration, length…) shown merged into their base cells."
       ⚠️ Note for methodology: pair-comparison counts (share N / lacks M)
       operate at base-symbol level — Hindi /t̪/ vs /ʈ/ retroflex contrast
       partially survives (both on chart) but aspirated series does not.
8. [ ] Accessibility: don't rely on color alone; alt text per cell; keyboard nav
9. [ ] GenAI log: document Kiro/LLM usage throughout (Best Use of GenAI award)

## Design decisions

### DECIDED: Interactive chart concept (2026-07)
- IPA-style clickable chart; click symbol → hear it (Wikimedia Commons audio)
- Default = English highlighted; user selects a 2nd language → overlap display

### DECIDED: Allophone handling — 3-state cells (2026-07)
| State | Visual | UI label |
|---|---|---|
| Shared phoneme | Full color | "Core sound in both" |
| Allophone-only | Half-fill / hatched, muted | "Exists as a variant" |
| Absent | Empty/gray | "Not in this language" |
- Rationale: pure binary marks Spanish as "missing" /ð/ (nada!) and Japanese
  as "missing" /f/ (Fuji!) — bilingual viewers + SME judges would flag as wrong.
  Full allophone equality shrinks the gaps and kills the story.
- Rule 1: never say "phoneme/allophone" in primary UI → "core sound" / "variant
  sound"; technical terms live in tooltips/methodology.
- Rule 2: headline counts ("Japanese is missing 12 English sounds") use
  phonemes ONLY; variant state is visual nuance, excluded from counts.
- Tooltips carry the story: "Japanese has this as a variant of h before u —
  that's why 'Fuji' sounds right."
- Hand-verify allophone state for top ~15 L1s (PHOIBLE Allophones column +
  Speech Accent Archive generalizations); other languages degrade to 2-state.

### Open
- [ ] Rows = languages sorted by... speaker count? # missing sounds? family?
- [ ] Include "English sounds that are rare globally" flip side? (/θ/ /ð/ /ɹ/ /æ/
      are genuinely rare worldwide — nice reverse hook: "English is the weird one")
- [ ] Dialect choice for English target (GenAm vs RP changes the vowel set)
- [ ] Near-match strictness for the shared state (e.g. Spanish trill /r/ vs
      English /ɹ/ = different segments; keep exact-match for full color)

## Known gotchas
- PHOIBLE marginal segments: filter Marginal=TRUE rows or show separately
- Allophones vs phonemes: PHOIBLE lists phonemes; a language may HAVE the sound
  as an allophone (ja [ɸ] for /f/-ish) — this nuance IS the substitution story
- Vowels are messier than consonants (length/quality tradeoffs); consider
  leading with consonants, vowels as a second panel

## Key dates
- Submission: Fri Aug 10, 2026 (~27 days from Jul 14)
