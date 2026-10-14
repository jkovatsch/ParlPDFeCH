/* ParlPDFeCH package, browser app. One script, no library, no build step.
   It loads nothing from another host, sets no cookie and stores nothing in the browser.
   All texts come from strings.json. The screens are hash routes (contract chapter 7.2).
   With the query fixture=1 the app reads stored example answers from fixtures/ and calls no API. */

const RECORD_RE = /^(s-[0-9]+|u-[0-9a-f]{16})(-rules)?$/;
const STAGES = ['read_pdf', 'lines', 'rules', 'apertus', 'write', 'check'];
const STATUS_FILTERS = ['all', 'certain', 'unsure', 'none'];
const SVGNS = 'http://www.w3.org/2000/svg';
const POLL_MS = 2000;
const FIXTURE_STEP_MS = 450;
const LONG_VALUE = 280;
const WORDING_START = 160;
/* The list «Words used on these pages»: the keys words.<name> of the strings file, in this sequence. */
const WORDS = ['value', 'states', 'apertus', 'block', 'label', 'probability', 'certain', 'rule', 'readout', 'dev', 'reference',
  'export', 'textblock', 'rdf', 'trig', 'turtle', 'shacl'];
/* The record of eCH-0295 on the result page: the entries of each group that have a row of their own, in this
   sequence. Each other entry of the group is in the list «other entries». */
const ECH_GROUPS = [
  { cls: 'Affair', step: null, rows: ['Affair.affair_type', 'Affair.title', 'Affair.affair_number'] },
  { cls: 'Submission', step: 'Affair.submission', rows: ['Submission.submission_date', 'Submission.sponsorship', 'Submission.texts'] },
  { cls: 'ResponseStep', step: 'Affair.response_steps', rows: ['ResponseStep.date_end_actual', 'ResponseStep.responder', 'ResponseStep.texts'] }
];

const S = {
  strings: null,
  lang: 'en',
  fixture: false,
  screen: null,
  health: null,
  healthWait: null,
  samples: [],
  sending: false,
  dropFile: null,
  pendingInput: null,
  job: null,
  view: null,
  viewId: null,
  ix: null,
  sel: null,
  filter: { status: 'all', group: 'all' },
  caseErr: null,
  retry: null,
  panelLoad: null,
  panelRun: 0,
  numbers: null,
  numbersWait: null,
  vsel: null,
  ttl: null
};
let api = null;

/* ---------- small tools ---------- */
function $(id) { return document.getElementById(id); }
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) { e.className = cls; }
  if (text !== undefined && text !== null) { e.textContent = text; }
  return e;
}
function svg(tag, attrs) {
  const e = document.createElementNS(SVGNS, tag);
  for (const k in attrs) { e.setAttribute(k, String(attrs[k])); }
  return e;
}
function clear(node) { node.replaceChildren(); return node; }
/* One form for each count: the thousands mark of the language (en 2,458; de 2’458).
   A probability is no count: it stays the stored decimal (function num). */
let countForm = null;
function count(n) {
  if (typeof n !== 'number' || !Number.isInteger(n)) { return String(n); }
  try {
    if (!countForm || countForm.lang !== S.lang) {
      countForm = { lang: S.lang, form: new Intl.NumberFormat(S.lang === 'de' ? 'de-CH' : 'en') };
    }
    return countForm.form.format(n);
  } catch (e) {
    return String(n);
  }
}
function fill(text, params) {
  return String(text).replace(/\{(\w+)\}/g, function (m, k) {
    const v = params ? params[k] : undefined;
    if (v === undefined || v === null) { return ''; }
    return typeof v === 'number' ? count(v) : String(v);
  });
}
function has(key) { return !!(S.strings && S.strings[key]); }
/* t: a text of the strings file by its full key. */
function t(key, params) {
  /* A hosted site (key hosted of /api/health): the key with the ending .hosted replaces the text, if the
     strings file has it. These are the texts that say "on this computer" in a local run. */
  const e = S.strings && ((hosted() && S.strings[key + '.hosted']) || S.strings[key]);
  if (!e) { return ''; }
  return fill(e[S.lang] || e.en || '', params);
}
/* tn: a text with a count. For the count 1 the key with the ending .one is used, if the strings file has it. */
function tn(key, n, params) {
  return t(n === 1 && has(key + '.one') ? key + '.one' : key, params);
}
/* tk: a text whose key ends with a value of the data. With no such key the fallback shows (default: the value as it is). */
function tk(prefix, suffix, params, fallback) {
  const key = prefix + suffix;
  if (has(key)) { return t(key, params); }
  return fallback !== undefined ? fallback : String(suffix);
}
function pick(obj) { return obj ? (obj[S.lang] || obj.en || '') : ''; }
/* The stored decimal as the JSON file gives it. No rounding, no percent sign. */
function num(p) {
  const s = String(p);
  if (s.indexOf('e') === -1) { return s; }
  return Number(p).toFixed(12).replace(/0+$/, '').replace(/\.$/, '');
}
/* A number with one decimal in the number form of the page language (en, de-CH). */
let decimalForm = null;
function round1(x) {
  try {
    if (!decimalForm || decimalForm.lang !== S.lang) {
      decimalForm = { lang: S.lang, form: new Intl.NumberFormat(S.lang === 'de' ? 'de-CH' : 'en', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) };
    }
    return decimalForm.form.format(x);
  } catch (e) {
    return (Math.round(x * 10) / 10).toFixed(1);
  }
}
/* The size of a file in words: MB from 0.1 MB, KB from 1 KB, bytes below. */
function fileSize(bytes) {
  if (bytes >= 104858) { return t('fmt.size.mb', { n: round1(bytes / 1048576) }); }
  if (bytes >= 1024) { return t('fmt.size.kb', { n: round1(bytes / 1024) }); }
  return t('fmt.size.bytes', { n: bytes });
}
function say(text) { const n = $('live'); n.textContent = ''; n.textContent = text; }
function intoView(node, block, instant) {
  const reduce = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const still = instant || reduce || document.hidden;
  if (node && node.scrollIntoView) { node.scrollIntoView({ behavior: still ? 'auto' : 'smooth', block: block || 'nearest' }); }
}
function go(hash) {
  if (location.hash === hash) { route(); } else { location.hash = hash; }
}
function dlRow(list, name, value, cls) {
  if (value === null || value === undefined || value === '') { return; }
  const row = el('div', 'row');
  row.appendChild(el('dt', '', name));
  row.appendChild(el('dd', cls || '', typeof value === 'number' ? count(value) : String(value)));
  list.appendChild(row);
}

/* ---------- errors ---------- */
class AppError extends Error {
  constructor(error) { super(error && error.code ? error.code : 'error'); this.error = error; }
}
/* A case that the page makes itself: its texts are in the strings file (case.<name>.*). */
function localCase(name, exits) {
  return { code: 'page_' + name, local: name, exits: exits || ['retry', 'start'], detail: {} };
}

/* ---------- the API of the server ---------- */
async function call(method, path, body) {
  let res;
  try {
    res = await fetch(path, { method: method, body: body, headers: { Accept: 'application/json' }, cache: 'no-store' });
  } catch (e) {
    throw new AppError(localCase('network'));
  }
  if (res.status === 204) { return null; }
  let data = null;
  try { data = await res.json(); } catch (e) { data = null; }
  if (!res.ok) {
    if (data && data.error && data.error.code) { throw new AppError(data.error); }
    throw new AppError(localCase(res.status >= 500 ? 'network' : 'bad_answer'));
  }
  if (data === null || typeof data !== 'object') { throw new AppError(localCase('bad_answer')); }
  return data;
}
const realApi = {
  health: function () { return call('GET', '/api/health'); },
  samples: function () { return call('GET', '/api/samples'); },
  startJob: function (form) { return call('POST', '/api/jobs', form); },
  job: function (id) { return call('GET', '/api/jobs/' + encodeURIComponent(id)); },
  stop: function (id) { return call('DELETE', '/api/jobs/' + encodeURIComponent(id)); },
  record: function (id) { return call('GET', '/api/records/' + encodeURIComponent(id)); },
  remove: function (id) { return call('DELETE', '/api/records/' + encodeURIComponent(id)); },
  events: function (id, hd) {
    let ended = false;
    const es = new EventSource('/api/jobs/' + encodeURIComponent(id) + '/events');
    function parsed(ev) { try { return JSON.parse(ev.data); } catch (e) { return null; } }
    es.addEventListener('stage', function (ev) { const d = parsed(ev); if (d) { hd.stage(d); } });
    ['done', 'failed', 'stopped'].forEach(function (name) {
      es.addEventListener(name, function (ev) {
        const d = parsed(ev);
        ended = true;
        es.close();
        if (d) { hd.end(d); } else { hd.broken(); }
      });
    });
    es.onerror = function () {
      if (ended) { return; }
      ended = true;
      es.close();
      hd.broken();
    };
    return { close: function () { ended = true; es.close(); } };
  }
};

/* ---------- fixture mode: stored example answers, no server ---------- */
async function fx(name, asText) {
  let res;
  try { res = await fetch('fixtures/' + name, { cache: 'no-store' }); } catch (e) { throw new AppError(localCase('network')); }
  if (!res.ok) { throw new AppError(localCase('network')); }
  return asText ? res.text() : res.json();
}
function emptyStages() {
  return STAGES.map(function (id) { return { id: id, state: 'pending', origin: null, seconds: null, counts: {}, reason: null }; });
}
async function fxError(code, detail) {
  const all = await fx('errors.json');
  const e = (all.errors || {})[code];
  if (!e) { return localCase('bad_answer'); }
  const health = await fx('health.json');
  const params = Object.assign({ max_mb: Math.round(health.limits.max_bytes / 1048576) }, detail || {});
  return {
    code: code,
    title: e.title,
    text: { en: fill(e.text.en, params), de: fill(e.text.de, params) },
    action: e.action,
    exits: e.exits,
    detail: detail || {}
  };
}
const fixtureApi = {
  health: function () { return fx('health.json'); },
  samples: function () { return fx('samples.json'); },
  startJob: async function (form) {
    const id = form.get('sample') ? 'fixture-sample' : 'fixture-upload';
    return { job_id: id, state: 'queued', events: '', status: '' };
  },
  job: async function (id) {
    return { schema: 'parlpdfech-job/1', job_id: id, state: 'queued', input: null, mode: 'auto', stages: emptyStages(),
      elapsed_seconds: 0, record_id: null, valid: null, apertus: null, error: null };
  },
  stop: async function (id) {
    return { schema: 'parlpdfech-job/1', job_id: id, state: 'stopped', stages: S.job ? stageList(S.job) : emptyStages(),
      elapsed_seconds: 0, record_id: null, valid: null, apertus: null, error: null };
  },
  record: function () { return fx('view_26171.json'); },
  remove: async function () { return null; },
  /* The events script of the contract, replayed with a timer. */
  events: function (id, hd) {
    let closed = false;
    const timers = [];
    (async function () {
      const text = await fx(id === 'fixture-upload' ? 'events_refused.jsonl' : 'events_sample.jsonl', true);
      const lines = text.split('\n').filter(function (l) { return l.trim(); }).map(function (l) { return JSON.parse(l); });
      const base = await fx('job.json');
      lines.forEach(function (ev, i) {
        timers.push(setTimeout(async function () {
          if (closed) { return; }
          if (ev.event === 'stage') { hd.stage(ev); return; }
          const job = Object.assign({}, base, { job_id: id, stages: S.job ? stageList(S.job) : emptyStages() });
          if (ev.event === 'done') {
            hd.end(Object.assign(job, { state: 'done', record_id: ev.record_id, valid: ev.valid, apertus: ev.apertus, error: null }));
          } else {
            const err = await fxError(ev.code, ev.detail);
            if (!closed) { hd.end(Object.assign(job, { state: 'failed', record_id: null, valid: null, apertus: null, error: err })); }
          }
        }, FIXTURE_STEP_MS * (i + 1)));
      });
    })().catch(function () { if (!closed) { hd.broken(); } });
    return { close: function () { closed = true; timers.forEach(clearTimeout); } };
  }
};

/* ---------- texts, language, screens ---------- */
function langUrl(lang) {
  return '?lang=' + lang + (S.fixture ? '&fixture=1' : '') + location.hash;
}
function applyStatic() {
  document.documentElement.lang = S.lang;
  document.querySelectorAll('[data-i18n]').forEach(function (n) { n.textContent = t(n.getAttribute('data-i18n')); });
  document.querySelectorAll('[data-i18n-label]').forEach(function (n) { n.setAttribute('aria-label', t(n.getAttribute('data-i18n-label'))); });
  document.querySelectorAll('[data-words]').forEach(function (list) {
    clear(list);
    WORDS.forEach(function (w) { list.appendChild(el('li', '', t('words.' + w))); });
  });
  syncLangLinks();
  /* The texts that a value of /api/health selects replace the static texts. */
  renderHealth();
}
function syncLangLinks() {
  ['en', 'de'].forEach(function (l) {
    const a = $('lang-' + l);
    a.setAttribute('href', langUrl(l));
    if (l === S.lang) { a.setAttribute('aria-current', 'true'); } else { a.removeAttribute('aria-current'); }
  });
}
function setLang(lang) {
  if (lang !== 'en' && lang !== 'de') { return; }
  S.lang = lang;
  try { history.replaceState(null, '', langUrl(lang)); } catch (e) { /* a sandbox can refuse it */ }
  applyStatic();
  if (S.screen === 'case') { renderCase(); setTitle('case'); } else { route({ rerender: true, keepFocus: true }); }
}
function setTitle(name) {
  const h = document.querySelector('#screen-' + name + ' h1');
  const words = h ? h.textContent : '';
  document.title = name === 'start' || !words ? t('app.title') : words + ' · ParlPDFeCH';
}
function show(name, keepFocus) {
  /* The RDF panel belongs to the screen of a result: it goes away with the screen. */
  if (S.screen === 'record' && name !== 'record') { unmountPanel(); }
  document.querySelectorAll('.screen').forEach(function (s) { s.hidden = s.id !== 'screen-' + name; });
  S.screen = name;
  document.querySelectorAll('[data-nav]').forEach(function (a) {
    if (a.getAttribute('data-nav') === name) { a.setAttribute('aria-current', 'page'); } else { a.removeAttribute('aria-current'); }
  });
  setTitle(name);
  if (!keepFocus) {
    window.scrollTo(0, 0);
    const h = document.querySelector('#screen-' + name + ' h1');
    if (h) { h.focus({ preventScroll: true }); }
  }
}
/* An outline on a heading that the script gave the focus shows only after a key press (class kbd on the root). */
function bindKeyboardMark() {
  const root = document.documentElement;
  window.addEventListener('keydown', function (ev) {
    if (ev.key === 'Tab' || ev.key.indexOf('Arrow') === 0) { root.classList.add('kbd'); }
  }, true);
  window.addEventListener('pointerdown', function () { root.classList.remove('kbd'); }, true);
}

/* ---------- cases: each error with its exits ---------- */
function showCase(err, retry) {
  let e = null;
  if (err instanceof AppError) { e = err.error; } else if (err && err.code && (err.local || err.title)) { e = err; }
  if (!e) {
    if (err && window.console) { console.error(err); }
    e = localCase('bad_answer');
  }
  S.caseErr = e;
  S.retry = retry || null;
  renderCase();
  show('case');
  $('alert').textContent = $('h-case').textContent + '. ' + $('case-text').textContent;
}
function renderCase() {
  const e = S.caseErr;
  if (!e) { return; }
  const local = e.local;
  /* The texts of two server codes name this computer or localhost. On a hosted site the page has its own. */
  const own = function (part, text) { return hosted() && !local ? tk('err.hosted.', e.code + '.' + part, null, text) : text; };
  $('h-case').textContent = local ? t('case.' + local + '.title') : pick(e.title);
  $('case-text').textContent = local ? t('case.' + local + '.text') : own('text', pick(e.text));
  $('case-action').textContent = local ? t('case.' + local + '.action') : own('action', pick(e.action));
  $('case-code').textContent = t('case.code', { code: e.code });
  const list = clear($('case-exits'));
  const acts = {
    other_pdf: function () { clearFile(); S.focusFile = true; go('#/upload'); },
    sample: function () { go('#/samples'); },
    start: function () { go('#/'); },
    retry: function () { const r = S.retry; if (r) { r(); } else { route(); } }
  };
  let exits = (e.exits || []).filter(function (x) { return acts[x]; });
  if (!exits.length) { exits = ['start']; }
  exits.forEach(function (x, i) {
    const li = el('li');
    const b = el('button', 'btn ' + (i === 0 ? 'btn-primary' : 'btn-second'), t('exit.' + x));
    b.type = 'button';
    b.addEventListener('click', acts[x]);
    li.appendChild(b);
    list.appendChild(li);
  });
  if (e.code === 'busy' && e.detail && e.detail.job_id) {
    const li = el('li');
    const a = el('a', 'btn btn-second', t('case.busy.open'));
    a.href = '#/job/' + encodeURIComponent(e.detail.job_id);
    li.appendChild(a);
    list.appendChild(li);
  }
}

/* ---------- health ---------- */
function loadHealth() {
  if (S.health) { return Promise.resolve(S.health); }
  if (!S.healthWait) {
    /* All static texts are set again: the answer selects the texts of a hosted site (function t). */
    S.healthWait = api.health().then(function (h) { S.health = h; S.healthWait = null; applyStatic(); return h; },
      function (e) { S.healthWait = null; throw e; });
  }
  return S.healthWait;
}
/* A public site (modes.read_only of /api/health): the server takes no file and refuses each DELETE.
   The page then shows no upload form, no delete button and no stop button. */
function readOnly() { return !!(S.health && S.health.modes && S.health.modes.read_only === true); }
/* False (modes.sample_runs): the server starts no run for a sample whose result is ready. */
function sampleRunsOff() { return !!(S.health && S.health.modes && S.health.modes.sample_runs === false); }
/* True (key hosted): the server is not on the computer of the reader. The function t then takes the keys
   with the ending .hosted. */
function hosted() { return !!(S.health && S.health.hosted === true); }
/* True (key site): the server gives the pages about the project below /. The page then shows a link. */
function hasSite() { return !!(S.health && S.health.site === true); }
/* The mode sentences come from the values of /api/health: if the site takes no file (modes.read_only),
   if an own PDF is converted (modes.upload), the text recognition (ocr) and if the samples have stored
   Apertus states (modes.apertus_stored). */
function modeLines(where) {
  const h = S.health;
  if (!h || !h.modes) { return []; }
  const upload = h.modes.upload === true && !readOnly();
  const out = [readOnly() ? t('mode.read_only') : (upload ? t('mode.upload.yes') : t('mode.upload.no'))];
  if (upload) { out.push(tk('mode.ocr.', h.ocr, null, '')); }
  if (where === 'start' && h.modes.apertus_stored === true) { out.push(t('mode.samples.stored')); }
  if (where === 'upload' && upload) { out.push(t('mode.upload.unchecked')); }
  return out.filter(Boolean);
}
function renderHealth() {
  const h = S.health;
  const start = $('start-mode');
  start.textContent = modeLines('start').join(' ');
  start.hidden = !h;
  const up = $('upload-mode');
  up.textContent = modeLines('upload').join(' ');
  up.hidden = !h;
  $('limits').textContent = h && h.limits ? t('s2.limits', { mb: Math.round(h.limits.max_bytes / 1048576), p: h.limits.max_pages }) : '';
  const fv = $('foot-version');
  fv.textContent = h ? t('foot.version', { version: h.version }) : '';
  fv.hidden = !h;
  const ro = readOnly();
  $('start-line').textContent = t(ro ? 's0.line.read_only' : 's0.line');
  /* A site that takes no file promises no upload: the second way of the start page, the navigation entry
     and the headline of S2 name the run on the own computer. */
  $('start-upload').textContent = t(ro ? 's0.button.local' : 's0.button.upload');
  $('start-upload-note').textContent = t(ro ? 's0.local.note' : 's0.upload.note');
  $('nav-upload').textContent = t(ro ? 'nav.local' : 'nav.upload');
  $('h-upload').textContent = t(ro ? 's2.title.read_only' : 's2.title');
  const off = sampleRunsOff();
  $('samples-lead').textContent = t(off ? 's1.lead.ready' : 's1.lead');
  /* The pages about the project: the German pages are below /de/. */
  const site = hasSite();
  const siteUrl = S.lang === 'de' ? '/de/' : '/';
  $('nav-site-item').hidden = !site;
  $('nav-site').setAttribute('href', siteUrl);
  $('upload-off-site').hidden = !site;
  $('upload-off-site-link').setAttribute('href', siteUrl);
  if (S.screen === 'upload' || S.screen === 'start') { setTitle(S.screen); }
  $('upload-form').hidden = ro;
  $('upload-off').hidden = !ro;
  up.hidden = !h || ro;
  $('job-stop').hidden = ro;
  $('rec-delete-part').hidden = ro;
  /* The cards of the samples have other buttons on such a site. */
  if (h && S.screen === 'samples' && S.samples.length && (ro || sampleRunsOff())) { renderSamples(); }
}

/* ---------- the numbers of the one fixed run (ui/run_numbers.json, made by ui/tools/make_run_numbers.py) ---------- */
/* The fields of a record in the sequence of the page. The colour class c<n> of a value is its place in this list:
   a row, a box on the page and the triples of one value have the same colour. The colour says which value it is;
   it says nothing about the value. */
const FIELD_ORDER = ['affair_type', 'title', 'affair_number', 'submission_date', 'sponsor', 'response_date', 'responder'];
function colourOf(field) { const i = FIELD_ORDER.indexOf(field); return 'c' + (i < 0 ? 7 : i); }
function loadNumbers() {
  if (S.numbers) { return Promise.resolve(S.numbers); }
  if (!S.numbersWait) {
    S.numbersWait = fetch('run_numbers.json', { cache: 'no-cache' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; })
      .then(function (d) { S.numbersWait = null; S.numbers = d && d.fields ? d : null; return S.numbers; });
  }
  return S.numbersWait;
}
/* A share of the run as a percent of the documents: the display value of numbers.json times 100, rounded. */
function pct(share) {
  const x = Number(share);
  return Number.isFinite(x) ? t('fmt.percent', { n: Math.round(x * 100) }) : '';
}
/* A bar from 0 to 1 (SVG, no inline style). */
function bar(share, cls) {
  const x = Math.max(0, Math.min(1, Number(share) || 0));
  const s = svg('svg', { class: 'bar ' + (cls || ''), viewBox: '0 0 100 8', preserveAspectRatio: 'none', 'aria-hidden': 'true', focusable: 'false' });
  s.appendChild(svg('rect', { class: 'bar-bg', x: 0, y: 0, width: 100, height: 8 }));
  s.appendChild(svg('rect', { class: 'bar-fg', x: 0, y: 0, width: (x * 100).toFixed(2), height: 8 }));
  return s;
}

/* ---------- S0 start ---------- */
function showStart(opts) {
  show('start', opts.keepFocus);
  renderHealth();
  renderGood();
  renderStartSamples();
  loadNumbers().then(function () { if (S.screen === 'start') { renderGood(); } });
  api.samples().then(function (data) {
    S.samples = (data && data.samples) || [];
    if (S.screen === 'start') { renderStartSamples(); }
  }, function () {
    if (S.screen === 'start' && !S.samples.length) { $('start-samples-wait').textContent = t('start.samples.none'); }
  });
  loadHealth().catch(function (e) {
    if (S.screen === 'start') { showCase(e, function () { go('#/'); }); }
  });
}
/* The mode of a sample card: the first mode of the sample (auto: code rules and stored Apertus results). */
function cardMode(s) { return (s.modes || [])[0] || 'auto'; }
function renderStartSamples() {
  const list = clear($('start-samples'));
  const wait = $('start-samples-wait');
  wait.hidden = S.samples.length > 0;
  if (!S.samples.length) { wait.textContent = t('app.loading'); }
  S.samples.forEach(function (s) {
    const mode = cardMode(s);
    const rid = s.record_id + (mode === 'rules' ? '-rules' : '');
    const ready = !!(s.ready && s.ready[mode] && s.record_id);
    const li = el('li', 'start-card');
    let act;
    if (ready) {
      act = el('a', 'start-card-act');
      act.href = '#/view/' + encodeURIComponent(rid);
    } else if (sampleRunsOff()) {
      act = el('a', 'start-card-act');
      act.href = '#/samples';
    } else {
      act = el('button', 'start-card-act');
      act.type = 'button';
      act.addEventListener('click', function () { startSample(s.doc_id, mode); });
    }
    const title = el('span', 'start-card-title', s.title);
    if (s.language) { title.lang = s.language; }
    act.appendChild(title);
    const facts = [nameId(s.parliament_name, s.parliament), affairType(s.kind), langName(s.language)].filter(Boolean);
    act.appendChild(el('span', 'start-card-facts', facts.join(' · ')));
    act.appendChild(el('span', 'start-card-go', ready ? t('start.card.open') : t('start.card.run')));
    act.setAttribute('aria-label', t('start.card.label', { title: s.title || '', facts: facts.join(', '),
      go: ready ? t('start.card.open') : t('start.card.run') }));
    li.appendChild(act);
    list.appendChild(li);
  });
}
/* The box «How often correct?»: the share correct of the 7 fields in the one fixed run (code rules only). */
function renderGood() {
  const n = S.numbers;
  const list = clear($('good-list'));
  $('good-lead').textContent = n ? t('start.good.lead', { date: n.run.date, docs: Number(n.run.documents), parl: Number(n.run.parliaments) }) : '';
  if (!n) { return; }
  FIELD_ORDER.forEach(function (f) {
    const x = n.fields[f];
    if (!x) { return; }
    const li = el('li', 'good-item');
    li.appendChild(el('span', 'good-pct n', pct(x.share_correct)));
    li.appendChild(el('span', 'good-name', tk('value.', f)));
    li.appendChild(bar(x.share_correct, 'good-bar'));
    li.appendChild(el('span', 'good-count small', t('start.good.count', { k: Number(x.correct), n: Number(x.with_reference) })));
    list.appendChild(li);
  });
}

/* ---------- About: the long texts, one section for each link «more» ---------- */
const ABOUT = { method: 'h-about', numbers: 'h-about-numbers', limits: 'h-about-limits', technical: 'h-about-technical' };
function showAbout(section, opts) {
  show('about', opts.keepFocus);
  renderHealth();
  renderNumbers();
  loadNumbers().then(function () { if (S.screen === 'about') { renderNumbers(); } });
  loadHealth().catch(function () { /* the mode line stays hidden */ });
  const h = section && ABOUT[section] ? $(ABOUT[section]) : null;
  if (h && !opts.rerender) { h.focus({ preventScroll: true }); intoView(h, 'start'); }
}
function renderNumbers() {
  const n = S.numbers;
  const body = clear($('numbers-rows'));
  $('numbers-lead').textContent = n ? t('about.numbers.lead', { date: n.run.date, docs: Number(n.run.documents), parl: Number(n.run.parliaments) }) : t('about.numbers.absent');
  $('numbers-source').textContent = n && n.source ? t('about.numbers.source', { made: n.source.made }) : '';
  if (!n) { return; }
  FIELD_ORDER.forEach(function (f) {
    const x = n.fields[f];
    if (!x) { return; }
    const tr = el('tr');
    tr.appendChild(el('th', 'num-field', tk('value.', f)));
    tr.lastChild.setAttribute('scope', 'row');
    const share = el('td', 'num-share');
    share.appendChild(el('span', 'n', pct(x.share_correct)));
    share.appendChild(bar(x.share_correct, 'num-bar'));
    tr.appendChild(share);
    tr.appendChild(el('td', 'n', t('start.good.count', { k: Number(x.correct), n: Number(x.with_reference) })));
    tr.appendChild(el('td', 'n', x.precision));
    body.appendChild(tr);
  });
}

/* ---------- S1 samples ---------- */
async function showSamples(opts) {
  show('samples', opts.keepFocus);
  const wait = $('samples-wait');
  if (!opts.rerender) { clear($('samples-list')); wait.hidden = false; wait.textContent = t('app.loading'); }
  let data;
  try { data = await api.samples(); } catch (e) { showCase(e, function () { go('#/samples'); }); return; }
  if (S.screen !== 'samples') { return; }
  S.samples = (data && data.samples) || [];
  renderSamples();
}
/* A name with its key in parentheses, for example the name of a body and the key of the export. */
function nameId(name, id) {
  if (name && id) { return t('fmt.name_id', { name: name, id: id }); }
  return name || id || null;
}
function affairType(value) { return value ? tk('affair_type.', value) : null; }
function langName(code) { return code ? tk('lang.name.', code) : null; }
/* The two results of one sample (the two modes), as plain counts of the two views. No other claim. */
async function loadCompare(baseId, node, link, currentId) {
  node.hidden = true;
  if (S.fixture || !/^s-[0-9]+$/.test(baseId)) { return; }
  let a;
  let r;
  try {
    const both = await Promise.all([api.record(baseId), api.record(baseId + '-rules')]);
    a = both[0];
    r = both[1];
  } catch (e) { return; }
  if (!a || !r || !a.run || !r.run || !a.counts || !r.counts || a.run.apertus !== 'stored' || r.run.apertus !== 'none') { return; }
  const la = a.counts.labels;
  const lr = r.counts.labels;
  clear(node);
  node.appendChild(document.createTextNode(t('cmp.line', { ac: la.certain, au: la.unsure, rc: lr.certain, ru: lr.unsure }) + ' ' + t('cmp.note')));
  if (link) {
    const other = currentId === baseId ? baseId + '-rules' : baseId;
    const words = other === baseId ? t('cmp.open.auto') : t('cmp.open.rules');
    const an = el('a', 'more', words);
    an.href = '#/record/' + encodeURIComponent(other);
    node.appendChild(document.createTextNode(' '));
    node.appendChild(an);
  }
  node.hidden = false;
}
function modeText(sample, mode) {
  return mode === 'auto' && sample.apertus === 'stored' ? t('mode.name.auto') : t('mode.name.rules');
}
function renderSamples() {
  const list = clear($('samples-list'));
  const wait = $('samples-wait');
  wait.hidden = S.samples.length > 0;
  wait.textContent = S.samples.length ? '' : t('s1.empty');
  S.samples.forEach(function (s) {
    const li = el('li', 'sample');
    const title = el('h2', 'sample-title', s.title);
    if (s.language) { title.lang = s.language; }
    li.appendChild(title);
    li.appendChild(el('p', 'sample-doc mono', t('s1.card.doc', { doc: s.doc_id })));
    const facts = el('dl', 'summary');
    dlRow(facts, t('s4.summary.affair_type'), affairType(s.kind));
    dlRow(facts, t('s1.card.parliament'), nameId(s.parliament_name, s.parliament));
    dlRow(facts, t('s1.card.language'), langName(s.language));
    dlRow(facts, t('s1.card.pages'), s.pages);
    dlRow(facts, t('s1.card.blocks'), s.blocks);
    dlRow(facts, t('s1.card.lines'), s.lines);
    li.appendChild(facts);
    li.appendChild(el('p', 'sample-note', t('s1.card.inputs')));
    if (s.in_sample === true) { li.appendChild(el('p', 'sample-note sample-dev', t('s1.card.dev'))); }
    const acts = el('ul', 'sample-acts');
    (s.modes || []).forEach(function (mode, i) {
      const words = modeText(s, mode);
      const item = el('li');
      const ready = !!(s.ready && s.ready[mode] && s.record_id);
      /* A site that serves the prepared results only: a ready result has no convert button. */
      const openOnly = ready && sampleRunsOff();
      if (!openOnly) {
        const b = el('button', 'btn ' + (i === 0 ? 'btn-primary' : 'btn-second'), t('s1.run', { mode: words }));
        b.type = 'button';
        b.setAttribute('aria-label', t('s1.run.label', { doc: s.doc_id, mode: words }));
        b.addEventListener('click', function () { startSample(s.doc_id, mode); });
        item.appendChild(b);
      }
      if (ready) {
        const a = el('a', openOnly ? 'btn ' + (i === 0 ? 'btn-primary' : 'btn-second') : 'more',
          openOnly || readOnly() ? t('s1.open.site', { mode: words }) : t('s1.open', { mode: words }));
        a.href = '#/view/' + encodeURIComponent(s.record_id + (mode === 'rules' ? '-rules' : ''));
        a.setAttribute('aria-label', t('s1.open.label', { doc: s.doc_id, mode: words }));
        item.appendChild(a);
      }
      acts.appendChild(item);
    });
    li.appendChild(acts);
    if (s.ready && s.ready.auto && s.ready.rules && s.record_id) {
      const cmp = el('p', 'sample-note sample-cmp');
      cmp.hidden = true;
      li.appendChild(cmp);
      loadCompare(s.record_id, cmp, false, null);
    }
    list.appendChild(li);
  });
}
async function sendJob(makeForm, input) {
  if (S.sending) { return; }
  S.sending = true;
  try {
    const answer = await api.startJob(makeForm());
    S.pendingInput = input;
    S.sending = false;
    go('#/job/' + encodeURIComponent(answer.job_id));
  } catch (e) {
    S.sending = false;
    showCase(e, function () { sendJob(makeForm, input); });
  }
}
function startSample(doc, mode) {
  return sendJob(function () {
    const form = new FormData();
    form.append('sample', String(doc));
    form.append('mode', mode);
    return form;
  }, { kind: 'sample', doc: String(doc) });
}

/* ---------- S2 upload ---------- */
function showUpload(opts) {
  show('upload', opts.keepFocus);
  renderHealth();
  renderFileLine();
  if (!opts.rerender) { uploadError('', null); }
  if (S.focusFile) { S.focusFile = false; $('file').focus(); }
  loadHealth().catch(function () { /* the limits line stays empty; the server still checks the limits */ });
}
function chosenFile() {
  const input = $('file');
  return (input.files && input.files[0]) || S.dropFile || null;
}
function clearFile() {
  try { $('file').value = ''; } catch (e) { /* a browser can refuse it */ }
  S.dropFile = null;
  renderFileLine();
}
function renderFileLine() {
  const f = chosenFile();
  $('file-line').textContent = f ? t('s2.selected', { name: f.name, size: fileSize(f.size) }) : t('s2.none');
}
function uploadError(text, field) {
  $('upload-err').textContent = text;
  ['file', 'doc-id'].forEach(function (id) { $(id).removeAttribute('aria-invalid'); });
  if (field) { field.setAttribute('aria-invalid', 'true'); field.focus(); }
}
function bindUpload() {
  const input = $('file');
  const drop = $('drop');
  input.addEventListener('change', function () { S.dropFile = null; uploadError('', null); renderFileLine(); });
  ['dragenter', 'dragover'].forEach(function (name) {
    drop.addEventListener(name, function (ev) { ev.preventDefault(); drop.classList.add('is-over'); });
  });
  ['dragleave', 'dragend'].forEach(function (name) {
    drop.addEventListener(name, function () { drop.classList.remove('is-over'); });
  });
  drop.addEventListener('drop', function (ev) {
    ev.preventDefault();
    drop.classList.remove('is-over');
    const files = ev.dataTransfer ? ev.dataTransfer.files : null;
    if (!files || !files.length) { return; }
    if (files.length > 1) { uploadError(t('s2.one_file'), null); return; }
    uploadError('', null);
    try { input.files = files; } catch (e) { /* a browser can refuse the assignment */ }
    S.dropFile = input.files && input.files[0] ? null : files[0];
    renderFileLine();
    say($('file-line').textContent);
  });
  /* A file that misses the drop zone must not replace the page. */
  ['dragover', 'drop'].forEach(function (name) {
    window.addEventListener(name, function (ev) { if (S.screen === 'upload') { ev.preventDefault(); } });
  });
  $('upload-form').addEventListener('submit', function (ev) {
    ev.preventDefault();
    const f = chosenFile();
    const doc = $('doc-id').value.trim();
    if (!f) { uploadError(t('s2.need_file'), input); return; }
    if (doc && !/^[0-9]+$/.test(doc)) { uploadError(t('s2.doc_id.bad'), $('doc-id')); return; }
    /* The page checks the size and the one-job rule before it sends the file. The server checks them again. */
    const max = S.health && S.health.limits ? S.health.limits.max_bytes : null;
    if (max && f.size > max) {
      uploadError(t('s2.too_large', { mb: round1(f.size / 1048576), max: Math.round(max / 1048576) }), input);
      return;
    }
    uploadError('', null);
    const send = function () {
      sendJob(function () {
        const form = new FormData();
        form.append('file', f, f.name);
        if (doc) { form.append('doc_id', doc); }
        form.append('mode', 'auto');
        return form;
      }, { kind: 'upload', name: f.name });
    };
    api.health().then(function (h) {
      if (h && h.busy === true) { uploadError(t('s2.busy'), null); return; }
      send();
    }, send);
  });
}

/* ---------- S3 stages ---------- */
function stageList(job) { return STAGES.map(function (id) { return job.stages[id]; }); }
function leaveJob() {
  const j = S.job;
  if (!j) { return; }
  if (j.stream) { j.stream.close(); j.stream = null; }
  clearInterval(j.tick);
  clearInterval(j.poll);
  j.tick = j.poll = null;
}
function newJob(id) {
  const stages = {};
  emptyStages().forEach(function (s) { stages[s.id] = s; });
  return { id: id, stages: stages, state: 'queued', input: S.pendingInput, t0: Date.now(), base: 0,
    stream: null, tick: null, poll: null, polling: false, ended: false };
}
function applyStage(ev) {
  const j = S.job;
  if (!j || !j.stages[ev.id]) { return; }
  const s = j.stages[ev.id];
  const before = s.state;
  s.state = ev.state || s.state;
  ['origin', 'seconds', 'reason'].forEach(function (k) { if (ev[k] !== undefined && ev[k] !== null) { s[k] = ev[k]; } });
  if (ev.counts) { s.counts = ev.counts; }
  if (j.state === 'queued') { j.state = 'running'; }
  if (before !== s.state && S.screen === 'job') {
    say(t('s3.announce', { i: STAGES.indexOf(ev.id) + 1, n: STAGES.length, stage: stageName(s), state: stageState(s) }));
  }
}
function applyJob(job) {
  const j = S.job;
  if (!j || !job) { return; }
  (job.stages || []).forEach(function (s) { if (s && s.state && j.stages[s.id] && s.state !== j.stages[s.id].state) { applyStage(s); } });
  if (job.input && job.input.kind) {
    j.input = { kind: job.input.kind, doc: job.input.doc_id, name: job.input.file_name };
  }
  if (typeof job.elapsed_seconds === 'number') { j.base = job.elapsed_seconds; j.t0 = Date.now(); }
  if (job.state) { j.state = job.state; }
  renderJob();
  if (job.state === 'done' || job.state === 'failed' || job.state === 'stopped') { endJob(job); }
}
function endJob(job) {
  const j = S.job;
  if (!j || j.ended) { return; }
  j.ended = true;
  leaveJob();
  if (S.screen !== 'job') { return; }
  if (job.state === 'done' && job.record_id) {
    say(t('s3.done'));
    S.view = null;
    location.replace('#/view/' + encodeURIComponent(job.record_id));
  } else if (job.state === 'failed') {
    showCase(job.error || localCase('bad_answer'), retryInput(j.input));
  } else if (job.state === 'stopped') {
    showCase(localCase('stopped', ['sample', 'start']), null);
  } else {
    showCase(localCase('bad_answer'), null);
  }
}
function retryInput(input) {
  if (input && input.kind === 'sample' && input.doc) { return function () { go('#/samples'); }; }
  return function () { go('#/upload'); };
}
function startPoll() {
  const j = S.job;
  if (!j || j.ended || j.poll) { return; }
  j.polling = true;
  renderJob();
  let fails = 0;
  const ask = async function () {
    try {
      const job = await api.job(j.id);
      fails = 0;
      if (S.job === j) { applyJob(job); }
    } catch (e) {
      fails += 1;
      const known = e instanceof AppError && e.error && !e.error.local;
      if ((known || fails >= 5) && S.job === j && !j.ended) {
        j.ended = true;
        leaveJob();
        if (S.screen === 'job') { showCase(e, function () { go('#/job/' + encodeURIComponent(j.id)); }); }
      }
    }
  };
  j.poll = setInterval(ask, POLL_MS);
  ask();
}
async function showJob(id, opts) {
  if (S.job && S.job.id === id && !S.job.ended && opts.rerender) {
    show('job', opts.keepFocus);
    renderJob();
    return;
  }
  leaveJob();
  const j = S.job = newJob(id);
  S.pendingInput = null;
  show('job', opts.keepFocus);
  renderJob();
  j.tick = setInterval(renderTime, 1000);
  try {
    const job = await api.job(id);
    if (S.job !== j) { return; }
    applyJob(job);
  } catch (e) {
    if (S.job === j) { j.ended = true; leaveJob(); showCase(e, function () { go('#/samples'); }); }
    return;
  }
  if (j.ended || S.job !== j) { return; }
  j.stream = api.events(id, {
    stage: function (ev) { if (S.job === j) { applyStage(ev); renderJob(); } },
    end: function (job) { if (S.job === j) { applyJob(job); } },
    broken: function () { if (S.job === j) { j.stream = null; startPoll(); } }
  });
}
/* The name of a step says what runs. For a sample the first two steps read stored pages and lines (the package
   holds no PDF of a sample), and the fourth step reads stored Apertus results; no model is asked.
   For an own PDF the fourth step is skipped: the package runs no language model. */
function stageName(s) {
  const input = S.job ? S.job.input : null;
  const sample = Boolean(input && input.kind === 'sample');
  if (s.id !== 'apertus') {
    const own = 's3.stage.' + s.id + '.sample';
    return sample && has(own) ? t(own) : t('s3.stage.' + s.id);
  }
  return t(sample ? 's3.stage.model.sample' : 's3.stage.model.own');
}
function stageState(s) {
  if (s.state === 'skipped' && s.reason) {
    const reason = s.id === 'apertus' && s.reason === 'not_in_package' ? 'no_model' : s.reason;
    return tk('s3.skip.', reason, null, t('s3.state.skipped'));
  }
  return tk('s3.state.', s.state);
}
function renderTime() {
  const j = S.job;
  if (!j) { return; }
  const s = Math.floor(j.base + (Date.now() - j.t0) / 1000);
  $('job-time').textContent = t('s3.time', { s: s });
}
function renderJob() {
  const j = S.job;
  if (!j) { return; }
  const input = j.input;
  $('job-input').textContent = !input ? '' : input.kind === 'sample'
    ? t('s3.input.sample', { doc: input.doc }) : (input.name ? t('s3.input.upload', { name: input.name }) : '');
  const list = clear($('job-stages'));
  stageList(j).forEach(function (s) {
    const li = el('li', 'stage is-' + s.state);
    if (s.state === 'running') { li.setAttribute('aria-current', 'step'); }
    const mark = el('span', 'stage-mark');
    mark.setAttribute('aria-hidden', 'true');
    li.appendChild(mark);
    li.appendChild(el('span', 'stage-name', stageName(s)));
    li.appendChild(el('span', 'stage-state', stageState(s)));
    const extra = [];
    if (s.state === 'done') {
      if (s.origin === 'stored') { extra.push(t('s3.origin.stored')); }
      if (typeof s.seconds === 'number') { extra.push(t('s3.seconds', { s: num(s.seconds) })); }
      Object.keys(s.counts || {}).forEach(function (k) { extra.push(tk('s3.count.', k, { n: s.counts[k] }, k + ': ' + s.counts[k])); });
    }
    if (extra.length) { li.appendChild(el('span', 'stage-extra', extra.join(' · '))); }
    list.appendChild(li);
  });
  renderTime();
  $('job-poll').hidden = !j.polling;
  $('job-stop').disabled = j.ended;
}
async function stopJob() {
  const j = S.job;
  if (!j || j.ended || readOnly()) { return; }
  $('job-stop').disabled = true;
  try {
    const job = await api.stop(j.id);
    if (S.job === j) { applyJob(job); }
  } catch (e) {
    if (S.job === j && !j.ended) { j.ended = true; leaveJob(); showCase(e, function () { go('#/'); }); }
  }
}

/* ---------- S4 result ---------- */
async function showRecord(id, labelId, opts) {
  /* An id with a wrong form names no record: the page shows the case itself, with no request. */
  if (!RECORD_RE.test(id)) { showCase(localCase('no_record', ['sample', 'start']), null); return; }
  const same = S.screen === 'record' && S.view && S.viewId === id;
  if (same && !opts.rerender) {
    if (labelId && S.ix.labels.has(labelId) && (S.sel !== labelId || S.ix.cardEl.get(labelId).hidden)) {
      selectLabel(labelId, { scroll: 'card', keepHash: true });
    }
    return;
  }
  if (!(await loadView(id, '#/record/'))) { return; }
  renderRecord();
  show('record', opts.keepFocus);
  const want = labelId && S.ix.labels.has(labelId) ? labelId : (opts.rerender ? S.sel : null);
  /* a link to one label (for example «Details» of the result view) jumps to its card at once: a smooth scroll
     over a long page can stop before the card */
  if (want) { selectLabel(want, { scroll: opts.rerender ? null : 'card', keepHash: true, quiet: true, instant: want === labelId }); }
  /* A link to one label: the focus goes to the heading of its card, so that the next Tab stays there. */
  if (want && want === labelId && !opts.rerender) {
    const h = S.ix.cardEl.get(want).querySelector('.card-name');
    if (h) { h.focus({ preventScroll: true }); }
  }
  mountPanel();
}
/* The view of a record (GET /api/records/<id>). One load for the result view and the technical view. */
async function loadView(id, back) {
  if (S.view && S.viewId === id) { return true; }
  let view;
  try { view = await api.record(id); } catch (e) { showCase(e, function () { go(back + encodeURIComponent(id)); }); return false; }
  if (!view || !Array.isArray(view.labels) || !Array.isArray(view.pages) || !view.run || !view.document || !view.counts) {
    showCase(localCase('bad_answer'), function () { go(back + encodeURIComponent(id)); });
    return false;
  }
  S.view = view;
  S.viewId = id;
  S.sel = null;
  S.vsel = null;
  S.ttl = null;
  S.filter = { status: 'all', group: 'all' };
  return true;
}
function buildIndex(view) {
  const ix = { labels: new Map(), atoms: new Map(), calib: new Map(), lineEl: new Map(), listEl: new Map(), cardEl: new Map(),
    line: new Map(), block: new Map(), order: [], value: new Map(), spans: new Map(), lineBox: new Map(), rowEl: new Map() };
  /* a value that a rule read from the PDF: by the id of its label; spans = the part of each line with the value */
  (view.values || []).forEach(function (x) { ix.value.set(x.label_id, x); ix.spans.set(x.label_id, x.spans || []); });
  view.blocks.forEach(function (b) { ix.block.set(b.id, b); });
  view.pages.forEach(function (p) { p.lines.forEach(function (l) { ix.line.set(l.atom_id, { line: l, page: p.number }); }); });
  (view.calibrations || []).forEach(function (c) { ix.calib.set(c.id, c); });
  view.labels.forEach(function (l) { ix.labels.set(l.id, l); ix.atoms.set(l.id, (l.target && l.target.atom_ids) || []); });
  const extra = (view.document.head || []).concat(view.document.text_blocks || []);
  extra.forEach(function (h) {
    if (h.label_id && ix.atoms.has(h.label_id) && !ix.atoms.get(h.label_id).length && h.atom_ids && h.atom_ids.length) {
      ix.atoms.set(h.label_id, h.atom_ids);
    }
  });
  return ix;
}
function optionName(kind, value) { return tk('option.' + kind + '.', value); }
/* The plain name of a property of the record. With no text in the strings file the stored name shows. */
function slotName(slot) { return tk('slot.', slot); }
function switchBlock(l) {
  if (l.note_params && l.note_params.before) { return l.note_params.before; }
  const m = /^switch-after-(B[0-9]+)$/.exec(l.id);
  return m ? m[1] : null;
}
/* The part of the record that a value belongs to, in plain words, from its place in the record
   (for example affairs[0].response_steps[0].responder.name.text gives: response, responder, name). */
function pathWords(path) {
  const names = String(path || '').split('.').map(function (x) { return x.replace(/\[[0-9]+\]$/, ''); });
  const words = [];
  const step = /response_steps\[([0-9]+)\]/.exec(String(path || ''));
  if (step) { words.push(Number(step[1]) > 0 ? t('part.nth', { name: t('part.ResponseStep'), n: Number(step[1]) + 1 }) : t('part.ResponseStep')); }
  else if (names.indexOf('submission') !== -1) { words.push(t('part.Submission')); }
  else if (names[0] === 'affairs') { words.push(t('part.affair')); }
  ['title', 'responder', 'name'].forEach(function (p) { if (names.indexOf(p) !== -1) { words.push(t('part.' + p)); } });
  /* the second and each later text of one step has its number */
  const m = /\.texts\[([0-9]+)\]/.exec(String(path || ''));
  if (m && Number(m[1]) > 0) { words.push(t('part.number', { n: Number(m[1]) + 1 })); }
  return words;
}
function isCandidate(l) { return /^candidate-/.test(String(l.id)); }
function labelName(l) {
  /* a candidate (label id candidate-<field>) is not a value of the record: its card says so. The body that a
     proposal addresses is not a weak candidate: it has its own heading. */
  if (l.kind === 'pdf_value' && isCandidate(l)) {
    const head = l.note_code === 'addressee_candidate' ? t('kind.pdf_addressee') : t('kind.pdf_candidate');
    return head + ' · ' + tk('value.', String(l.id).replace(/^candidate-/, ''));
  }
  if (l.kind === 'pdf_value') { return tk('kind.', l.kind) + ' · ' + tk('value.', String(l.id).replace(/^pdf-/, '')); }
  let parts = [tk('kind.', l.kind)];
  const block = l.target && l.target.block_id ? l.target.block_id : (l.kind === 'author_switch' ? switchBlock(l) : null);
  if (block) { parts.push(t('s4.card.block', { block: block })); }
  else if (l.target && l.target.type !== 'document' && l.kind !== 'author_switch') {
    parts = parts.concat(pathWords(l.target.instance_path));
    parts.push(slotName(l.slot));
  }
  return parts.join(' · ');
}
function sourceLine(l, cal) {
  const g = l.source.group;
  if (l.kind === 'pdf_value') { return t('source.rule.value'); }
  /* A code rule selects the answer; the number is the value of a read-out for that answer. */
  if (g === 'rule' && cal && cal.method === 'verifier_platt') { return t('source.rule.readout_number'); }
  /* The label «response of the executive» of a sample is a stored value: this computer does not calculate it. */
  if (l.kind === 'executive_response' && l.source.kind === 'apertus_head' && S.view.run.apertus === 'stored') {
    return t('source.stored_value');
  }
  const key = g === 'apertus_readout' ? 'source.readout.' + l.source.kind : 'source.' + g;
  return has(key) ? t(key) : String(l.source.kind);
}
function placeLine(l) {
  const tg = l.target || {};
  const parts = [];
  if (tg.type === 'document') { parts.push(t('s4.card.whole')); }
  if (tg.block_id) { parts.push(t('s4.card.block', { block: tg.block_id })); }
  if (tg.page !== null && tg.page !== undefined) {
    parts.push(tg.last_page && tg.last_page !== tg.page ? t('s4.card.pages', { page: tg.page, last: tg.last_page }) : t('s4.card.page', { page: tg.page }));
  }
  if (tg.char_start !== null && tg.char_start !== undefined && tg.char_end !== null && tg.char_end !== undefined) {
    /* The end of a range is exclusive: an equal start and end is a block with no text (for example a picture). */
    parts.push(tg.char_end > tg.char_start ? t('s4.card.chars', { start: tg.char_start, end: tg.char_end }) : t('s4.card.nochars'));
  }
  return parts.join(' · ');
}
/* The sentence for a label whose selected answer has not the highest number. It says who selected the answer
   and, for a code rule, why the answer stays. */
function otherHigher(l, cal) {
  const params = { chosen: optionName(l.kind, l.value), pc: num(l.probability),
    option: optionName(l.kind, l.top_option.value), p: num(l.top_option.probability) };
  if (l.source.group === 'rule') { return t('unc.why.rule', params); }
  if (l.source.group === 'apertus_readout' && l.source.kind === 'code_step') { return t('unc.other_higher.readout', params); }
  return t('unc.other_higher', params);
}
/* The counts that the number of a rule comes from (calibration key basis), in plain words. */
function basisLine(l, cal, v) {
  if (!cal || !cal.basis || l.source.group !== 'rule') { return ''; }
  const b = cal.basis;
  /* a value read from the PDF: the measurement compares the rule with the OpenParlData export */
  if (l.kind === 'pdf_value') { return t('values.detail.basis', { n: b.n, k: b.agreed }); }
  let words = '';
  if (b.n !== null && b.n !== undefined) { words = t('unc.rule.basis.blocks', { n: b.n, k: b.agreed }); }
  else if (b.documents !== null && b.documents !== undefined) { words = t('unc.basis.documents', { n: b.documents, k: b.agreed }); }
  /* For a PDF with no export record the rule of the document label had no export values. */
  if (words && l.kind === 'document_text_parts' && v.run.origin === 'new' && v.document.has_export === false) {
    words += ' ' + t('unc.basis.no_export');
  }
  return words;
}
/* The text of a wording label: the lines of its text block. The stored value of the label is a hash. */
function wordingText(l, ix) {
  return (ix.atoms.get(l.id) || []).map(function (a) { const r = ix.line.get(a); return r ? r.line.text : ''; })
    .filter(Boolean).join(' ');
}
/* What a card shows as its value: { caption, text, raw (a stored name or address), doc (text in the language of the document) }. */
function cardValue(l, ix) {
  if (l.kind === 'text_wording') {
    const text = wordingText(l, ix);
    if (text) {
      return { caption: t('s4.card.wording'), text: text.length > WORDING_START ? text.slice(0, WORDING_START) + ' …' : text, raw: false, doc: true };
    }
  }
  if (l.kind === 'export_value' || l.kind === 'constant_value' || l.kind === 'text_wording' || l.kind === 'pdf_value') {
    let text = String(l.value);
    if (l.slot === 'affairType') { text = affairType(l.value); }
    else if (l.slot === 'textLanguage') { text = langName(l.value); }
    else if (l.slot === 'textType') { text = tk('option.block_slot.', l.value); }
    const doc = l.slot === 'text' || (l.kind === 'pdf_value' && l.slot !== 'affairType' && !/Date/.test(l.slot));
    if (text.length > LONG_VALUE) { text = text.slice(0, LONG_VALUE) + ' …'; }
    const caption = l.kind === 'pdf_value' && isCandidate(l) ? t('s4.card.candidate') : t('s4.card.value');
    return { caption: caption, text: text, raw: text === String(l.value) && !doc, doc: doc };
  }
  const shown = optionName(l.kind, l.value);
  return { caption: t('s4.card.label'), text: shown, raw: shown === l.value, doc: false };
}
/* The note of a label. The view gives a code for a known note (keys note.<code>). The working text of the
   converter is not shown; a note with no code is the text that the view cleaned. */
function noteText(l) {
  if (l.kind === 'executive_response' || !('note_code' in l)) { return null; }
  const params = l.note_params || {};
  if (l.note_code === 'final_check') { return null; }
  if (l.note_code === 'value_derivation') { return tk('note.value_derivation.', params.derivation, null, '') || null; }
  if (l.note_code) { return tk('note.', l.note_code, params, '') || null; }
  return l.note || null;
}
function statusNode(status, probability) {
  const p = el('p', 'card-status st-' + status);
  const shape = el('span', 'shape shape-' + status);
  shape.setAttribute('aria-hidden', 'true');
  p.appendChild(shape);
  p.appendChild(el('span', 'st-word', tk('status.', status)));
  if (status !== 'none' && probability !== null && probability !== undefined) {
    p.appendChild(document.createTextNode(' · '));
    const n = el('span', 'n', num(probability));
    n.setAttribute('translate', 'no');
    p.appendChild(n);
  }
  return p;
}
function noticeText(n, v) {
  const params = n.params || {};
  /* The text recognition: the counts of the pages by their text source, from the pages of the view. */
  if (n.code === 'ocr_apple') {
    const c = { pdf: 0, ocr: 0, mixed: 0 };
    v.pages.forEach(function (p) { if (c[p.text_source] !== undefined) { c[p.text_source] += 1; } });
    return t('ocr.apple.pages', { p: c.pdf, o: c.ocr, m: c.mixed });
  }
  /* In the mode with code rules only, the notice says why another answer can have a higher number. */
  let code = n.code === 'chosen_not_top' && v.run.apertus === 'none' ? 'chosen_not_top.rules' : n.code;
  if (params.n === 1 && has('notice.' + code + '.one')) { code += '.one'; }
  return tk('notice.', code, params, t('notice.unknown', { code: n.code }));
}
function renderRecord() {
  const v = S.view;
  const ix = S.ix = buildIndex(v);
  $('rec-to-view').href = '#/view/' + encodeURIComponent(v.record_id);
  const d = v.document;
  const c = v.counts;

  /* the document line and the head line */
  const doc = clear($('rec-doc'));
  if (d.title) {
    const title = el('span', 'rec-title', d.title);
    if (d.language) { title.lang = d.language; }
    doc.appendChild(title);
  }
  if (v.doc_id) { doc.appendChild(el('span', 'rec-docid mono', t('s1.card.doc', { doc: v.doc_id }))); }
  $('rec-headline').textContent = tk('s4.headline.', v.run.origin === 'stored' ? 'stored' : 'new',
    { mode: tk('mode.inline.', v.run.apertus === 'stored' ? 'auto' : 'rules') });

  /* the notices in plain words */
  const notices = clear($('rec-notices'));
  (v.notices || []).forEach(function (n) {
    notices.appendChild(el('li', 'notice-' + n.code, noticeText(n, v)));
  });
  const lc = c.labels;
  let countText = t('s4.count', { n: lc.total, a: lc.with_probability, c: lc.certain, u: lc.unsure, b: lc.none });
  /* the limit of the labels of the blocks; a value that is read from the PDF has its own limit in each mode */
  const withThreshold = (v.calibrations || []).some(function (k) { return k.kind !== 'pdf_value' && k.certain_threshold !== null && k.certain_threshold !== undefined; });
  if (lc.with_probability > 0 && !withThreshold) { countText += ' ' + t('unc.no_threshold'); }
  $('rec-count').textContent = countText;
  loadCompare(v.record_id.replace(/-rules$/, ''), $('rec-cmp'), true, v.record_id);

  const sum = clear($('rec-summary'));
  dlRow(sum, t('s4.summary.affair_number'), d.affair_number);
  dlRow(sum, t('s4.summary.affair_type'), affairType(d.affair_type));
  dlRow(sum, t('s1.card.parliament'), nameId(d.parliament_name, d.parliament));
  dlRow(sum, t('s1.card.language'), langName(d.language));
  dlRow(sum, t('s1.card.pages'), c.pages);
  dlRow(sum, t('s1.card.lines'), c.lines);
  dlRow(sum, t('s1.card.blocks'), c.blocks);

  renderPages(v, ix);
  renderEch(v, ix);
  renderCards(v, ix);
  renderFilters(v);
  applyFilter(true);
  renderHead(v, ix);
  renderChecks(v);
  renderDownloads(v);
  renderTech(v);
  resetDelete();
  $('rec-marked').textContent = t('s4.marked.start');
  $('rec-line').hidden = true;
  $('rec-to-card').hidden = true;
  /* On a narrow screen the drawn page is small: the text list of the lines is open. */
  if (window.matchMedia && window.matchMedia('(max-width: 47.5rem)').matches) { $('rec-lines-box').open = true; }
}

/* The page drawn from the line frames. Each line is a control: one tab stop, arrow keys move, Enter selects. */
function renderPages(v, ix) {
  const host = clear($('rec-pages'));
  const list = clear($('rec-lines'));
  const lang = v.document.language || '';
  /* The one tab stop of the drawing starts on the first line with text; a record with no such line starts on its first line. */
  const all = v.pages.reduce(function (acc, p) { return acc.concat(p.lines); }, []);
  const start = all.find(function (a) { return Boolean(a.text); }) || all[0] || null;
  v.pages.forEach(function (p) {
    const fig = el('figure', 'pg');
    const caption = t('s4.page.caption', { page: p.number, n: v.pages.length });
    const s = svg('svg', { class: 'pgs', viewBox: '0 0 ' + p.width + ' ' + p.height, role: 'group', 'aria-label': caption,
      'aria-describedby': 'rec-page-help', 'data-page': p.number });
    s.appendChild(svg('rect', { class: 'pg-paper', x: 0, y: 0, width: p.width, height: p.height }));
    const lines = svg('g', { class: 'pg-lines' });
    if (lang) { lines.setAttribute('lang', lang); }
    if (v.pages.length > 1) { list.appendChild(el('li', 'lines-page', t('s4.lines.page', { page: p.number }))); }
    p.lines.forEach(function (a) {
      const x1 = a.frame[0], y1 = a.frame[1], x2 = a.frame[2], y2 = a.frame[3];
      const bw = Math.max(x2 - x1, 1), bh = Math.max(y2 - y1, 1);
      const block = ix.block.get(a.block_id);
      const g = svg('g', { class: 'ln' + (block && block.docling_label === 'section_header' ? ' hd' : '') + (a.text ? '' : ' ln-empty'), 'data-a': a.atom_id,
        role: 'button', tabindex: start && a === start ? 0 : -1,
        'aria-label': a.text ? t('s4.line.aria', { id: a.atom_id, text: a.text }) : t('s4.line.aria.empty', { id: a.atom_id }) });
      g.appendChild(svg('rect', { x: x1 - 2, y: y1 - 1.5, width: bw + 4, height: bh + 3, rx: 1.5 }));
      if (a.text) {
        const fs = Math.max(3, Math.min(bh * 0.8, 14));
        const tl = a.frame_source === 'text_layer' ? bw : Math.min(bw, a.text.length * fs * 0.5);
        const tx = svg('text', { x: x1, y: (y2 - bh * 0.22).toFixed(2), 'font-size': fs.toFixed(2),
          textLength: Math.max(tl, 1).toFixed(2), lengthAdjust: 'spacingAndGlyphs', 'aria-hidden': 'true' });
        tx.textContent = a.text;
        g.appendChild(tx);
        ix.lineBox.set(a.atom_id, { host: g, x: x1, y: y1, w: Math.max(tl, 1), h: bh, len: a.text.length });
      }
      lines.appendChild(g);
      ix.lineEl.set(a.atom_id, g);
      ix.order.push(a.atom_id);

      const li = el('li');
      li.setAttribute('data-line-item', a.atom_id);
      const b = el('button', 'line-btn', a.text || a.atom_id);
      b.type = 'button';
      if (lang) { b.lang = lang; }
      b.addEventListener('click', function () { selectLine(a.atom_id, { scroll: 'card' }); });
      li.appendChild(b);
      list.appendChild(li);
      ix.listEl.set(a.atom_id, li);
    });
    s.appendChild(lines);
    fig.appendChild(s);
    /* A frame that is not from the text layer is an estimate or the frame of the block. The text source says
       if a text recognition gave the text, and if it ran before (a sample) or in this conversion. */
    const notLayer = p.lines.filter(function (a) { return a.frame_source !== 'text_layer'; }).length;
    const words = [caption];
    if (notLayer > 0) { words.push(t('s4.page.frames', { e: notLayer, t: p.lines.length })); }
    words.push(tk('s4.page.source.', p.text_source === 'pdf' ? 'pdf' : p.text_source + '.' + v.run.origin, null, ''));
    const cap = el('figcaption', '', words.filter(Boolean).join(' '));
    fig.appendChild(cap);
    host.appendChild(fig);
  });
}
function onPageKey(ev) {
  const g = ev.target.closest ? ev.target.closest('.ln') : null;
  if (!g || !S.ix) { return; }
  const order = S.ix.order;
  const i = order.indexOf(g.getAttribute('data-a'));
  let j = -1;
  if (ev.key === 'ArrowDown' || ev.key === 'ArrowRight') { j = Math.min(i + 1, order.length - 1); }
  else if (ev.key === 'ArrowUp' || ev.key === 'ArrowLeft') { j = Math.max(i - 1, 0); }
  else if (ev.key === 'Home') { j = 0; }
  else if (ev.key === 'End') { j = order.length - 1; }
  else if (ev.key === 'Enter' || ev.key === ' ') {
    ev.preventDefault();
    selectLine(g.getAttribute('data-a'), { scroll: 'card' });
    return;
  }
  if (j !== -1) {
    ev.preventDefault();
    g.setAttribute('tabindex', '-1');
    const next = S.ix.lineEl.get(order[j]);
    next.setAttribute('tabindex', '0');
    next.focus();
  }
}

function renderCards(v, ix) {
  const host = clear($('rec-cards'));
  const lang = v.document.language || '';
  v.labels.forEach(function (l) {
    const li = el('li', 'card');
    li.id = 'card-' + l.id;
    li.setAttribute('data-status', l.value_status);
    li.setAttribute('data-group', l.source.group);
    const name = labelName(l);
    const h = el('h3', 'card-name', name);
    h.id = 'card-h-' + l.id;
    h.tabIndex = -1;
    li.setAttribute('aria-labelledby', h.id);
    li.appendChild(h);

    /* The caption says what the value is: a label (an answer with a probability) or a plain value. */
    const shown = cardValue(l, ix);
    const val = el('p', 'card-val');
    val.appendChild(el('span', 'card-k', shown.caption));
    const value = el('span', 'card-v' + (shown.raw ? ' raw' : ''), shown.text);
    if (shown.doc && lang) { value.lang = lang; }
    val.appendChild(value);
    li.appendChild(val);
    const cal = l.calibration_id ? ix.calib.get(l.calibration_id) : null;
    li.appendChild(statusNode(l.value_status, l.probability));
    if (l.chosen_is_top === false && l.top_option) {
      li.appendChild(el('p', 'card-other', otherHigher(l, cal)));
    }
    li.appendChild(el('p', 'card-src', sourceLine(l, cal)));
    const basis = basisLine(l, cal, v);
    if (basis) { li.appendChild(el('p', 'card-cal', basis)); }
    /* finding V4-04: the document label is the result of the rule chain; rule V5 gave the kind after it */
    const casc = v.head_values ? v.head_values.cascade : null;
    if (l.kind === 'document_text_parts' && casc && casc.kind_from === 'rule_v5') {
      li.appendChild(el('p', 'card-cal', t('unc.doclabel.v5', { kind: kindName(casc.kind) })));
    }
    /* finding V5-07: a response value of a document with a kind by rule V5 is unsure also at or above the limit */
    if (cal && l.kind === 'pdf_value' && l.value_status === 'unsure' && casc && casc.kind_from === 'rule_v5'
      && typeof cal.certain_threshold === 'number' && l.probability >= cal.certain_threshold
      && (v.values || []).some(function (x) { return x.label_id === l.id && (x.field === 'responder' || x.field === 'response_date'); })) {
      li.appendChild(el('p', 'card-cal', t('unc.card.v5_unsure')));
    }
    if (cal && l.kind !== 'pdf_value' && l.value_status === 'unsure' && (cal.certain_threshold === null || cal.certain_threshold === undefined)) {
      li.appendChild(el('p', 'card-cal', t('unc.card.no_limit')));
    }
    const place = placeLine(l);
    if (place) {
      const pl = el('p', 'card-place');
      pl.appendChild(el('span', 'card-k', t('s4.card.place')));
      pl.appendChild(document.createTextNode(place));
      li.appendChild(pl);
    }
    if (ix.atoms.get(l.id).length) {
      const b = el('button', 'btn btn-s card-show', t('s4.card.show'));
      b.type = 'button';
      b.setAttribute('aria-pressed', 'false');
      b.setAttribute('aria-label', t('s4.card.show.label', { label: name }));
      /* A second press releases the button: the marks go away. */
      b.addEventListener('click', function () {
        if (S.sel === l.id) { clearSelection(false); } else { selectLabel(l.id, { scroll: 'page' }); }
      });
      li.appendChild(b);
    }
    if (l.options && l.options.length) {
      const box = el('div', 'opts');
      box.appendChild(el('h4', '', t('unc.all_options')));
      const ul = el('ul', 'opt-list');
      l.options.forEach(function (o) {
        const on = o.value === l.value;
        const item = el('li', on ? 'is-on' : '');
        item.appendChild(el('span', 'opt-name', optionName(l.kind, o.value)));
        const n = el('span', 'n', num(o.probability));
        n.setAttribute('translate', 'no');
        item.appendChild(n);
        item.appendChild(el('span', 'opt-mark', on ? t('s4.card.selected_mark') : ''));
        ul.appendChild(item);
      });
      box.appendChild(ul);
      li.appendChild(box);
    }
    /* The final check of the label «response of the executive», from the count of the record. */
    const agrees = v.counts.record ? v.counts.record.r2_agrees_with_block_path : null;
    if (l.kind === 'executive_response' && (agrees === true || agrees === false)) {
      li.appendChild(el('p', 'card-cal', t(agrees ? 'unc.r2.agrees' : 'unc.r2.differs')));
    }
    if (cal && cal.target_status) {
      li.appendChild(el('p', 'card-cal', tk('unc.target.', cal.target_status)));
    }

    /* The technical details hold the stored names and values. They hold no working name of the project. */
    const det = el('details', 'card-det');
    const sum = el('summary', '', t('s4.card.details'));
    sum.setAttribute('aria-label', t('s4.card.details.label', { label: name }));
    det.appendChild(sum);
    const dl = el('dl', 'summary');
    dlRow(dl, t('detail.id'), l.id, 'mono');
    dlRow(dl, t('detail.slot'), l.slot, 'mono');
    dlRow(dl, t('detail.path'), l.target ? l.target.instance_path : null, 'mono');
    dlRow(dl, t('detail.value'), l.value, 'mono');
    dlRow(dl, t('detail.iri'), l.iri, 'mono');
    if (l.kind === 'pdf_value') {
      dlRow(dl, t('values.detail.tier'), l.source.tier, 'mono');
      dlRow(dl, t('values.detail.rule'), l.source.rule_id, 'mono');
    }
    if (cal) {
      dlRow(dl, t('detail.method'), tk('method.', cal.method, null, ''));
      dlRow(dl, t('detail.fit_n'), cal.fit_n);
      dlRow(dl, t('detail.threshold'), cal.certain_threshold === null || cal.certain_threshold === undefined ? null : num(cal.certain_threshold));
    }
    if (l.in_sample === true || l.in_sample === false) { dlRow(dl, t('detail.in_sample'), t(l.in_sample ? 'word.yes' : 'word.no')); }
    dlRow(dl, t(l.note_code ? 'detail.note' : 'detail.note.raw'), noteText(l));
    det.appendChild(dl);
    li.appendChild(det);

    host.appendChild(li);
    ix.cardEl.set(l.id, li);
  });
}
function renderFilters(v) {
  const sel = clear($('rec-filter-source'));
  const all = el('option', '', t('s4.filter.source.all'));
  all.value = 'all';
  sel.appendChild(all);
  const groups = v.counts.labels.by_group || {};
  Object.keys(groups).forEach(function (g) {
    const o = el('option', '', tk('group.', g, { n: groups[g] }, g + ' (' + groups[g] + ')'));
    o.value = g;
    sel.appendChild(o);
  });
  if (S.filter.group !== 'all' && !(S.filter.group in groups)) { S.filter.group = 'all'; }
  sel.value = S.filter.group;
}
function applyFilter(quiet) {
  if (!S.ix) { return; }
  let shown = 0;
  S.ix.cardEl.forEach(function (li) {
    const ok = (S.filter.status === 'all' || li.getAttribute('data-status') === S.filter.status) &&
      (S.filter.group === 'all' || li.getAttribute('data-group') === S.filter.group);
    li.hidden = !ok;
    if (ok) { shown += 1; }
  });
  document.querySelectorAll('#rec-filter-status [data-filter]').forEach(function (b) {
    b.setAttribute('aria-pressed', b.getAttribute('data-filter') === S.filter.status ? 'true' : 'false');
  });
  $('rec-filter-source').value = S.filter.group;
  const text = shown === 0 && S.ix.cardEl.size > 0 ? t('s4.filter.empty') : t('s4.filter.count', { n: shown, t: S.ix.cardEl.size });
  $('rec-filter-count').textContent = text;
  if (!quiet) { say(text); }
}

/* Marks: the lines of one label on the page and in the text list. spans: the part of a line that holds a
   value read from the PDF; it gets a frame on the drawn page (the place is an estimate from the letter count). */
function setMarks(atomIds, spans) {
  const on = new Set(atomIds || []);
  const ix = S.ix;
  document.querySelectorAll('#rec-pages .span-mark').forEach(function (n) { n.remove(); });
  (spans || []).forEach(function (sp) {
    const box = ix.lineBox.get(sp.atom_id);
    if (!box || !box.len || sp.end <= sp.start) { return; }
    const a = Math.max(0, Math.min(sp.start, box.len)) / box.len;
    const b = Math.max(0, Math.min(sp.end, box.len)) / box.len;
    box.host.appendChild(svg('rect', { class: 'span-mark', x: (box.x + a * box.w - 1).toFixed(2), y: (box.y - 2.5).toFixed(2),
      width: Math.max((b - a) * box.w + 2, 2).toFixed(2), height: (box.h + 5).toFixed(2), rx: 1.5, 'aria-hidden': 'true' }));
  });
  ix.rowEl.forEach(function (row, key) { row.classList.toggle('is-sel', key === S.sel && !!S.sel); });
  ix.lineEl.forEach(function (g, id) {
    g.classList.remove('is-line');
    if (on.has(id)) { g.setAttribute('aria-current', 'true'); } else { g.removeAttribute('aria-current'); }
  });
  ix.listEl.forEach(function (li, id) {
    li.classList.remove('is-line');
    if (on.has(id)) { li.setAttribute('aria-current', 'true'); } else { li.removeAttribute('aria-current'); }
  });
}
function setCard(id) {
  S.ix.cardEl.forEach(function (li, key) {
    const on = key === id;
    li.classList.toggle('is-sel', on);
    const b = li.querySelector('.card-show');
    if (b) { b.setAttribute('aria-pressed', on ? 'true' : 'false'); }
  });
  $('rec-to-card').hidden = !id;
}
/* No label is selected: no mark on the page, no pressed button. */
function clearSelection(quiet) {
  if (!S.ix) { return; }
  S.sel = null;
  setMarks([]);
  setCard(null);
  $('rec-line').hidden = true;
  const text = t('s4.marked.cleared');
  $('rec-marked').textContent = text;
  try { history.replaceState(null, '', '#/record/' + encodeURIComponent(S.viewId)); } catch (e) { /* a sandbox can refuse it */ }
  syncLangLinks();
  if (!quiet) { say(text); }
}
function selectLabel(id, opt) {
  opt = opt || {};
  const ix = S.ix;
  const l = ix && ix.labels.get(id);
  if (!l) { return; }
  const card = ix.cardEl.get(id);
  if (card.hidden) { S.filter = { status: 'all', group: 'all' }; applyFilter(true); }
  S.sel = id;
  const atoms = ix.atoms.get(id);
  setMarks(atoms, ix.spans.get(id));
  setCard(id);
  if (!opt.keepLine) { $('rec-line').hidden = true; }
  if (!opt.keepHash) {
    try { history.replaceState(null, '', '#/record/' + encodeURIComponent(S.viewId) + '/label/' + encodeURIComponent(id)); } catch (e) { /* a sandbox can refuse it */ }
    syncLangLinks();
  }
  const name = labelName(l);
  const firstAtom = atoms.length ? ix.line.get(atoms[0]) : null;
  const text = atoms.length ? tn('s4.marked', atoms.length, { label: name, n: atoms.length, page: firstAtom ? firstAtom.page : '' }) : t('s4.marked.none', { label: name });
  $('rec-marked').textContent = text;
  if (!opt.quiet) { say(text); }
  if (opt.scroll === 'page') {
    intoView(atoms.length ? ix.lineEl.get(atoms[0]) : $('rec-pages'), 'center');
  } else if (opt.scroll === 'card') {
    intoView(card, opt.instant ? 'start' : 'nearest', opt.instant);
  }
}
/* A line of the page selects the label that uses it. The label with the fewer lines wins (a block before a text block). */
function selectLine(atomId, opt) {
  opt = opt || {};
  const ix = S.ix;
  const rec = ix.line.get(atomId);
  if (!rec) { return; }
  const users = [];
  ix.atoms.forEach(function (atoms, key) { if (atoms.indexOf(atomId) !== -1) { users.push(key); } });
  users.sort(function (a, b) { return ix.atoms.get(a).length - ix.atoms.get(b).length; });
  const key = users.indexOf(S.sel) !== -1 ? S.sel : users[0];
  const a = rec.line;
  let text;
  if (key) {
    selectLabel(key, { scroll: opt.scroll, keepLine: true, quiet: true });
    text = t('s4.line.usedby', { id: atomId, start: a.char_start, end: a.char_end, label: labelName(ix.labels.get(key)) });
  } else {
    S.sel = null;
    setMarks([]);
    setCard(null);
    text = t('s4.line.nolabel', { id: atomId, start: a.char_start, end: a.char_end });
  }
  const g = ix.lineEl.get(atomId);
  if (g) { g.classList.add('is-line'); }
  const li = ix.listEl.get(atomId);
  if (li) { li.classList.add('is-line'); }
  const panel = $('rec-line');
  panel.textContent = text;
  panel.hidden = false;
  say(text);
}

/* The plain name of a value of the record, from its name in eCH-0295 (for example Postulate.title.text). */
function headName(slot) {
  const parts = String(slot).split('.');
  const words = [tk('part.', parts[0], null, t('part.affair'))];
  parts.slice(1, -1).forEach(function (p) { if (has('part.' + p)) { words.push(t('part.' + p)); } });
  const camel = parts[parts.length - 1].replace(/_([a-z])/g, function (m, c) { return c.toUpperCase(); });
  const key = camel === 'globalUri' ? 'globalURI' : camel;
  if (has('slot.' + key)) { words.push(t('slot.' + key)); }
  return parts.length > 1 ? words.join(' · ') : String(slot);
}
/* A text value can hold marks for headings and paragraphs. The page shows the text with no marks. */
function plainText(value) {
  if (!/<\/?[a-zA-Z][^<>]*>/.test(value)) { return { text: value, marks: false }; }
  const text = value.replace(/<\/?[a-zA-Z][^<>]*>/g, ' ').replace(/&nbsp;/g, ' ').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&').replace(/\s+/g, ' ').trim();
  return { text: text, marks: true };
}
function renderHead(v, ix) {
  const host = clear($('rec-head'));
  const lang = v.document.language || '';
  (v.document.head || []).forEach(function (hd) {
    const li = el('li', 'head-item');
    const name = headName(hd.ech_slot);
    li.appendChild(el('p', 'head-name', name));
    const last = String(hd.ech_slot).split('.').pop();
    const stored = hd.value === null || hd.value === undefined ? '' : String(hd.value);
    const plain = plainText(stored);
    let value = plain.text;
    if (last === 'affair_type') { value = affairType(value) || value; }
    else if (last === 'text_language') { value = langName(value) || value; }
    else if (last === 'text_type') { value = tk('option.block_slot.', value); }
    const long = value.length > LONG_VALUE;
    const shown = el('p', 'head-value', long ? value.slice(0, LONG_VALUE) + ' …' : (value || t('s4.summary.none')));
    if (last === 'text' && lang && value) { shown.lang = lang; }
    li.appendChild(shown);
    if (long) { li.appendChild(el('p', 'small', t('s4.head.long', { n: stored.length }))); }
    if (plain.marks) { li.appendChild(el('p', 'small', t('s4.head.markup'))); }
    const facts = el('dl', 'summary');
    dlRow(facts, t('s4.head.source'), tk('origin.', hd.origin));
    /* The earlier form of the record compares an export value with the PDF. The new form compares a value of
       the PDF with the export: the part «The eCH-0295 record» shows that comparison. */
    if (!fromPdf(v)) { dlRow(facts, t('s4.head.pdf'), tk('consistency.', hd.pdf_consistency)); }
    li.appendChild(facts);
    li.appendChild(el('p', 'head-slot mono', t('s4.head.slot', { slot: hd.ech_slot })));
    const atoms = hd.atom_ids || [];
    if (atoms.length) {
      const b = el('button', 'btn btn-s', t('s4.card.show'));
      b.type = 'button';
      b.setAttribute('aria-label', t('s4.head.show.label', { slot: name }));
      b.addEventListener('click', function () {
        if (hd.label_id && ix.labels.has(hd.label_id)) { selectLabel(hd.label_id, { scroll: 'page' }); return; }
        S.sel = null;
        setMarks(atoms);
        setCard(null);
        const text = tn('s4.head.marked', atoms.length, { slot: name, n: atoms.length });
        $('rec-marked').textContent = text;
        $('rec-line').hidden = true;
        say(text);
        intoView(ix.lineEl.get(atoms[0]) || $('rec-pages'), 'center');
      });
      li.appendChild(b);
    }
    host.appendChild(li);
  });
}
/* true: code rules read the head values of this record from the PDF (view key head_values.source). */
function fromPdf(v) { return !!(v && v.head_values && v.head_values.source === 'pdf'); }
/* A value of the record as the page shows it: the stored value; for a list value, the word of the list in
   parentheses (the record holds the stored value, not the word). */
function valueShown(x) {
  if (x.field === 'affair_type' && has('affair_type.' + x.value)) {
    return t('values.list_value', { value: x.value, word: affairType(x.value) });
  }
  return x.value;
}
function exportShown(x) {
  return x.field === 'affair_type' && has('affair_type.' + x.export_value)
    ? t('values.list_value', { value: x.export_value, word: affairType(x.export_value) }) : x.export_value;
}
/* The text of a reason of a slot. The state "not searched in this kind of document" is a decision of the rules:
   the text names the kind of the document that the rules chose. */
function kindName(kind) { return tk('doc_kind.', kind || 'unknown'); }
function reasonText(v, s) {
  const hv = v.head_values || {};
  if (s.reason === 'not_in_this_document_type') {
    /* result not_searched: the cascade cuts the entry for this kind of document (slots[].kind) */
    if (s.result === 'not_searched') { return t('slot_reason.not_searched', { kind: kindName(s.kind) }); }
    return t('slot_reason.not_in_this_document_type', { kind: kindName(hv.document_kind) });
  }
  /* reader_scope: the cascade searches the entry, and the rule of the entry does not read this document */
  if (s.reason === 'reader_scope') { return tk('slot_reason.reader_scope.', s.field, null, t('slot_reason.reader_scope')); }
  return tk('slot_reason.', s.reason);
}
/* The word of a state. An address that the converter made is not a value of a register. */
function stateWord(s) { return s.reason === 'minted_iri' ? t('slot_state.minted') : tk('slot_state.', s.state); }
/* The technical details of one value (a value of the record or a weak candidate). */
function valueDetails(ix, s, x, name) {
  const det = el('details', 'card-det');
  const sum = el('summary', '', t('s4.card.details'));
  sum.setAttribute('aria-label', t('values.details.label', { name: name }));
  det.appendChild(sum);
  const dl = el('dl', 'summary');
  dlRow(dl, t('values.detail.tier'), x.tier, 'mono');
  dlRow(dl, t('values.detail.rule'), x.rule_id, 'mono');
  dlRow(dl, t('values.detail.norm'), x.normalisation_rule, 'mono');
  if (x.page !== null && x.char_start !== null && x.char_end !== null) {
    dlRow(dl, t('values.detail.place'), t('values.place', { page: x.page, start: x.char_start, end: x.char_end }));
  }
  dlRow(dl, t('values.detail.slot'), s.slot, 'mono');
  dlRow(dl, t('values.detail.printed'), x.value_printed, 'mono');
  if (x.written) {
    dlRow(dl, t('detail.path'), x.instance_path, 'mono');
    dlRow(dl, t('detail.value'), x.value, 'mono');
  }
  if (x.comparison_value !== null && x.comparison_value !== undefined) { dlRow(dl, t('values.detail.comparison'), x.comparison_value, 'mono'); }
  dlRow(dl, t('values.detail.calibration'), x.calibration_id, 'mono');
  if (x.tier_probability !== null && x.tier_probability !== undefined) { dlRow(dl, t('values.detail.tier_probability'), num(x.tier_probability), 'mono'); }
  det.appendChild(dl);
  return det;
}
/* The probability of a value: the stored word and the stored decimal, then the counts behind the number. */
function valueProbability(ix, x, host) {
  host.appendChild(statusNode(x.value_status, x.probability));
  const cal = x.calibration_id ? ix.calib.get(x.calibration_id) : null;
  if (cal && cal.basis && cal.basis.n !== null && cal.basis.n !== undefined) {
    host.appendChild(el('p', 'small', t('values.prob.basis', { n: cal.basis.n, k: cal.basis.agreed })));
  }
}
/* One row of the record table: an entry of eCH-0295 with its state. */
function echRow(v, ix, s, crossCheck) {
  const x = s.label_id ? ix.value.get(s.label_id) : null;
  const name = tk('pslot.', s.slot);
  const tr = el('tr', 'ech-row st-' + s.state + (x && x.written === false ? ' is-candidate' : ''));
  const th = el('th', 'ech-name', name);
  th.scope = 'row';
  tr.appendChild(th);
  const cell = function (head, cls) { const td = el('td', cls); td.setAttribute('data-th', head); tr.appendChild(td); return td; };
  const state = cell(t('values.col.state'), 'ech-state');
  state.appendChild(el('p', 'ech-state-word', stateWord(s)));
  const prob = cell(t('values.col.probability'), 'ech-prob');
  const showButton = function () {
    const b = el('button', 'btn btn-s ech-show', t('s4.card.show'));
    b.type = 'button';
    b.setAttribute('aria-label', t('values.show.label', { name: name }));
    b.addEventListener('click', function () {
      if (S.sel === x.label_id) { clearSelection(false); return; }
      selectLabel(x.label_id, { scroll: 'page' });
    });
    return b;
  };
  if (x && x.written !== false) {
    /* a value of the record. If its form in the record differs from the printed wording (a list value, a
       calendar day, a wording on two lines), the row shows the two strings and names the rule. */
    if (x.differs_from_printed) {
      const both = el('p', 'ech-value', t('values.record_value', { printed: x.value_printed, value: valueShown(x) }));
      state.appendChild(both);
      state.appendChild(el('p', 'small', tk('values.form.', x.value_form)));
    } else {
      const printed = el('p', 'ech-value', x.value);
      if (v.document.language) { printed.lang = v.document.language; }
      state.appendChild(printed);
    }
    state.appendChild(showButton());
    state.appendChild(valueDetails(ix, s, x, name));
    valueProbability(ix, x, prob);
    if (x.in_sample === true) { prob.appendChild(el('p', 'small', t('values.prob.in_sample'))); }
    ix.rowEl.set(x.label_id, tr);
  } else if (x) {
    /* a candidate: the rules found it, and it is NOT in the record. weak: a rule tier below the floor.
       addressee: the body that a proposal addresses; no response step is searched in that kind of document. */
    const addressee = x.candidate === 'addressee';
    state.appendChild(el('p', 'small', reasonText(v, s)));
    const cand = el('p', 'ech-value ech-candidate', addressee ? t('values.addressee', { value: x.value_printed }) : t('values.candidate', { value: x.value_printed }));
    state.appendChild(cand);
    state.appendChild(showButton());
    state.appendChild(valueDetails(ix, s, x, name));
    valueProbability(ix, x, prob);
    const floor = v.head_values && v.head_values.floor ? v.head_values.floor.threshold : null;
    if (addressee) { prob.appendChild(el('p', 'small', t('values.addressee.prob'))); }
    else if (floor !== null && floor !== undefined) { prob.appendChild(el('p', 'small', t('values.candidate.floor', { floor: num(floor) }))); }
    ix.rowEl.set(x.label_id, tr);
  } else if (s.reason === 'text_blocks') {
    const n = (v.document.text_blocks || []).filter(function (tb) { return String(tb.ech_slot) === s.slot; }).length;
    state.appendChild(el('p', 'small', n ? tn('values.texts', n, { n: n }) : reasonText(v, s)));
    const b = el('button', 'btn btn-s', t('values.texts.goto'));
    b.type = 'button';
    b.addEventListener('click', function () { const h = $('h-rec-labels'); h.focus({ preventScroll: true }); intoView(h, 'start'); });
    state.appendChild(b);
    prob.appendChild(el('p', 'small', t('values.texts.prob')));
  } else {
    state.appendChild(el('p', 'small', reasonText(v, s)));
    prob.appendChild(el('p', 'st-none', t('values.no_probability')));
  }
  if (crossCheck) {
    const ex = cell(t('values.col.export'), 'ech-export');
    if (x && x.written !== false) {
      const tolerant = x.export_check === 'equal_to_export' && x.export_match === 'after_normalisation';
      ex.appendChild(el('p', 'ech-check ck-' + x.export_check, tolerant ? t('export_match.after_normalisation') : tk('export_check.', x.export_check)));
      if (x.export_value !== null && x.export_value !== undefined && (x.export_check === 'differs_from_export' || tolerant)) {
        ex.appendChild(el('p', 'small', t('values.export_value', { value: exportShown(x) })));
      }
      /* equal by the comparison rule, with another wording: the cell names the rule */
      if (tolerant) { ex.appendChild(el('p', 'small', tk('export_rule.', x.field, null, t('export_rule.other')))); }
    } else if (s.export_has_value === true || s.export_has_value === false) {
      ex.appendChild(el('p', 'small', t(s.export_has_value ? 'values.export_has_value.yes' : 'values.export_has_value.no')));
    } else {
      ex.appendChild(el('p', 'st-none', tk('export_check.', 'not_compared')));
    }
  }
  return tr;
}
/* The cascade of ONE record in plain words (view key head_values.cascade): the kind of the document, the affair
   type, the steps that this kind can state and the state of each of the 7 entries that code rules read. */
function cascadeEntry(v, ix, c, e) {
  const li = el('li', 'cascade-entry ce-' + e.state);
  const name = tk('pslot.', e.slot);
  li.appendChild(el('span', 'cascade-name', name));
  const body = el('span', 'cascade-state');
  const x = e.label_id ? ix.value.get(e.label_id) : null;
  const kind = kindName(c.kind);
  if (x && e.state === 'read_from_pdf') {
    body.appendChild(el('span', 'cascade-word', t('cascade.state.read_from_pdf')));
    const val = el('span', 'cascade-value', valueShown(x));
    if (v.document.language && x.field !== 'affair_type') { val.lang = v.document.language; }
    body.appendChild(val);
    body.appendChild(el('span', 'cascade-prob', t('cascade.prob', { p: num(x.probability), word: tk('status.', x.value_status) })));
  } else if (x && e.state === 'weak_candidate') {
    body.appendChild(el('span', 'cascade-word', t('cascade.state.weak_candidate')));
    body.appendChild(el('span', 'cascade-value is-candidate', x.value_printed));
    body.appendChild(el('span', 'cascade-prob', t('cascade.prob', { p: num(x.probability), word: tk('status.', x.value_status) })));
  } else if (x && e.state === 'addressee_candidate') {
    body.appendChild(el('span', 'cascade-word', t('cascade.state.not_searched', { kind: kind })));
    body.appendChild(el('span', 'cascade-note', t('cascade.state.addressee_candidate')));
    body.appendChild(el('span', 'cascade-value is-candidate', x.value_printed));
  } else if (e.state === 'not_searched') {
    body.appendChild(el('span', 'cascade-word', t('cascade.state.not_searched', { kind: kind })));
  } else if (e.state === 'reader_scope') {
    /* searched, and the rule of the entry does not read this document: a result of a search, with its cause */
    body.appendChild(el('span', 'cascade-word', t('cascade.state.reader_scope')));
    body.appendChild(el('span', 'cascade-note', tk('slot_reason.reader_scope.', e.field, null, t('slot_reason.reader_scope'))));
  } else {
    body.appendChild(el('span', 'cascade-word', t('cascade.state.not_found_in_pdf')));
  }
  if (x) {
    const b = el('button', 'btn btn-s cascade-show', t('s4.card.show'));
    b.type = 'button';
    b.setAttribute('aria-label', t('values.show.label', { name: name }));
    b.addEventListener('click', function () {
      if (S.sel === x.label_id) { clearSelection(false); return; }
      selectLabel(x.label_id, { scroll: 'page' });
    });
    body.appendChild(b);
  }
  li.appendChild(body);
  return li;
}
function renderCascade(v, ix) {
  const host = clear($('rec-cascade'));
  const c = v.head_values ? v.head_values.cascade : null;
  host.hidden = !c;
  if (!c) { return; }
  const h = el('h3', 'cascade-title', t('cascade.title'));
  h.id = 'h-rec-cascade';
  host.appendChild(h);
  host.appendChild(el('p', 'cascade-idea', t('cascade.idea')));
  const dl = el('dl', 'summary cascade-head');
  dlRow(dl, t('cascade.kind'), c.kind ? kindName(c.kind) : t('cascade.kind.unknown'));
  /* where the kind comes from: the rule chain, or rule V5 (the rule chain made no decision; 2 facts of the PDF decide) */
  const kf = c.kind_facts;
  if (c.kind) {
    const from = c.kind_from === 'rule_v5' ? t('cascade.kind.from.rule_v5')
      : (kf ? t('cascade.kind.from.no_decision') : tk('cascade.kind.from.', c.kind_from));
    dlRow(dl, t('cascade.kind.from'), from);
  }
  if (kf) {
    const word = kf.type_word ? t('cascade.kind.fact.type.yes', { value: kf.type_word, word: affairType(kf.type_word) || kf.type_word })
      : t('cascade.kind.fact.type.no');
    dlRow(dl, t('cascade.kind.fact.type'), word);
    /* reader version 4: only an explicit response cue gives the kind response; another sign of the executive counts with a type word only */
    dlRow(dl, t('cascade.kind.fact.response'), kf.response_cue ? t('cascade.kind.fact.response.yes')
      : (kf.response_sign ? t('cascade.kind.fact.response.sign') : t('cascade.kind.fact.response.no')));
    dlRow(dl, t('cascade.kind.fact.result'), kf.changed
      ? t('cascade.kind.fact.result.changed', { kind: kindName(c.kind), before: kindName(kf.kind_of_the_rule_chain) })
      : (kf.type_word === 'draft_decree' ? t('cascade.kind.fact.result.draft', { kind: kindName(c.kind) })
        : (kf.response_sign ? t('cascade.kind.fact.result.sign', { kind: kindName(c.kind) })
          : t('cascade.kind.fact.result.same', { kind: kindName(c.kind) }))));
  }
  const type = c.affair_type && c.affair_type !== 'none'
    ? t('cascade.type.value', { value: c.affair_type, word: affairType(c.affair_type) || c.affair_type }) : t('cascade.type.none');
  dlRow(dl, t('cascade.type'), type);
  host.appendChild(dl);
  /* finding S3-03: signs of a response in a document of the kind proposal; the kind does not change */
  const signs = (v.notices || []).filter(function (n) { return n.code === 'response_signs'; })[0];
  if (signs) { host.appendChild(el('p', 'cascade-warn', noticeText(signs, v))); }
  const stepOf = {};
  (c.steps || []).forEach(function (s) { stepOf[s.step] = s; });
  const textOf = {};
  (c.texts || []).forEach(function (x) { textOf[x.step] = x; });
  [['affair', 'Affair'], ['submission', 'Submission'], ['response', 'ResponseStep']].forEach(function (g) {
    const box = el('div', 'cascade-step');
    const st = stepOf[g[0]];
    const can = g[0] === 'affair' ? t('cascade.step.affair') : (st && st.applies ? t('cascade.step.applies') : t('cascade.step.not'));
    const head = el('h4', 'cascade-step-name', tk('pgroup.', g[1]));
    box.appendChild(head);
    box.appendChild(el('p', 'small', can));
    const ul = el('ul', 'cascade-list');
    (c.entries || []).filter(function (e) { return e.group === g[0]; }).forEach(function (e) { ul.appendChild(cascadeEntry(v, ix, c, e)); });
    const tx = textOf[g[0]];
    if (tx && tx.slot) {
      const li = el('li', 'cascade-entry');
      li.appendChild(el('span', 'cascade-name', tk('pslot.', tx.slot)));
      const body = el('span', 'cascade-state');
      const text = tx.blocks ? tn('cascade.texts', tx.blocks, { n: tx.blocks })
        : (tx.cut || !tx.applies ? t('cascade.state.not_searched', { kind: kindName(c.kind) }) : t('cascade.texts.none'));
      body.appendChild(el('span', 'cascade-word', text));
      /* a text block whose text slot the cascade does not give to the kind is not written to the eCH-0295 part */
      if (tx.not_written) { body.appendChild(el('span', 'cascade-note', tn('cascade.texts.not_written', tx.not_written, { n: tx.not_written }))); }
      /* finding V5-05: rule V5 does not change the block roles; the answer of the executive can be in the submitted text */
      if (g[0] === 'submission' && tx.blocks && c.kind_from === 'rule_v5' && c.kind === 'combined') {
        body.appendChild(el('span', 'cascade-note', tn('cascade.texts.v5_roles', tx.blocks, { n: tx.blocks })));
      }
      li.appendChild(body);
      ul.appendChild(li);
    }
    box.appendChild(ul);
    host.appendChild(box);
  });
  if (c.text_blocks_not_written) { host.appendChild(el('p', 'small', tn('cascade.texts.cut', c.text_blocks_not_written, { n: c.text_blocks_not_written }))); }
  host.appendChild(el('p', 'small', t('cascade.register', { n: c.register_only })));
  const det = el('details', 'cascade-all');
  det.appendChild(el('summary', '', t('cascade.all')));
  det.appendChild(el('p', 'small', t('cascade.all.lead')));
  const ol = el('ol', 'cascade-stages');
  ol.start = 0;
  [0, 1, 2, 3, 4].forEach(function (n) { ol.appendChild(el('li', '', t('cascade.stage.' + n))); });
  det.appendChild(ol);
  if (c.version) { det.appendChild(el('p', 'small mono', t('cascade.version', { version: c.version, reader: c.reader || '' }))); }
  host.appendChild(det);
}
/* The eCH-0295 record as three tables: the affair and its two steps. Each entry has one of 4 states. */
function renderEch(v, ix) {
  const part = $('rec-record-part');
  const host = clear($('rec-record'));
  const on = fromPdf(v) && Array.isArray(v.slots) && v.slots.length > 0;
  part.hidden = !on;
  $('goto-record').hidden = !on;
  if (!on) { return; }
  const hv = v.head_values;
  const crossCheck = hv.cross_check === true;
  $('rec-record-lead').textContent = t(crossCheck ? 's4.record.lead.check' : 's4.record.lead.no_check');
  renderCascade(v, ix);
  $('rec-record-measured').textContent = t('s4.record.measured');
  const gaps = (hv.i95_gaps || []).map(function (g) { return tk('pslot.Affair.', g); });
  $('rec-record-conf').textContent = gaps.length ? t('s4.record.gaps', { slots: gaps.join(', ') }) : t('s4.record.complete');
  const bySlot = new Map();
  v.slots.forEach(function (s) { bySlot.set(s.slot, s); });
  ECH_GROUPS.forEach(function (grp) {
    const box = el('section', 'ech-group');
    const step = grp.step ? bySlot.get(grp.step) : null;
    const title = tk('pgroup.', grp.cls);
    const h = el('h3', 'ech-group-name', step ? t('s4.record.step', { name: title, state: stateWord(step) }) : title);
    h.id = 'ech-h-' + grp.cls;
    box.setAttribute('aria-labelledby', h.id);
    box.appendChild(h);
    if (step) { box.appendChild(el('p', 'small', reasonText(v, step))); }
    const table = el('table', 'ech-table');
    table.setAttribute('aria-labelledby', h.id);
    const head = el('tr');
    [t('values.col.entry'), t('values.col.state'), t('values.col.probability')].concat(crossCheck ? [t('values.col.export')] : []).forEach(function (text) {
      const th = el('th', '', text);
      th.scope = 'col';
      head.appendChild(th);
    });
    const thead = el('thead');
    thead.appendChild(head);
    table.appendChild(thead);
    const body = el('tbody');
    grp.rows.forEach(function (name) { const s = bySlot.get(name); if (s) { body.appendChild(echRow(v, ix, s, crossCheck)); } });
    table.appendChild(body);
    box.appendChild(table);
    const used = new Set(grp.rows.concat(grp.step ? [grp.step] : []));
    const others = v.slots.filter(function (s) {
      return !used.has(s.slot) && s.slot.indexOf(grp.cls + '.') === 0 && !(grp.cls === 'Affair' && (s.slot === 'Affair.submission' || s.slot === 'Affair.response_steps'));
    });
    if (others.length) {
      const det = el('details', 'ech-other');
      det.appendChild(el('summary', '', t('values.other', { n: others.length })));
      const ul = el('ul', 'ech-other-list');
      others.forEach(function (s) {
        const li = el('li');
        li.appendChild(el('span', 'ech-other-name', tk('pslot.', s.slot)));
        li.appendChild(el('span', 'ech-other-state', stateWord(s)));
        li.appendChild(el('span', 'small', reasonText(v, s)));
        ul.appendChild(li);
      });
      det.appendChild(ul);
      box.appendChild(det);
    }
    host.appendChild(box);
  });
}
function renderChecks(v) {
  const checks = v.checks || [];
  const passed = checks.filter(function (c) { return c.state === 'passed'; }).length;
  const skipped = checks.filter(function (c) { return c.state === 'skipped'; }).map(function (c) { return tk('check.', c.id); });
  $('rec-checks-line').textContent = skipped.length
    ? t('s4.checks', { p: passed, t: checks.length, skipped: skipped.join(', ') })
    : t('s4.checks.all_run', { p: passed, t: checks.length });
  const list = clear($('rec-checks'));
  checks.forEach(function (c) {
    const li = el('li', 'check is-' + c.state);
    const mark = el('span', 'check-mark');
    mark.setAttribute('aria-hidden', 'true');
    li.appendChild(mark);
    li.appendChild(el('span', 'check-name', has('check.' + c.id) ? t('s4.checks.id', { name: t('check.' + c.id), id: c.id }) : c.id));
    let words = tk('check.state.', c.state);
    if (c.reason) { words += ': ' + tk('check.reason.', c.reason); }
    li.appendChild(el('span', 'check-state', words));
    list.appendChild(li);
  });
}
function fileItem(title, note, url, name, f) {
  const li = el('li', 'dl-item');
  const a = el('a', 'dl-link', title);
  a.href = url;
  a.setAttribute('download', name);
  li.appendChild(a);
  const meta = [name];
  if (f && typeof f.bytes === 'number') { meta.push(t('dl.size', { kb: round1(f.bytes / 1024) })); }
  li.appendChild(el('span', 'dl-meta mono', meta.join(' · ')));
  if (note) { li.appendChild(el('p', 'dl-note', note)); }
  if (f && f.sha256 && !note) { li.appendChild(el('p', 'dl-sha mono', t('dl.sha', { sha: f.sha256 }))); }
  return li;
}
function renderDownloads(v) {
  const main = clear($('rec-downloads'));
  const other = clear($('rec-files'));
  const titles = {
    gesamt_trig: ['dl.trig', 'dl.trig.note'],
    ech_ttl: ['dl.ttl', 'dl.ttl.note'],
    gesamt_rdfxml: ['dl.rdfxml', 'dl.rdfxml.note'],
    ech_rdfxml: ['dl.rdfxml.ech', 'dl.rdfxml.ech.note']
  };
  (v.files || []).forEach(function (f) {
    const url = f.url + '?download=1';
    if (titles[f.role]) {
      main.appendChild(fileItem(t(titles[f.role][0]), t(titles[f.role][1]), url, f.name, f));
    } else {
      other.appendChild(fileItem(tk('dl.role.', f.role, null, f.name), '', url, f.name, f));
    }
  });
  const zip = 'parlpdfech-' + v.record_id + '.zip';
  main.appendChild(fileItem(t('dl.zip'), t('dl.zip.note'), '/api/records/' + encodeURIComponent(v.record_id) + '/bundle.zip', zip, null));
}
/* The machine field run.status is not shown on the page (CONTRACT.md chapter 7.5). The working names of the
   project (the name of the converter variant and of its mode) are not shown: the mode shows in the words of the page. */
function renderTech(v) {
  const dl = clear($('rec-tech'));
  dlRow(dl, t('tech.record_id'), v.record_id, 'mono');
  dlRow(dl, t('tech.generated'), v.run.generated_at, 'mono');
  dlRow(dl, t('tech.mode'), tk('mode.name.', v.run.apertus === 'stored' ? 'auto' : 'rules'));
  dlRow(dl, t('tech.profile'), v.run.profile, 'mono');
  dlRow(dl, t('tech.model'), v.run.apertus === 'stored' ? v.run.model : null, 'mono');
  dlRow(dl, t('tech.pdf_sha'), v.document.pdf_sha256, 'mono');
  dlRow(dl, t('tech.source_iri'), v.document.source_iri, 'mono');
  dlRow(dl, t('tech.record_iri'), v.document.record_iri, 'mono');
  dlRow(dl, t('tech.triples'), v.counts.triples ? v.counts.triples.union : null);
}
function resetDelete() {
  $('rec-delete-ask').hidden = true;
  $('rec-delete').setAttribute('aria-expanded', 'false');
  $('rec-delete-yes').disabled = false;
}
async function deleteRecord() {
  const id = S.viewId;
  if (!id || readOnly()) { return; }
  $('rec-delete-yes').disabled = true;
  try {
    await api.remove(id);
  } catch (e) {
    showCase(e, function () { go('#/record/' + encodeURIComponent(id)); });
    return;
  }
  unmountPanel();
  S.view = null;
  S.viewId = null;
  S.ix = null;
  S.sel = null;
  go('#/');
  say(t('s4.deleted'));
}

/* ---------- the RDF panel (WebAssembly); the app works with no panel ---------- */
function panelAbsent(host) {
  clear(host);
  const h = el('h2', '', t('rdf.title'));
  h.id = 'h-rdf-panel';
  host.setAttribute('aria-labelledby', h.id);
  host.appendChild(h);
  host.appendChild(el('p', '', t('rdf.absent')));
  host.hidden = false;
  $('goto-rdf').hidden = false;
}
function panelReady() {
  if (window.ParlRdfPanel) { return Promise.resolve(); }
  return new Promise(function (resolve, reject) {
    const timer = setTimeout(function () { reject(new Error('panel')); }, 4000);
    document.addEventListener('parl-rdfpanel-ready', function () { clearTimeout(timer); resolve(); }, { once: true });
  });
}
async function mountPanel() {
  const host = $('rdf-panel');
  const run = ++S.panelRun;
  const v = S.view;
  const file = function (role) { return (v.files || []).filter(function (f) { return f.role === role; })[0]; };
  try {
    if (!S.panelLoad) { S.panelLoad = import('./rdfpanel.js'); }
    await S.panelLoad;
    await panelReady();
    if (run !== S.panelRun || S.view !== v) { return; }
    const trig = file('gesamt_trig');
    const manifest = file('manifest');
    if (!trig || !manifest || !window.ParlRdfPanel || typeof window.ParlRdfPanel.mount !== 'function') { throw new Error('panel'); }
    const result = await window.ParlRdfPanel.mount(host, { trigUrl: trig.url, manifestUrl: manifest.url, lang: S.lang,
      /* the example query for the head values needs a record with an affair: a record with values from the
         PDF has one; the earlier form has one only with an export record */
      hasExport: fromPdf(v) || v.document.has_export !== false });
    if (run !== S.panelRun) { return; }
    if (!result || result.ok !== true) { throw new Error('panel'); }
    host.hidden = false;
    $('goto-rdf').hidden = false;
  } catch (e) {
    if (run === S.panelRun) { panelAbsent(host); }
  }
}
function unmountPanel() {
  S.panelRun += 1;
  const host = $('rdf-panel');
  try {
    if (window.ParlRdfPanel && typeof window.ParlRdfPanel.unmount === 'function') { window.ParlRdfPanel.unmount(host); }
  } catch (e) { /* the panel is an addition */ }
  clear(host);
  host.hidden = true;
  $('goto-rdf').hidden = true;
}

/* ---------- the result view: the PDF, the values with their probability, the RDF (route #/view/<record_id>) ---------- */
function fileOf(v, role) { return (v.files || []).find(function (f) { return f.role === role; }) || null; }
function writtenValues(v) {
  return (v.values || []).filter(function (x) { return x.written; }).sort(function (a, b) {
    return FIELD_ORDER.indexOf(a.field) - FIELD_ORDER.indexOf(b.field);
  });
}
function fieldName(field) { return tk('value.', field); }
async function showView(id, opts) {
  if (!RECORD_RE.test(id)) { showCase(localCase('no_record', ['sample', 'start']), null); return; }
  if (!(await loadView(id, '#/view/'))) { return; }
  renderView();
  show('view', opts.keepFocus);
  loadNumbers().then(function () { if (S.screen === 'view' && S.viewId === id) { renderViewRows(S.view); applyViewSel(null); } });
  /* the title of a sample (for a record with no title from the PDF) comes from the list of the samples */
  if (/^s-/.test(id) && !S.samples.length) {
    api.samples().then(function (data) {
      S.samples = (data && data.samples) || [];
      if (S.screen === 'view' && S.viewId === id) { renderViewHead(S.view); setTitle('view'); }
    }, function () { /* the heading keeps its text */ });
  }
  loadTtl(S.view);
}
/* The sample of a record id (s-<doc> or s-<doc>-rules), if the list of the samples has it. */
function sampleOf(id) {
  const m = /^s-([0-9]+)(-rules)?$/.exec(id);
  return m ? S.samples.find(function (s) { return String(s.doc_id) === m[1]; }) || null : null;
}
/* The heading of the result view. A title that the rules read from the PDF is the heading. With no such title:
   the title of OpenParlData for a sample, or the weak candidate, each with a line that says what it is. */
function renderViewHead(v) {
  const d = v.document;
  const h = $('h-view');
  const note = $('view-title-note');
  const tx = (v.values || []).find(function (x) { return x.field === 'title'; }) || null;
  const weak = tx && !tx.written ? tx : null;
  const sample = sampleOf(v.record_id);
  let words = d.title;
  const lines = [];
  if (!words && sample && sample.title) {
    words = sample.title;
    lines.push(t('view.title.sample'));
    if (weak) { lines.push(t('view.title.weak', { p: num(weak.probability) })); }
  } else if (!words && weak) {
    words = weak.value;
    lines.push(t('view.title.weak', { p: num(weak.probability) }));
  }
  h.textContent = words || t('view.no_title');
  if (d.language) { h.lang = d.language; } else { h.removeAttribute('lang'); }
  note.textContent = lines.join(' ');
  note.hidden = !lines.length;
}
function renderView() {
  const v = S.view;
  const d = v.document;
  const id = v.record_id;
  $('view-kicker').textContent = t('view.kicker', { mode: t(v.run.apertus === 'stored' ? 'mode.name.auto' : 'mode.name.rules') });
  renderViewHead(v);
  const facts = [nameId(d.parliament_name, d.parliament), affairType(d.affair_type), langName(d.language),
    v.doc_id ? t('s1.card.doc', { doc: v.doc_id }) : null].filter(Boolean);
  $('view-facts').textContent = facts.join(' · ');
  /* where the values come from: code rules; Apertus gives only the labels of the text blocks of a sample */
  const own = v.run.origin === 'new';
  let source = t('view.source.rules');
  if (v.run.apertus === 'stored') { source = t('view.source.auto'); } else if (own) { source = t('view.source.own'); }
  $('view-source').textContent = source;
  $('view-tech').href = '#/record/' + encodeURIComponent(id);
  $('view-pdf-more').href = '#/record/' + encodeURIComponent(id);
  $('view-rdf-more').href = '#/record/' + encodeURIComponent(id);
  /* the other mode of a sample, if its result is ready */
  const other = $('view-other-mode');
  const m = /^s-([0-9]+)(-rules)?$/.exec(id);
  const sample = sampleOf(id);
  const otherMode = m && m[2] ? 'auto' : 'rules';
  other.hidden = !(sample && sample.ready && sample.ready[otherMode]);
  if (!other.hidden) {
    other.href = '#/view/' + encodeURIComponent('s-' + m[1] + (otherMode === 'rules' ? '-rules' : ''));
    other.textContent = t('view.other', { mode: t(otherMode === 'auto' ? 'mode.name.auto' : 'mode.name.rules') });
  }
  $('view-none').hidden = writtenValues(v).length > 0;
  const pdf = fileOf(v, 'source_pdf');
  $('view-pdf-dl').hidden = !pdf;
  if (pdf) { $('view-pdf-dl').href = pdf.url + '?download=1'; }
  renderViewPages(v);
  renderViewRows(v);
  renderTtl();
  applyViewSel(null);
}
/* The box of a value on the page: the part of each line that its span covers (the same estimate as the
   technical view: the share of the characters of the line). With no span: the frames of its lines. */
function valueRects(v, x) {
  const lines = new Map();
  v.pages.forEach(function (p) { p.lines.forEach(function (l) { lines.set(l.atom_id, { l: l, page: p.number }); }); });
  const out = [];
  const spans = (x.spans || []).length ? x.spans : (x.atom_ids || []).map(function (a) { return { atom_id: a, start: null, end: null }; });
  spans.forEach(function (sp) {
    const hit = lines.get(sp.atom_id);
    if (!hit) { return; }
    const f = hit.l.frame;
    const len = (hit.l.text || '').length;
    let x1 = f[0];
    let x2 = f[2];
    if (len && sp.start !== null && sp.end !== null && sp.end > sp.start) {
      const a = Math.max(0, Math.min(sp.start, len)) / len;
      const b = Math.max(0, Math.min(sp.end, len)) / len;
      x1 = f[0] + a * (f[2] - f[0]);
      x2 = f[0] + b * (f[2] - f[0]);
    }
    out.push({ page: hit.page, x: x1 - 2, y: f[1] - 2, w: Math.max(x2 - x1, 2) + 4, h: Math.max(f[3] - f[1], 2) + 4 });
  });
  return out;
}
function renderViewPages(v) {
  const host = clear($('view-pages'));
  const images = v.pages.length > 0 && v.pages.every(function (p) { return Boolean(p.image); });
  $('view-pdf-note').textContent = t(images ? 'view.pdf.image' : 'view.pdf.drawn');
  const lang = v.document.language || '';
  const blocks = new Map();
  v.pages.forEach(function (p) {
    p.lines.forEach(function (l) {
      const key = p.number + '|' + l.block_id;
      const b = blocks.get(key) || { page: p.number, x1: Infinity, y1: Infinity, x2: -Infinity, y2: -Infinity };
      b.x1 = Math.min(b.x1, l.frame[0]); b.y1 = Math.min(b.y1, l.frame[1]);
      b.x2 = Math.max(b.x2, l.frame[2]); b.y2 = Math.max(b.y2, l.frame[3]);
      blocks.set(key, b);
    });
  });
  const values = writtenValues(v);
  v.pages.forEach(function (p) {
    const fig = el('figure', 'vpg');
    const caption = t('view.page', { page: p.number, n: v.pages.length });
    const s = svg('svg', { class: 'vpgs', viewBox: '0 0 ' + p.width + ' ' + p.height, role: 'group', 'aria-label': caption });
    if (p.image) {
      s.appendChild(svg('rect', { class: 'pg-paper', x: 0, y: 0, width: p.width, height: p.height }));
      s.appendChild(svg('image', { href: p.image, x: 0, y: 0, width: p.width, height: p.height, preserveAspectRatio: 'none', 'aria-hidden': 'true' }));
    } else {
      /* the fall-back: the lines of the text layer, drawn at their places */
      s.appendChild(svg('rect', { class: 'pg-paper', x: 0, y: 0, width: p.width, height: p.height }));
      const g = svg('g', { class: 'vpg-lines', 'aria-hidden': 'true' });
      if (lang) { g.setAttribute('lang', lang); }
      p.lines.forEach(function (a) {
        if (!a.text) { return; }
        const bh = Math.max(a.frame[3] - a.frame[1], 1);
        const bw = Math.max(a.frame[2] - a.frame[0], 1);
        const fs = Math.max(3, Math.min(bh * 0.8, 14));
        const tx = svg('text', { x: a.frame[0], y: (a.frame[3] - bh * 0.22).toFixed(2), 'font-size': fs.toFixed(2),
          textLength: bw.toFixed(2), lengthAdjust: 'spacingAndGlyphs' });
        tx.textContent = a.text;
        g.appendChild(tx);
      });
      s.appendChild(g);
    }
    blocks.forEach(function (b) {
      if (b.page !== p.number) { return; }
      s.appendChild(svg('rect', { class: 'blk', x: (b.x1 - 3).toFixed(2), y: (b.y1 - 3).toFixed(2),
        width: (b.x2 - b.x1 + 6).toFixed(2), height: (b.y2 - b.y1 + 6).toFixed(2), 'aria-hidden': 'true' }));
    });
    values.forEach(function (x) {
      const rects = valueRects(v, x).filter(function (r) { return r.page === p.number; });
      if (!rects.length) { return; }
      const g = svg('g', { class: 'vbox ' + colourOf(x.field), 'data-f': x.field, role: 'button', tabindex: 0,
        'aria-label': t('view.box.aria', { name: fieldName(x.field), value: x.value_printed, page: p.number }) });
      rects.forEach(function (r) {
        g.appendChild(svg('rect', { x: r.x.toFixed(2), y: r.y.toFixed(2), width: r.w.toFixed(2), height: r.h.toFixed(2), rx: 2 }));
      });
      s.appendChild(g);
    });
    fig.appendChild(s);
    const cap = el('figcaption', '', caption);
    if (p.image) {
      const full = el('a', 'vpg-full', t('view.pdf.full', { page: p.number }));
      full.href = p.image;
      full.target = '_blank';
      full.rel = 'noopener';
      cap.appendChild(document.createTextNode(' · '));
      cap.appendChild(full);
    }
    fig.appendChild(cap);
    host.appendChild(fig);
  });
}
/* The few development documents below which a stored number is not stable (rule G6 item 14: 30 units). */
const FEW_DOCS = 30;
function calibrationOf(v, id) {
  return id ? (v.calibrations || []).find(function (c) { return c.id === id; }) || null : null;
}
/* The line of a value below its row: the documents behind the number, the fixed run, the OpenParlData value. */
function rowFacts(v, x, run) {
  const td = el('td', 'vrow-facts small');
  td.colSpan = 4;
  const cal = calibrationOf(v, x.calibration_id);
  const basis = cal && cal.basis && cal.basis.n !== null && cal.basis.n !== undefined ? cal.basis : null;
  if (basis) {
    const few = Number(basis.n) < FEW_DOCS;
    let words = x.in_sample ? t('view.basis.in', { k: basis.agreed, n: basis.n }) : t('view.basis', { k: basis.agreed, n: basis.n });
    if (few) { words += ' ' + t('view.basis.few'); }
    td.appendChild(el('span', 'vf' + (few ? ' vf-few' : ''), words));
  }
  if (run && run.given) {
    td.appendChild(el('span', 'vf', t('view.run_precision', { p: pct(run.precision), k: Number(run.correct), n: Number(run.given) })));
  }
  const check = x.export_check;
  if (check === 'equal_to_export' || check === 'differs_from_export') {
    const tolerant = check === 'equal_to_export' && x.export_match === 'after_normalisation';
    let words = t('view.export', { result: tolerant ? t('export_match.after_normalisation') : tk('export_check.', check) });
    if (x.export_value !== null && x.export_value !== undefined && (check === 'differs_from_export' || tolerant)) {
      words += ' · ' + t('values.export_value', { value: exportShown(x) });
    }
    td.appendChild(el('span', 'vf vf-' + check, words));
  } else if (check === 'no_export_value') {
    td.appendChild(el('span', 'vf', t('export_check.no_export_value')));
  }
  return td;
}
function renderViewRows(v) {
  const body = clear($('view-rows'));
  const n = S.numbers;
  const id = v.record_id;
  writtenValues(v).forEach(function (x) {
    const name = fieldName(x.field);
    const tr = el('tr', 'vrow ' + colourOf(x.field));
    tr.setAttribute('data-f', x.field);
    tr.tabIndex = 0;
    tr.setAttribute('aria-label', t('view.row.aria', { name: name, value: x.value_printed }));
    const th = el('th', 'vrow-name');
    th.setAttribute('scope', 'row');
    th.appendChild(el('span', 'swatch', ''));
    th.lastChild.setAttribute('aria-hidden', 'true');
    th.appendChild(document.createTextNode(name));
    tr.appendChild(th);
    const val = el('td', 'vrow-value');
    const shown = el('span', 'vrow-printed', x.value_printed);
    if (v.document.language) { shown.lang = v.document.language; }
    val.appendChild(shown);
    if (x.differs_from_printed) { val.appendChild(el('span', 'vrow-record small', t('view.in_record', { value: valueShown(x) }))); }
    const more = el('a', 'vrow-more small', t('view.row.more'));
    more.href = '#/record/' + encodeURIComponent(id) + '/label/' + encodeURIComponent(x.label_id);
    more.setAttribute('aria-label', t('view.row.more.label', { name: name }));
    val.appendChild(more);
    tr.appendChild(val);
    const prob = el('td', 'vrow-prob');
    const line = el('span', 'vrow-pline');
    const cal = calibrationOf(v, x.calibration_id);
    const few = !!(cal && cal.basis && Number(cal.basis.n) < FEW_DOCS);
    line.appendChild(bar(x.probability, 'prob-bar' + (few ? ' is-few' : '')));
    const num1 = el('span', 'n', num(x.probability));
    num1.setAttribute('translate', 'no');
    line.appendChild(num1);
    line.appendChild(el('span', 'st st-' + x.value_status, tk('status.', x.value_status)));
    prob.appendChild(line);
    tr.appendChild(prob);
    tr.appendChild(el('td', 'vrow-page n', x.page === null || x.page === undefined ? '' : String(x.page)));
    body.appendChild(tr);
    /* the facts of the value on one line below the row; a click on it selects the value too */
    const sub = el('tr', 'vrow-sub ' + colourOf(x.field));
    sub.setAttribute('data-f', x.field);
    sub.appendChild(rowFacts(v, x, n && n.fields ? n.fields[x.field] : null));
    body.appendChild(sub);
  });
  /* the fields that were searched and not found, a weak candidate, the body that a proposal addresses; one line
     for the fields that the role of the document does not search */
  const hv = v.head_values || {};
  const cascade = hv.cascade || null;
  const entries = cascade && Array.isArray(cascade.entries) ? cascade.entries.slice() : [];
  entries.sort(function (a, b) { return FIELD_ORDER.indexOf(a.field) - FIELD_ORDER.indexOf(b.field); });
  entries.forEach(function (e) {
    if (e.state !== 'not_found_in_pdf' && e.state !== 'weak_candidate' && e.state !== 'addressee_candidate') { return; }
    const tr = el('tr', 'vrow-miss');
    const th = el('th', 'vrow-name', fieldName(e.field));
    th.setAttribute('scope', 'row');
    tr.appendChild(th);
    let words = t('view.miss.not_found');
    const cand = e.state !== 'not_found_in_pdf' ? (v.values || []).find(function (x) { return x.label_id === e.label_id; }) : null;
    if (cand && e.state === 'weak_candidate') { words = t('view.miss.weak', { value: cand.value_printed, p: num(cand.probability) }); }
    if (cand && e.state === 'addressee_candidate') { words = t('view.miss.addressee', { value: cand.value_printed, p: num(cand.probability) }); }
    if (!cand && e.state === 'addressee_candidate') { return; }
    const td = el('td', 'small', words);
    td.colSpan = 3;
    tr.appendChild(td);
    body.appendChild(tr);
  });
  const not = entries.filter(function (e) { return e.state === 'not_searched'; });
  $('view-not').textContent = not.length ? t('view.role', { kind: kindName(cascade.kind),
    fields: not.map(function (e) { return fieldName(e.field); }).join(', ') }) : '';
  $('view-not').hidden = !not.length;
}

/* ---------- the RDF place: the two Turtle files as text with colours ---------- */
async function loadTtl(v) {
  const id = v.record_id;
  if (S.ttl && S.ttl.id === id) { renderTtl(); return; }
  S.ttl = { id: id, tab: 'ech', ech: null, values: null, state: { ech: 'wait', values: 'wait' } };
  renderTtl();
  const want = { ech: fileOf(v, 'ech_ttl'), values: fileOf(v, 'values_ttl') };
  ['ech', 'values'].forEach(function (k) {
    const f = want[k];
    $(k === 'ech' ? 'rdf-dl-ech' : 'rdf-dl-values').hidden = !f;
    if (f) { $(k === 'ech' ? 'rdf-dl-ech' : 'rdf-dl-values').href = f.url + '?download=1'; }
  });
  await Promise.all(['ech', 'values'].map(async function (k) {
    const f = want[k];
    let text = null;
    if (f && !S.fixture) {
      try {
        const res = await fetch(f.url, { cache: 'no-store' });
        text = res.ok ? await res.text() : null;
      } catch (e) { text = null; }
    }
    if (!S.ttl || S.ttl.id !== id) { return; }
    S.ttl[k] = text;
    S.ttl.state[k] = text === null ? 'absent' : 'ok';
    if (S.ttl.tab === k && S.screen === 'view') { renderTtl(); applyViewSel(null); }
  }));
}
/* Turtle tokens: a comment, an IRI, a string, a keyword, a prefixed name, a number. A string with three quote
   marks can go over more lines (state long). */
const TTL_TOKEN = /(#.*$)|(<[^>\s]*>)|("""|"(?:[^"\\]|\\.)*")|(@prefix|@base|\ba\b)|((?:[A-Za-z][\w-]*)?:[\w.-]*[\w-]|[A-Za-z][\w-]*:)|(-?\d+(?:\.\d+)?)/g;
const TTL_CLASS = ['', 'tk-c', 'tk-i', 'tk-s', 'tk-k', 'tk-p', 'tk-n'];
function ttlLine(text, long) {
  const span = el('span', 'tl');
  let rest = text;
  if (long.on) {
    const end = rest.indexOf('"""');
    if (end === -1) { span.appendChild(el('span', 'tk-s', rest)); return span; }
    span.appendChild(el('span', 'tk-s', rest.slice(0, end + 3)));
    rest = rest.slice(end + 3);
    long.on = false;
  }
  let last = 0;
  TTL_TOKEN.lastIndex = 0;
  let m;
  while ((m = TTL_TOKEN.exec(rest)) !== null) {
    if (m.index > last) { span.appendChild(document.createTextNode(rest.slice(last, m.index))); }
    let kind = 1;
    while (kind < m.length && m[kind] === undefined) { kind += 1; }
    if (m[3] === '"""') {
      const end = rest.indexOf('"""', m.index + 3);
      if (end === -1) { span.appendChild(el('span', 'tk-s', rest.slice(m.index))); long.on = true; return span; }
      span.appendChild(el('span', 'tk-s', rest.slice(m.index, end + 3)));
      last = end + 3;
      TTL_TOKEN.lastIndex = last;
      continue;
    }
    span.appendChild(el('span', TTL_CLASS[kind] || '', m[0]));
    last = m.index + m[0].length;
    if (m[0].length === 0) { TTL_TOKEN.lastIndex += 1; }
  }
  if (last < rest.length) { span.appendChild(document.createTextNode(rest.slice(last))); }
  return span;
}
function ttlEscape(s) { return String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n'); }
/* The lines of a value in a Turtle text. eCH-0295 record: each line that holds the value as a whole string.
   Values file: the lines of the node <record>/value/<field>, up to the line that ends the statement. */
function ttlMarks(v, tab, lines) {
  const marks = new Map();
  writtenValues(v).forEach(function (x) {
    const at = [];
    if (tab === 'ech') {
      const lit = '"' + ttlEscape(x.value) + '"';
      lines.forEach(function (l, i) { if (l.indexOf(lit) !== -1) { at.push(i); } });
    } else {
      const head = '<' + v.document.record_iri + '/value/' + x.field + '>';
      const i0 = lines.findIndex(function (l) { return l.indexOf(head) === 0; });
      if (i0 !== -1) {
        for (let i = i0; i < lines.length; i += 1) { at.push(i); if (/\s\.\s*$/.test(lines[i])) { break; } }
      }
    }
    if (at.length) { marks.set(x.field, at); }
  });
  return marks;
}
function renderTtl() {
  const pre = clear($('rdf-text'));
  const tt = S.ttl;
  const v = S.view;
  const tab = tt ? tt.tab : 'ech';
  ['ech', 'values'].forEach(function (k) {
    const b = $('tab-' + k);
    b.setAttribute('aria-selected', k === tab ? 'true' : 'false');
    b.tabIndex = k === tab ? 0 : -1;
  });
  pre.setAttribute('aria-labelledby', 'tab-' + tab);
  const f = v ? fileOf(v, tab === 'ech' ? 'ech_ttl' : 'values_ttl') : null;
  const isEch = tab === 'ech';
  $('rdf-note').textContent = !f ? '' : (isEch ? t('view.rdf.note.ech', { name: f.name }) : t('view.rdf.note.values', { name: f.name }));
  if (!tt || tt[tab] === null) {
    const absent = !f || (tt && tt.state[tab] === 'absent');
    pre.appendChild(el('span', 'tl-wait', t(absent ? 'view.rdf.absent' : 'view.rdf.wait')));
    return;
  }
  const lines = tt[tab].replace(/\n$/, '').split('\n');
  const marks = ttlMarks(v, tab, lines);
  const byLine = new Map();
  marks.forEach(function (at, field) { at.forEach(function (i) { if (!byLine.has(i)) { byLine.set(i, field); } }); });
  const long = { on: false };
  const first = new Set();
  lines.forEach(function (l, i) {
    const span = ttlLine(l, long);
    if (byLine.has(i)) {
      const field = byLine.get(i);
      span.classList.add('tm', colourOf(field));
      span.setAttribute('data-f', field);
      /* the first line of a value is a button for the keyboard; the other lines of the value are for the mouse */
      if (!first.has(field)) {
        first.add(field);
        span.tabIndex = 0;
        span.setAttribute('role', 'button');
        span.setAttribute('aria-label', t('view.ttl.aria', { name: fieldName(field) }));
      }
    }
    pre.appendChild(span);
    pre.appendChild(document.createTextNode('\n'));
  });
}

/* ---------- one value selected: its row, its box and its triples ---------- */
function applyViewSel(scroll) {
  const f = S.vsel;
  document.querySelectorAll('#view-rows tr[data-f], #view-pages .vbox, #rdf-text .tm').forEach(function (n) {
    const on = !!f && n.getAttribute('data-f') === f;
    n.classList.toggle('is-sel', on);
    if (n.classList.contains('vrow') || n.classList.contains('vbox') || n.getAttribute('role') === 'button') { n.setAttribute('aria-pressed', on ? 'true' : 'false'); }
  });
  document.querySelectorAll('#view-pages .vbox').forEach(function (n) { n.classList.toggle('is-dim', !!f && n.getAttribute('data-f') !== f); });
  if (!f || !scroll) { return; }
  const box = document.querySelector('#view-pages .vbox[data-f="' + f + '"]');
  if (box && scroll !== 'box') { intoView(box, 'center'); }
  const row = document.querySelector('#view-rows tr[data-f="' + f + '"]');
  if (row && scroll !== 'row') { intoView(row, 'nearest'); }
  const line = document.querySelector('#rdf-text .tm[data-f="' + f + '"]');
  const pre = $('rdf-text');
  if (line && scroll !== 'ttl') { pre.scrollTop = Math.max(0, line.offsetTop - pre.offsetTop - 24); }
}
function selectValue(field, from) {
  S.vsel = S.vsel === field ? null : field;
  applyViewSel(from);
  say(S.vsel ? t('view.selected', { name: fieldName(S.vsel) }) : t('view.unselected'));
}
function bindView() {
  function pickFrom(ev, sel) { return ev.target.closest ? ev.target.closest(sel) : null; }
  $('view-rows').addEventListener('click', function (ev) {
    if (pickFrom(ev, 'a')) { return; }
    const tr = pickFrom(ev, 'tr[data-f]');
    if (tr) { selectValue(tr.getAttribute('data-f'), 'row'); }
  });
  $('view-rows').addEventListener('keydown', function (ev) {
    const tr = pickFrom(ev, 'tr[data-f]');
    if (tr && ev.target === tr && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); selectValue(tr.getAttribute('data-f'), 'row'); }
  });
  $('view-pages').addEventListener('click', function (ev) {
    const g = pickFrom(ev, '.vbox');
    if (g) { selectValue(g.getAttribute('data-f'), 'box'); }
  });
  $('view-pages').addEventListener('keydown', function (ev) {
    const g = pickFrom(ev, '.vbox');
    if (g && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); selectValue(g.getAttribute('data-f'), 'box'); }
  });
  $('rdf-text').addEventListener('click', function (ev) {
    const l = pickFrom(ev, '.tm');
    if (l) { selectValue(l.getAttribute('data-f'), 'ttl'); }
  });
  $('rdf-text').addEventListener('keydown', function (ev) {
    const l = pickFrom(ev, '.tm');
    if (l && ev.target === l && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); selectValue(l.getAttribute('data-f'), 'ttl'); }
  });
  ['ech', 'values'].forEach(function (k) {
    $('tab-' + k).addEventListener('click', function () {
      if (!S.ttl) { return; }
      S.ttl.tab = k;
      renderTtl();
      applyViewSel(S.vsel ? 'box' : null);
    });
  });
  $('view-grid').querySelector('.rdf-tabs').addEventListener('keydown', function (ev) {
    if (ev.key !== 'ArrowLeft' && ev.key !== 'ArrowRight') { return; }
    const next = S.ttl && S.ttl.tab === 'ech' ? 'values' : 'ech';
    if (!S.ttl) { return; }
    S.ttl.tab = next;
    renderTtl();
    applyViewSel(null);
    $('tab-' + next).focus();
  });
}

/* ---------- routes ---------- */
function route(opts) {
  opts = opts || {};
  syncLangLinks();
  let parts;
  try {
    parts = location.hash.replace(/^#/, '').split('/').filter(Boolean).map(decodeURIComponent);
  } catch (e) {
    parts = [];
  }
  const name = parts[0] || '';
  if (name !== 'job') { leaveJob(); }
  if (name !== 'record' && S.screen === 'record') { unmountPanel(); }
  try {
    if (name === 'samples' && parts.length === 1) { showSamples(opts); }
    else if (name === 'upload' && parts.length === 1) { showUpload(opts); }
    else if (name === 'job' && parts.length === 2) { showJob(parts[1], opts).catch(function (e) { showCase(e, null); }); }
    else if (name === 'record' && (parts.length === 2 || (parts.length === 4 && parts[2] === 'label'))) {
      showRecord(parts[1], parts[3] || null, opts).catch(function (e) { showCase(e, null); });
    }
    else if (name === 'view' && parts.length === 2) { showView(parts[1], opts).catch(function (e) { showCase(e, null); }); }
    else if (name === 'about' && parts.length <= 2) { showAbout(parts[1] || null, opts); }
    else { showStart(opts); }
  } catch (e) {
    showCase(e, null);
  }
}

function bind() {
  $('skip').addEventListener('click', function () {
    const h = document.querySelector('.screen:not([hidden]) h1');
    if (h) { h.focus(); intoView(h, 'start'); }
  });
  $('langs').addEventListener('click', function (ev) {
    const a = ev.target.closest ? ev.target.closest('[data-lang]') : null;
    if (!a || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) { return; }
    ev.preventDefault();
    setLang(a.getAttribute('data-lang'));
  });
  bindView();
  bindUpload();
  bindKeyboardMark();
  /* The list of the parts of a result: a button moves the focus to the heading of the part. */
  $('rec-parts').addEventListener('click', function (ev) {
    const b = ev.target.closest ? ev.target.closest('[data-goto]') : null;
    const target = b ? $(b.getAttribute('data-goto')) : null;
    if (!target || target.hidden) { return; }
    target.focus({ preventScroll: true });
    intoView(target, 'start');
  });
  $('job-stop').addEventListener('click', stopJob);
  $('rec-pages').addEventListener('keydown', onPageKey);
  $('rec-pages').addEventListener('click', function (ev) {
    const g = ev.target.closest ? ev.target.closest('.ln') : null;
    if (!g) { return; }
    S.ix.lineEl.forEach(function (n) { n.setAttribute('tabindex', '-1'); });
    g.setAttribute('tabindex', '0');
    selectLine(g.getAttribute('data-a'), { scroll: 'card' });
  });
  $('rec-to-card').addEventListener('click', function () {
    const card = S.sel && S.ix ? S.ix.cardEl.get(S.sel) : null;
    if (!card) { return; }
    const h = card.querySelector('.card-name');
    h.focus({ preventScroll: true });
    intoView(card, 'center');
  });
  $('rec-filter-status').addEventListener('click', function (ev) {
    const b = ev.target.closest ? ev.target.closest('[data-filter]') : null;
    if (!b) { return; }
    const f = b.getAttribute('data-filter');
    S.filter.status = STATUS_FILTERS.indexOf(f) !== -1 ? f : 'all';
    applyFilter(false);
  });
  $('rec-filter-source').addEventListener('change', function (ev) {
    S.filter.group = ev.target.value || 'all';
    applyFilter(false);
  });
  $('rec-delete').addEventListener('click', function () {
    $('rec-delete-ask').hidden = false;
    $('rec-delete').setAttribute('aria-expanded', 'true');
    $('rec-delete-q').focus();
  });
  $('rec-delete-no').addEventListener('click', function () { resetDelete(); $('rec-delete').focus(); });
  $('rec-delete-yes').addEventListener('click', deleteRecord);
  window.addEventListener('hashchange', function () { route(); });
}

async function boot() {
  const query = new URLSearchParams(location.search);
  S.fixture = query.get('fixture') === '1';
  const asked = query.get('lang');
  S.lang = asked === 'en' || asked === 'de' ? asked : (String(navigator.language || '').toLowerCase().indexOf('de') === 0 ? 'de' : 'en');
  const bootNote = $('boot');
  try {
    const res = await fetch('strings.json', { cache: 'no-cache' });
    if (!res.ok) { throw new Error('strings'); }
    S.strings = await res.json();
  } catch (e) {
    bootNote.classList.add('is-on');
    return;
  }
  bootNote.hidden = true;
  api = S.fixture ? fixtureApi : realApi;
  $('fixture-note').hidden = !S.fixture;
  bind();
  /* The health answer comes before the first text: it says if the server is a hosted site (other texts)
     and if the site takes a file. A failure shows on S0 and S2 only; the version line then stays hidden. */
  try { await loadHealth(); } catch (e) { /* the screens ask again */ }
  applyStatic();
  route();
}

boot();
