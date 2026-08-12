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
 * `symbol` is a real IPA segment. Most sides use its isolated reference file in
 * DATA.audio; a `file` override uses a contextual word recording when that is
 * what the claim requires. The two sides never relabel the same recording.
 *
 * Invariant: every side has a real playback target and the two targets differ.
 * tests/comparison_consistency.mjs enforces both.
 */
const DEMOS = {
  // ---------------------------------------------------------------------------
  // A WITHIN-ONE-LANGUAGE example, used at the definition so a reader meets
  // "phoneme vs allophone" before meeting any cross-language comparison.
  //
  // The other sections compare phones, phoneme labels or learner substitutions
  // across languages. This strip is the direct phoneme-vs-allophone case: a
  // single English phoneme /t/ in three positions, none of which changes a
  // word's meaning.
  //
  // Each variant plays a real recording of the WHOLE WORD, not an isolated IPA
  // segment. The claim depends on context: the [t] of "stop" is unaspirated
  // because of the
  // preceding /s/, and the tap in "butter" is a positional allophone of /t/
  // rather than a segment any IPA reference files under English. Playing an
  // isolated /t/ and labelling it would be a fabricated comparison.
  //
  // WORD CHOICE — prefer dependable contextual patterns. "cat" was used here for the
  // unreleased [t̚] and was removed: word-final stop release in English is
  // OPTIONAL, so the recording did not dependably contain the allophone the card
  // claimed. (Caught by listening to the file, not by any test — the character
  // was in the markup either way.) "stop" replaces it because suppression of
  // aspiration after /s/ is the regular General American pattern. "top" vs
  // "stop" is also a near-minimal pair, which
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

  // Broad transcription labels and spelling can hide different phonetic targets.
  realization: [
    {
      title: "The letter b",
      sound: "English [b] and a common Spanish [β] pronunciation",
      sides: [
        { lang: "English", symbol: "b", desc: "full stop — lips close completely", word: "“a bit”" },
        { lang: "Spanish", symbol: "β", desc: "lips never quite meet, air keeps flowing", word: "“la Habana”" }
      ],
      why: "In many Spanish varieties, the same word category is pronounced with full lip closure [b] after a pause or nasal, and with a more open [β]-like sound between vowels. Spanish does not normally use that difference to distinguish words."
    },
    {
      title: "Two kinds of r",
      sound: "English /ɹ/ and Spanish /r/",
      sides: [
        { lang: "English", symbol: "ɹ", desc: "approximant — narrowed without a full closure", word: "“red”" },
        { lang: "Spanish", symbol: "r", desc: "trill — tongue tip vibrating on the ridge", word: "“perro” (dog)" }
      ],
      why: "These occupy different chart cells and are different phonemes in their respective language systems: the selected English inventory uses the approximant /ɹ/, while Spanish /r/ is a trill. Spanish also contrasts it with the tap /ɾ/ — <em>perro</em> (dog) versus <em>pero</em> (but). Some broad English transcriptions write its rhotic phoneme as /r/"
    },
    {
      title: "The letter h",
      sound: "both have /h/",
      sides: [
        { lang: "English", symbol: "h", desc: "glottal — plain breath from the throat", word: "“hood”" },
        { lang: "Japanese", symbol: "ɸ", desc: "bilabial — breath forced between the lips", word: "フード “fūdo”" }
      ],
      why: "Japanese /h/ is commonly pronounced [ɸ] before /ɯ/, the vowel often written <em>u</em>. English <em>food</em> and <em>hood</em> can both be said as フード <em>fūdo</em>, in Japanese as a result of loanwords adapting to available Japanese sounds."
    },
    {
      title: "The letter s",
      sound: "both have /s/",
      sides: [
        { lang: "English", symbol: "s", desc: "usually an alveolar hiss before a vowel", word: "“see”, “saw”" },
        { lang: "Japanese", symbol: "ɕ", desc: "palatalised before /i/", word: "し “shi”" }
      ],
      why: "Japanese /s/ shifts to a palatal hiss before /i/ — which is why romanisation writes <em>sashimi</em> with an s but <em>shiitake</em> with sh. Japanese normally treats [s] and [ɕ] as context-shaped versions of one category there, while English uses /s/ and /ʃ/ to distinguish words such as <em>sip</em> and <em>ship</em>."
    }
  ],

  // Qualitative bridge candidates: a familiar gesture may help, but an inventory
  // cannot establish an individual learner's perception or deliberate control.
  bridges: [
    {
      title: "Retroflex t",
      sound: "Hindi phoneme /ʈ/ · possible English near-match",
      sides: [
        { lang: "Hindi", symbol: "ʈ", desc: "a full phoneme — it changes word meaning", word: "टीका “ṭīkā”" },
        { lang: "English", symbol: "t", desc: "plain /t/, dragged back before r", word: "“tree”" }
      ],
      why: "For some English speakers, the following /ɹ/ retracts the /t/ in “tree”, providing a possible articulatory reference for Hindi /ʈ/. That does not mean every speaker produces the Hindi phone or can perceive and control the Hindi contrast; it is a comparison to test by listening."
    },
    {
      title: "The tap",
      sound: "Hindi phoneme /ɾ/ · English allophone [ɾ]",
      sides: [
        { lang: "Hindi", symbol: "ɾ", desc: "a phoneme in its own right", word: "in most positions" },
        { lang: "English", symbol: "ɾ", file: "audio/en-us-butter.ogg",
          desc: "/t/ becomes this tap between vowels", word: "“butter”" }
      ],
      why: "Many North American English speakers realize /t/ in “butter” with an alveolar tap [ɾ], which can be a useful reference for Hindi /ɾ/. Familiarity in that English context does not by itself show that a learner can use the phone deliberately as a Hindi contrast. The English button uses the contextual “butter” recording credited above."
    }
  ]
};
