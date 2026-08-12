#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DOCS = path.join(ROOT, "docs");
const htmlFiles = fs.readdirSync(DOCS).filter(file => file.endsWith(".html"));
const jsFiles = fs.readdirSync(DOCS).filter(file => file.endsWith(".js"));

for (const file of jsFiles) {
  const source = fs.readFileSync(path.join(DOCS, file), "utf8");
  new vm.Script(source, { filename: file });
}

let inlineBlocks = 0;
let localReferences = 0;
for (const file of htmlFiles) {
  const source = fs.readFileSync(path.join(DOCS, file), "utf8");
  assert.match(source, /<html\s+lang="en">/i, `${file} declares its language`);
  assert.equal((source.match(/<h1\b/gi) || []).length, 1,
    `${file} has exactly one main heading`);
  assert.doesNotMatch(source, /\uFFFD|[窶筺繧繝縺]/,
    `${file} contains no replacement characters or common UTF-8 mojibake`);

  const inline = /<script(?![^>]*\bsrc\s*=)[^>]*>([\s\S]*?)<\/script>/gi;
  for (const match of source.matchAll(inline)) {
    if (!match[1].trim()) continue;
    new vm.Script(match[1], { filename: `${file}:inline` });
    inlineBlocks++;
  }

  const reference = /(?:href|src)="([^"#?]+)[^"#]*"/gi;
  for (const match of source.matchAll(reference)) {
    const target = match[1];
    if (/^(?:https?:|mailto:|data:|javascript:|\/\/)/i.test(target)) continue;
    assert.ok(fs.existsSync(path.resolve(DOCS, target)),
      `${file} local reference exists: ${target}`);
    localReferences++;
  }
}

const nav = fs.readFileSync(path.join(DOCS, "nav.js"), "utf8");
assert.match(nav, /skipLink\.href/,
  "shared navigation creates a skip link");
assert.match(nav, /insertBefore\(skipLink, nav\)/,
  "the skip link is placed before navigation in keyboard order");

const index = fs.readFileSync(path.join(DOCS, "index.html"), "utf8");
assert.match(index, /id="heatmapTable"/,
  "the sound heatmap has a table alternative");
const difficulty = fs.readFileSync(path.join(DOCS, "difficulty.html"), "utf8");
assert.match(difficulty, /id="scatterTable"/,
  "the learner scatterplot has a table alternative");
const spectrograms = fs.readFileSync(path.join(DOCS, "spectrograms.html"), "utf8");
const spectrogramCode = fs.readFileSync(path.join(DOCS, "spectrograms.js"), "utf8");
assert.match(spectrograms, /id="vowelButtons"/,
  "the vowel chart exposes standard button controls");
assert.match(spectrogramCode, /Play the reference vowel/,
  "reference-vowel buttons have spoken labels");

console.log(`site integrity: ${htmlFiles.length} pages, ${jsFiles.length} scripts, ` +
  `${inlineBlocks} inline blocks and ${localReferences} local references`);
