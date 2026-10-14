//! The error object of CONTRACT.md chapter 5.1.
//!
//! Titles, texts, actions, exits and HTTP status values come from
//! `contract/errors.json`. The file is included at compile time.

use std::sync::LazyLock;

use axum::http::{header, HeaderValue, StatusCode};
use axum::response::{IntoResponse, Response};
use serde_json::{json, Map, Value};

static CATALOG: LazyLock<Map<String, Value>> = LazyLock::new(|| {
    let text = include_str!("../../contract/errors.json");
    serde_json::from_str::<Value>(text)
        .ok()
        .and_then(|v| v.get("errors").and_then(Value::as_object).cloned())
        .unwrap_or_default()
});

/// All error codes of the catalog.
pub fn codes() -> Vec<String> {
    CATALOG.keys().cloned().collect()
}

/// True if the catalog holds the code.
pub fn is_code(code: &str) -> bool {
    CATALOG.contains_key(code)
}

/// One error of the API. `detail` holds only short scalar values.
#[derive(Debug, Clone)]
pub struct ApiError {
    code: String,
    detail: Map<String, Value>,
}

impl ApiError {
    /// An error with a code of the catalog. An unknown code becomes `internal`.
    pub fn new(code: &str) -> Self {
        let code = if is_code(code) { code } else { "internal" };
        ApiError {
            code: code.to_string(),
            detail: Map::new(),
        }
    }

    /// Adds one value to `detail`.
    pub fn with(mut self, key: &str, value: impl Into<Value>) -> Self {
        self.detail.insert(key.to_string(), value.into());
        self
    }

    /// Replaces `detail` with a full map.
    pub fn with_detail(mut self, detail: Map<String, Value>) -> Self {
        self.detail = detail;
        self
    }

    pub fn code(&self) -> &str {
        &self.code
    }

    /// The HTTP status of the catalog.
    pub fn status(&self) -> StatusCode {
        CATALOG
            .get(&self.code)
            .and_then(|e| e.get("http"))
            .and_then(Value::as_u64)
            .and_then(|n| u16::try_from(n).ok())
            .and_then(|n| StatusCode::from_u16(n).ok())
            .unwrap_or(StatusCode::INTERNAL_SERVER_ERROR)
    }

    /// The inner error object (without the key `error`).
    pub fn object(&self) -> Value {
        let entry = CATALOG.get(&self.code);
        let texts = |key: &str| -> Value {
            let mut out = Map::new();
            for lang in ["en", "de"] {
                let raw = entry
                    .and_then(|e| e.get(key))
                    .and_then(|t| t.get(lang))
                    .and_then(Value::as_str)
                    .unwrap_or("");
                out.insert(lang.to_string(), Value::String(fill(raw, &self.detail)));
            }
            Value::Object(out)
        };
        json!({
            "code": self.code,
            "title": texts("title"),
            "text": texts("text"),
            "action": texts("action"),
            "exits": entry.and_then(|e| e.get("exits")).cloned().unwrap_or_else(|| json!([])),
            "detail": Value::Object(self.detail.clone()),
        })
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let body = json!({ "error": self.object() }).to_string();
        let mut res = (self.status(), body).into_response();
        res.headers_mut().insert(
            header::CONTENT_TYPE,
            HeaderValue::from_static("application/json; charset=utf-8"),
        );
        res
    }
}

/// Replaces each placeholder `{name}` with `detail.name`. A placeholder with no value becomes empty.
fn fill(text: &str, detail: &Map<String, Value>) -> String {
    let mut out = String::with_capacity(text.len());
    let mut rest = text;
    while let Some(start) = rest.find('{') {
        out.push_str(&rest[..start]);
        let after = &rest[start + 1..];
        match after.find('}') {
            Some(end)
                if end > 0
                    && after[..end]
                        .chars()
                        .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '_') =>
            {
                match detail.get(&after[..end]) {
                    Some(Value::String(s)) => out.push_str(s),
                    Some(Value::Number(n)) => out.push_str(&n.to_string()),
                    Some(Value::Bool(b)) => out.push_str(&b.to_string()),
                    _ => {}
                }
                rest = &after[end + 1..];
            }
            _ => {
                out.push('{');
                rest = after;
            }
        }
    }
    out.push_str(rest);
    out
}

/// Keeps only short scalar values of a `detail` object from the worker.
/// A string with a character outside `[A-Za-z0-9_.:-]` is dropped. Thus no path and no trace passes.
pub fn clean_detail(value: Option<&Value>) -> Map<String, Value> {
    let mut out = Map::new();
    let Some(Value::Object(map)) = value else {
        return out;
    };
    for (key, val) in map.iter().take(16) {
        if key.is_empty()
            || key.len() > 40
            || !key.chars().all(|c| c.is_ascii_alphanumeric() || c == '_')
        {
            continue;
        }
        match val {
            Value::String(s)
                if s.len() <= 128
                    && s.chars().all(|c| {
                        c.is_ascii_alphanumeric() || matches!(c, '_' | '.' | ':' | '-')
                    })
                    && !s.contains("..") =>
            {
                out.insert(key.clone(), val.clone());
            }
            Value::Number(_) | Value::Bool(_) => {
                out.insert(key.clone(), val.clone());
            }
            _ => {}
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn catalog_has_the_22_codes() {
        assert_eq!(codes().len(), 22);
        for code in codes() {
            let e = ApiError::new(&code);
            let o = e.object();
            assert!(e.status().as_u16() >= 400, "{code}");
            for key in ["title", "text", "action"] {
                for lang in ["en", "de"] {
                    assert!(
                        !o[key][lang].as_str().unwrap().is_empty(),
                        "{code} {key} {lang}"
                    );
                }
            }
            assert!(o["exits"].is_array());
        }
    }

    #[test]
    fn placeholders_are_filled_or_empty() {
        let o = ApiError::new("too_large").with("max_mb", 20).object();
        assert!(o["text"]["en"].as_str().unwrap().contains(" 20 MB"));
        let o = ApiError::new("too_large").object();
        assert!(!o["text"]["en"].as_str().unwrap().contains('{'));
        assert_eq!(fill("a {x} b {y} {Not} {", &Map::new()), "a  b  {Not} {");
    }

    #[test]
    fn unknown_code_becomes_internal() {
        assert_eq!(ApiError::new("no_such_code").code(), "internal");
        assert_eq!(ApiError::new("busy").status().as_u16(), 409);
    }

    #[test]
    fn detail_of_the_worker_is_cleaned() {
        let v = json!({"note": "writer", "path": "/home/x/y.py", "trace": "Traceback (most recent call last)",
                       "pages": 30, "up": "..", "nested": {"a": 1}, "bad key": "x"});
        let d = clean_detail(Some(&v));
        assert_eq!(d.get("note"), Some(&json!("writer")));
        assert_eq!(d.get("pages"), Some(&json!(30)));
        assert_eq!(d.len(), 2);
    }
}
