//! Web server of the ParlPDFeCH package (CONTRACT.md chapters 2 and 5).
//!
//! The server gives the pages, the API and the files of a record. It starts one worker
//! process for each conversion. It converts nothing itself and opens no connection to another host.

pub mod errors;
pub mod ids;
pub mod jobs;
pub mod records;
pub mod statics;

use std::path::PathBuf;
use std::sync::Arc;
use std::time::{Duration, Instant};

use axum::extract::{DefaultBodyLimit, Request, State};
use axum::http::{header, HeaderName, HeaderValue, Method};
use axum::middleware::{self, Next};
use axum::response::{IntoResponse, Response};
use axum::routing::{get, post};
use axum::Router;
use serde_json::{json, Value};

use errors::ApiError;
use tokio::sync::watch;

/// The internal status of each result of the package. A machine field. The pages do not show it.
pub const STATUS: &str = "EXCEPTION, NOT RELEASED";

/// Limit for each request body that is not the upload, and for the form fields of the upload.
pub const SMALL_BODY: u64 = 64 * 1024;

const CSP: &str =
    "default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self'; img-src 'self'; \
font-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'";
/// The policy of each answer that is not below `/app/` or `/api/`: the static site and the redirects. The
/// pages of the site load one script, one style sheet and pictures of this server, and they read data
/// files of this server. They use no WebAssembly, no font file and no form.
const SITE_CSP: &str =
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; \
base-uri 'none'; form-action 'none'; frame-ancestors 'none'";
/// The policy of each answer below `/api/`: a record file that a browser shows as a document is inert.
const API_CSP: &str = "default-src 'none'; sandbox; frame-ancestors 'none'";

/// The configuration of the server (CONTRACT.md chapter 2.1).
#[derive(Debug, Clone)]
pub struct Config {
    pub profile: String,
    pub bind: String,
    pub ui_dir: PathBuf,
    pub data_dir: PathBuf,
    pub work_dir: PathBuf,
    pub worker_cmd: Vec<String>,
    pub worker_cwd: Option<PathBuf>,
    pub site_dir: Option<PathBuf>,
    pub max_bytes: u64,
    pub max_pages: u32,
    pub job_timeout: Duration,
    pub commit: String,
    /// Time between two ping comments of an event stream.
    pub ping_interval: Duration,
    /// Time between the signal TERM and the signal KILL for a worker that is stopped.
    pub kill_grace: Duration,
    /// Host names that a request can name in its `Host` header, in addition to `localhost`,
    /// `127.0.0.1` and `[::1]` (variable `PARLPDFECH_ALLOWED_HOSTS`, a list with commas).
    pub allowed_hosts: Vec<String>,
    /// Time limit for the read of the body of `POST /api/jobs`.
    pub upload_timeout: Duration,
    /// A public site (variable `PARLPDFECH_READONLY=1`): the server takes no PDF file and refuses each
    /// DELETE. A visitor cannot write a file of its own, stop a job or delete a record. The runs of the
    /// samples stay (one at a time).
    pub readonly: bool,
    /// Variable `PARLPDFECH_SAMPLE_RUNS` (`on` or `off`, default `on`). With `off` the server starts no
    /// run for a sample whose record of that mode is in the work folder: a public site serves the
    /// prepared records only. A sample with no record still runs, so that the site can make it.
    pub sample_runs: bool,
    /// Variable `PARLPDFECH_HOSTED` (`0` or `1`, default `0`). `1` = the operator says that this server is
    /// not on the computer of the reader. The server only reports the value in `/api/health`; the page then
    /// uses the texts for a hosted site in place of the texts that say "on this computer".
    pub hosted: bool,
}

impl Config {
    /// Reads the configuration from the environment. An invalid value is an error text.
    pub fn from_env() -> Result<Config, String> {
        let var = |name: &str| std::env::var(name).ok().filter(|v| !v.is_empty());
        let absolute =
            |p: String| std::path::absolute(&p).map_err(|_| format!("invalid path: {p}"));
        let number = |name: &str, default: u64| -> Result<u64, String> {
            match var(name) {
                None => Ok(default),
                Some(v) => v
                    .parse::<u64>()
                    .map_err(|_| format!("{name} is not a number")),
            }
        };
        let profile = var("PARLPDFECH_PROFILE").unwrap_or_else(|| "native".into());
        if !["slim", "full", "native"].contains(&profile.as_str()) {
            return Err("PARLPDFECH_PROFILE is not slim, full or native".into());
        }
        let worker_cmd: Vec<String> = match var("PARLPDFECH_WORKER_CMD") {
            None => vec!["python3".into(), "worker/serve_convert.py".into()],
            Some(v) => serde_json::from_str(&v)
                .map_err(|_| "PARLPDFECH_WORKER_CMD is not a JSON array of strings")?,
        };
        if worker_cmd.is_empty() || worker_cmd[0].is_empty() {
            return Err("PARLPDFECH_WORKER_CMD is empty".into());
        }
        let max_bytes = number("PARLPDFECH_MAX_BYTES", 20 * 1024 * 1024)?;
        let max_pages = u32::try_from(number("PARLPDFECH_MAX_PAGES", 25)?)
            .map_err(|_| "PARLPDFECH_MAX_PAGES is too large")?;
        let timeout = number("PARLPDFECH_JOB_TIMEOUT", 600)?;
        if max_bytes == 0 || max_pages == 0 || timeout == 0 {
            return Err("a limit is 0".into());
        }
        Ok(Config {
            profile,
            bind: var("PARLPDFECH_BIND").unwrap_or_else(|| "127.0.0.1:8080".into()),
            ui_dir: absolute(var("PARLPDFECH_UI_DIR").unwrap_or_else(|| "ui".into()))?,
            data_dir: absolute(var("PARLPDFECH_DATA_DIR").unwrap_or_else(|| "data".into()))?,
            work_dir: absolute(var("PARLPDFECH_WORK_DIR").unwrap_or_else(|| "work".into()))?,
            worker_cmd,
            worker_cwd: var("PARLPDFECH_WORKER_CWD").map(absolute).transpose()?,
            site_dir: var("PARLPDFECH_SITE_DIR").map(absolute).transpose()?,
            max_bytes,
            max_pages,
            job_timeout: Duration::from_secs(timeout),
            commit: var("PARLPDFECH_COMMIT").unwrap_or_else(|| "unknown".into()),
            ping_interval: Duration::from_secs(15),
            kill_grace: Duration::from_secs(3),
            allowed_hosts: var("PARLPDFECH_ALLOWED_HOSTS")
                .map(|v| {
                    v.split(',')
                        .map(|h| h.trim().to_ascii_lowercase())
                        .filter(|h| !h.is_empty())
                        .collect()
                })
                .unwrap_or_default(),
            upload_timeout: Duration::from_secs(number("PARLPDFECH_UPLOAD_TIMEOUT", 120)?.max(1)),
            readonly: match var("PARLPDFECH_READONLY").as_deref() {
                None | Some("0") => false,
                Some("1") => true,
                Some(_) => return Err("PARLPDFECH_READONLY is not 0 or 1".into()),
            },
            sample_runs: match var("PARLPDFECH_SAMPLE_RUNS").as_deref() {
                None | Some("on") => true,
                Some("off") => false,
                Some(_) => return Err("PARLPDFECH_SAMPLE_RUNS is not on or off".into()),
            },
            hosted: match var("PARLPDFECH_HOSTED").as_deref() {
                None | Some("0") => false,
                Some("1") => true,
                Some(_) => return Err("PARLPDFECH_HOSTED is not 0 or 1".into()),
            },
        })
    }

    /// Drops the site folder if it has no file `index.html`. The address `/` then redirects to `/app/`,
    /// and `/api/health` says `site: false`. Returns true if a folder was dropped.
    pub fn drop_absent_site(&mut self) -> bool {
        let absent = self
            .site_dir
            .as_ref()
            .is_some_and(|dir| !dir.join("index.html").is_file());
        if absent {
            self.site_dir = None;
        }
        absent
    }

    pub fn records_dir(&self) -> PathBuf {
        self.work_dir.join("records")
    }

    pub fn jobs_dir(&self) -> PathBuf {
        self.work_dir.join("jobs")
    }
}

/// A flag that is set one time. Tasks wait for it.
#[derive(Debug, Clone)]
pub struct Flag(Arc<watch::Sender<bool>>);

impl Default for Flag {
    fn default() -> Self {
        Flag(Arc::new(watch::channel(false).0))
    }
}

impl Flag {
    pub fn set(&self) {
        self.0.send_replace(true);
    }

    /// Returns when the flag is set.
    pub async fn wait(&self) {
        let mut rx = self.0.subscribe();
        let _ = rx.wait_for(|set| *set).await;
    }
}

/// The shared state of all handlers.
#[derive(Clone)]
pub struct AppState {
    pub cfg: Arc<Config>,
    pub jobs: Arc<jobs::Jobs>,
}

impl AppState {
    pub fn new(cfg: Config) -> Self {
        AppState {
            cfg: Arc::new(cfg),
            jobs: Arc::new(jobs::Jobs::default()),
        }
    }

    /// Takes the exclusive lock of the work folder (the file `.lock`). The process keeps the returned
    /// file open until it ends. A second server with the same work folder gets an error and MUST stop
    /// before it changes a file: `prepare_work_dir` deletes the job folders.
    pub fn lock_work_dir(&self) -> std::io::Result<std::fs::File> {
        std::fs::create_dir_all(&self.cfg.work_dir)?;
        let file = std::fs::OpenOptions::new()
            .create(true)
            .truncate(false)
            .write(true)
            .open(self.cfg.work_dir.join(".lock"))?;
        match file.try_lock() {
            Ok(()) => Ok(file),
            Err(std::fs::TryLockError::WouldBlock) => Err(std::io::Error::new(
                std::io::ErrorKind::ResourceBusy,
                "another server process uses this work folder",
            )),
            Err(std::fs::TryLockError::Error(e)) => Err(e),
        }
    }

    /// Makes `records/` and `jobs/` and deletes what an earlier process left in `jobs/`
    /// and half moved folders in `records/`. Call it only with the lock of `lock_work_dir`.
    pub fn prepare_work_dir(&self) -> std::io::Result<()> {
        std::fs::create_dir_all(self.cfg.records_dir())?;
        std::fs::create_dir_all(self.cfg.jobs_dir())?;
        for entry in std::fs::read_dir(self.cfg.jobs_dir())?.flatten() {
            let _ = std::fs::remove_dir_all(entry.path())
                .or_else(|_| std::fs::remove_file(entry.path()));
        }
        for entry in std::fs::read_dir(self.cfg.records_dir())?.flatten() {
            if entry.file_name().to_string_lossy().starts_with('.') {
                let _ = std::fs::remove_dir_all(entry.path());
            }
        }
        Ok(())
    }
}

/// Builds the router with all addresses of CONTRACT.md chapters 2.2 and 5.2.
pub fn build_app(state: AppState) -> Router {
    let upload_limit =
        usize::try_from(state.cfg.max_bytes.saturating_add(SMALL_BODY)).unwrap_or(usize::MAX);
    Router::new()
        .route("/healthz", get(healthz))
        .route("/api/health", get(health))
        .route("/api/samples", get(jobs::get_samples))
        .route(
            "/api/jobs",
            post(jobs::post_job).layer(DefaultBodyLimit::max(upload_limit)),
        )
        .route(
            "/api/jobs/{id}",
            get(jobs::get_job).delete(jobs::delete_job),
        )
        .route("/api/jobs/{id}/events", get(jobs::job_events))
        .route(
            "/api/records/{record_id}",
            get(records::get_view).delete(records::delete_record),
        )
        .route(
            "/api/records/{record_id}/files/{name}",
            get(records::get_file),
        )
        .route(
            "/api/records/{record_id}/bundle.zip",
            get(records::get_bundle),
        )
        .method_not_allowed_fallback(statics::method_not_allowed)
        .fallback(statics::fallback)
        .layer(middleware::from_fn_with_state(state.clone(), guard))
        .with_state(state)
}

async fn healthz() -> Response {
    ([(header::CONTENT_TYPE, "text/plain; charset=utf-8")], "ok").into_response()
}

async fn health(State(st): State<AppState>) -> Result<Response, ApiError> {
    let samples = jobs::read_index(&st.cfg).await?;
    let has_mode = |mode: &str| {
        samples.iter().any(|s| {
            s.get("modes")
                .and_then(Value::as_array)
                .is_some_and(|m| m.iter().any(|x| x.as_str() == Some(mode)))
        })
    };
    let stored = samples
        .iter()
        .any(|s| s.get("apertus").and_then(Value::as_str) == Some("stored"));
    // Stage P0b: the profiles `native` and `full` convert a PDF that is not a sample (code rules only).
    // The profile `slim` has no Docling: the worker refuses such a PDF with `not_in_package`.
    let upload = st.cfg.profile != "slim" && !st.cfg.readonly;
    let upload_reason = if upload {
        Value::Null
    } else if st.cfg.profile == "slim" {
        json!("profile_slim")
    } else {
        json!("read_only")
    };
    // `apple`: the worker of the profile `native` on macOS uses the OCR of the stored settings.
    // `none`: no OCR engine runs (the image has none).
    let ocr = if st.cfg.profile == "native" && cfg!(target_os = "macos") {
        "apple"
    } else {
        "none"
    };
    let wasm = tokio::fs::metadata(
        st.cfg
            .ui_dir
            .join("pkg")
            .join("parlpdfech_rdfcheck_bg.wasm"),
    )
    .await
    .map(|m| m.is_file())
    .unwrap_or(false);
    let active = st.jobs.active_id();
    Ok(json_response(&json!({
        "schema": "parlpdfech-health/1",
        "version": env!("CARGO_PKG_VERSION"),
        "commit": st.cfg.commit,
        "profile": st.cfg.profile,
        "status": STATUS,
        "modes": {
            "samples": !samples.is_empty(),
            "rules": has_mode("rules"),
            "apertus_stored": stored,
            "upload": upload,
            "apertus_gpu": false,
            // A public site: the page hides the upload, the delete button and the stop button.
            "read_only": st.cfg.readonly,
            // False: the server starts no run for a sample whose record is ready.
            "sample_runs": st.cfg.sample_runs,
            "reason": {"upload": upload_reason, "apertus_gpu": "not_implemented"},
        },
        "ocr": ocr,
        "limits": {
            "max_bytes": st.cfg.max_bytes,
            "max_pages": st.cfg.max_pages,
            "job_timeout_seconds": st.cfg.job_timeout.as_secs(),
        },
        "busy": active.is_some(),
        "job_id": active,
        "wasm": wasm,
        // True: the server gives a static site below `/`. The page then shows a link to it.
        "site": st.cfg.site_dir.is_some(),
        // True: the operator set `PARLPDFECH_HOSTED=1`. The page then uses the texts for a hosted site.
        "hosted": st.cfg.hosted,
    })))
}

/// A JSON answer with the media type of the contract.
pub fn json_response(value: &Value) -> Response {
    bytes_response(
        value.to_string().into_bytes(),
        "application/json; charset=utf-8",
    )
}

/// An answer with bytes that are not changed.
pub fn bytes_response(bytes: Vec<u8>, media_type: &'static str) -> Response {
    (
        [(header::CONTENT_TYPE, HeaderValue::from_static(media_type))],
        bytes,
    )
        .into_response()
}

fn is_api(path: &str) -> bool {
    path == "/api" || path.starts_with("/api/")
}

/// The host name of a `Host` value or of a URI authority, in lower case, with no port.
fn host_name(value: &str) -> String {
    let value = value.trim();
    let name = if value.starts_with('[') {
        value.find(']').map_or(value, |end| &value[..=end])
    } else {
        value.rsplit_once(':').map_or(value, |(name, port)| {
            if port.bytes().all(|b| b.is_ascii_digit()) {
                name
            } else {
                value
            }
        })
    };
    name.to_ascii_lowercase()
}

/// True if the request names this server: the `Host` header (and the authority of an absolute request
/// target) is a loopback name or a name of the list. A page of another site whose host name resolves to
/// 127.0.0.1 (DNS rebinding) sends its own host name and is refused.
fn host_allowed(cfg: &Config, req: &Request) -> bool {
    let ok = |value: &str| {
        let name = host_name(value);
        matches!(name.as_str(), "localhost" | "127.0.0.1" | "[::1]")
            || cfg.allowed_hosts.contains(&name)
    };
    let header_ok = req
        .headers()
        .get(header::HOST)
        .and_then(|v| v.to_str().ok())
        .is_some_and(ok);
    let target_ok = req.uri().authority().is_none_or(|a| ok(a.as_str()));
    header_ok && target_ok
}

/// True if a request that changes something comes from a page of this server or from no page.
/// A browser sends `Origin` with each POST and DELETE of a page and `Sec-Fetch-Site` with each request.
fn origin_allowed(req: &Request) -> bool {
    let text = |name: &str| {
        req.headers()
            .get(name)
            .and_then(|v| v.to_str().ok())
            .map(|v| v.trim().to_ascii_lowercase())
    };
    if text("sec-fetch-site").is_some_and(|v| v != "same-origin" && v != "none") {
        return false;
    }
    match text("origin") {
        None => true,
        Some(origin) => {
            let host = text("host").unwrap_or_default();
            origin
                .strip_prefix("http://")
                .or_else(|| origin.strip_prefix("https://"))
                .is_some_and(|rest| rest == host)
        }
    }
}

/// True if the path is valid UTF-8 after the percent decoding.
fn path_is_utf8(path: &str) -> bool {
    let bytes = path.as_bytes();
    let mut out = Vec::with_capacity(bytes.len());
    let mut i = 0;
    while i < bytes.len() {
        let hex = |b: u8| (b as char).to_digit(16);
        match (
            bytes[i],
            bytes.get(i + 1).copied().and_then(hex),
            bytes.get(i + 2).copied().and_then(hex),
        ) {
            (b'%', Some(a), Some(b)) => {
                out.push((a * 16 + b) as u8);
                i += 3;
            }
            (b, _, _) => {
                out.push(b);
                i += 1;
            }
        }
    }
    std::str::from_utf8(&out).is_ok()
}

fn refused(api: bool) -> Response {
    if api {
        ApiError::new("forbidden").into_response()
    } else {
        (
            axum::http::StatusCode::FORBIDDEN,
            [(header::CONTENT_TYPE, "text/plain; charset=utf-8")],
            "forbidden",
        )
            .into_response()
    }
}

/// One layer for all requests: the host and origin rules, the body limit of the small requests, the
/// headers of CONTRACT.md chapter 5.4 and one log line for each request.
async fn guard(State(st): State<AppState>, req: Request, next: Next) -> Response {
    let started = Instant::now();
    let method = req.method().clone();
    let path = req.uri().path().to_string();
    let api = is_api(&path);
    let is_upload = method == Method::POST && path == "/api/jobs";
    let read_only = matches!(method, Method::GET | Method::HEAD);
    let declared = req
        .headers()
        .get(header::CONTENT_LENGTH)
        .and_then(|v| v.to_str().ok())
        .and_then(|v| v.parse::<u64>().ok());

    let foreign = (path != "/healthz" && !host_allowed(&st.cfg, &req))
        || (!read_only && !origin_allowed(&req));
    let mut res = if foreign {
        refused(api)
    } else if st.cfg.readonly && method == Method::DELETE {
        // A public site: no visitor stops the job or deletes the record of another visitor.
        if api {
            ApiError::new("read_only")
                .with("note", "delete")
                .into_response()
        } else {
            refused(false)
        }
    } else if api && !path_is_utf8(&path) {
        ApiError::new("not_found").into_response()
    } else if !is_upload && declared.is_some_and(|n| n > SMALL_BODY) {
        if api {
            ApiError::new("bad_request")
                .with("field", "body")
                .into_response()
        } else {
            (axum::http::StatusCode::PAYLOAD_TOO_LARGE, "body too large").into_response()
        }
    } else {
        next.run(req).await
    };

    let status = res.status();
    let h = res.headers_mut();
    let mut set = |name: &'static str, value: &'static str| {
        h.insert(
            HeaderName::from_static(name),
            HeaderValue::from_static(value),
        );
    };
    set("x-content-type-options", "nosniff");
    set("referrer-policy", "no-referrer");
    set("x-frame-options", "DENY");
    set("cross-origin-opener-policy", "same-origin");
    set("cross-origin-resource-policy", "same-origin");
    set(
        "permissions-policy",
        "camera=(), microphone=(), geolocation=()",
    );
    if api || path == "/healthz" {
        set("cache-control", "no-store");
        // A record file that a browser opens as a document runs no script and loads nothing.
        set("content-security-policy", API_CSP);
    } else {
        set(
            "content-security-policy",
            if path == "/app" || path.starts_with("/app/") {
                CSP
            } else {
                SITE_CSP
            },
        );
        if status.is_success() && ids::is_hashed_name(&path) {
            set("cache-control", "public, max-age=31536000, immutable");
        } else {
            set("cache-control", "no-cache");
        }
    }
    // The log line holds at most 200 characters of the path of the client.
    let shown: String = path.chars().take(200).collect();
    tracing::info!(
        target: "http",
        method = %method,
        path = %shown,
        status = status.as_u16(),
        ms = started.elapsed().as_millis() as u64,
        "request"
    );
    res
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn host_names() {
        assert_eq!(host_name("LocalHost:8080"), "localhost");
        assert_eq!(host_name("127.0.0.1"), "127.0.0.1");
        assert_eq!(host_name("[::1]:8894"), "[::1]");
        assert_eq!(host_name("evil.example:8080"), "evil.example");
    }

    #[test]
    fn utf8_paths() {
        assert!(path_is_utf8("/api/records/s-1"));
        assert!(path_is_utf8("/api/records/%C3%A4"));
        assert!(!path_is_utf8("/api/records/%ff"));
        assert!(path_is_utf8("/api/records/%zz"));
    }
}
