/* Broad sound-area matching for the Sound Chart.
 *
 * PHOIBLE inventories inherit the transcription choices of their sources. A
 * source may write English pʰ where another writes Spanish p even though both
 * belong in the broad p area. Exact string equality therefore makes
 * transcription detail look like a language difference.
 *
 * We group source entries by the reference IPA square they light, then count an
 * occupied square once. English pʰ and Spanish p therefore share the broad p
 * area, while the tooltip retains both source labels. If one source records
 * several distinctions in an area, that remains useful qualitative detail but
 * does not create several inferred cross-language matches. Entries without a
 * chart square keep their source label as their broad key.
 */
(function (global) {
  "use strict";

  const pronunciationNotes = {
    "English|p": "English /p/ is commonly [pʰ] in pin and [p] after /s/ in spin.",
    "English|t": "English /t/ is commonly [tʰ] in top and [t] after /s/ in stop.",
    "English|k": "English /k/ is commonly [kʰ] in cat and [k] after /s/ in scat.",
    "Spanish|p": "Spanish /p/ is generally pronounced without English-style aspiration: [p].",
    "Spanish|t": "Spanish /t/ is generally pronounced without English-style aspiration: [t].",
    "Spanish|k": "Spanish /k/ is generally pronounced without English-style aspiration: [k]."
  };

  function groupsFor(language) {
    if (!language) return {};
    if (language.comparisonGroups) return language.comparisonGroups;

    const inventory = new Set(language.comparisonPhonemes || []);
    const assigned = new Set();
    const groups = {};

    for (const [cell, entries] of Object.entries(language.cellPhonemes || {})) {
      const members = [...new Set(entries)].filter(entry => inventory.has(entry));
      if (!members.length) continue;
      groups[cell] = members.sort();
      for (const member of members) assigned.add(member);
    }

    // Diphthongs, sequences and other entries without a reference square retain
    // their own source label rather than being forced into a false base category.
    for (const entry of inventory) {
      if (!assigned.has(entry)) groups[entry] = [entry];
    }
    return groups;
  }

  function pairSummary(language1, language2) {
    const groups1 = groupsFor(language1), groups2 = groupsFor(language2);
    const keys = [...new Set([...Object.keys(groups1), ...Object.keys(groups2)])]
      .sort((a, b) => a.localeCompare(b));
    const groups = keys.map(key => {
      const source1 = groups1[key] || [], source2 = groups2[key] || [];
      const present1 = source1.length > 0, present2 = source2.length > 0;
      return {
        key,
        source1,
        source2,
        shared: present1 && present2 ? 1 : 0,
        only1: present1 && !present2 ? 1 : 0,
        only2: present2 && !present1 ? 1 : 0
      };
    });
    const total = field => groups.reduce((sum, group) => sum + group[field], 0);
    const shared = total("shared"), only1 = total("only1"), only2 = total("only2");
    const union = shared + only1 + only2;
    return { groups, shared, only1, only2, union, jaccard: union ? shared / union : 0 };
  }

  function categoryForSource(language, sourceEntry) {
    for (const [category, entries] of Object.entries(groupsFor(language))) {
      if (entries.includes(sourceEntry)) return category;
    }
    return sourceEntry;
  }

  function noteFor(languageName, category) {
    return pronunciationNotes[`${languageName}|${category}`] || "";
  }

  function pairKey(a, b) {
    return a < b ? `${a}|${b}` : `${b}|${a}`;
  }

  function refreshPairOverlap(data) {
    const pairs = {};
    const languages = data.languages || [];
    for (let i = 0; i < languages.length; i++) {
      for (let j = i + 1; j < languages.length; j++) {
        const a = languages[i], b = languages[j];
        const result = pairSummary(a, b);
        pairs[pairKey(a.name, b.name)] = [result.shared, +result.jaccard.toFixed(3)];
      }
    }
    data.pairOverlap = pairs;
    data.pronunciationNotes = Object.assign({}, pronunciationNotes,
      data.pronunciationNotes || {});
    return pairs;
  }

  function clusterOrder(languages, pairOverlap) {
    let clusters = languages.map(language => [language.name]).sort((a, b) =>
      a[0].localeCompare(b[0]));
    const similarity = (a, b) => pairOverlap[pairKey(a, b)][1];
    const average = (left, right) => {
      let sum = 0, count = 0;
      for (const a of left) for (const b of right) {
        sum += similarity(a, b); count++;
      }
      return sum / count;
    };
    while (clusters.length > 1) {
      let best = -1, bestI = 0, bestJ = 1;
      for (let i = 0; i < clusters.length; i++) {
        for (let j = i + 1; j < clusters.length; j++) {
          const score = average(clusters[i], clusters[j]);
          if (score > best) { best = score; bestI = i; bestJ = j; }
        }
      }
      const merged = clusters[bestI].concat(clusters[bestJ]);
      clusters = clusters.filter((_, index) => index !== bestI && index !== bestJ);
      clusters.push(merged);
    }
    return clusters[0] || [];
  }

  const api = {
    groupsFor,
    pairSummary,
    categoryForSource,
    noteFor,
    pairKey,
    refreshPairOverlap,
    clusterOrder
  };
  global.SOUND_COMPARISON = api;
  if (global.DATA) refreshPairOverlap(global.DATA);
})(typeof window === "undefined" ? globalThis : window);
