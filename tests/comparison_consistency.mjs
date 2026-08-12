#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function readConst(relative, name) {
  const source = fs.readFileSync(path.join(ROOT, relative), "utf8");
  const prefix = `const ${name} = `;
  assert.ok(source.startsWith(prefix), `${relative} starts with ${prefix}`);
  return JSON.parse(source.slice(prefix.length).trimEnd().slice(0, -1));
}

const data = readConst("docs/data.js", "DATA");
const generatedPairs = structuredClone(data.pairOverlap);
const context = { DATA: data };
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(ROOT, "docs/comparison.js"), "utf8"), context);
const comparison = context.SOUND_COMPARISON;

assert.equal(data.languages.length, 34);
assert.equal(Object.keys(generatedPairs).length, 561);
assert.ok(data.languages.every(language => language.comparisonGroups),
  "every deployed language carries generated comparison groups");

for (let i = 0; i < data.languages.length; i++) {
  for (let j = i + 1; j < data.languages.length; j++) {
    const left = data.languages[i], right = data.languages[j];
    const result = comparison.pairSummary(left, right);
    const key = comparison.pairKey(left.name, right.name);
    assert.deepEqual([result.shared, +result.jaccard.toFixed(3)], generatedPairs[key],
      `${key} generated and browser calculations agree`);
    assert.ok(result.groups.every(group => [0, 1].includes(group.shared) &&
      [0, 1].includes(group.only1) && [0, 1].includes(group.only2)),
      `${key} counts each broad area at most once`);
    assert.equal(result.union,
      new Set([
        ...Object.keys(left.comparisonGroups),
        ...Object.keys(right.comparisonGroups)
      ]).size,
      `${key} union is the number of occupied broad areas`);
  }
}

const byName = Object.fromEntries(data.languages.map(language => [language.name, language]));
const englishSpanish = comparison.pairSummary(byName.English, byName.Spanish);
const pArea = englishSpanish.groups.find(group => group.key === "p");
assert.deepEqual(pArea.source1, ["pʰ"]);
assert.deepEqual(pArea.source2, ["p"]);
assert.equal(pArea.shared, 1, "English pʰ and Spanish p share one broad p area");
assert.equal(pArea.only1 + pArea.only2, 0, "transcription detail does not create an exclusive p");

const hindiSpanish = comparison.pairSummary(byName.Hindi, byName.Spanish);
const hindiP = hindiSpanish.groups.find(group => group.key === "p");
assert.equal(hindiP.source1.length, 2, "Hindi source detail remains available");
assert.equal(hindiP.shared, 1, "two Hindi p labels still create one shared broad area");
assert.equal(hindiP.only1, 0, "the second Hindi label is qualitative, not an inferred extra match");

const stories = JSON.stringify(data.stories);
assert.doesNotMatch(stories,
  /Spanish speakers say this sound every day|Spanish b and v are the same sound|French h is silent|most famous sound merger/,
  "chart stories avoid categorical claims about whole languages or their speakers");
assert.match(data.stories["Mandarin Chinese|v"], /selected source/,
  "source-dependent pronunciation-variant claims are labelled as such");

const difficulty = fs.readFileSync(path.join(ROOT, "docs/difficulty.html"), "utf8");
assert.ok(difficulty.indexOf('src="data.js') < difficulty.indexOf('src="comparison.js'),
  "learner page loads inventory data before the shared comparison code");
assert.match(difficulty, /SOUND_COMPARISON\.pairSummary/,
  "learner directions use the same comparison function as the chart");
assert.doesNotMatch(difficulty, /under the same counting rules/,
  "learner copy no longer describes stale generated rules");

const about = fs.readFileSync(path.join(ROOT, "docs/about.html"), "utf8");
assert.doesNotMatch(about, /Six test suites|Cantonese requires one new sound|~850 of the 915/);
const history = fs.readFileSync(path.join(ROOT, "docs/history_data.js"), "utf8");
assert.doesNotMatch(history, /educate|all owe their standing|spellings frozen/);

const demoContext = {};
vm.createContext(demoContext);
vm.runInContext(fs.readFileSync(path.join(ROOT, "docs/demos.js"), "utf8") +
  ";globalThis.TEST_DEMOS = DEMOS;", demoContext);
for (const variant of demoContext.TEST_DEMOS.englishT.variants) {
  assert.ok(fs.existsSync(path.join(ROOT, "docs", variant.file)),
    `English /t/ word recording exists: ${variant.file}`);
}
for (const demo of [...demoContext.TEST_DEMOS.realization, ...demoContext.TEST_DEMOS.bridges]) {
  assert.equal(demo.sides.length, 2, `${demo.title} has two listening sides`);
  const targets = demo.sides.map(side => side.file || data.audio[side.symbol]?.file);
  assert.notEqual(targets[0], targets[1],
    `${demo.title} compares two different playback targets`);
  for (const side of demo.sides) {
    if (side.file) {
      assert.ok(fs.existsSync(path.join(ROOT, "docs", side.file)),
        `${demo.title} contextual recording exists: ${side.file}`);
    } else {
      assert.ok(data.audio[side.symbol], `${demo.title} has audio for ${side.symbol}`);
    }
  }
}

console.log("comparison consistency: 34 languages, 561 pairs, one occupied-area policy");
