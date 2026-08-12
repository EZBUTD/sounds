# GenAI usage log

An LLM (Kiro, Claude) wrote essentially all of the code and prose in this project, and a human directed
the questions, rejected bad output, and made every judgement call about what was
good enough to publish. The most valuable pattern was not generation — it was
**using the model to attack its own output until the numbers survived scrutiny.**

## What the model did

- **All analysis code** (~15 Python scripts) and the two front-end pages,
  including the canvas visualisations, written from natural-language direction.
- **Dataset discovery**: identified PHOIBLE, WikiPron, Glottolog, Natural Earth,
  `wordfreq`, and the Ethnologue-via-Wikipedia speaker table as viable sources,
  and identified which candidates to reject (see below).
- **Domain explanation**: phoneme vs allophone, why inventories disagree between
  sources, what makes a merger, what a Sprachbund is.
- **Narrative drafting**: section copy, tooltips, glossary definitions.
- **Its own test harness**: every analysis ships with assertions, several of
  which later caught real regressions.

## What the human did

- Chose the subject and the thesis, and rejected earlier ideas (food fusion,
  spice maps, L2 acquisition) before this one.
- Caught **factual errors in model output** that the model had stated
  confidently. These drove the biggest quality gains in the project:
  - "Italian should have ~30 phonemes, not 55" → exposed that the
    inventory-selection rule was biased toward maximalist analyses; led to
    `select_inventories.py` and corrected 6 languages.
  - "English has 44 phonemes, we show 36" → exposed unexplained accounting;
    led to `audit_accounting.py` proving nothing was silently dropped.
  - "Hindi is 44–49 online, we show 74" → led to the explicit counting policy.
  - "Remove Egyptian Arabic, it's confusing vs MSA" → led to `audit_roster.py`
    and removal of two register-pairs that were distorting the findings.
- Set the editorial line: no jargon in primary UI, footnote the disagreements,
  make encouragement the takeaway rather than exoticism.

## Where the model was wrong, and how it was caught

This is the part worth reading. In every case the error was caught by *testing
against known ground truth*, not by inspection.

| Model error | How it surfaced | Fix |
|---|---|---|
| Inventory rule picked maximalist analyses (Italian 55 phonemes) | Human domain knowledge | Median-based selection rule |
| Loanword mergers modelled on pure feature distance: predicted Spanish /b/→[p], Japanese /r/→[j] | Validation against 9 documented mergers — only 1 passed | Pinned conventional substitutions; 9/9 pass |
| Allophones treated as substitution targets, inventing a Korean coat/goat contrast | Same validation suite | Restricted targets to phonemes; documented why |
| Wrong validation anchor: asserted Mandarin *thin/din* merge | Model's own failing test, re-checked against phonology | Corrected to *thin/sin* — the test was wrong, not the code |
| Example words were dictionary junk (`ahi`, `ezh`, `bih`) | Reading the output | Added `wordfreq` Zipf filter |
| Claimed "no correlation" between sound rarity and learner counts | Computed r = 0.56, contradicting the prose | Confound check: the partial association is 0.16 controlling inventory size; lingua-franca status correlates at 0.71 in this small roster, without establishing cause |
| Diphthongs ranked as "world's rarest sounds" (English /əʊ/ at 0%) | Implausible result | Excluded multi-segment symbols from rarity; documented as notation artifact |
| Implied English is uniquely hard to learn | Checked whether it was an inventory-size effect | It is — Dutch ranks higher; reframed as arithmetic, not prestige |
| Counted one-sided allophone documentation as "realized differently", reporting Hindi + Punjabi as diverging on 100% of shared sounds | Human read the stat as implausible; PHOIBLE check showed Punjabi has allophone records for 1 of 73 rows | Divergence now requires records on *both* sides; languages under 15% coverage gated out; the whole cross-pair metric pulled from the page |
| Claimed an unreleased [t̚] in a recording of "cat" | Human listened to the file and heard a released stop | Word-final release is *optional* in English, so the recording need not contain it. Replaced with "stop", where post-/s/ lack of aspiration is the regular pattern; test now rejects the known-optional environment |
| Three successive voice-onset-time detectors returned wrong values (5 ms, 0 ms, then 174 ms for a ~26 ms interval) | Each contradicted the published range for English stops, and a frame-by-frame hand read of the audio | Anchored segmentation on the stop *closure* rather than on energy peaks; all three failures are written into the script so they are not retried |
| Formant estimator silently returned nothing for back vowels like [u] | A test with synthetic spectra at planted F1/F2 values | F2 search began at max(900 Hz, F1+250), above the real F2 of [u] (~800 Hz). Now searches from just above F1 |
| Set the vowel-label canvas font to `"600 15px var(--ipa-font), …"` | A test that reads back every font string the renderer assigns | A canvas font is not a CSS declaration: `var()` makes the shorthand invalid, so the assignment is *discarded* and the label falls back to 10 px sans-serif. Nothing throws. The stack is now resolved to literal font names before it reaches `ctx.font` |
| Wrote a test for the live-dot fix that passed on broken code | Deliberately deleting the fix and re-running — the test still passed | The test set the value through its own hook and then grepped the source for `lastLive = f`, which matched *the hook's own assignment*. Removed the setter and rewrote the test to push a synthetic voiced spectrum through the real `frameLoop` |
| Merger model predicted Japanese forms that are not Japanese words (ハスト for *fast*) while its own test suite passed 8/8 | A Japanese speaker looked up the output words | Four defects, the largest being that the shared normaliser strips vowel length — which Japanese contrasts phonemically — so the model invented mergers from the contrast it discarded. The transliterator test fed hand-written strings the pipeline never produces; end to end, *food* → フド, not the フード the test asserted. Page deleted rather than repaired: predicted collisions have no ground truth, and 9 passing anchors proved compatible with being wrong across 11,792 words |

Two of these are worth calling out because the model corrected *itself* by
running a test it had written: the merger model went 1/7 → 9/9 only because the
validation suite existed, and the "no correlation" claim was killed by the
model's own computation contradicting its own prose.

The last two rows are a different species of error and the most uncomfortable
ones: a *test* that was wrong rather than code. The live-dot case was found by
breaking the fix on purpose and confirming the test went red — and it did not.
Every new assertion is now checked that way, by reverting the thing it guards and
watching it fail, because a test that cannot fail is worse than no test: it reports
confidence it has not earned. Two of the four guards added for the clickable
vowel chart only became real tests after this exercise.

The merger row is the same disease at a larger scale, and it cost a whole page.
Its test suite was green the entire time the page was shipping non-words, because
the suite tested the transliterator on inputs the pipeline never sends it. The
lesson generalises past this project: **test the seam, not the function.** Every
one of the three test-that-passed-on-broken-code failures here lived at a boundary
that no assertion crossed.

The acoustic work on the Seeing Sounds page is where this discipline paid off
fastest. Voice onset time has a published expected range, so every wrong detector
announced itself immediately: 5 ms and 0 ms for an interval that should be ~70 ms,
then 174 ms for one that should be ~26 ms. Having an external anchor turned four
hours of plausible-looking output into four caught errors. The formant estimator
got the same treatment — synthetic spectra with planted F1/F2 peaks, which is how
the back-vowel failure surfaced before any user could hit it.

That contrast is the lesson. Where a number can be checked against something
outside the code, check it and the errors surface in minutes. Where it cannot,
be suspicious of publishing it at all:

The allophone divergence bug is the one the tests did *not* catch, and it is the
most instructive failure here. Every assertion about it was of the form "is this
number populated and is it large?" — which a metric measuring the wrong thing
passes easily. `divRate > 50` was true; it was true *because* the metric was
broken. Nothing compared the metric against ground truth, because there was no
ground truth to compare against: unlike the merger model, which could be checked
against 9 documented mergers, "how differently do these two languages realize
/t/?" has no published answer to test against. A human reading the output found
it in one glance. The lesson taken forward: when a claim cannot be validated
against an external anchor, that is itself a reason to be suspicious of
publishing it, not merely a reason to caveat it.

## The scope cut (2026-08)

The allophone layer was cut back after the review in `ALLOPHONE_REVIEW.md`.
PHOIBLE's allophone column cannot support cross-language comparison — real
variation is recorded for 74% of Russian's phoneme rows but 3% of Swahili's, 1% of
Punjabi's and 0% of Marathi's and Yoruba's. (Measured
by `audit_coverage.py`. A first version of that audit counted merely *populated*
cells, which reads ~100% almost everywhere because rows often just restate the
phoneme, and wrongly concluded coverage was binary — the metric that matters is
whether a listed variant *differs* from its phoneme.) Any pairwise "realized
differently" rate computed from it is substantially a measure of how much
fieldwork happens to be recorded.

**Correction (2026-08-10, prompted by the user).** Four files said English "has no
allophones", short-handing "the inventory we pinned for the chart records none".
That reads as a claim about the language and it is false. PHOIBLE's SPA inventory
160 documents differing variants for **68% of its 40 English phonemes** (27 rows) —
the highest coverage of any English inventory in the dataset — while the RP
inventory we chart (2252) and 2515 record 0%, and the PH inventories sit in between
(Australian 52%, British 42%, New Zealand 16%). The 0% is an artifact of which
inventory each source chose to annotate. Wording fixed in `allophones.html`,
`index.html`, `demos.js` and `analyze_allophones.py` to name the inventory rather
than the language, with a link to inv 160 so a reader can check. This is the third
data-quality issue the user caught by inspection (after Zulu clicks and the
coverage-metric error) and, like both of those, it was real.

Removed: the overlap-vs-divergence scatter, the six per-pair comparison cards,
the ranked bridge table, and every published divergence percentage.

Initially kept, because they did not depend on that column being complete:

- **The bridge lift** (English–Hindi overlap 52% → 61%) reads only *English's*
  variants. It was later removed because awarding an arbitrary half point still
  made a qualitative observation look like a measured improvement. The current
  page keeps bridge examples qualitative.
- **"Lost in translation"** never used the column at all — it mapped English
  phonemes onto each target inventory by 38 articulatory features and validated
  against 9 documented mergers. *(That page was later cut for an unrelated and
  worse reason; see "The second scope cut" below. The one allophone rule it cited
  — Japanese /h/ is commonly [ɸ] before /ɯ/ — is hand-pinned from reference
  grammars and survives on the Sound Variants page. The page now makes clear that
  several loanword patterns, not that alternation alone, help <em>food</em> and
  <em>hood</em> converge as <em>fūdo</em>.)*

Replaced with: six curated A/B **listening demos** (`docs/demos.js`) where
the reader hears the difference instead of being handed a percentage. Each side
has a distinct real playback target; one bridge uses the contextual recording of
<em>butter</em> because an isolated [t] would not demonstrate its [ɾ] allophone.
Two originally planned demos — English
alveolar /t/ vs Hindi dental /t̪/, and clear vs dark /l/ — were dropped because
neither /t̪/ nor /ɫ/ exists in the 117-file audio set, and playing a plain /t/
while labelling it "dental" would have been a fabricated comparison of exactly
the kind this cut was meant to remove.

## The second scope cut: "Lost in Translation" removed entirely (2026-08-11)

The merger page was the project's origin story — the thing that made me start it —
and it is now deleted. It generalised *food*/*hood* → フード into a model: map each
English phoneme to the closest sound a target language has (38 PHOIBLE features,
weighted Hamming, class-guarded), apply that to 11,792 common English words, and
report which pairs collapse into a homophone. It reported a collision rate per
language and reproduced 9/9 documented mergers.

**How it was caught.** A user asked where the words came from, having looked up the
Japanese output: "most of them are not real, like ハスト." Tracing all 8 shipped
Japanese examples back through the pipeline found four defects:

1. **Vowel length was discarded.** `norm()` strips length marks, and the pinned
   overrides mapped `ɑ æ ʌ ɜ ə` all to `a`. So *fast* /fɑːst/ and *first* /fɜːst/
   became the same string. Japanese length is **phonemic** — ファスト and ファースト
   are different words — so the model manufactured a merger out of the exact
   contrast it had thrown away. This inflated every collision rate, not only the
   examples, which is why the rates were less defensible than the cards.
2. **Half the examples rode on a dialect variant.** The lexicon holds 1.35
   pronunciations per word (24% of words have more than one) and dropped every
   variant into the collision buckets with equal weight. Restricting to each word's
   first-listed pronunciation, **4 of 8** examples vanished. *late = rate = right*
   needed *right* pronounced /ɹeɪt/ — which is simply the word *rate*.
3. **A pinned substitution overreached.** /f/ → /h/ was pinned to set up the seed
   case, since Japanese /h/ is [ɸ] before /u/. The context rule fired only before
   /u/, so every other /f/ stayed /h/: ハスト for *fast*, ヘスト for *first*.
4. **A fix written at the wrong layer.** `build_native_script.py` mapped /ŋ/ → ング
   with a comment saying ン "gave ロン for long, which is a different word". The
   merger model had already rewritten ŋ → ɴ upstream, so the rule could never fire
   and the page still showed ロン.

**The part that matters for this log.** `test_native_script.py` passed 8/8,
including a case asserting `h·u·u·d·o` → フード. That input is hand-written and the
pipeline never produces it: run end to end, *food* comes out `h·u·d` → **フド**. The
page's own headline example was not reproduced by the code that generated the page,
and every test was green. The `ɾ·o·ŋ` → ロング case in the same suite is the tell —
no shipped form ever contained `ŋ`.

That is the third instance in this project of a test passing on broken code, and
they share one shape: **the test's subject was adjacent to the thing that shipped.**
The divergence-rate test asserted a number was large. The dendrogram test validated
a bug against itself. This one tested a function on inputs its caller never sends.

**Why removal rather than repair.** All four defects were fixable in a day. The
decision to delete instead rests on the same reasoning that killed the divergence
metric: predicted collisions have **no external ground truth**. The 9-merger suite
was the only anchor available, and it turned out that passing it was fully
compatible with being wrong across 11,792 words. A model whose only validation is
9 hand-picked cases cannot be trusted to the 4-significant-figure collision rates
the page was printing. Fixing the four known defects would have produced a model
that was wrong in *unknown* ways instead of known ones.

Deleted: the legacy `translation.html` and `nativescript.js`,
`build_native_script.py`, `test_native_script.py`, `analyze_mergers.py`,
`merger_analysis.json`, and `DEEP.mergers` (deep.js fell from 10 KB to 1.9 KB).

Kept: the documented alternation underneath it — Japanese /h/ is commonly [ɸ]
before /ɯ/ — which lives on the Sound Variants page with audio, sourced to
reference grammars rather than modelled. The revised copy does not present that
single alternation as the cause of the *food*/*hood* loanword convergence.

The removal is enforced rather than assumed. `smoke_pages.mjs` now fails if the
page, the transliterator, `DEEP.mergers`, or any link to them reappears, and if
the About page stops explaining the cut. Each of those four guards was checked by
restoring the thing it guards and confirming the test went red.

## Replacing the MDS scatter with a dendrogram (2026-08-10)

A reader said the "sound map" scatter "looks a bit random" and asked whether it
could be made understandable or should be cut. Checking the number rather than
defending the chart: the MDS embedding correlated with the true pairwise
distances at only **r = 0.67**, so roughly half the distance structure did not
survive the projection — and MDS axes carry no interpretable meaning by
construction, so there was nothing for a reader to anchor on. The impression of
randomness was substantially correct.

Rather than cut the section, it was redrawn as a **dendrogram of the UPGMA tree
the project already computed** and previously discarded after using it for the
heatmap row order and the 60% cluster cut. This is lossless where the scatter was
not: every fork sits at the exact average similarity at which its two branches
merged, so a position on the x-axis *is* a measured number. It is also the same
shape as a family tree, which is precisely the comparison the section is making.

The switch surfaced a factual error in the draft copy. The new prose asserted that
every sound neighbourhood at the cut mixes language families; the test written
alongside it failed with "only 5 of 6 are". **Dutch + French + German** is a
single-family group. The honest version is better material — it names the one case
where ancestry does win, and why (a thousand years of contact between neighbours).
The rendered fraction is now generated from the data, and the test asserts the
single-family exception stays unique and stays named in the prose.

`analyze_families.py` also had to stop reordering a fork's children for visual
tidiness: doing so desynchronised the tree's leaf order from `heatmapOrder`,
which is derived from the same merge sequence, so the two visuals would have
disagreed about which languages are adjacent. A test now asserts the two orders
are identical.

Because canvas drawing is invisible to the DOM stub, the layout math is
replicated in `smoke_chart.mjs`: row height clears the label size, no fork spills
off-canvas or overruns the label gutter, the cut line lands inside the fork range,
and the longest label fits. A layout regression now fails a test rather than only
showing up in a browser.

## Tone pass: matching the confidence of the prose to the evidence

Late in the project the reader-facing copy was rewritten. The problem wasn't
individual facts — those had been checked — but framing. The prose had a habit of
presenting findings as reveals ("Plot twist", "The data disagrees", "That reading
is a trap"), and of stating conclusions more firmly than one inventory per language
from a partial sample can support.

That mattered here more than it might elsewhere, because **four separate factual
errors in this project were errors of overconfidence rather than of arithmetic**: a
claimed "no correlation" that was r=0.56; "English has no allophones" when one
inventory lacked them; "every sound neighbourhood mixes families" when it was 5 of
6; and a divergence metric reported as a finding when it was mostly measuring
documentation density. In each case the sentence was more certain than the data. A
voice that reaches for the strong version of a claim will keep producing that class
of error.

The rewrite moved toward describing what the data shows and letting the reader draw
the conclusion. Concretely: "The data disagrees" → "By this measure it sits on the
other side"; "Languages don't inherit their sound pools" → "Ancestry is a weak
predictor of how a language sounds"; "That reading is a trap, and the trap is worth
showing" → "That reading doesn't hold up, and it's worth walking through why";
"sound difficulty simply doesn't predict learner numbers — empire, trade and
schooling do" → "doesn't appear to predict learner numbers in this sample", with
the sample size named. Several passages gained a sentence of scope rather than
losing one: the 90% Amharic–Indonesian figure now notes it shouldn't be read as
more precise than it is, and the lone branch on the tree is now described as a
property of these 34 languages rather than of the language itself.

Two things were fixed rather than reworded. A paragraph still said "these 36
languages" from before two were removed from the roster — a stale number surfaced
by reading the prose as prose. And the /t/ strip's caveat box was one 150-word
sentence, now split.

A `tone` guard was added to `smoke_pages.mjs`: ten regexes for the specific
phrasings that produced the earlier errors ("the data disagrees", "this proves",
"no correlation", "is a trap", "plot twist", "English has no allophones", and so
on), checked against reader-visible prose with scripts and comments stripped.
Verified by reintroducing "Plot twist" and watching it fail. The `no correlation`
pattern deliberately allows the phrase inside quotation marks, since the About page
legitimately quotes it when describing the error it caused.

## The axis was mislabelled, and a reader's question found it

A reader asked why Mandarin hangs off the root alone when it looks closer to
Cantonese and Korean than the root's 36%. The question contained a correct
observation about the chart that I had not noticed.

Checking the arithmetic: **a UPGMA fork sits at the average overlap across every
pair spanning its two branches, not at the closest pair.** Verified for all 33
forks — each one equals its cross-branch mean to within 1e-3. The root fork's
35.83% is exactly Mandarin's mean overlap against all 33 other languages
(35.83%), not its distance from any neighbour.

The axis had been labelled *"sound overlap at which two branches merge"*, which
invites precisely the reading the reader gave it: that the leftmost fork is
Mandarin's similarity to its nearest relative. Under that reading the chart looks
wrong, because Mandarin–Korean is 46%, well right of 36%. The label was the defect,
not the tree. Now: *"average sound overlap between the two branches a fork
joins"*, with the intro prose matching, and a test asserting every fork equals its
cross-branch mean **and** that the word "average" is present in the label. A
mislabelled axis is a wrong chart even when the geometry is right.

The second half of the answer is real too: Mandarin's best match (Korean, 46%) is
the weakest best-match in the dataset — every other language has a partner above
54% — and its two nearest neighbours prefer each other, Cantonese–Korean at 58%,
so that branch closes before Mandarin can join it. Both halves are now explained
in generated copy: the loner is found by inspecting the tree, and every figure is
computed, so if the inventories change the paragraph follows instead of becoming a
stale anecdote naming the wrong language.

Also removed, at the reader's request: the dashed 60% cut line. The threshold still
defines the neighbourhoods the prose cites, but drawing it as a vertical rule
implied the number mattered in itself rather than being the slice we chose. A test
now fails if the line comes back.

## "Still not visible": a silent failure, found only by using a real browser

After the axis inversion was fixed, the reader reported the dendrogram *still* not
rendering — while every test passed. Two wrong claims in a row about the same
chart, which is the signal to stop reasoning about the code and go look at it.

Installed Playwright and loaded the page in headless Chromium. The chart rendered
**correctly**: 54,944 non-background pixels, ink spanning x=15..831 of 900, 344
pixel rows carrying leaf-label text, no console errors. So the shipped code was
fine and the reader's *session* differed.

The hypothesis that fit was a **stale cached `analysis.js`**: the tree data was
added to that bundle in this same session, and the drawing block was guarded by a
bare `if (ANALYSIS.tree)`. Reproduced it by intercepting the request and serving
the bundle with its `tree` key deleted — blank canvas, empty placeholders, empty
legend, **and nothing logged anywhere**. Exactly "not visible", with no diagnostic
trail. `file://` pages get no cache headers, so a browser can hold a bundle
indefinitely.

Three fixes, in order of how much they matter:

1. **The page now fails loudly.** The bare `if` became an `if/else` that writes a
   visible panel into `#treeWrap` naming the cause and the remedy (hard reload;
   re-run `analyze_families.py`) and logs to the console. A missing data key can no
   longer present as a blank space.
2. **`stamp_assets.py`** appends a content hash to every local `src`/`href`
   (`analysis.js?v=807348e5`). Regenerating a bundle changes the URL, so a stale
   copy cannot be served. Run it after any build script.
3. **A former real-browser smoke suite** loaded every page in
   Chromium, fails on any console error or uncaught exception, and reads back
   canvas pixels: minimum ink per canvas, bounding box spanning the expected width
   and height, label text present in the right-hand band, all word-audio files
   actually loading, and a regression case asserting the stale-bundle path shows
   its visible message. This is the gap the DOM stub could never cover — its
   canvas context swallows every drawing call, so it proves the code *runs*, never
   that anything *appears*.

Two of my own test bugs surfaced while writing that suite, both worth noting
because they are the same species as the thing being tested: the stale-bundle case
initially failed because the helper counted the guard's own intentional
`console.error` as a failure, and the audio check failed because `fetch()` is
blocked cross-origin on `file://` — switched to an `<audio>` element, which is what
the page actually uses. A test asserting the wrong thing fails just as loudly as a
real bug, and is easy to mistake for one.

Rendered output saved to `soundtree_render.png` so the chart can be checked
without a browser.

## The test that validated a bug against itself (2026-08-10)

The dendrogram shipped **not rendering** — or rather, rendering illegibly: the
x-mapping was written with an inverted term, `PL + plotW * (1 - t)`, which put the
root fork at x=728 (the right edge, in the label gutter), the leaf tips at x=16,
and every language label at x=31 — drawn directly on top of the branches. The axis
also ran backwards relative to the scale printed underneath it.

**The geometry test passed anyway, because it hard-copied the buggy formula.** It
had been written by inlining the layout math from `index.html`, so it inherited the
inversion and then checked that inverted output against inverted expectations. It
verified that forks fell inside the plot box — true in both orientations — and
never checked *direction* or whether labels collided with the drawing.

This is the same failure mode as the allophone divergence bug recorded above,
in a new costume: an assertion that a value is present and in range cannot catch a
value that is computed wrongly. There the metric measured the wrong thing; here the
test measured the code against a copy of itself.

Fixed on both sides. The mapping now ascends (higher similarity draws further
right, matching the printed scale). The test now **parses the real constants and
the real `xOf` expression out of `index.html`** and evaluates them, then asserts
the properties that make the chart readable rather than restating the arithmetic:

- higher similarity must draw further right, and the mapping must be strictly
  monotonic across the whole range
- the root fork anchors the left pad; the leaf tips anchor the label gutter
- **label text must begin to the right of every fork** — this check alone would
  have caught the inversion
- the longest label must fit on canvas, rows must clear the font size, the dashed
  cut line must land among the forks, and every axis tick must be on canvas

Verified by reintroducing the inversion: the test now fails with
`x-axis is inverted: 90% draws at x=76 but 40% at x=678`. A test that can't be
shown to fail on the bug it targets isn't evidence of anything.

## Word audio for the English /t/ allophones (2026-08-10)

The /t/ strip originally played isolated IPA segments and had to leave the middle
cell silent, labelled "no isolated recording". The reader suggested Wikimedia
Commons word recordings, which is the better answer: **two of the three
realisations need to be heard inside a word.** A contextual word recording shows
why a pronunciation appears there; an isolated reference phone cannot do that on
its own. The tap in "butter," for example, is a positional variant of English
/t/, even though a generic [ɾ] reference recording also exists.

Three files, fetched and licence-verified live against the Commons API by
`download_word_audio.py`: `En-us-top.ogg`, `En-us-stop.ogg`,
`En-us-butter.ogg` — all by **Dvortygirl**, General American,
**CC BY-SA 3.0**. One speaker across all three matters here: with three different
voices the listener would be hearing speaker differences, not allophony.

The strip names the shared phoneme `/t/` once, then shows the different phonetic
transcription on each card. This keeps the phoneme/allophone distinction visible
without repeating a near-identical broad line three times. Attribution renders on
the page; the manifest is `audio_manifest_words.csv`.

The current consistency test asserts that every contextual word file exists and
that each cross-language listening card has two different, real playback targets.
The site-integrity test separately checks scripts, local links and accessible chart
alternatives.

## A playable button with the wrong label on it (2026-08-10)

The History of English page writes sounds into prose with a `{{x}}` token that is
substituted for a playable chip. English's *sh* sound came from an earlier
**/sk/**, so the draft wrote `{{sk}}` — and, because /sk/ has no single chart
symbol, the code aliased the token to `"s"`. The page then rendered **a clickable
button reading "s" in the middle of a sentence about sk**, which played the /s/
recording.

This is the third appearance of one failure mode in this project:

| where | what was substituted | why it was wrong |
|---|---|---|
| `build_chart_data.py` | `ç` → `c` (diacritic stripped by `norm()`) | gave English a palatal *stop* it does not have |
| `analyze_geography.py` | Zulu `kǀ` vs `ǀ` | clicks scored as "not rare"; later, rare-sounds rows read "signature sound of —" |
| `history.html` | `sk` → `s` | a control that plays a real sound, labelled as a different sound |

**A symbol that looks close enough is not the same symbol.** The fix follows the
rule already adopted for the native-script transliterations: render nothing rather
than something approximate. Clusters are now listed in a `CLUSTERS` table and
emitted as italic spellings — *sk*, *kn* — never as chips.

### Five of my own guards were not guards

I wrote ten checks for this page, then tampered each corresponding line to confirm
it failed. **Five passed with the bug reintroduced:**

- the cluster check asserted `data-sym="sk"` was *absent* — but the bug emitted
  `data-sym="s"`, which is a perfectly valid chip. It now requires each cluster to
  reach the page **as its own spelling**, which is the property that was actually
  broken.
- the "timeline is not from PHOIBLE" check scanned the whole file and was satisfied
  by a **source comment no reader ever sees**. It passed with the disclosure
  deleted from the visible page. Now scans reader-visible prose only.
- the hedged-dates check allowed one unhedged date as slack, so changing
  `about 1400 to 1700` to `1400-1700` slipped through. Now zero tolerance.
- the sources check only looked for a phoneme URL, so relabelling
  **Sources → Notes** passed. Now requires the heading too.
- the causes-are-open check matched either of two phrases, so removing one still
  passed. Now requires both.

Two of my *tampers* were also wrong — they reintroduced a defect the code
legitimately handled, so "no failure" was the correct outcome and I misread it as a
missing guard. The dead-chip case needed **two** simultaneous edits (reference a
symbol without audio *and* remove the audio check); either alone is harmless.

After fixing: all ten regressions fail the suite, and the original passes. The
harness was deleted. Restating the earlier lesson, sharpened — it is not enough to
write a guard and see it pass. **A guard must be shown to fail on the specific
defect it names, and the tamper used to show it has to be checked too.**

## Three layout bugs a string test cannot see (2026-08-10)

The sound-lineage diagram is CSS-positioned — percentage offsets inside a grid,
no canvas — so `smoke_pages.mjs` can only check the markup that goes in. It
passed. Measuring the same diagram in Chromium found three defects, each
invisible to those assertions:

1. **Outcome labels sat on the track with an opaque background**, masking the
   right end of every line. A sound that survives to the present looked like it
   stopped at its label — which inverts the diagram's single most important
   reading. Fixed by giving the labels their own grid column.
2. **The year axis drifted out of alignment with the track** once that third
   column was added, so every loss marker sat under the wrong century. Now
   checked to within 2px.
3. **Per-row lane tags overlapped the lane they labelled.** Repeating "English /
   German, Dutch" on all six rows also added twelve labels of text to a diagram
   whose purpose was to *replace* text. Moved into the first row alone, the lower
   tag landed on the continental lane. Replaced with one key line above.

The lesson is the same one the dendrogram taught, in a new medium: **for anything
positioned rather than written, the test has to measure the rendered result.** The
checks now live in `smoke_render.mjs` and assert geometry — axis aligned to the
track, ticks ascending, no lane under a label, a `kept` lane reaching the right
edge, a `lost` lane not reaching it, the two lanes at different heights, each ✕
within 6px of its lane end, and the whole thing surviving a 520px viewport.

### The overlap guard was measuring the wrong thing
Written and seen to pass, it compared each lane's right edge against the *outcome
column's* left edge. Tampering revealed that says nothing about the actual bug:
with the labels positioned back inside the track, the (now empty) column still sat
to the right, so the check passed while the labels covered the lines. It now
compares the label and lane **elements** directly — box against box.

Caught only because the first tamper attempt was too broad: it broke alignment as
well as overlap, so the *axis* guard fired and I nearly recorded the overlap guard
as verified on the strength of a failure it did not cause. Isolating the defect to
one change is part of the check. All seven layout guards now fail on their own
regression and the original passes.

## The visual that could not express the subject (2026-08-10)

The history page's second visual drew each sound as a row with two lanes: English
above, German and Dutch below. It was measured, tested, and geometrically correct.
The reader's verdict: *"hard to read, and doesn't seem to display gained phonemes
from other languages."*

The second half of that is the real fault, and no amount of layout polish would
have fixed it. **The two-lane form could only express English against its
siblings.** A sound English acquired from French had nowhere to come *from*, so it
was drawn as "arrived from inside English" or left out entirely. A page about a
language reshaped by borrowing had a diagram structurally incapable of showing
borrowing — and I had spent the previous round fixing pixel alignment inside it.

Rebuilt as one English trunk with branches flowing in and out. Six arrivals (three
from French, two from inside English) and two departures, each meeting the line at
its year, each carrying the cognates on both ends. The form change made a new claim
expressible: `dʒ` came in from French around 1250, and **French later lost it**, so
English now keeps a sound its donor gave up. The two-lane version had no way to
say that.

Worth generalising: a chart can pass every geometry check and still be the wrong
chart. "Does the layout work?" and "can this shape hold the argument?" are separate
questions, and I only asked the first.

### Measuring the rebuild found two more layout bugs
Both invisible to markup assertions, both found by reading back rendered boxes:
**five pairs of labels drawn on top of each other** (labels are ~250 units wide and
several sounds arrive within decades — v and z both land at 1200), then **one more
across the trunk** once each side was packed independently: ŋ arriving in 1600
collided with y leaving in 1300. Fixed with first-fit interval packing per side,
plus explicit clearance above and below the line.

### A tamper that proved the wrong thing
I wrote a case that reverted row packing to one-row-per-flow, expecting overlaps.
It produced none — `ROW` exceeds a label's height, so naive stacking is *safe*,
just 300px taller (1025px vs 725px). The mechanism I had described as an overlap
guard is really a **compactness** mechanism, and no overlap check can defend it.

So the guard now asserts what packing actually buys: that eight branches occupy
fewer than eight distinct rows, and that the diagram stays under ~820px. On a page
whose brief was "less text, more visual", silent vertical bloat is the regression
worth catching. This is the second round in a row where tampering corrected my
description of my own code rather than finding a bug in the page.

## Process failures worth not repeating

Distinct from the data errors above: these are ways the *work* stalled, not ways
the *numbers* were wrong.

- **Never grep a minified / single-line data file.** `docs/data.js` is a large
  of JSON on one physical line. Searching it for a key that appears ~20 times
  returns the same multi-kilobyte line ~20 times — no new information per hit, and
  it swamps the context. Symptom: identical truncated output repeating. Instead,
  load the file and query it: `node -e "const D=new Function(fs.readFileSync
  ('data.js','utf8')+';return DATA;')(); ..."`, or `python3 -c` for the JSON/CSV
  equivalents. Same rule for `mapdata.js` (202 KB, one line) and `rarity.js`.
  Grep is for source you intend to *read*; use a parser for data you intend to
  *query*. (Recorded once, then repeated immediately afterwards on `rarity.js` —
  the rule needs applying at the moment the include pattern is written, not
  recalled after the output arrives. The generated `docs/*.js` bundles are
  *all* single-line; only `chart_extras.js`, `nav.js`, `demos.js` and the HTML are
  human-written and safe to grep.)
- **Don't build a one-off verification script and delete it.** The dendrogram's
  canvas geometry was first checked with a throwaway `.geom.mjs`. Anything worth
  checking once is worth checking on every run: it was inlined into
  `smoke_chart.mjs` instead, where it now guards against label collisions and
  off-canvas drawing permanently. Throwaway scripts are for *edits*; checks belong
  in the suite.
- **Never let a test hard-copy the code it is testing.** Inlining that geometry
  check copied the formulas out of `index.html`, so the copy inherited an inverted
  x-axis and validated the bug against itself (full write-up above). Parse the real
  expression out of the source and evaluate it, or assert an invariant the
  implementation cannot satisfy by accident — never restate the arithmetic.
- **Assert direction and collision, not just bounds.** "Is this inside the canvas"
  is true for a chart drawn backwards. For any layout: check ordering, check that
  text does not overlap the drawing, and confirm the check fails when the bug is
  deliberately reintroduced.
- **A canvas stub proves the code runs, not that the output is legible.** The
  dendrogram executed cleanly and issued 40 strokes and 34 leaf dots while being
  unreadable on screen. Where the harness cannot see a visual, test the
  *coordinates* it would produce — and better, load it in a real browser and read
  back pixels (`smoke_render.mjs`).
- **Two wrong claims about the same thing means stop reasoning and go look.** The
  dendrogram was declared fixed twice while still failing for the reader. The
  browser was available the whole time; installing Playwright took one command and
  answered in one run what two rounds of inference got wrong. When a report
  contradicts a passing test, the test is the thing in doubt.
- **Never guard a render on data with a bare `if`.** `if (ANALYSIS.tree) { …draw… }`
  turns a missing key into an invisible no-op — the worst possible failure, because
  there is nothing to search for. Always add the `else` that says what is missing
  and why.
- **Regenerated data bundles need cache-busting.** Same filename plus new contents
  is precisely what browser caches get wrong, and `file://` has no cache headers to
  negotiate with. `stamp_assets.py` hashes every asset reference; run it after any
  build script.
- **`!!` and bare `!` break under zsh history expansion.** `node -e "...!!x..."`
  was mangled into a syntax error mid-debugging. Write probes to a file and run
  the file.
- **Label the statistic you actually computed.** The dendrogram's axis said "the
  overlap at which two branches merge" when the value was the *average* overlap
  across the branches. Geometry correct, chart wrong — a reader followed the label,
  got a contradiction, and reported it as a bug in the tree. When an axis shows an
  aggregate, name the aggregate, and assert the wording in a test alongside the
  arithmetic.
- **A reader asking "why is X like this?" is often reporting a defect.** Three of
  the four issues found by inspection in this project arrived as questions rather
  than bug reports (Zulu clicks, English allophones, this axis). Check the data
  before explaining the behaviour.
- **Overconfident voice produces overconfident errors.** Four of the factual
  mistakes in this project were the strong version of a defensible claim, not bad
  arithmetic. Writing "in this sample" and "appears to" isn't hedging for its own
  sake; it keeps the sentence inside what the data actually covers. Reaching for
  the punchier phrasing is what generated the errors in the first place.
- **Verify the verifier before trusting it.** Chasing whether English's borrowed
  allophones were real, I wrote three throwaway checkers in a row and each had its
  own bug — one reported the chart renders 28 symbols when it renders 92, because
  the object walker was wrong. Two turns went into inspecting output that was
  itself untrustworthy. A checker whose result you cannot sanity-check against a
  known number is not evidence. The productive move was abandoning the data change
  entirely: the request ("remove the asterisk") never required it.
- **When a sub-task balloons, re-read the actual request.** The asterisk removal
  became an inventory-merging exercise because I decided the marker should become
  accurate rather than disappear. Removing a misleading marker is a one-line
  display change; making it accurate meant transplanting allophones between
  inventories, which surfaced diacritic-stripping artifacts (`ç` → `c`, a different
  sound), self-restating entries, and multi-segment symbols. Reverted and
  documented as a deliberate non-goal in `build_chart_data.py`.
- **Derive index tables, don't hand-number them.** The Hangul composer put ㅎ at
  lead index 19 when the alphabet has 19 letters and so ends at 18, producing a
  surrogate codepoint instead of a syllable. Looking the letter up in the jamo
  string (`LEADS.index("ᄒ")`) cannot drift out of step with the formula that
  consumes it. Same lesson as the katakana digraph table, where indexing a
  concatenated string returned half a character.
- **A transliterator needs ground truth before it ships.** `test_native_script.py`
  checks the output against borrowings whose spelling is well known (<em>food</em> →
  フード, <em>long</em> → ロング, <em>hot</em> → 홋). It caught four real bugs and
  went 6/8 → 14/14. Without it, ロン for "long" — a different word — would have
  shipped looking plausible.
- **Read the prose as prose, periodically.** Extracting all the copy as plain text
  surfaced a stale "these 36 languages" (the roster is 34) and a 150-word sentence,
  neither of which any data test would catch. Tests check numbers; only reading
  checks writing.
- **Quote a fraction, not "all", unless a test enforces "all".** Draft copy
  claimed every sound neighbourhood mixes language families. It is 5 of 6. The
  generated-fraction pattern (`${mixed} of its ${nCl} groups`) cannot go stale
  when the data shifts, whereas a hand-written "all" silently becomes a lie.
- **Don't surgically line-edit a test whose subject has moved.** Rewrite it.
  `smoke_explore.mjs` was patched twice against a page that no longer existed
  before being rewritten cleanly as `smoke_map.mjs`.
- **When a fresh measurement contradicts an already-documented finding, suspect
  the measurement first.** A re-run of the coverage audit reported ~100% allophone
  coverage almost everywhere, contradicting `ALLOPHONE_REVIEW.md`. Acting on the
  new number would have meant rewriting correct prose to be wrong; the new number
  was measuring cell population, not variation.
- **Bulk structural deletions belong in a throwaway script with assertions, not
  in a sequence of hand edits.** Removing the duplicated sections from
  `index.html` was done by a one-shot Python script that asserted each expected
  marker was inside the cut region, then printed a checklist of identifiers that
  must no longer appear. That converts "did I get all of it?" into a test.

## Rejected sources (and why)

- **IPA Handbook audio** — license forbids embedding. Used Wikimedia Commons.
- **Wikipedia phoneme-count list** — the page itself warns counts "differ
  radically between sources"; would break single-source consistency.
- **Ethnologue** — paywalled; used its figures as tabulated on Wikipedia, cited.
- **Wikidata speaker counts** — has L1 but no L2 split; mixing it with Ethnologue
  would produce inconsistent numbers, so 9 languages are shown as "unknown"
  rather than silently filled from a second source.
- **PhoneticFlashCards repo** — same Commons files at second hand, fewer of them.

## Verification practice

Every analysis has an executable check, and the front-end has six smoke suites
that run the real page code against a DOM stub (plus one against a real browser).
Assertions encode *claims made in the prose*, so if a finding stops being true the
test fails — the difficulty page test fails if the copy ever claims "no
correlation" again, and the spectrogram test fails if a measured voice onset time
drifts outside the published range for English stops.

The suite also carries *negative* assertions guarding both scope cuts. It fails if
the divergence scatter returns to `deep.js`, if the render script emits a "realized
differently" rate, if the `a-divrate` placeholder reappears, if Punjabi, Swahili or
Polish are ever trusted for divergence again, if any listening demo references a
sound with no audio file or plays the same recording on both sides of an A/B pair,
and — after the second cut — if `translation.html`, `nativescript.js` or
`DEEP.mergers` reappears, if any page links to them, or if the About page stops
explaining why they went.

Known gaps, in order of how much they have actually cost:

- **A test can be adjacent to its subject and still pass.** This has happened three
  times here, and once it cost an entire page. Assertions now have to cross the
  seam they care about: drive the real pipeline, not a function the pipeline calls
  with different arguments.
- **A number being present and large proves nothing** about whether it measures the
  right thing (the divergence bug).
- **A test is not a test until it has been seen to fail.** Every new guard is now
  checked by reverting the thing it guards.
- Visual rendering is only partly covered: `smoke_render.mjs` catches console
  errors and blank canvases in a real browser, but layout quality is still eye-checked.

## Reproducing

```bash
python3 build/select_inventories.py
python3 build/build_chart_data.py       # -> docs/data.js
python3 build/mine_examples.py          # optional WikiPron candidate examples
python3 build/analyze_pairs.py          # 561 pairwise overlaps
python3 build/analyze_families.py       # -> docs/analysis.js
python3 build/analyze_allophones.py
python3 build/analyze_spectrograms.py   # -> docs/spectro.js
python3 build/build_deep_data.py        # -> docs/deep.js
python3 build/fetch_geo_speakers.py
python3 build/analyze_geography.py
python3 build/analyze_l2_drivers.py
python3 build/analyze_asymmetry.py
python3 build/build_map_data.py         # -> docs/mapdata.js
python3 build/build_history_data.py     # -> docs/history_data.js
python3 build/stamp_assets.py           # cache-bust asset refs; run last

node tests/comparison_consistency.mjs
node tests/site_integrity.mjs
python3 build/audit_coverage.py
```
