/* Static checks of the browser app. No library, no network.
   Run from the folder package/:  node ui/tools/check_ui.mjs
   Exit code 0 = no finding of the kind "error". Findings of the kind "note" do not change the exit code.
   The checks:
   1 strings.json parses; each key has a text in en and in de.
   2 each key of contract/strings.contract.json is in strings.json with the same texts.
   3 each key that app.js or index.html uses is in strings.json; each key of strings.json is used.
     A key with the ending .hosted is the text of its base key on a hosted site: the base key exists and is
     used, the placeholders are the same, and the text does not name this computer.
   4 each id that app.js uses is in index.html; no id is there twice.
   5 no text of strings.json matches a pattern of the stop list of the preview site (if the file is there).
   6 the page has no inline script, no inline style and no address of another host.
   7 the fixtures are byte-equal copies of the contract examples.
   8 no German text holds the letter sharp s; no file holds a home path.
   9 rdfpanel.strings.json: each key has a text in en and in de with the same placeholders; each key that
     rdfpanel.js uses is there; no stop list match; no sharp s.
  10 rdfpanel.js: a file in which no label has an inSample statement gives the text "not known", not the number 0;
     no stored name of a source or of a count stands in the text of a table cell. */
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ui = join(dirname(fileURLToPath(import.meta.url)), '..');
const pkg = join(ui, '..');
const read = (p) => readFileSync(p, 'utf8');
const errors = [];
const notes = [];
const err = (m) => errors.push(m);
const note = (m) => notes.push(m);

const js = read(join(ui, 'app.js'));
const html = read(join(ui, 'index.html'));
const css = read(join(ui, 'app.css'));
let strings = {};
try { strings = JSON.parse(read(join(ui, 'strings.json'))); } catch (e) { err('strings.json does not parse: ' + e.message); }
const keys = Object.keys(strings);
const stopFile = join(pkg, '..', 'web', 'content', 'stop_list.json');

/* 1 */
for (const k of keys) {
  const v = strings[k];
  const names = Object.keys(v || {}).sort().join(',');
  if (names !== 'de,en') { err(`strings: key ${k} has the languages [${names}]`); continue; }
  if (typeof v.en !== 'string' || typeof v.de !== 'string' || !v.en.trim() || !v.de.trim()) { err(`strings: key ${k} has an empty text`); }
  const ph = (s) => (s.match(/\{\w+\}/g) || []).sort().join(',');
  if (ph(v.en) !== ph(v.de)) { err(`strings: key ${k} has different placeholders in en and de`); }
}

/* 2 */
const contractFile = join(pkg, 'contract', 'strings.contract.json');
let contract = {};
if (existsSync(contractFile)) {
  contract = JSON.parse(read(contractFile));
  for (const k of Object.keys(contract)) {
    if (!strings[k]) { err(`contract key ${k} is not in strings.json`); continue; }
    if (strings[k].en !== contract[k].en || strings[k].de !== contract[k].de) { err(`contract key ${k} has another text in strings.json`); }
  }
} else { note('contract/strings.contract.json is absent: check 2 did not run'); }

/* 3 */
const used = new Set();
const prefixes = new Set();
for (const m of js.matchAll(/\bt\(\s*'([^']+)'\s*([,)+])/g)) {
  if (m[2] === '+') { prefixes.add(m[1]); } else { used.add(m[1]); }
}
for (const m of js.matchAll(/\btk\(\s*'([^']+)'\s*([,+])/g)) { prefixes.add(m[1]); }
/* tn: a text with a count; the key with the ending .one is the form for the count 1 */
for (const m of js.matchAll(/\btn\(\s*'([^']+)'\s*,/g)) { used.add(m[1]); if (strings[m[1] + '.one']) { used.add(m[1] + '.one'); } }
for (const m of js.matchAll(/\bt\(([\w.]+) \? '([^']+)' : '([^']+)'\)/g)) { used.add(m[2]); used.add(m[3]); }
for (const m of js.matchAll(/'((?:dl|source)\.[a-z_.]*)'/g)) { if (strings[m[1]]) { used.add(m[1]); } else { prefixes.add(m[1]); } }
for (const m of html.matchAll(/data-i18n(?:-label)?="([^"]+)"/g)) { used.add(m[1]); }
for (const k of used) { if (!strings[k]) { err(`key ${k} is used and is not in strings.json`); } }
/* the list of words: each name of the constant WORDS of app.js needs the key words.<name> */
const wordsMatch = js.match(/const WORDS = \[([^\]]*)\]/);
const wordKeys = wordsMatch ? [...wordsMatch[1].matchAll(/'([a-z_]+)'/g)].map((m) => m[1]) : [];
for (const w of wordKeys) { if (!strings['words.' + w]) { err(`key words.${w} is used and is not in strings.json`); } }
/* keys that the page builds from a value of the data: the prefix is in app.js */
const dynamic = ['exit.', 'case.', 's4.head.', 's3.stage.'];
const isUsed = (k) => used.has(k) || [...prefixes, ...dynamic].some((p) => k.startsWith(p)) ||
  (k.startsWith('words.') && (k === 'words.title' || wordKeys.includes(k.slice(6))));
/* a key with the ending .hosted is the text of its base key on a hosted site (function t of app.js):
   the base key must exist, must be used, and the two texts must have the same placeholders */
const HOSTED = '.hosted';
const placeholders = (text) => [...String(text).matchAll(/\{([a-z_]+)\}/g)].map((m) => m[1]).sort().join(',');
let hostedKeys = 0;
for (const k of keys) {
  if (!k.endsWith(HOSTED)) { continue; }
  hostedKeys += 1;
  const base = k.slice(0, -HOSTED.length);
  if (!strings[base]) { err(`key ${k}: the base key ${base} is not in strings.json`); continue; }
  if (contract[k]) { err(`key ${k} is a contract key; a hosted text is a key of the page`); }
  for (const lang of ['en', 'de']) {
    if (placeholders(strings[k][lang]) !== placeholders(strings[base][lang])) { err(`key ${k} (${lang}) has other placeholders than ${base}`); }
    if (/this computer|diese[mnr]? computer|localhost|127\.0\.0\.1/i.test(strings[k][lang])) { err(`key ${k} (${lang}) names this computer`); }
  }
}
const panelKeys = [];
for (const k of keys) {
  if (isUsed(k) || (k.endsWith(HOSTED) && isUsed(k.slice(0, -HOSTED.length)))) { continue; }
  if (k.startsWith('rdf.') && contract[k]) { panelKeys.push(k); continue; }
  if (contract[k]) { note(`contract key ${k} is not used by app.js`); continue; }
  err(`key ${k} of strings.json is not used`);
}
if (panelKeys.length) { note(`${panelKeys.length} contract keys are for the RDF panel module, not for app.js: ${panelKeys.join(', ')}`); }

/* 4 */
const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]);
const seen = new Set();
for (const id of ids) { if (seen.has(id)) { err(`id ${id} is in index.html more than one time`); } seen.add(id); }
const usedIds = new Set([...js.matchAll(/\$\('([^']+)'\)/g)].map((m) => m[1]));
for (const id of usedIds) { if (!seen.has(id)) { err(`id ${id} is used in app.js and is not in index.html`); } }
for (const m of js.matchAll(/\$\('([a-z-]+)' \+/g)) { if (![...seen].some((i) => i.startsWith(m[1]))) { err(`no id of index.html starts with ${m[1]}`); } }
for (const m of html.matchAll(/(?:aria-labelledby|aria-describedby|aria-controls|for)="([^"]+)"/g)) {
  for (const id of m[1].split(/\s+/)) { if (!seen.has(id)) { err(`index.html refers to the id ${id}; it is not there`); } }
}
for (const m of js.matchAll(/querySelector(?:All)?\('#([a-z-]+)/g)) { if (!seen.has(m[1]) && m[1] !== 'screen-') { err(`selector #${m[1]} of app.js has no element`); } }

/* 5 */
if (existsSync(stopFile)) {
  const stop = JSON.parse(read(stopFile));
  const mine = [];
  const fromContract = [];
  const test = (k, lang, text) => {
    for (const p of stop.patterns) {
      const hit = text.match(new RegExp(p.pattern, 'i'));
      if (hit) { (contract[k] ? fromContract : mine).push(`${k} (${lang}): «${hit[0]}» [${p.id}]`); }
    }
    const suf = stop.superlative_suffix;
    if (suf && lang === 'en') {
      for (const hit of text.toLowerCase().match(new RegExp(suf.pattern, 'g')) || []) {
        if (!suf.not_superlatives.includes(hit)) { (contract[k] ? fromContract : mine).push(`${k} (${lang}): «${hit}» [superlative suffix]`); }
      }
    }
    if (/\blive\b/i.test(text)) { err(`${k} (${lang}) uses the word "live"`); }
  };
  for (const k of keys) { test(k, 'en', strings[k].en || ''); test(k, 'de', strings[k].de || ''); }
  for (const m of mine) { err('stop list: ' + m); }
  for (const m of fromContract) { note('stop list match in a text that the contract fixes: ' + m); }
} else { note('the stop list of the preview site is absent: check 5 did not run'); }

/* 6 */
if (/<script(?![^>]*\ssrc=)[^>]*>/.test(html)) { err('index.html has an inline script'); }
if (/<style[\s>]/.test(html) || /\sstyle="/.test(html)) { err('index.html has an inline style'); }
if (/\son[a-z]+="/.test(html)) { err('index.html has an inline event handler'); }
for (const [name, text] of [['index.html', html], ['app.css', css], ['app.js', js]]) {
  const hosts = (text.match(/https?:\/\/[^\s"')]+/g) || []).filter((u) => !u.startsWith('http://www.w3.org/2000/svg'));
  if (hosts.length) { err(`${name} holds an address of another host: ${hosts.join(', ')}`); }
}
if (/innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\(|new Function|setAttribute\('style'|localStorage|sessionStorage|document\.cookie|indexedDB/.test(js)) {
  err('app.js uses a function that the rules of the page exclude (HTML strings, eval, inline style or storage)');
}
for (const m of js.matchAll(/t\('status\.'|EXCEPTION|NOT RELEASED/g)) { if (m[0] !== "t('status.'") { err('app.js holds an internal status word'); } }
if (/EXCEPTION|NOT RELEASED/.test(html + JSON.stringify(strings))) { err('index.html or strings.json holds an internal status word'); }

/* 7 */
const pairs = [['health.json', 'examples/health.json'], ['samples.json', 'examples/samples.json'], ['job.json', 'examples/job.json'],
  ['error.json', 'examples/error.json'], ['view_26171.json', 'examples/view_26171.json'], ['events_sample.jsonl', 'examples/events_sample.jsonl'],
  ['events_refused.jsonl', 'examples/events_refused.jsonl'], ['errors.json', 'errors.json']];
for (const [a, b] of pairs) {
  const fa = join(ui, 'fixtures', a);
  const fb = join(pkg, 'contract', b);
  if (!existsSync(fa)) { err(`fixture ${a} is absent`); continue; }
  if (!existsSync(fb)) { note(`contract file ${b} is absent: fixture ${a} not compared`); continue; }
  if (!readFileSync(fa).equals(readFileSync(fb))) { err(`fixture ${a} differs from contract/${b}`); }
}

/* 8 */
for (const k of keys) { if ((strings[k].de || '').includes('ß')) { err(`${k} (de) holds the letter sharp s`); } }
for (const [name, text] of [['index.html', html], ['app.css', css], ['app.js', js], ['strings.json', JSON.stringify(strings)]]) {
  if (/\/Users\/|\/home\/[a-z]/.test(text)) { err(`${name} holds a home path`); }
}

/* 9 */
const panelJs = read(join(ui, 'rdfpanel.js'));
let panel = {};
try { panel = JSON.parse(read(join(ui, 'rdfpanel.strings.json'))); } catch (e) { err('rdfpanel.strings.json does not parse: ' + e.message); }
for (const k of Object.keys(panel)) {
  const v = panel[k] || {};
  if (Object.keys(v).sort().join(',') !== 'de,en' || !String(v.en).trim() || !String(v.de).trim()) { err(`panel strings: key ${k} needs a text in en and in de`); continue; }
  const ph = (x) => (x.match(/\{\w+\}/g) || []).sort().join(',');
  if (ph(v.en) !== ph(v.de)) { err(`panel strings: key ${k} has different placeholders in en and de`); }
  if (v.de.includes('ß')) { err(`panel strings: ${k} (de) holds the letter sharp s`); }
  if (contract[k] && (contract[k].en !== v.en || contract[k].de !== v.de)) { err(`contract key ${k} has another text in rdfpanel.strings.json`); }
  if (existsSync(stopFile)) {
    const stop = JSON.parse(read(stopFile));
    for (const [lang, text] of [['en', v.en], ['de', v.de]]) {
      for (const p of stop.patterns) {
        const hit = text.match(new RegExp(p.pattern, 'i'));
        if (hit) { (contract[k] ? note : err)(`panel strings, stop list: ${k} (${lang}): «${hit[0]}» [${p.id}]`); }
      }
      const suf = stop.superlative_suffix;
      if (suf && lang === 'en') {
        for (const hit of text.toLowerCase().match(new RegExp(suf.pattern, 'g')) || []) {
          if (!suf.not_superlatives.includes(hit)) { err(`panel strings, stop list: ${k} (${lang}): «${hit}» [superlative suffix]`); }
        }
      }
    }
  }
}
for (const m of panelJs.matchAll(/\bt\(\s*"([^"]+)"\s*([,)+])/g)) {
  if (m[2] === '+') { if (!Object.keys(panel).some((k) => k.startsWith(m[1]))) { err(`panel: no key starts with ${m[1]}`); } }
  else if (!panel[m[1]]) { err(`panel: key ${m[1]} is used and is not in rdfpanel.strings.json`); }
}
if (/\/Users\/|\/home\/[a-z]/.test(panelJs + JSON.stringify(panel))) { err('the panel files hold a home path'); }

/* 10 */
if (!/const inSampleKnown = "true" in bySample \|\| "false" in bySample;/.test(panelJs) ||
    !/const inSampleTrue = inSampleKnown \? [^:]+ : null;/.test(panelJs) ||
    !/value === null \? t\("rdf\.summary\.not_known"\)/.test(panelJs)) {
  err('panel: the row of the labels with an inSample statement does not show "not known" for a file with no such statement');
}
if (/el\("code", (?:null|"rdfpanel-key"), (?:key|r\.name)\)/.test(panelJs)) { err('panel: a stored name stands in the text of a table cell'); }

console.log(`texts for a hosted site: ${hostedKeys} keys with the ending .hosted`);
console.log(`strings: ${keys.length} keys; used by a full key: ${used.size}; key prefixes in app.js: ${prefixes.size}; ids in index.html: ${ids.length}; ids used by app.js: ${usedIds.size}`);
for (const n of notes) { console.log('note: ' + n); }
for (const e of errors) { console.log('error: ' + e); }
console.log(errors.length ? `FAILED: ${errors.length} errors` : 'PASSED: 0 errors');
process.exit(errors.length ? 1 : 0);
