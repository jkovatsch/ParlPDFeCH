//! Static files: the UI below `/app/`, the optional site below `/`, and the answer for each
//! address that no route has (CONTRACT.md chapter 2.2).

use std::path::Path;

use axum::body::Body;
use axum::extract::{Request, State};
use axum::http::{header, HeaderValue, StatusCode, Uri};
use axum::response::{IntoResponse, Response};
use tower::ServiceExt;
use tower_http::services::ServeDir;

use crate::errors::ApiError;
use crate::AppState;

fn plain(status: StatusCode, text: &'static str) -> Response {
    (
        status,
        [(header::CONTENT_TYPE, "text/plain; charset=utf-8")],
        text,
    )
        .into_response()
}

fn redirect(status: StatusCode, target: &str, query: Option<&str>) -> Response {
    let location = match query {
        Some(q) => format!("{target}?{q}"),
        None => target.to_string(),
    };
    match HeaderValue::from_str(&location) {
        Ok(value) => (status, [(header::LOCATION, value)]).into_response(),
        Err(_) => (
            status,
            [(header::LOCATION, HeaderValue::from_static("/app/"))],
        )
            .into_response(),
    }
}

/// File extensions of the UI that the server gives at the top level of `/app/`.
const UI_TOP: [&str; 9] = [
    "html", "js", "css", "json", "svg", "ico", "png", "woff2", "txt",
];
/// File extensions that the server gives below `/app/pkg/` (the WebAssembly bundle).
const UI_PKG: [&str; 2] = ["js", "wasm"];

fn plain_name(name: &str) -> bool {
    !name.is_empty()
        && name.len() <= 100
        && !name.starts_with('.')
        && name
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'.' | b'_' | b'-'))
}

/// The UI path that the server gives for a request path below `/app`, or `None`.
/// The server gives the page files only: a file at the top level with an extension of the page, and
/// the two kinds of file below `pkg/`. It does not give another folder (the fixtures and the tools of
/// the development), a file with another extension (the README), a dot file or a folder.
pub fn ui_path(rest: &str) -> Option<String> {
    let rest = rest.strip_prefix('/')?;
    if rest.is_empty() {
        return Some("index.html".into());
    }
    let (folder, name) = match rest.split_once('/') {
        None => (None, rest),
        Some(("pkg", name)) => (Some("pkg"), name),
        Some(_) => return None,
    };
    let (_, extension) = name.rsplit_once('.')?;
    let allowed = if folder.is_some() {
        UI_PKG.contains(&extension)
    } else {
        UI_TOP.contains(&extension)
    };
    (plain_name(name) && allowed).then(|| match folder {
        Some(f) => format!("{f}/{name}"),
        None => name.to_string(),
    })
}

/// The media type of a file whose name the table of `ServeDir` does not know or gives another type
/// than the record files have (CONTRACT.md chapter 3).
fn own_media_type(path: &str) -> Option<&'static str> {
    let name = path.rsplit('/').next().unwrap_or("");
    match name.rsplit_once('.') {
        Some((_, "yaml" | "yml")) => Some("application/yaml"),
        // A list of SHA-256 values in the form of `sha256sum`.
        None if name == "SHA256SUMS" => Some("text/plain; charset=utf-8"),
        _ => None,
    }
}

/// Serves one file of a folder. `ServeDir` refuses each path that leaves the folder and
/// sets the media type from the file extension (also `application/wasm`).
async fn serve(dir: &Path, path: &str, query: Option<&str>, mut req: Request) -> Response {
    // A dot file is not a page file. A longer name than a file system permits gives 404, not an error.
    if path
        .split('/')
        .any(|part| part.starts_with('.') || part.len() > 255)
    {
        return plain(StatusCode::NOT_FOUND, "not found");
    }
    let target = match query {
        Some(q) => format!("{path}?{q}"),
        None => path.to_string(),
    };
    let Ok(uri) = target.parse::<Uri>() else {
        return plain(StatusCode::NOT_FOUND, "not found");
    };
    *req.uri_mut() = uri;
    match ServeDir::new(dir)
        .append_index_html_on_directories(true)
        .oneshot(req)
        .await
    {
        Ok(res) if res.status() == StatusCode::NOT_FOUND || res.status().is_server_error() => {
            plain(StatusCode::NOT_FOUND, "not found")
        }
        Ok(mut res) => {
            if res.status().is_success() {
                if let Some(media) = own_media_type(path) {
                    res.headers_mut()
                        .insert(header::CONTENT_TYPE, HeaderValue::from_static(media));
                }
            }
            // The text files of the package are UTF-8. `ServeDir` gives the media type with no charset.
            let media = res
                .headers()
                .get(header::CONTENT_TYPE)
                .and_then(|v| v.to_str().ok())
                .unwrap_or("");
            let text = media.starts_with("text/")
                || media == "application/json"
                || media == "image/svg+xml";
            if text && !media.contains("charset") {
                if let Ok(value) = HeaderValue::from_str(&format!("{media}; charset=utf-8")) {
                    res.headers_mut().insert(header::CONTENT_TYPE, value);
                }
            }
            res.map(Body::new)
        }
        Err(never) => match never {},
    }
}

/// Serves one page file of the UI folder. The file MUST be a regular file (no symbolic link).
async fn serve_ui(dir: &Path, rest: &str, query: Option<&str>, req: Request) -> Response {
    let Some(file) = ui_path(rest) else {
        return plain(StatusCode::NOT_FOUND, "not found");
    };
    match tokio::fs::symlink_metadata(dir.join(&file)).await {
        Ok(meta) if meta.is_file() => serve(dir, &format!("/{file}"), query, req).await,
        _ => plain(StatusCode::NOT_FOUND, "not found"),
    }
}

/// Serves one file of the static site. A path with no file gets the page `404.html` of the site with
/// the status 404, if the site has one.
async fn serve_site(dir: &Path, path: &str, query: Option<&str>, req: Request) -> Response {
    let res = serve(dir, path, query, req).await;
    if res.status() != StatusCode::NOT_FOUND {
        return res;
    }
    let page = dir.join("404.html");
    match tokio::fs::symlink_metadata(&page).await {
        Ok(meta) if meta.is_file() && meta.len() <= 1024 * 1024 => {
            match tokio::fs::read(&page).await {
                Ok(bytes) => (
                    StatusCode::NOT_FOUND,
                    [(header::CONTENT_TYPE, "text/html; charset=utf-8")],
                    bytes,
                )
                    .into_response(),
                Err(_) => res,
            }
        }
        _ => res,
    }
}

/// Each address with no route.
pub async fn fallback(State(st): State<AppState>, req: Request) -> Response {
    let path = req.uri().path().to_string();
    let query = req.uri().query().map(str::to_string);
    let query = query.as_deref();
    if path == "/api" || path.starts_with("/api/") {
        return ApiError::new("not_found").into_response();
    }
    if path == "/app" {
        return redirect(StatusCode::PERMANENT_REDIRECT, "/app/", query);
    }
    if let Some(rest) = path.strip_prefix("/app") {
        if rest.starts_with('/') {
            return serve_ui(&st.cfg.ui_dir, rest, query, req).await;
        }
    }
    match &st.cfg.site_dir {
        Some(site) => serve_site(site, &path, query, req).await,
        None if path == "/" => redirect(StatusCode::TEMPORARY_REDIRECT, "/app/", query),
        None => plain(StatusCode::NOT_FOUND, "not found"),
    }
}

/// A known address with a method that it does not have. Below `/api/` the answer is the error object.
pub async fn method_not_allowed() -> Response {
    ApiError::new("not_found").into_response()
}

#[cfg(test)]
mod tests {
    use super::ui_path;

    #[test]
    fn ui_paths() {
        assert_eq!(ui_path("/").as_deref(), Some("index.html"));
        assert_eq!(ui_path("/app.js").as_deref(), Some("app.js"));
        assert_eq!(
            ui_path("/rdfpanel.strings.json").as_deref(),
            Some("rdfpanel.strings.json")
        );
        assert_eq!(
            ui_path("/pkg/parlpdfech_rdfcheck_bg.wasm").as_deref(),
            Some("pkg/parlpdfech_rdfcheck_bg.wasm")
        );
        for bad in [
            "",
            "/README.md",
            "/tools/check_ui.mjs",
            "/fixtures/view_26171.json",
            "/pkg",
            "/pkg/",
            "/pkg/x.json",
            "/.hidden",
            "/.env.json",
            "/a/../app.js",
            "/pkg/../app.js",
            "/app.js/",
            "//app.js",
            "/%2e%2e/x.js",
            "/sub/a.html",
            "/noext",
        ] {
            assert_eq!(ui_path(bad), None, "{bad:?}");
        }
        assert_eq!(ui_path(&format!("/{}.js", "a".repeat(300))), None);
    }
}
