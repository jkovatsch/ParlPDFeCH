# parlpdfech-rdfcheck

A Rust crate that reads one TriG file of a ParlPDFeCH record, counts its
content, compares the counts with `manifest.json` and runs SPARQL queries.
The crate compiles to WebAssembly for the browser panel (`ui/rdfpanel.js`)
and to native code for the tests. The reference for the panel is
`CONTRACT.md` chapter 7.4.

The engine is oxigraph 0.5.9 with `default-features = false` and the feature
`js` (in-memory store, no RocksDB). The module makes no network request.
A `SERVICE` call in a query gives an error.

## Files

| Path | Content |
|---|---|
| `src/core.rs` | All functions. No browser type. |
| `src/lib.rs` | The browser interface (`wasm-bindgen`). Each method returns one JSON text. |
| `tests/samples.rs` | Native tests. |
| `build.sh` | The build for the browser. Output: `ui/pkg/`. |
| `tools/check_wasm.mjs` | Runs the built module in node, outside the browser. |

## Functions for the browser

`ui/pkg/parlpdfech_rdfcheck.js` exports the class `RdfCheck` and two functions.
Each result is a JSON text with `"ok": true`, or `"ok": false` and
`error: {code, message}`.

| Call | Result |
|---|---|
| `new RdfCheck()` | An empty handle. |
| `load(bytes)` | `{ok, statements}`. A syntax error gives `code: "parse"` with `line` and `column` (both start at 1). |
| `summary()` | `{ok, summary}`: `statements`, `triples_distinct`, `subjects_distinct`, `graphs[] {iri, statements}`, `label_assertions`, `labels_with_probability`, `by_value_status`, `by_source`, `by_kind`, `by_in_sample`, `blocks`, `atoms`. |
| `compare(manifest_json)` | `{ok, rows[] {name, in_file, in_manifest, equal}, all_equal}`. |
| `query(sparql, max_rows, max_ms)` | `{ok, result}`: `kind` (`select` or `ask`), `variables`, `rows`, `boolean`, `truncated`, `timed_out`, `elapsed_ms`. The value 0 selects the default (500 rows, 5000 ms). |
| `examples()` | `{ok, examples[] {id, title_en, title_de, sparql}}`: 5 fixed queries. |
| `version()` | The crate version. |

### Vocabulary

The counts use the IRIs of `src/m10_label_schema.yaml` (prefix `plb`,
`https://schema.parlpdfech.example/labels/`):

- A label is a subject with the type `plb:LabelAssertion`.
- `by_value_status` groups the labels by `plb:valueStatus` (`certain`, `unsure`). The key `none` holds the labels that have no status.
- `by_source` groups by `plb:labelSource`, `by_kind` by `plb:labelKind`, `by_in_sample` by `plb:inSample`.
- `blocks` and `atoms` count the subjects with the types `plb:PdfBlock` and `plb:PdfAtom`.

The group names are the local names that the file holds. The crate holds no
fixed list of sources or kinds.

### Rows of the comparison

`compare` gives one row for each of these counts, if `manifest.json` holds it:

- `rdf.triples.<key>` for each named graph of `rdf.named_graphs`, and `rdf.triples.union` (distinct triples of all graphs).
- `counts.label_assertions`.
- `counts.label_assertions_by_source.<source>` for each source of the manifest or of the file.
- `counts.certain_labels`, `counts.unsure_labels`, `counts.blocks`.

A named graph or a source that only the file holds gives a row with
`in_manifest: null` and `equal: false`. The other counts of `manifest.json`
(for example `block_options`, `leaf_values`, `e19`) have no row: the crate
does not compute them.

### Queries

- Only `SELECT` and `ASK` run. An update gives `code: "update_refused"`. `CONSTRUCT` and `DESCRIBE` give `code: "form_refused"`. A syntax error gives `code: "syntax"` with the message of the parser.
- The prefixes `aff`, `mcm`, `plb`, `ppx`, `prov`, `rdf`, `skos`, `xsd` are known with no `PREFIX` line.
- A query with no `FROM` clause reads the union of all named graphs. `GRAPH` selects one named graph. The union does not remove a triple that is in two named graphs; such a triple gives two rows. The three sample records hold no such triple (measured: `statements` equals `triples_distinct`).
- Row limit: the output stops at `max_rows`; `truncated` is true if one more row exists.
- Time limit: the Rust code tests the clock between result rows and stops with `timed_out: true`. It cannot stop a query that works a long time before its first row. For that case the panel runs the module in a worker and ends the worker after 8 seconds.

## Build for the browser

```sh
sh rdfcheck/build.sh
```

The script runs three commands and uses no network:

1. `cargo build --offline --release --target wasm32-unknown-unknown -p parlpdfech-rdfcheck`
2. `wasm-bindgen --target web --no-typescript --out-dir ui/pkg <wasm file>`
3. `wasm-opt -Oz`

Necessary tools: cargo with the target `wasm32-unknown-unknown`, the
`wasm-bindgen` CLI 0.2.127 (the same version as the crate `wasm-bindgen`),
`wasm-opt` (optional). The script sets four profile values for this build
only: `opt-level = "z"`, `lto = "fat"`, `codegen-units = 1`, `panic = "abort"`.
The build folder is `target-wasm/` (`CARGO_TARGET_DIR`).

Measured on the build host (cargo 1.97.1, wasm-opt 130, arm64 macOS, all crates in the local cache):

| Step | Size |
|---|---|
| Output of cargo | 4 434 612 bytes |
| `ui/pkg/parlpdfech_rdfcheck_bg.wasm` after `wasm-bindgen` and `wasm-opt -Oz` | 2 070 826 bytes |
| The same file with `gzip -9` | 764 694 bytes |
| `ui/pkg/parlpdfech_rdfcheck.js` | 13 174 bytes |

Build time of the full script after the removal of the release folder: 26 s (real).
With the profile of the workspace and no added value the final file had
2 984 717 bytes (gzip 1 052 515 bytes).

## Tests

```sh
CARGO_TARGET_DIR=target-wasm cargo test --offline -p parlpdfech-rdfcheck
PARLPDFECH_TEST_RECORDS=<records folder> CARGO_TARGET_DIR=target-wasm cargo test --offline -p parlpdfech-rdfcheck -- --nocapture
node rdfcheck/tools/check_wasm.mjs <records folder> 26171 879163 714840
```

The records folder holds one sub-folder for each document id with
`<doc>.gesamt.trig`, `manifest.json` and `validation.json`
(`check_wasm.mjs` reads the first two).

A record of a PDF with no export record (folder and file prefix `local`,
`manifest.json` conformance `pdf_only_with_recorded_gaps`):
`node rdfcheck/tools/check_wasm.mjs <records folder> local`. For it the
example `ech_head` must give 0 rows (the eCH-0295 graph holds one statement),
and no label may have the statement `plb:inSample` (`by_in_sample` has the
key `none` only).

No path of the build host: `build.sh` gives the compiler the flags
`--remap-path-prefix` for the home folder, the package folder, the folder of
cargo and the folder of rustup (fixed names `/build-home`, `/package`,
`/cargo`, `/rustup`), then it searches the two files of `ui/pkg` for the home
folder, the package folder, the start of a home folder on macOS and the
start `/home/`; a hit stops
the build. `check_wasm.mjs` makes the same search. Measured (13.10.2026):
0 hits in the module (2,067,498 bytes) and in the glue script; the module
before the change held 163 such strings. Without
`PARLPDFECH_TEST_RECORDS` the two record tests print `SKIPPED` and make no
check; the five other tests use a small file inside the test.

The record tests check for the documents 26171, 879163 and 714840:

- The statements count equals the triples count of `validation.json` (`C2_parse`, the entry of the TriG file).
- The named graphs are the four graphs of `manifest.json`.
- Each row of the comparison is equal.
- Each example query gives one or more rows.

Measured results of the three samples:

| Document | Statements | Subjects | Labels | With probability | certain / unsure / none | Blocks | Text lines | Rows compared |
|---|---|---|---|---|---|---|---|---|
| 26171 | 2577 | 365 | 33 | 15 | 9 / 6 / 18 | 13 | 36 | 15 |
| 879163 | 3122 | 451 | 42 | 26 | 12 / 14 / 16 | 24 | 45 | 15 |
| 714840 | 1182 | 169 | 18 | 10 | 6 / 4 / 8 | 8 | 11 | 14 |

## The panel

`ui/rdfpanel.js` sets `window.ParlRdfPanel = { mount, unmount }` and sends the
event `parl-rdfpanel-ready` on `document`.
`mount(element, {trigUrl, manifestUrl, lang})` gives `Promise<{ok}>`.

- The panel adds the style sheet `ui/rdfpanel.css` to the page. Its texts are in `ui/rdfpanel.strings.json`.
- The same file is the script of a module worker. The worker holds the WebAssembly module. If the worker does not start, the module runs in the page; then only the time limit between rows applies.
- If the module, the WebAssembly file or the TriG file does not load, the element shows the text `rdf.absent` only, and `mount` gives `{ok: false}`.
- If `manifest.json` does not load, the counts and the queries work, and the comparison shows one line.
- A different count has the sign `≠`, the word "different" and a dashed border. An equal count has the sign `=`, the word "equal" and a solid border.
- The Content-Security-Policy of the contract is sufficient: `script-src 'self' 'wasm-unsafe-eval'`, `style-src 'self'`, `connect-src 'self'`. The worker loads from the same origin. The panel has no inline script, no inline style and no `eval`.
