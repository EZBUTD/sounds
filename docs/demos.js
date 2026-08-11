/* Curated allophone listening demos.
 *
 * WHY THIS FILE IS HAND-WRITTEN, NOT GENERATED
 * PHOIBLE records actual allophonic VARIATION very unevenly: Russian 74% of its
 * phoneme rows, Zulu 47%, Hindi 39%, but Swahili 3%, Punjabi 1%, and Marathi and
 * Yoruba 0% (audit_coverage.py measures this; note the raw `Allophones` cell is
 * non-empty for ~100% of rows in most inventories, often just restating the
 * phoneme, so cell-population is not the metric that matters).
 *
 * English is unevenness of a different kind: the RP inventory pinned for the
 * Sound Chart (PHOIBLE 2252) records 0%, but PHOIBLE's SPA inventory 160
 * documents differing variants for 68% of its English phonemes (27/40), and the
 * PH inventories land between (Australian 52%, British 42%, American 26%). So the
 * variation is well documented for English — just not in the inventory we chart.
 * That is why `analyze_allophones.py` supplements English from inv 160, and why
 * the page must say "the charted inventory records none", never "English has none".
 *
 * Mining it for "these two languages realize /x/
 * differently" therefore compares fieldwork depth, not speakers — and the records
 * that do exist are stacked phonetic diacritics (d̪̤̚, t̪̚ʰ) that most fonts cannot
 * render legibly.
 *
 * So each contrast below is taken from standard descriptive accounts, and each
 * `symbol` is a real IPA segment that has its own audio file in DATA.audio —
 * the two sides of every pair are genuinely different recordings, never the
 * same file relabelled.
 *
 * Invariant: every `symbol` must exist in DATA.audio, and the two symbols in a
 * pair must differ. smoke_test.mjs enforces both.
 */
const DEMOS = {
  // ---------------------------------------------------------------------------
  // A WITHIN-ONE-LANGUAGE example, used at the definition so a reader meets
  // "phoneme vs allophone" before meeting any cross-language comparison.
  //
  // Everything else in this file compares ONE phoneme across TWO languages,
  // which readers were mistaking for phoneme-vs-allophone. This strip is the
  // real thing: a single English phoneme /t/ in three positions, none of which
  // changes a word's meaning.
  //
  // Each variant plays a real recording of the WHOLE WORD, not an isolated IPA
  // segment. That is the only honest way to demonstrate this: these allophones
  // exist only in context. The [t] of "stop" is unaspirated BECAUSE of the
  // preceding /s/, and the tap in "butter" is a positional allophone of /t/
  // rather than a segment any IPA reference files under English. Playing an
  // isolated /t/ and labelling it would be a fabricated comparison.
  //
  // WORD CHOICE — prefer OBLIGATORY allophones. "cat" was used here for the
  // unreleased [t̚] and was removed: word-final stop release in English is
  // OPTIONAL, so the recording did not dependably contain the allophone the card
  // claimed. (Caught by listening to the file, not by any test — the character
  // was in the markup either way.) "stop" replaces it because suppression of
  // aspiration after /s/ is exceptionless in General American, so any competent
  // recording demonstrates it. "top" vs "stop" is also a near-minimal pair, which
  // makes the contrast easier to hear than two unrelated words.
  //
  // All three files are by the SAME speaker (Dvortygirl, General American,
  // CC BY-SA 3.0), so the listener hears the allophonic difference rather than
  // three different voices. Fetched and licence-verified by
  // download_word_audio.py; attribution in audio_manifest_words.csv.
  //
  // `phonemic` is the broad transcription (what the language treats as the same
  // sound); `phonetic` is the narrow one (what the mouth actually does). Showing
  // both side by side IS the phoneme/allophone distinction, in notation.
  // Transcriptions from Wiktionary.
  englishT: {
    phoneme: "t",
    credit: "Recordings by Dvortygirl, Wikimedia Commons, CC BY-SA 3.0",
    variants: [
      { word: "top", file: "audio/en-us-top.ogg",
        phonemic: "/tɑp/", phonetic: "[tʰɑp]", allophone: "tʰ",
        label: "aspirated",
        desc: "word-initial: released with an audible puff of air" },
      { word: "stop", file: "audio/en-us-stop.ogg",
        phonemic: "/stɑp/", phonetic: "[stɑp]", allophone: "t",
        label: "unaspirated",
        desc: "after /s/: the puff of air is suppressed" },
      { word: "butter", file: "audio/en-us-butter.ogg",
        phonemic: "/ˈbʌtəɹ/", phonetic: "[ˈbʌɾɚ]", allophone: "ɾ",
        label: "tapped",
        desc: "between vowels: a single quick tap of the tongue" }
    ]
  },

  // "Same sounds, different mouths" — both languages list the phoneme on the
  // chart; the everyday realization differs.
  realization: [
    {
      title: "The letter b",
      sound: "both have /b/",
      sides: [
        { lang: "English", symbol: "b", desc: "full stop — lips close completely", word: "“a bit”" },
        { lang: "Spanish", symbol: "β", desc: "lips never quite meet, air keeps flowing", word: "“la Habana”" }
      ],
      why: "Spanish /b/ is a hard stop at the start of an utterance but softens to a fricative between vowels, so <em>Habana</em> has no full lip closure at all. Both languages list /b/ on the chart, and Spanish speakers hear no difference between the two versions — but an English speaker pronouncing every /b/ as a hard stop is instantly identifiable. The same rule applies to Spanish /d/ and /g/."
    },
    {
      title: "The letter r",
      sound: "both have an /r/",
      sides: [
        { lang: "English", symbol: "ɹ", desc: "approximant — tongue bunched, never touching", word: "“red”" },
        { lang: "Spanish", symbol: "r", desc: "trill — tongue tip vibrating on the ridge", word: "“perro” (dog)" }
      ],
      why: "Chart matching puts these in the same slot, but they are made in completely different ways: English never lets the tongue contact the roof of the mouth, while Spanish taps it repeatedly. Spanish also contrasts the trill with a single tap — <em>perro</em> (dog) versus <em>pero</em> (but) — a distinction English uses only accidentally, in the middle of words like “butter”."
    },
    {
      title: "The letter h",
      sound: "both have /h/",
      sides: [
        { lang: "English", symbol: "h", desc: "glottal — plain breath from the throat", word: "“hood”" },
        { lang: "Japanese", symbol: "ɸ", desc: "bilabial — breath forced between the lips", word: "フード “fūdo”" }
      ],
      why: "Japanese /h/ becomes a bilabial fricative before /u/, which is why <em>hood</em> and <em>food</em> both arrive as フード — two English words that Japanese cannot keep apart. Unlike most of PHOIBLE's allophone records this rule appears in every reference grammar of Japanese, which is why it is quoted here as a fact rather than modelled."
    },
    {
      title: "The letter s",
      sound: "both have /s/",
      sides: [
        { lang: "English", symbol: "s", desc: "the same /s/ before every vowel", word: "“see”, “saw”" },
        { lang: "Japanese", symbol: "ɕ", desc: "palatalised before /i/", word: "し “shi”" }
      ],
      why: "Japanese /s/ shifts to a palatal hiss before /i/ — which is why romanisation writes <em>sashimi</em> with an s but <em>shiitake</em> with sh, even though Japanese treats them as one sound. Japanese speakers do not hear two different consonants there; English speakers hear the contrast clearly, because in English /s/ and /ʃ/ distinguish “sip” from “ship”."
    }
  ],

  // "The chart undersells you" — sounds an English speaker already produces
  // as accidental variants, which are full contrastive phonemes in Hindi.
  bridges: [
    {
      title: "Retroflex t",
      sound: "Hindi phoneme /ʈ/ · English accidental variant",
      sides: [
        { lang: "Hindi", symbol: "ʈ", desc: "a full phoneme — it changes word meaning", word: "टीका “ṭīkā”" },
        { lang: "English", symbol: "t", desc: "plain /t/, dragged back before r", word: "“tree”" }
      ],
      why: "In “tree” the following r pulls an English speaker's tongue back off the alveolar ridge toward the retroflex position. You already produce something close to Hindi's /ʈ/ — you have just never had to tell it apart from /t/, because English never uses that difference to separate two words."
    },
    {
      title: "The tap",
      sound: "Hindi phoneme /ɾ/ · English accidental variant",
      sides: [
        { lang: "Hindi", symbol: "ɾ", desc: "a phoneme in its own right", word: "in most positions" },
        { lang: "English", symbol: "t", desc: "/t/ becomes a tap between vowels", word: "“butter”, “water”" }
      ],
      why: "Most North American English speakers pronounce the middle of “butter” as a tap rather than a /t/ — physically the same gesture as Hindi's /ɾ/. The sound is already in your motor repertoire; what is new is having to use it to tell words apart."
    }
  ]
};
