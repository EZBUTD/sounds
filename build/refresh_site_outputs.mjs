#!/usr/bin/env node
/* Refresh generated fields that depend only on the already-shipped bundles.
 *
 * The full Python build still begins with the raw PHOIBLE data. This small Node
 * step is intentionally narrower: it keeps the deployed comparison fields and
 * corrected hand-authored history copy in sync when the raw datasets are not
 * present locally.
 */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DOCS = path.join(ROOT, "docs");
const UNIT = "one occupied broad IPA sound area per language after length collapse; standalone tone rows excluded; source detail retained qualitatively";

function readConst(file, name) {
  const source = fs.readFileSync(file, "utf8");
  const prefix = `const ${name} = `;
  const start = source.indexOf(prefix);
  if (start < 0 || !source.trimEnd().endsWith(";")) {
    throw new Error(`Unexpected ${name} wrapper in ${file}`);
  }
  return JSON.parse(source.slice(start + prefix.length).trimEnd().slice(0, -1));
}

function writeConst(file, name, value, header = "") {
  fs.writeFileSync(file, `${header}const ${name} = ${JSON.stringify(value)};\n`, "utf8");
}

function stampAssetReferences() {
  const pattern = /(src|href)="([A-Za-z0-9_-]+\.(?:js|css))(?:\?v=[0-9a-f]+)?"/g;
  const hashes = new Map();
  for (const page of fs.readdirSync(DOCS).filter(file => file.endsWith(".html"))) {
    const file = path.join(DOCS, page);
    const source = fs.readFileSync(file, "utf8");
    const stamped = source.replace(pattern, (whole, attribute, asset) => {
      const target = path.join(DOCS, asset);
      if (!fs.existsSync(target)) return whole;
      if (!hashes.has(asset)) {
        const digest = crypto.createHash("sha256").update(fs.readFileSync(target))
          .digest("hex").slice(0, 8);
        hashes.set(asset, digest);
      }
      return `${attribute}="${asset}?v=${hashes.get(asset)}"`;
    });
    if (stamped !== source) fs.writeFileSync(file, stamped, "utf8");
  }
}

function groupsFor(language) {
  const inventory = new Set(language.comparisonPhonemes || []);
  const assigned = new Set();
  const groups = {};
  for (const [cell, entries] of Object.entries(language.cellPhonemes || {})) {
    const members = [...new Set(entries)].filter(entry => inventory.has(entry)).sort();
    if (!members.length) continue;
    groups[cell] = members;
    members.forEach(member => assigned.add(member));
  }
  for (const entry of inventory) {
    if (!assigned.has(entry)) groups[entry] = [entry];
  }
  return Object.fromEntries(Object.entries(groups).sort(([a], [b]) => a.localeCompare(b)));
}

function pairKey(a, b) {
  return a < b ? `${a}|${b}` : `${b}|${a}`;
}

function pairMetrics(left, right) {
  const a = new Set(Object.keys(left)), b = new Set(Object.keys(right));
  const shared = [...a].filter(key => b.has(key)).length;
  const union = new Set([...a, ...b]).size;
  return [shared, union ? +(shared / union).toFixed(3) : 0];
}

function buildPairs(languages) {
  const pairs = {};
  const sorted = languages.slice().sort((a, b) => a.name.localeCompare(b.name));
  for (let i = 0; i < sorted.length; i++) {
    for (let j = i + 1; j < sorted.length; j++) {
      pairs[pairKey(sorted[i].name, sorted[j].name)] =
        pairMetrics(sorted[i].comparisonGroups, sorted[j].comparisonGroups);
    }
  }
  return pairs;
}

function buildAsymmetry(sets, frequency) {
  const names = Object.keys(sets).sort();
  const rows = {};
  for (const learner of names) {
    for (const target of names) {
      if (learner === target) continue;
      const unfamiliar = [...sets[target]].filter(area => !sets[learner].has(area)).sort();
      rows[`${learner}|${target}`] = {
        newSounds: unfamiliar.length,
        load: +unfamiliar.reduce((sum, area) => sum + 1 - (frequency[area] || 0), 0).toFixed(3),
        sounds: unfamiliar.slice(0, 14)
      };
    }
  }
  const outward = names.filter(n => n !== "English").map(n => rows[`English|${n}`].newSounds);
  const inward = names.filter(n => n !== "English").map(n => rows[`${n}|English`].newSounds);
  const lopsided = [];
  for (let i = 0; i < names.length; i++) {
    for (let j = i + 1; j < names.length; j++) {
      const a = names[i], b = names[j];
      const ab = rows[`${a}|${b}`], ba = rows[`${b}|${a}`];
      const forwardIsEasier = ab.newSounds <= ba.newSounds;
      lopsided.push({
        a, b, gap: Math.abs(ab.newSounds - ba.newSounds),
        easyDir: forwardIsEasier ? `${a}→${b}` : `${b}→${a}`,
        easyN: forwardIsEasier ? ab.newSounds : ba.newSounds,
        hardDir: forwardIsEasier ? `${b}→${a}` : `${a}→${b}`,
        hardN: forwardIsEasier ? ba.newSounds : ab.newSounds
      });
    }
  }
  lopsided.sort((x, y) => y.gap - x.gap || x.a.localeCompare(y.a) || x.b.localeCompare(y.b));
  return {
    pairs: rows,
    englishOutMean: +(outward.reduce((a, b) => a + b, 0) / outward.length).toFixed(2),
    englishInMean: +(inward.reduce((a, b) => a + b, 0) / inward.length).toFixed(2),
    englishHarderForN: names.filter(n => n !== "English")
      .filter(n => rows[`${n}|English`].newSounds > rows[`English|${n}`].newSounds).length,
    rosterSize: names.length,
    mostLopsided: lopsided.slice(0, 12)
  };
}

function buildWeightedPairs(sets, frequency) {
  const pairs = {};
  const names = Object.keys(sets).sort();
  for (let i = 0; i < names.length; i++) {
    for (let j = i + 1; j < names.length; j++) {
      const a = sets[names[i]], b = sets[names[j]];
      const shared = [...a].filter(area => b.has(area));
      const union = [...new Set([...a, ...b])];
      const sharedWeight = shared.reduce((sum, area) => sum + 1 - (frequency[area] || 0), 0);
      const unionWeight = union.reduce((sum, area) => sum + 1 - (frequency[area] || 0), 0);
      pairs[`${names[i]}|${names[j]}`] = {
        plain: +(shared.length / union.length).toFixed(4),
        weighted: +(unionWeight ? sharedWeight / unionWeight : 0).toFixed(4)
      };
    }
  }
  return pairs;
}

const dataFile = path.join(DOCS, "data.js");
const rarityFile = path.join(DOCS, "rarity.js");
const mapFile = path.join(DOCS, "mapdata.js");
const historyFile = path.join(DOCS, "history_data.js");

const data = readConst(dataFile, "DATA");
for (const language of data.languages) language.comparisonGroups = groupsFor(language);
data.pairOverlap = buildPairs(data.languages);
data.comparisonUnit = UNIT;
Object.assign(data.stories, {
  "Japanese|f": "Japanese /h/ is often pronounced [ɸ] before /ɯ/. English loanwords are reshaped by several Japanese sound patterns, which can make 'food' and 'hood' converge as fūdo.",
  "Japanese|l": "English /l/ and /r/ are often adapted toward the Japanese tap /ɾ/ in loanwords. That is a language pattern, not a claim that individual listeners cannot hear a difference.",
  "Japanese|ɹ": "English /l/ and /r/ are often adapted toward the Japanese tap /ɾ/ in loanwords. That is a language pattern, not a claim that individual listeners cannot hear a difference.",
  "Japanese|θ": "English /θ/ is often adapted toward /s/ in Japanese loanwords. Individual learners' pronunciations vary.",
  "Japanese|ð": "English /ð/ is often adapted toward /z/ or /d/ in Japanese loanwords. Individual learners' pronunciations vary.",
  "Spanish|ð": "In many varieties, d can have a [ð]-like pronunciation between vowels, as in nada. Sources differ in how they label the underlying category and its variants.",
  "Spanish|v": "Many Spanish varieties do not use an English-style /b/ versus /v/ contrast, even though both letters occur in spelling.",
  "Korean|f": "English /f/ is often adapted with a Korean p sound in loanwords, as in keopi for 'coffee'. Individual learners can learn a different pronunciation.",
  "French|θ": "Some French-accented English uses /s/ or /f/ where English has /θ/. Individual speakers vary.",
  "French|h": "French usually does not pronounce written h in native words, so English /h/ can be an unfamiliar contrast for some learners.",
  "German|w": "The German letter w usually represents /v/. That spelling difference can shape some learners' first attempts at English w.",
  "Russian|θ": "Some Russian-accented English uses /s/ or /t/ where English has /θ/. Individual speakers vary.",
  "Hindi|θ": "Hindi dental /t̪ʰ/ is made near English /θ/, but it stops the airflow instead of letting it continue.",
  "Mandarin Chinese|v": "The selected source records [v] as a pronunciation variant rather than a separate category. Mandarin varieties and speakers differ."
});

const rarity = readConst(rarityFile, "RARITY");
const previousFrequency = rarity.comparisonFreq || {};
const sets = Object.fromEntries(data.languages.map(language =>
  [language.name, new Set(Object.keys(language.comparisonGroups))]));
const selectedAreas = [...new Set(Object.values(sets).flatMap(set => [...set]))].sort();
const frequency = Object.fromEntries(selectedAreas.map(area => [
  area,
  rarity.globalFreq?.[area] ?? previousFrequency[area] ?? 0
]));
const weightedPairs = buildWeightedPairs(sets, frequency);
const asymmetry = buildAsymmetry(sets, frequency);

rarity.comparisonUnit = UNIT;
rarity.comparisonFreq = frequency;
rarity.weightedPairs = weightedPairs;
if (rarity.tone) {
  delete rarity.tone.excludedFromAllMetrics;
  rarity.tone.excludedFromOverlapAndRarity = true;
}

const mapdata = readConst(mapFile, "MAPDATA");
mapdata.comparisonUnit = UNIT;
mapdata.comparisonFreq = frequency;
mapdata.weightedPairs = weightedPairs;
mapdata.asymmetry = asymmetry;
if (mapdata.tone) {
  delete mapdata.tone.excludedFromAllMetrics;
  mapdata.tone.excludedFromOverlapAndRarity = true;
}

const history = readConst(historyFile, "HIST");
const zh = history.flows.find(flow => flow.sym === "ʒ");
if (zh) zh.how = "English gained this sound through more than one route. French vocabulary supplied words in which it later appeared, while {{z}} and {{j}} also ran together inside English, as in some pronunciations of <em>as you</em>. It never got a letter of its own.";
const norman = history.events.find(event => event.title === "The Norman Conquest");
if (norman) norman.body = "French becomes the language of court, and a large layer of vocabulary follows. French loans help {{v}}, {{z}} and {{dʒ}} appear in more positions and become firmly established as separate English sounds; changes inside English also contributed.";
const vowelShift = history.events.find(event => event.title === "The Great Vowel Shift");
if (vowelShift) vowelShift.body = "English's long vowels move in a chain. <em>Name</em> once had a more open, ah-like vowel, while <em>mine</em> had an ee-like one. The highest vowels broke into gliding vowels, helping produce today's <em>mine</em> and <em>house</em>.";
const printing = history.events.find(event => event.title.startsWith("Printing"));
if (printing) {
  printing.title = "Printing helps spelling settle";
  printing.body = "Caxton sets up England's first press at Westminster. Spelling settles toward its modern form over the next two centuries — while the vowels were still moving and ⟨gh⟩ was still being lost. Printing helped spread and stabilize conventions, but the process was gradual rather than one moment when spelling froze.";
}

writeConst(dataFile, "DATA", data);
writeConst(rarityFile, "RARITY", rarity);
writeConst(mapFile, "MAPDATA", mapdata);
writeConst(historyFile, "HIST", history,
  "// GENERATED by build_history_data.py — do not edit by hand.\n// Every branch end is verified against docs/data.js at build time.\n");
stampAssetReferences();

console.log(`Refreshed ${data.languages.length} languages, ${Object.keys(data.pairOverlap).length} pairs and ${Object.keys(asymmetry.pairs).length} learner directions.`);
