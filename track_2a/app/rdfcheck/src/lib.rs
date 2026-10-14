//! RDF check of ParlPDFeCH for the browser (WebAssembly) and for native tests.
//!
//! The module `core` holds all functions. This file is the thin browser
//! interface: each method returns one JSON text. A result has `"ok": true`;
//! an error has `"ok": false` and an object `error` with `code` and `message`.

pub mod core;

use serde::Serialize;
use serde_json::json;
use wasm_bindgen::prelude::*;

use crate::core::{Checker, DEFAULT_MAX_MS, DEFAULT_MAX_ROWS};

fn ok<T: Serialize>(key: &str, value: &T) -> String {
    json!({ "ok": true, key: value }).to_string()
}

fn err<T: Serialize>(error: &T) -> String {
    json!({ "ok": false, "error": error }).to_string()
}

fn err_text(code: &str, message: &str) -> String {
    json!({ "ok": false, "error": { "code": code, "message": message } }).to_string()
}

#[cfg(target_arch = "wasm32")]
fn now_ms() -> f64 {
    js_sys::Date::now()
}

#[cfg(not(target_arch = "wasm32"))]
fn now_ms() -> f64 {
    use std::sync::OnceLock;
    use std::time::Instant;
    static START: OnceLock<Instant> = OnceLock::new();
    START.get_or_init(Instant::now).elapsed().as_secs_f64() * 1000.0
}

/// Sets the panic hook, so a panic of the Rust code gives a text in the browser console.
#[wasm_bindgen(start)]
pub fn start() {
    console_error_panic_hook::set_once();
}

/// Version of this crate.
#[wasm_bindgen]
pub fn version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

/// The fixed example queries as JSON: `{"ok":true,"examples":[{id,title_en,title_de,sparql}]}`.
#[wasm_bindgen]
pub fn examples() -> String {
    ok("examples", &core::examples())
}

/// One TriG file in an in-memory store.
#[wasm_bindgen]
pub struct RdfCheck {
    inner: Option<Checker>,
}

impl Default for RdfCheck {
    fn default() -> Self {
        Self::new()
    }
}

#[wasm_bindgen]
impl RdfCheck {
    /// An empty handle. Call `load` next.
    #[wasm_bindgen(constructor)]
    pub fn new() -> RdfCheck {
        RdfCheck { inner: None }
    }

    /// Parses the TriG bytes. Result: `{"ok":true,"statements":n}` or an error
    /// with `code: "parse"`, `message`, `line` and `column` (both start at 1).
    pub fn load(&mut self, trig: &[u8]) -> String {
        match Checker::load(trig) {
            Ok(checker) => {
                let statements = checker.summary().map(|s| s.statements).unwrap_or(0);
                self.inner = Some(checker);
                ok("statements", &statements)
            }
            Err(e) => {
                self.inner = None;
                err(&e)
            }
        }
    }

    /// Counts of the file: `{"ok":true,"summary":{...}}`.
    pub fn summary(&self) -> String {
        match &self.inner {
            None => err_text("no_data", "No file is loaded."),
            Some(c) => match c.summary() {
                Ok(s) => ok("summary", &s),
                Err(e) => err_text("store", &e),
            },
        }
    }

    /// Comparison with manifest.json: `{"ok":true,"rows":[{name,in_file,in_manifest,equal}],"all_equal":bool}`.
    pub fn compare(&self, manifest_json: &str) -> String {
        match &self.inner {
            None => err_text("no_data", "No file is loaded."),
            Some(c) => match c.compare(manifest_json) {
                Ok(rows) => {
                    let all_equal = !rows.is_empty() && rows.iter().all(|r| r.equal);
                    json!({ "ok": true, "rows": rows, "all_equal": all_equal }).to_string()
                }
                Err(e) => err_text("manifest", &e),
            },
        }
    }

    /// Runs one SELECT or ASK query: `{"ok":true,"result":{...}}`.
    /// `max_rows` 0 and `max_ms` 0 select the defaults (500 rows, 5000 ms).
    pub fn query(&self, sparql: &str, max_rows: u32, max_ms: f64) -> String {
        let max_rows = if max_rows == 0 {
            DEFAULT_MAX_ROWS
        } else {
            max_rows as usize
        };
        let max_ms = if max_ms > 0.0 { max_ms } else { DEFAULT_MAX_MS };
        match &self.inner {
            None => err_text("no_data", "No file is loaded."),
            Some(c) => match c.query(sparql, max_rows, max_ms, &now_ms) {
                Ok(result) => ok("result", &result),
                Err(e) => err(&e),
            },
        }
    }
}
