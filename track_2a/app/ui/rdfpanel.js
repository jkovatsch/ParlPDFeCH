// RDF panel of the ParlPDFeCH package (CONTRACT.md chapter 7.4).
//
// This one file has two roles:
//  1. In the page it sets window.ParlRdfPanel = { mount, unmount }.
//  2. It is also the script of a module worker. The worker holds the
//     WebAssembly module, so a long query cannot block the page and can be
//     stopped (the page ends the worker and starts a new one).
// If a worker cannot start, the WebAssembly module runs in the page.
//
// No inline script, no eval. The Content-Security-Policy needs
// script-src 'self' 'wasm-unsafe-eval' and connect-src 'self' only.

const IN_WORKER =
  typeof WorkerGlobalScope !== "undefined" && self instanceof WorkerGlobalScope;

const MAX_ROWS = 500; // row limit of one query
const MAX_MS = 5000; // time limit inside the Rust code (tested between rows)
const HARD_MS = 8000; // after this time the page ends the worker
const INIT_MS = 30000; // time limit for the start of the module
const CELL_CHARS = 400; // longer cell texts are cut in the table

// ---------------------------------------------------------------------------
// Engine: the calls into the WebAssembly module. Used in the worker and,
// as a fallback, in the page.
// ---------------------------------------------------------------------------

let glue = null;
let check = null;

async function engineCall(op, payload) {
  if (op === "init") {
    if (!glue) {
      const mod = await import("./pkg/parlpdfech_rdfcheck.js");
      await mod.default();
      glue = mod;
    }
    return { ok: true, version: glue.version(), examples: JSON.parse(glue.examples()).examples };
  }
  if (!glue) return { ok: false, error: { code: "no_module", message: "The module is not loaded." } };
  if (op === "load") {
    if (check) check.free();
    check = new glue.RdfCheck();
    return JSON.parse(check.load(new Uint8Array(payload.bytes)));
  }
  if (!check) return { ok: false, error: { code: "no_data", message: "No file is loaded." } };
  if (op === "summary") return JSON.parse(check.summary());
  if (op === "compare") return JSON.parse(check.compare(payload.manifest));
  if (op === "query") return JSON.parse(check.query(payload.sparql, payload.maxRows, payload.maxMs));
  return { ok: false, error: { code: "bad_call", message: "Unknown call." } };
}

if (IN_WORKER) {
  self.onmessage = async (event) => {
    const { id, op, payload } = event.data;
    try {
      self.postMessage({ id, result: await engineCall(op, payload) });
    } catch (e) {
      self.postMessage({ id, failure: String(e && e.message ? e.message : e) });
    }
  };
} else {
  setUpPage();
}

// ---------------------------------------------------------------------------
// Page side
// ---------------------------------------------------------------------------

function setUpPage() {
  const BUILT_IN = {
    "rdf.absent": {
      en: "The RDF check in the browser did not start. All other functions work.",
      de: "Die RDF-Prüfung im Browser ist nicht gestartet. Alle anderen Funktionen arbeiten.",
    },
  };
  const PREFIXES = [
    ["aff", "https://ch.paf.link/schema/affairs/"],
    ["mcm", "https://ld.ech.ch/schema/0292/meta-common/"],
    ["plb", "https://schema.parlpdfech.example/labels/"],
    ["ppx", "https://schema.parlpdfech.example/profile/"],
    ["prov", "http://www.w3.org/ns/prov#"],
    ["rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"],
    ["skos", "http://www.w3.org/2004/02/skos/core#"],
    ["xsd", "http://www.w3.org/2001/XMLSchema#"],
  ];

  let stringsPromise = null;
  let enginePromise = null;
  let engineLoadedFor = null; // the serial number of the mount whose file is in the store
  const states = new WeakMap(); // element -> state of its mount

  // ---- texts --------------------------------------------------------------

  function loadStrings() {
    if (!stringsPromise) {
      stringsPromise = fetch(new URL("./rdfpanel.strings.json", import.meta.url))
        .then((r) => (r.ok ? r.json() : {}))
        .catch(() => ({}));
    }
    return stringsPromise;
  }

  function translator(strings, lang) {
    const language = lang === "de" ? "de" : "en";
    return (key, values) => {
      const entry = strings[key] || BUILT_IN[key];
      let text = entry ? entry[language] || entry.en || key : key;
      if (values) {
        for (const name of Object.keys(values)) {
          text = text.split("{" + name + "}").join(String(values[name]));
        }
      }
      return text;
    };
  }

  function number(lang, n) {
    try {
      return new Intl.NumberFormat(lang === "de" ? "de-CH" : "en").format(n);
    } catch (e) {
      return String(n);
    }
  }

  // ---- engine in a worker, with a fallback in the page --------------------

  function startWorkerEngine() {
    return new Promise((resolve, reject) => {
      let worker;
      try {
        worker = new Worker(import.meta.url, { type: "module" });
      } catch (e) {
        reject(e);
        return;
      }
      const pending = new Map();
      let nextId = 1;
      let dead = false;
      const failAll = (reason) => {
        dead = true;
        for (const entry of pending.values()) {
          clearTimeout(entry.timer);
          entry.reject(reason);
        }
        pending.clear();
      };
      worker.onmessage = (event) => {
        const entry = pending.get(event.data.id);
        if (!entry) return;
        pending.delete(event.data.id);
        clearTimeout(entry.timer);
        if ("failure" in event.data) entry.reject(new Error(event.data.failure));
        else entry.resolve(event.data.result);
      };
      worker.onerror = (event) => {
        if (event && event.preventDefault) event.preventDefault();
        failAll(new Error("worker error"));
        worker.terminate();
      };
      const engine = {
        kind: "worker",
        call(op, payload, limitMs) {
          if (dead) return Promise.reject(new Error("worker ended"));
          return new Promise((res, rej) => {
            const id = nextId++;
            const timer = setTimeout(() => {
              // The worker does not answer: end it. The next call starts a new one.
              worker.terminate();
              enginePromise = null;
              engineLoadedFor = null;
              const error = new Error("timeout");
              error.code = "timeout";
              failAll(error);
            }, limitMs);
            pending.set(id, { resolve: res, reject: rej, timer });
            worker.postMessage({ id, op, payload });
          });
        },
      };
      engine.call("init", null, INIT_MS).then(
        (info) => {
          engine.info = info;
          resolve(engine);
        },
        (e) => {
          worker.terminate();
          reject(e);
        }
      );
    });
  }

  async function startDirectEngine() {
    const info = await engineCall("init", null);
    return {
      kind: "page",
      info,
      call(op, payload) {
        return engineCall(op, payload);
      },
    };
  }

  function getEngine() {
    if (!enginePromise) {
      engineLoadedFor = null;
      const started = startWorkerEngine().catch(() => startDirectEngine());
      enginePromise = started;
      started.catch(() => {
        if (enginePromise === started) enginePromise = null;
      });
    }
    return enginePromise;
  }

  // Puts the file of this mount into the store if another file (or none) is there.
  async function ensureLoaded(state) {
    const engine = await getEngine();
    if (engineLoadedFor !== state.serial) {
      const loaded = await engine.call("load", { bytes: state.bytes.slice(0) }, INIT_MS);
      if (!loaded.ok) {
        const error = new Error(loaded.error.message);
        error.detail = loaded.error;
        throw error;
      }
      engineLoadedFor = state.serial;
    }
    return engine;
  }

  // ---- DOM helpers (text nodes only; no HTML string is parsed) -------------

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  // A table in a box that scrolls sideways on a narrow screen. The box is a named region. It is a tab stop
  // only while its content is wider than the box (a keyboard user can then scroll it with the arrow keys).
  const scrollBoxes = new Set();
  function syncScrollBox(wrap) {
    if (!wrap.isConnected) {
      scrollBoxes.delete(wrap);
      if (boxObserver) boxObserver.unobserve(wrap);
      return;
    }
    if (wrap.scrollWidth > wrap.clientWidth + 1) wrap.tabIndex = 0;
    else wrap.removeAttribute("tabindex");
  }
  function syncScrollBoxes() {
    for (const wrap of Array.from(scrollBoxes)) syncScrollBox(wrap);
  }
  window.addEventListener("resize", syncScrollBoxes);
  // The size of a box changes with the window and with the fonts: an observer tests the box after each layout.
  const boxObserver =
    typeof ResizeObserver === "function"
      ? new ResizeObserver((entries) => {
          for (const entry of entries) syncScrollBox(entry.target);
        })
      : null;

  function table(caption, heads, numericColumns, name) {
    const wrap = el("div", "rdfpanel-scroll");
    wrap.setAttribute("role", "region");
    wrap.setAttribute("aria-label", name || caption || "");
    scrollBoxes.add(wrap);
    if (boxObserver) boxObserver.observe(wrap);
    const t = el("table", "rdfpanel-table");
    if (caption) t.append(el("caption", null, caption));
    const thead = el("thead");
    const tr = el("tr");
    heads.forEach((h, i) => {
      const th = el("th", numericColumns && numericColumns.includes(i) ? "rdfpanel-num" : null, h);
      th.scope = "col";
      tr.append(th);
    });
    thead.append(tr);
    const tbody = el("tbody");
    t.append(thead, tbody);
    wrap.append(t);
    return { wrap, tbody };
  }

  function row(tbody, cells, numericColumns) {
    const tr = el("tr");
    cells.forEach((c, i) => {
      const td = el("td", numericColumns && numericColumns.includes(i) ? "rdfpanel-num" : null);
      if (c instanceof Node) td.append(c);
      else td.textContent = c === null || c === undefined ? "" : String(c);
      tr.append(td);
    });
    tbody.append(tr);
    return tr;
  }

  function ensureStylesheet() {
    const href = new URL("./rdfpanel.css", import.meta.url).href;
    for (const link of document.querySelectorAll('link[rel="stylesheet"]')) {
      if (link.href === href) return;
    }
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.append(link);
  }

  // A part of the panel: a section with its heading as its name.
  let partCounter = 0;
  function part(title) {
    const section = el("section", "rdfpanel-part");
    const h = el("h3", null, title);
    h.id = "rdfpanel-part-" + ++partCounter;
    section.setAttribute("aria-labelledby", h.id);
    section.append(h);
    return section;
  }

  function shortIri(iri) {
    for (const [prefix, ns] of PREFIXES) {
      if (iri.startsWith(ns) && iri.length > ns.length) return prefix + ":" + iri.slice(ns.length);
    }
    return iri;
  }

  function cutText(text) {
    return text.length > CELL_CHARS ? text.slice(0, CELL_CHARS) + " …" : text;
  }

  // ---- rendering ----------------------------------------------------------

  function renderAbsent(element, lang, strings) {
    const t = translator(strings || {}, lang);
    element.replaceChildren(el("p", "rdfpanel-absent", t("rdf.absent")));
    element.classList.add("rdfpanel");
    element.removeAttribute("hidden");
  }

  function renderSummary(root, t, lang, summary, loadInfo) {
    const section = part(t("rdf.summary.title"));
    section.append(
      el(
        "p",
        "rdfpanel-note",
        t("rdf.summary.loaded", {
          bytes: number(lang, loadInfo.bytes),
          n: number(lang, summary.statements),
          ms: number(lang, Math.round(loadInfo.ms)),
        })
      )
    );
    const counts = table(null, [t("rdf.summary.what"), t("rdf.summary.value")], [1], t("rdf.summary.title"));
    // No label of the file has an inSample statement: the value is not known, not 0.
    const bySample = summary.by_in_sample || {};
    const inSampleKnown = "true" in bySample || "false" in bySample;
    const inSampleTrue = inSampleKnown ? bySample["true"] || 0 : null;
    [
      ["rdf.summary.statements", summary.statements],
      ["rdf.summary.subjects", summary.subjects_distinct],
      ["rdf.summary.labels", summary.label_assertions],
      ["rdf.summary.with_probability", summary.labels_with_probability],
      ["rdf.summary.in_sample", inSampleTrue],
      ["rdf.summary.blocks", summary.blocks],
      ["rdf.summary.atoms", summary.atoms],
    ].forEach(([key, value]) =>
      row(counts.tbody, [t(key), value === null ? t("rdf.summary.not_known") : number(lang, value)], [1])
    );
    section.append(counts.wrap);

    const graphs = table(t("rdf.graphs.title"), [t("rdf.graphs.iri"), t("rdf.graphs.statements")], [1]);
    summary.graphs.forEach((g) => {
      const name = g.iri === null ? el("span", null, t("rdf.graphs.default")) : el("code", null, g.iri);
      row(graphs.tbody, [name, number(lang, g.statements)], [1]);
    });
    section.append(graphs.wrap);

    const groups = el("div", "rdfpanel-columns");
    const status = table(t("rdf.status.title"), [t("rdf.status.name"), t("rdf.group.labels")], [1]);
    const statusKeys = Object.keys(summary.by_value_status).sort((a, b) => {
      const order = ["certain", "unsure", "none"];
      return (order.indexOf(a) + 1 || 9) - (order.indexOf(b) + 1 || 9) || a.localeCompare(b);
    });
    statusKeys.forEach((key) => {
      const known = ["certain", "unsure", "none"].includes(key);
      row(status.tbody, [known ? t("rdf.status." + key) : key, number(lang, summary.by_value_status[key])], [1]);
    });
    const source = table(t("rdf.source.title"), [t("rdf.source.name"), t("rdf.group.labels")], [1]);
    Object.keys(summary.by_source).forEach((key) => {
      row(source.tbody, [sourceName(t, key), number(lang, summary.by_source[key])], [1]);
    });
    groups.append(status.wrap, source.wrap);
    section.append(groups);
    root.append(section);
  }

  // The source of a label in the words of the page. The stored name is in the title attribute, not in the text.
  const SOURCES = ["rule", "apertus_head", "code_step", "constant", "export", "copy"];
  function sourceWords(t, key) {
    return SOURCES.includes(key) ? t("rdf.source." + key) : key;
  }
  function sourceName(t, key) {
    const span = el("span", null, sourceWords(t, key));
    if (SOURCES.includes(key)) span.title = t("rdf.stored_name", { key });
    return span;
  }

  function compareRowName(t, graphKeys, name) {
    if (name === "rdf.triples.union") return t("rdf.compare.row.union");
    if (name.startsWith("rdf.triples.")) {
      const key = name.slice("rdf.triples.".length);
      return t("rdf.compare.row.graph", { name: graphKeys[key] ? key : key.replace(/^<|>$/g, "") });
    }
    if (name === "counts.label_assertions") return t("rdf.compare.row.labels");
    if (name.startsWith("counts.label_assertions_by_source.")) {
      return t("rdf.compare.row.source", { name: sourceWords(t, name.slice("counts.label_assertions_by_source.".length)) });
    }
    if (name === "counts.certain_labels") return t("rdf.compare.row.certain");
    if (name === "counts.unsure_labels") return t("rdf.compare.row.unsure");
    if (name === "counts.blocks") return t("rdf.compare.row.blocks");
    return name;
  }

  // A result mark: a shape, a word and a border style. The color is not the only sign.
  function mark(t, equal) {
    const span = el("span", equal ? "rdfpanel-mark rdfpanel-equal" : "rdfpanel-mark rdfpanel-different");
    const shape = el("span", "rdfpanel-shape", equal ? "=" : "≠");
    shape.setAttribute("aria-hidden", "true");
    span.append(shape, el("span", null, t(equal ? "rdf.compare.equal" : "rdf.compare.different")));
    return span;
  }

  function renderCompare(root, t, lang, compared, manifest) {
    const section = part(t("rdf.compare.title"));
    if (!compared) {
      section.append(el("p", "rdfpanel-note", t("rdf.compare.no_manifest")));
      root.append(section);
      return;
    }
    if (!compared.ok || compared.rows.length === 0) {
      section.append(el("p", "rdfpanel-note", t(compared.ok ? "rdf.compare.no_rows" : "rdf.compare.no_manifest")));
      root.append(section);
      return;
    }
    section.append(el("p", "rdfpanel-note", t("rdf.compare.intro")));
    const verdict = el("p", "rdfpanel-verdict");
    verdict.append(
      mark(t, compared.all_equal),
      el("span", null, " " + t(compared.all_equal ? "rdf.counts.agree" : "rdf.counts.differ"))
    );
    section.append(verdict);
    const graphKeys = (manifest && manifest.rdf && manifest.rdf.named_graphs) || (manifest && manifest.named_graphs) || {};
    const tab = table(
      null,
      [t("rdf.compare.name"), t("rdf.compare.in_file"), t("rdf.compare.in_manifest"), t("rdf.compare.result")],
      [1, 2],
      t("rdf.compare.title")
    );
    const value = (v) => (v === null || v === undefined ? t("rdf.compare.absent_value") : number(lang, v));
    compared.rows.forEach((r) => {
      // A row that the panel has a text for shows the text; the stored key is in the title attribute.
      const words = compareRowName(t, graphKeys, r.name);
      const name = el("span", null, words);
      if (words !== r.name) name.title = t("rdf.stored_name", { key: r.name });
      const tr = row(tab.tbody, [name, value(r.in_file), value(r.in_manifest), mark(t, r.equal)], [1, 2]);
      if (!r.equal) tr.className = "rdfpanel-row-different";
    });
    section.append(tab.wrap);
    root.append(section);
  }

  function renderCell(t, cell) {
    if (cell === null || cell === undefined) return el("span", "rdfpanel-unbound", t("rdf.result.unbound"));
    if (cell.type === "iri") {
      const code = el("code", null, cutText(shortIri(cell.value)));
      code.title = cell.value;
      return code;
    }
    if (cell.type === "bnode") return el("code", null, "_:" + cell.value);
    const span = el("span", null, cutText(cell.value));
    if (cell.value.length > CELL_CHARS) span.title = cell.value.slice(0, 4000);
    if (cell.lang) span.append(el("span", "rdfpanel-tag", " @" + cell.lang));
    return span;
  }

  function renderResult(box, t, lang, answer, seconds) {
    box.replaceChildren();
    if (!answer.ok) {
      const code = answer.error && answer.error.code;
      const known = ["syntax", "update_refused", "form_refused", "evaluation", "timeout"].includes(code);
      const p = el("p", "rdfpanel-error", t(known ? "rdf.error." + code : "rdf.error.other", { seconds }));
      p.setAttribute("role", "alert");
      box.append(p);
      if (answer.error && answer.error.message && (code === "syntax" || code === "evaluation" || !known)) {
        box.append(el("p", "rdfpanel-note", t("rdf.error.detail", { message: answer.error.message })));
      }
      return;
    }
    const result = answer.result;
    if (result.kind === "ask") {
      box.append(el("p", "rdfpanel-answer", t(result.boolean ? "rdf.result.ask_true" : "rdf.result.ask_false")));
      return;
    }
    const meta = el(
      "p",
      "rdfpanel-note",
      result.rows.length === 0
        ? t("rdf.result.no_rows")
        : t(result.rows.length === 1 ? "rdf.result.rows.one" : "rdf.result.rows", {
            n: number(lang, result.rows.length),
            ms: number(lang, Math.round(result.elapsed_ms)),
          })
    );
    box.append(meta);
    if (result.truncated) box.append(el("p", "rdfpanel-warning", t("rdf.result.truncated", { rows: result.max_rows })));
    if (result.timed_out) box.append(el("p", "rdfpanel-warning", t("rdf.result.timed_out")));
    if (result.rows.length === 0) return;
    const tab = table(t("rdf.result.title"), [t("rdf.result.row_number")].concat(result.variables.map((v) => "?" + v)), [0]);
    result.rows.forEach((cells, i) => {
      row(tab.tbody, [String(i + 1)].concat(cells.map((c) => renderCell(t, c))), [0]);
    });
    box.append(tab.wrap);
    syncScrollBox(tab.wrap);
  }

  // The example «labels» sorts by the page. The rows of the labels with a page come first: the labels with
  // no page (values and constants) have «no value» in 3 columns.
  function exampleQuery(ex) {
    if (ex.id === "labels") return ex.sparql.replace("ORDER BY ?page ?label", "ORDER BY DESC(BOUND(?page)) ?page ?label");
    return ex.sparql;
  }

  function renderQueries(root, t, lang, state, examples) {
    const section = part(t("rdf.examples.title"));
    section.append(el("p", "rdfpanel-note", t("rdf.examples.intro")));
    const buttons = el("div", "rdfpanel-buttons");
    section.append(buttons);

    section.append(el("h3", null, t("rdf.query.title")));
    const form = el("form", "rdfpanel-form");
    const id = "rdfpanel-query-" + state.serial;
    const label = el("label", null, t("rdf.query.label"));
    label.htmlFor = id;
    const area = el("textarea", "rdfpanel-query");
    area.id = id;
    area.rows = 9;
    area.spellcheck = false;
    area.setAttribute("autocapitalize", "off");
    area.setAttribute("autocomplete", "off");
    const hint = el(
      "p",
      "rdfpanel-note",
      t("rdf.query.hint", { rows: MAX_ROWS, seconds: MAX_MS / 1000, hard: HARD_MS / 1000 })
    );
    hint.id = id + "-hint";
    area.setAttribute("aria-describedby", hint.id);
    const run = el("button", "rdfpanel-run", t("rdf.query.run"));
    run.type = "submit";
    form.append(label, area, hint, run);
    section.append(form);

    const status = el("p", "rdfpanel-note rdfpanel-status");
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    const box = el("div", "rdfpanel-result");
    section.append(status, box);

    let busy = false;
    async function runQuery() {
      if (busy) return;
      const sparql = area.value.trim();
      if (!sparql) {
        box.replaceChildren();
        status.textContent = t("rdf.query.empty");
        return;
      }
      busy = true;
      run.disabled = true;
      status.textContent = t("rdf.query.running");
      let answer;
      try {
        const engine = await ensureLoaded(state);
        answer = await engine.call("query", { sparql, maxRows: MAX_ROWS, maxMs: MAX_MS }, HARD_MS);
      } catch (e) {
        answer = { ok: false, error: { code: e && e.code === "timeout" ? "timeout" : "other", message: String((e && e.message) || e) } };
      }
      busy = false;
      run.disabled = false;
      if (states.get(state.element) !== state) return; // the panel was replaced
      status.textContent = "";
      renderResult(box, t, lang, answer, HARD_MS / 1000);
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      runQuery();
    });
    area.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        runQuery();
      }
    });
    examples.forEach((ex) => {
      // A record with no export record has no eCH-0295 head values: this example can give no row.
      if (ex.id === "ech_head" && state.hasExport === false) {
        buttons.after(el("p", "rdfpanel-note", t("rdf.examples.no_head")));
        return;
      }
      const b = el("button", "rdfpanel-example", lang === "de" ? ex.title_de : ex.title_en);
      b.type = "button";
      b.addEventListener("click", () => {
        area.value = exampleQuery(ex);
        runQuery();
      });
      buttons.append(b);
    });
    root.append(section);
  }

  // ---- contract functions ---------------------------------------------------

  let serialCounter = 0;

  async function mount(element, options) {
    const opts = options || {};
    const lang = opts.lang === "de" ? "de" : "en";
    const before = states.get(element);
    const state = { element, serial: ++serialCounter, bytes: null, manifestText: null, hasExport: opts.hasExport !== false,
      trigUrl: opts.trigUrl, manifestUrl: opts.manifestUrl || null };
    states.set(element, state);
    const current = () => states.get(element) === state;
    let strings = {};
    try {
      ensureStylesheet();
      element.classList.add("rdfpanel");
      element.removeAttribute("hidden");
      strings = await loadStrings();
      if (!current()) return { ok: false };
      const t = translator(strings, lang);
      const loading = el("p", "rdfpanel-note", t("rdf.loading"));
      loading.setAttribute("role", "status");
      const title = el("h2", null, t("rdf.title"));
      title.id = "rdfpanel-title-" + state.serial;
      element.setAttribute("aria-labelledby", title.id);
      element.replaceChildren(title, el("p", "rdfpanel-note", t("rdf.intro")), loading);

      let manifestText;
      if (before && before.bytes && before.trigUrl === state.trigUrl && before.manifestUrl === state.manifestUrl) {
        // The same record is mounted again with no unmount between (a change of the language): the files are not read again.
        state.bytes = before.bytes;
        manifestText = before.manifestText;
      } else {
        const [trigResponse, text] = await Promise.all([
          fetch(opts.trigUrl),
          opts.manifestUrl
            ? fetch(opts.manifestUrl).then((r) => (r.ok ? r.text() : null)).catch(() => null)
            : Promise.resolve(null),
        ]);
        if (!trigResponse.ok) throw new Error("TriG file: HTTP " + trigResponse.status);
        state.bytes = await trigResponse.arrayBuffer();
        manifestText = text;
      }
      state.manifestText = manifestText;
      const engine = await getEngine();
      if (!current()) return { ok: false };

      const t0 = performance.now();
      const loaded = await engine.call("load", { bytes: state.bytes.slice(0) }, INIT_MS);
      const loadMs = performance.now() - t0;
      if (!current()) return { ok: false };
      if (!loaded.ok) {
        engineLoadedFor = null;
        const where =
          loaded.error.line !== null && loaded.error.line !== undefined
            ? t("rdf.parse_error.where", {
                line: loaded.error.line,
                column: loaded.error.column,
                message: loaded.error.message,
              })
            : loaded.error.message;
        const alert = el("p", "rdfpanel-error", t("rdf.parse_error"));
        alert.setAttribute("role", "alert");
        loading.replaceWith(alert, el("p", "rdfpanel-note", where));
        return { ok: false };
      }
      engineLoadedFor = state.serial;
      const summary = await engine.call("summary", null, INIT_MS);
      if (!summary.ok) throw new Error(summary.error.message);
      let manifest = null;
      let compared = null;
      if (manifestText !== null) {
        compared = await engine.call("compare", { manifest: manifestText }, INIT_MS);
        try {
          manifest = JSON.parse(manifestText);
        } catch (e) {
          manifest = null;
        }
      }
      if (!current()) return { ok: false };

      const root = document.createDocumentFragment();
      renderSummary(root, t, lang, summary.summary, { bytes: state.bytes.byteLength, ms: loadMs });
      renderCompare(root, t, lang, compared, manifest);
      renderQueries(root, t, lang, state, engine.info.examples);
      loading.replaceWith(root);
      syncScrollBoxes();
      element.dataset.rdfpanel = "ready";
      element.dataset.rdfpanelEngine = engine.kind;
      return { ok: true };
    } catch (e) {
      if (current()) {
        renderAbsent(element, lang, strings);
        element.dataset.rdfpanel = "absent";
      }
      if (typeof console !== "undefined") console.warn("RDF panel:", e);
      return { ok: false };
    }
  }

  function unmount(element) {
    const state = states.get(element);
    if (state && engineLoadedFor === state.serial) engineLoadedFor = null;
    states.delete(element);
    element.replaceChildren();
    element.removeAttribute("aria-labelledby");
    scrollBoxes.clear();
    delete element.dataset.rdfpanel;
    delete element.dataset.rdfpanelEngine;
  }

  window.ParlRdfPanel = { mount, unmount };
  document.dispatchEvent(new CustomEvent("parl-rdfpanel-ready"));
}
