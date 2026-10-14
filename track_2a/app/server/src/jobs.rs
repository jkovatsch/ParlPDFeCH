//! Jobs: the upload checks, the worker process, the stage events and the job addresses
//! (CONTRACT.md chapters 4.1, 4.2, 5.2 and 5.3).

use std::collections::VecDeque;
use std::convert::Infallible;
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex, MutexGuard};
use std::time::{Duration, Instant};

use axum::body::{Body, Bytes};
use axum::extract::multipart::{Field, Multipart};
use axum::extract::{FromRequest, Path as UrlPath, Request, State};
use axum::http::{header, HeaderValue, StatusCode};
use axum::response::{IntoResponse, Response};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use tokio::io::{AsyncBufRead, AsyncBufReadExt, AsyncReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, Command};
use tokio::sync::{mpsc, watch};
use tokio_stream::wrappers::ReceiverStream;
use tokio_stream::StreamExt;

use crate::errors::{clean_detail, ApiError};
use crate::{ids, json_response, AppState, Config, Flag, SMALL_BODY};

/// The 6 stage ids in their sequence.
pub const STAGES: [&str; 6] = ["read_pdf", "lines", "rules", "apertus", "write", "check"];
const STAGE_STATES: [&str; 4] = ["running", "done", "skipped", "failed"];
/// Codes that the worker can send with the exit code 3.
const REFUSED: [&str; 9] = [
    "pdf_unreadable",
    "protected_pdf",
    "too_long",
    "no_text_layer",
    "not_in_package",
    "doc_id_unknown",
    "pdf_differs_from_doc_id",
    "sample_unknown",
    "bad_request",
];
/// The longest line of the worker that the server reads. A longer line is dropped.
const MAX_LINE: usize = 1024 * 1024;
/// The largest number of stage events of one job. The protocol has at most 12 (2 for each stage).
/// A worker with an error that repeats a stage line cannot fill the memory.
const MAX_STAGE_EVENTS: usize = 64;
/// The longest part of a line of standard error of the worker that goes to the log.
const MAX_LOG_LINE: usize = 2000;
/// The number of jobs that the server keeps in memory.
const KEEP_JOBS: usize = 20;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum JobState {
    Queued,
    Running,
    Done,
    Failed,
    Stopped,
}

impl JobState {
    fn word(self) -> &'static str {
        match self {
            JobState::Queued => "queued",
            JobState::Running => "running",
            JobState::Done => "done",
            JobState::Failed => "failed",
            JobState::Stopped => "stopped",
        }
    }

    fn ended(self) -> bool {
        matches!(self, JobState::Done | JobState::Failed | JobState::Stopped)
    }
}

#[derive(Debug, Clone)]
struct Stage {
    state: String,
    origin: Value,
    seconds: Value,
    counts: Value,
    reason: Value,
}

impl Default for Stage {
    fn default() -> Self {
        Stage {
            state: "pending".into(),
            origin: Value::Null,
            seconds: Value::Null,
            counts: json!({}),
            reason: Value::Null,
        }
    }
}

/// What the job converts.
#[derive(Debug, Clone)]
pub struct JobInput {
    pub kind: &'static str,
    pub doc_id: Option<String>,
    pub file_name: Option<String>,
    pub bytes: Option<u64>,
    pub pdf_sha256: Option<String>,
}

#[derive(Debug)]
struct JobData {
    state: JobState,
    stages: [Stage; 6],
    record_id: Option<String>,
    valid: Option<bool>,
    apertus: Option<String>,
    error: Option<Value>,
    /// All events of the job in their sequence: (event name, data line).
    events: Vec<(&'static str, String)>,
    elapsed: Option<f64>,
}

/// One job. The worker task writes it, the handlers read it.
#[derive(Debug)]
pub struct Job {
    pub id: String,
    pub input: JobInput,
    pub mode: String,
    /// The record id that the server expects for this input (CONTRACT.md chapter 3).
    pub record_id: String,
    /// The sample number for the argument `--sample`; `None` for an upload.
    sample: Option<String>,
    created: Instant,
    data: Mutex<JobData>,
    /// Holds the number of events. A reader of the event stream waits on it.
    changed: watch::Sender<usize>,
    cancel: Flag,
}

impl Job {
    fn new(
        id: String,
        input: JobInput,
        mode: String,
        record_id: String,
        sample: Option<String>,
    ) -> Self {
        Job {
            id,
            input,
            mode,
            record_id,
            sample,
            created: Instant::now(),
            data: Mutex::new(JobData {
                state: JobState::Queued,
                stages: Default::default(),
                record_id: None,
                valid: None,
                apertus: None,
                error: None,
                events: Vec::new(),
                elapsed: None,
            }),
            changed: watch::channel(0).0,
            cancel: Flag::default(),
        }
    }

    fn data(&self) -> MutexGuard<'_, JobData> {
        self.data.lock().unwrap_or_else(|e| e.into_inner())
    }

    pub fn state(&self) -> JobState {
        self.data().state
    }

    /// The job object of `GET /api/jobs/{id}`.
    pub fn to_json(&self) -> Value {
        let d = self.data();
        self.json_of(&d)
    }

    fn json_of(&self, d: &JobData) -> Value {
        let stages: Vec<Value> = STAGES
            .iter()
            .zip(d.stages.iter())
            .map(|(id, s)| {
                json!({"id": id, "state": s.state, "origin": s.origin, "seconds": s.seconds,
                       "counts": s.counts, "reason": s.reason})
            })
            .collect();
        let elapsed = d
            .elapsed
            .unwrap_or_else(|| self.created.elapsed().as_secs_f64());
        json!({
            "schema": "parlpdfech-job/1",
            "job_id": self.id,
            "state": d.state.word(),
            "input": {
                "kind": self.input.kind,
                "doc_id": self.input.doc_id,
                "file_name": self.input.file_name,
                "bytes": self.input.bytes,
                "pdf_sha256": self.input.pdf_sha256,
            },
            "mode": self.mode,
            "stages": stages,
            "elapsed_seconds": (elapsed * 1000.0).round() / 1000.0,
            "record_id": d.record_id,
            "valid": d.valid,
            "apertus": d.apertus,
            "error": d.error,
            "events": format!("/api/jobs/{}/events", self.id),
            "status": format!("/api/jobs/{}", self.id),
        })
    }

    /// Stores one stage line of the worker and sends it to the readers. The server builds the event
    /// again from checked values (`clean_stage`): no other key and no free text of the worker passes.
    /// The answer is false if the job has the largest number of stage events.
    fn push_stage(&self, value: &Map<String, Value>) -> bool {
        let Some(index) = value
            .get("id")
            .and_then(Value::as_str)
            .and_then(|id| STAGES.iter().position(|s| *s == id))
        else {
            return true;
        };
        let clean = clean_stage(value);
        let mut d = self.data();
        if d.state.ended() {
            return true;
        }
        if d.events.len() >= MAX_STAGE_EVENTS {
            return false;
        }
        let stage = &mut d.stages[index];
        stage.state = clean
            .get("state")
            .and_then(Value::as_str)
            .unwrap_or("pending")
            .to_string();
        for (key, slot) in [
            ("origin", &mut stage.origin),
            ("seconds", &mut stage.seconds),
            ("reason", &mut stage.reason),
        ] {
            if let Some(v) = clean.get(key) {
                *slot = v.clone();
            }
        }
        if let Some(v) = clean.get("counts") {
            stage.counts = v.clone();
        }
        d.events.push(("stage", Value::Object(clean).to_string()));
        let n = d.events.len();
        drop(d);
        self.changed.send_replace(n);
        true
    }

    /// Sets the end state and sends the last event. A second call changes nothing.
    fn finish(&self, outcome: Outcome) {
        let mut d = self.data();
        if d.state.ended() {
            return;
        }
        d.elapsed = Some(self.created.elapsed().as_secs_f64());
        // A stage that ran at the end of a job with no record did not end: it is not `running` in the job object.
        let reason = match &outcome {
            Outcome::Done { .. } => None,
            Outcome::Failed(error) if error.code() == "timeout" => Some("timeout"),
            Outcome::Failed(_) => Some("job_failed"),
            Outcome::Stopped => Some("stopped"),
        };
        if let Some(reason) = reason {
            for stage in d.stages.iter_mut().filter(|s| s.state == "running") {
                stage.state = "failed".into();
                stage.reason = json!(reason);
            }
        }
        let name = match outcome {
            Outcome::Done { valid, apertus } => {
                d.state = JobState::Done;
                d.valid = Some(valid);
                d.apertus = apertus;
                d.record_id = Some(self.record_id.clone());
                "done"
            }
            Outcome::Failed(error) => {
                d.state = JobState::Failed;
                d.error = Some(error.object());
                "failed"
            }
            Outcome::Stopped => {
                d.state = JobState::Stopped;
                "stopped"
            }
        };
        let data = self.json_of(&d).to_string();
        d.events.push((name, data));
        let n = d.events.len();
        drop(d);
        self.changed.send_replace(n);
    }

    /// The events from the position `from`, and whether the job ended.
    fn events_from(&self, from: usize) -> (Vec<(&'static str, String)>, bool) {
        let d = self.data();
        (
            d.events.get(from..).map(<[_]>::to_vec).unwrap_or_default(),
            d.state.ended(),
        )
    }

    /// Waits until the job has an end state, at most `limit`.
    async fn wait_end(&self, limit: Duration) {
        let mut rx = self.changed.subscribe();
        let _ = tokio::time::timeout(limit, async {
            while !self.state().ended() {
                if rx.changed().await.is_err() {
                    break;
                }
            }
        })
        .await;
    }
}

enum Outcome {
    Done {
        valid: bool,
        apertus: Option<String>,
    },
    Failed(ApiError),
    Stopped,
}

#[derive(Default)]
struct JobsInner {
    list: VecDeque<Arc<Job>>,
    active: Option<String>,
}

/// The jobs of this process. One job is `queued` or `running` at one time.
#[derive(Default)]
pub struct Jobs {
    inner: Mutex<JobsInner>,
    /// True while one request sends a file. A second upload at the same time gets `busy`.
    uploading: AtomicBool,
}

/// The one upload slot. It is free again when this value is dropped.
struct UploadSlot<'a>(&'a AtomicBool);

impl Drop for UploadSlot<'_> {
    fn drop(&mut self) {
        self.0.store(false, Ordering::Release);
    }
}

/// A word of the worker for a stage event: letters, digits, `_`, `.`, `:` and `-`, at most 64 characters.
fn clean_stage_word(value: Option<&Value>) -> Option<Value> {
    let s = value?.as_str()?;
    let ok = !s.is_empty()
        && s.len() <= 64
        && s.chars()
            .all(|c| c.is_ascii_alphanumeric() || matches!(c, '_' | '.' | ':' | '-'))
        && !s.contains("..");
    ok.then(|| json!(s))
}

/// The stage event that the server stores and sends, built from checked values of the worker line:
/// `id` and `state` of the lists, `origin` `stored` or `new`, `seconds` a number, `counts` a flat map
/// of numbers with short keys, `reason` and `note` one short word.
fn clean_stage(value: &Map<String, Value>) -> Map<String, Value> {
    let mut out = Map::new();
    out.insert("event".into(), json!("stage"));
    for key in ["id", "state"] {
        if let Some(v) = value.get(key).filter(|v| v.is_string()) {
            out.insert(key.into(), v.clone());
        }
    }
    if let Some(v) = value
        .get("origin")
        .filter(|v| matches!(v.as_str(), Some("stored" | "new")))
    {
        out.insert("origin".into(), v.clone());
    }
    if let Some(v) = value
        .get("seconds")
        .filter(|v| v.as_f64().is_some_and(|x| x.is_finite() && x >= 0.0))
    {
        out.insert("seconds".into(), v.clone());
    }
    if let Some(Value::Object(counts)) = value.get("counts") {
        let clean: Map<String, Value> = counts
            .iter()
            .filter(|(k, v)| {
                !k.is_empty()
                    && k.len() <= 32
                    && k.chars().all(|c| c.is_ascii_alphanumeric() || c == '_')
                    && v.is_number()
            })
            .take(12)
            .map(|(k, v)| (k.clone(), v.clone()))
            .collect();
        out.insert("counts".into(), Value::Object(clean));
    }
    for key in ["reason", "note"] {
        if let Some(v) = clean_stage_word(value.get(key)) {
            out.insert(key.into(), v);
        }
    }
    out
}

impl Jobs {
    fn inner(&self) -> MutexGuard<'_, JobsInner> {
        self.inner.lock().unwrap_or_else(|e| e.into_inner())
    }

    /// Takes the upload slot, or `None` if another request sends a file now.
    fn try_upload(&self) -> Option<UploadSlot<'_>> {
        self.uploading
            .compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
            .ok()
            .map(|_| UploadSlot(&self.uploading))
    }

    /// The id of the job that runs now.
    pub fn active_id(&self) -> Option<String> {
        self.inner().active.clone()
    }

    pub fn find(&self, id: &str) -> Option<Arc<Job>> {
        self.inner().list.iter().find(|j| j.id == id).cloned()
    }

    /// Makes the job the one active job. If another job is active, the answer is its id.
    fn try_start(&self, job: Arc<Job>) -> Result<(), String> {
        let mut inner = self.inner();
        if let Some(active) = &inner.active {
            return Err(active.clone());
        }
        inner.active = Some(job.id.clone());
        inner.list.push_back(job);
        while inner.list.len() > KEEP_JOBS {
            inner.list.pop_front();
        }
        Ok(())
    }

    fn clear_active(&self, id: &str) {
        let mut inner = self.inner();
        if inner.active.as_deref() == Some(id) {
            inner.active = None;
        }
    }

    /// Stops the active job (if one runs) and waits for its end. For the stop of the server.
    pub async fn stop_active(&self, limit: Duration) {
        let job = self.active_id().and_then(|id| self.find(&id));
        if let Some(job) = job {
            job.cancel.set();
            job.wait_end(limit).await;
        }
    }
}

// ---------------------------------------------------------------------------------------------
// The sample index
// ---------------------------------------------------------------------------------------------

/// Reads `samples/index.json`. An absent file gives an empty list. A broken file gives `internal`.
pub async fn read_index(cfg: &Config) -> Result<Vec<Value>, ApiError> {
    let path = cfg.data_dir.join("samples").join("index.json");
    let bytes = match tokio::fs::read(&path).await {
        Ok(b) => b,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
            tracing::warn!(target: "samples", "the sample index is absent");
            return Ok(Vec::new());
        }
        Err(e) => {
            tracing::error!(target: "samples", error = %e, "the sample index cannot be read");
            return Err(ApiError::new("internal").with("note", "samples_index"));
        }
    };
    let broken = || ApiError::new("internal").with("note", "samples_index");
    let value: Value = serde_json::from_slice(&bytes).map_err(|e| {
        tracing::error!(target: "samples", error = %e, "the sample index is not JSON");
        broken()
    })?;
    let samples = value
        .get("samples")
        .and_then(Value::as_array)
        .cloned()
        .ok_or_else(broken)?;
    // Only an entry with a valid document number is a sample.
    Ok(samples
        .into_iter()
        .filter(|s| sample_doc(s).is_some())
        .collect())
}

fn sample_doc(sample: &Value) -> Option<String> {
    let doc = match sample.get("doc_id")? {
        Value::String(s) => s.clone(),
        Value::Number(n) => n.to_string(),
        _ => return None,
    };
    ids::is_doc_number(&doc).then_some(doc)
}

fn record_id_for(base: &str, mode: &str) -> String {
    if mode == "rules" {
        format!("{base}-rules")
    } else {
        base.to_string()
    }
}

async fn record_ready(cfg: &Config, record_id: &str) -> bool {
    ids::is_record_id(record_id)
        && tokio::fs::metadata(cfg.records_dir().join(record_id).join("view.json"))
            .await
            .map(|m| m.is_file())
            .unwrap_or(false)
}

/// `GET /api/samples`
pub async fn get_samples(State(st): State<AppState>) -> Result<Response, ApiError> {
    let mut samples = read_index(&st.cfg).await?;
    for sample in &mut samples {
        let Some(doc) = sample_doc(sample) else {
            continue;
        };
        let base = format!("s-{doc}");
        let ready = json!({
            "auto": record_ready(&st.cfg, &base).await,
            "rules": record_ready(&st.cfg, &format!("{base}-rules")).await,
        });
        if let Some(map) = sample.as_object_mut() {
            map.insert("ready".into(), ready);
        }
    }
    Ok(json_response(
        &json!({"schema": "parlpdfech-samples/1", "samples": samples}),
    ))
}

// ---------------------------------------------------------------------------------------------
// POST /api/jobs
// ---------------------------------------------------------------------------------------------

/// Deletes the job folder if the request does not become a job.
struct DirGuard {
    path: PathBuf,
    keep: bool,
}

impl Drop for DirGuard {
    fn drop(&mut self) {
        if !self.keep {
            let _ = std::fs::remove_dir_all(&self.path);
        }
    }
}

struct Upload {
    file_name: String,
    bytes: u64,
    sha256: String,
}

#[derive(Default)]
struct Form {
    sample: Option<String>,
    doc_id: Option<String>,
    mode: Option<String>,
    upload: Option<Upload>,
}

fn bad(field: &str) -> ApiError {
    ApiError::new("bad_request").with("field", field)
}

fn too_large(cfg: &Config) -> ApiError {
    let mb = cfg.max_bytes as f64 / (1024.0 * 1024.0);
    let detail = if mb.fract() == 0.0 {
        json!(mb as u64)
    } else {
        json!((mb * 100.0).round() / 100.0)
    };
    ApiError::new("too_large")
        .with("max_mb", detail)
        .with("max_bytes", cfg.max_bytes)
}

/// `POST /api/jobs`: `multipart/form-data` (fields `file` or `sample`, `doc_id`, `mode`)
/// or JSON `{"sample": "<doc id>", "mode": "auto|rules"}` for a sample.
pub async fn post_job(State(st): State<AppState>, req: Request) -> Result<Response, ApiError> {
    // An early answer: the server first reads the rest of the body (up to the limit), so that a client
    // that sends the full body before it reads gets the answer and no reset of the connection.
    let drain_limit = st.cfg.max_bytes.saturating_add(4 * 1024 * 1024);
    if let Some(active) = st.jobs.active_id() {
        drain_body(req.into_body(), drain_limit).await;
        return Err(ApiError::new("busy").with("job_id", active));
    }
    let job_id = uuid::Uuid::new_v4().to_string();
    let job_dir = st.cfg.jobs_dir().join(&job_id);
    let mut guard = DirGuard {
        path: job_dir.clone(),
        keep: false,
    };

    let content_type = req
        .headers()
        .get(header::CONTENT_TYPE)
        .and_then(|v| v.to_str().ok())
        .unwrap_or("")
        .to_ascii_lowercase();
    let declared = req
        .headers()
        .get(header::CONTENT_LENGTH)
        .and_then(|v| v.to_str().ok())
        .and_then(|v| v.parse::<u64>().ok());

    let form = if content_type.starts_with("application/json") {
        if declared.is_some_and(|n| n > SMALL_BODY) {
            return Err(bad("body"));
        }
        let bytes = axum::body::to_bytes(req.into_body(), SMALL_BODY as usize)
            .await
            .map_err(|_| bad("body"))?;
        read_json_form(&bytes)?
    } else if content_type.starts_with("multipart/form-data") {
        if declared.is_some_and(|n| n > st.cfg.max_bytes.saturating_add(SMALL_BODY)) {
            drain_body(req.into_body(), drain_limit).await;
            return Err(too_large(&st.cfg));
        }
        // One request sends a file at one time: each open upload holds up to `max_bytes` in the work folder.
        let Some(_slot) = st.jobs.try_upload() else {
            drain_body(req.into_body(), drain_limit).await;
            return Err(
                ApiError::new("busy").with("job_id", st.jobs.active_id().unwrap_or_default())
            );
        };
        let mut multipart = Multipart::from_request(req, &())
            .await
            .map_err(|_| bad("body"))?;
        let read = tokio::time::timeout(
            st.cfg.upload_timeout,
            read_multipart_form(&st.cfg, &mut multipart, &job_dir),
        )
        .await;
        match read {
            Ok(Ok(form)) => form,
            Ok(Err(e)) => {
                drain_multipart(&mut multipart).await;
                return Err(e);
            }
            Err(_) => {
                tracing::warn!(target: "upload", seconds = st.cfg.upload_timeout.as_secs(), "the upload did not end in the time limit");
                return Err(bad("body"));
            }
        }
    } else {
        return Err(bad("body"));
    };

    let mode = form.mode.unwrap_or_else(|| "auto".into());
    if mode != "auto" && mode != "rules" {
        return Err(bad("mode"));
    }
    let samples = read_index(&st.cfg).await?;

    let job = match (form.upload, form.sample) {
        (Some(_), Some(_)) => return Err(bad("sample")),
        (None, None) => return Err(bad("file")),
        (None, Some(sample)) => {
            if form.doc_id.is_some() {
                return Err(bad("doc_id"));
            }
            if !ids::is_doc_number(&sample) {
                return Err(ApiError::new("sample_unknown").with("doc_id", clean_word(&sample)));
            }
            let entry = samples
                .iter()
                .find(|s| sample_doc(s).as_deref() == Some(sample.as_str()))
                .ok_or_else(|| ApiError::new("sample_unknown").with("doc_id", sample.clone()))?;
            let modes = entry.get("modes").and_then(Value::as_array);
            if modes.is_some_and(|m| !m.iter().any(|x| x.as_str() == Some(mode.as_str()))) {
                return Err(bad("mode"));
            }
            let input = JobInput {
                kind: "sample",
                doc_id: Some(sample.clone()),
                file_name: None,
                bytes: None,
                pdf_sha256: entry
                    .get("pdf_sha256")
                    .and_then(Value::as_str)
                    .filter(|s| is_sha256(s))
                    .map(str::to_string),
            };
            let record_id = record_id_for(&format!("s-{sample}"), &mode);
            // A site that serves the prepared records only: no new run for a record that is ready.
            if !st.cfg.sample_runs && record_ready(&st.cfg, &record_id).await {
                return Err(ApiError::new("sample_runs_off").with("record_id", record_id));
            }
            Job::new(job_id.clone(), input, mode, record_id, Some(sample))
        }
        (Some(upload), None) => {
            if let Some(doc) = &form.doc_id {
                if !ids::is_doc_number(doc) {
                    return Err(bad("doc_id"));
                }
            }
            // An upload whose SHA-256 is in the sample index gets the id of the sample.
            let base = samples
                .iter()
                .find(|s| {
                    s.get("pdf_sha256").and_then(Value::as_str) == Some(upload.sha256.as_str())
                })
                .and_then(sample_doc)
                .map(|doc| format!("s-{doc}"))
                .unwrap_or_else(|| format!("u-{}", &upload.sha256[..16]));
            let input = JobInput {
                kind: "upload",
                doc_id: form.doc_id,
                file_name: Some(upload.file_name),
                bytes: Some(upload.bytes),
                pdf_sha256: Some(upload.sha256),
            };
            let record_id = record_id_for(&base, &mode);
            Job::new(job_id.clone(), input, mode, record_id, None)
        }
    };

    let job = Arc::new(job);
    if let Err(active) = st.jobs.try_start(job.clone()) {
        return Err(ApiError::new("busy").with("job_id", active));
    }
    guard.keep = true;
    tracing::info!(
        target: "job",
        job_id = %job.id,
        kind = job.input.kind,
        mode = %job.mode,
        record_id = %job.record_id,
        bytes = job.input.bytes.unwrap_or(0),
        "job accepted"
    );
    tokio::spawn(run_job(st.clone(), job.clone()));

    let mut res = json_response(&json!({
        "job_id": job.id,
        "state": "queued",
        "events": format!("/api/jobs/{}/events", job.id),
        "status": format!("/api/jobs/{}", job.id),
    }));
    *res.status_mut() = StatusCode::ACCEPTED;
    Ok(res)
}

fn is_sha256(s: &str) -> bool {
    s.len() == 64
        && s.bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

/// A client value for `detail`: letters, digits, `_` and `-` only, at most 40 characters.
fn clean_word(s: &str) -> String {
    s.chars()
        .filter(|c| c.is_ascii_alphanumeric() || matches!(c, '_' | '-'))
        .take(40)
        .collect()
}

fn read_json_form(bytes: &[u8]) -> Result<Form, ApiError> {
    let value: Value = serde_json::from_slice(bytes).map_err(|_| bad("body"))?;
    let map = value.as_object().ok_or_else(|| bad("body"))?;
    if map.contains_key("file") {
        return Err(bad("file"));
    }
    let text = |key: &str| -> Result<Option<String>, ApiError> {
        match map.get(key) {
            None | Some(Value::Null) => Ok(None),
            Some(Value::String(s)) if s.len() <= 256 => Ok(Some(s.clone())),
            Some(Value::Number(n)) if n.is_u64() => Ok(Some(n.to_string())),
            _ => Err(bad(key)),
        }
    };
    Ok(Form {
        sample: text("sample")?,
        doc_id: text("doc_id")?,
        mode: text("mode")?,
        upload: None,
    })
}

/// Reads and drops the rest of a request body, at most `limit` bytes and 5 s.
async fn drain_body(body: Body, limit: u64) {
    let mut stream = body.into_data_stream();
    let mut total: u64 = 0;
    let _ = tokio::time::timeout(Duration::from_secs(5), async {
        while let Some(Ok(chunk)) = stream.next().await {
            total += chunk.len() as u64;
            if total > limit {
                break;
            }
        }
    })
    .await;
}

/// Reads and drops the rest of a form after an error, at most 5 s. The body limit of the route applies.
async fn drain_multipart(multipart: &mut Multipart) {
    let _ = tokio::time::timeout(Duration::from_secs(5), async {
        while let Ok(Some(mut field)) = multipart.next_field().await {
            while let Ok(Some(_)) = field.chunk().await {}
        }
    })
    .await;
}

async fn read_multipart_form(
    cfg: &Config,
    multipart: &mut Multipart,
    job_dir: &Path,
) -> Result<Form, ApiError> {
    let mut form = Form::default();
    let mut small: u64 = 0;
    loop {
        let field = match multipart.next_field().await {
            Ok(Some(f)) => f,
            Ok(None) => break,
            Err(e) if e.status() == StatusCode::PAYLOAD_TOO_LARGE => return Err(too_large(cfg)),
            Err(_) => return Err(bad("body")),
        };
        let name = field.name().unwrap_or("").to_string();
        match name.as_str() {
            "file" => {
                // A public site takes no file: nothing of the body is written to the work folder.
                if cfg.readonly {
                    return Err(ApiError::new("read_only").with("note", "upload"));
                }
                if form.upload.is_some() {
                    return Err(bad("file"));
                }
                form.upload = Some(read_file_field(cfg, field, job_dir).await?);
            }
            "sample" | "doc_id" | "mode" => {
                let text = read_small_field(cfg, field, &mut small).await?;
                let text = String::from_utf8(text)
                    .map_err(|_| bad(&name))?
                    .trim()
                    .to_string();
                if text.len() > 256 {
                    return Err(bad(&name));
                }
                let slot = match name.as_str() {
                    "sample" => &mut form.sample,
                    "doc_id" => &mut form.doc_id,
                    _ => &mut form.mode,
                };
                // An empty optional field of a browser form counts as absent.
                if !text.is_empty() {
                    *slot = Some(text);
                }
            }
            _ => {
                read_small_field(cfg, field, &mut small).await?;
            }
        }
    }
    Ok(form)
}

/// Reads a form field that is not the file. All such fields together have the limit of 64 KB.
async fn read_small_field(
    cfg: &Config,
    mut field: Field<'_>,
    total: &mut u64,
) -> Result<Vec<u8>, ApiError> {
    let mut out = Vec::new();
    loop {
        match field.chunk().await {
            Ok(Some(chunk)) => {
                *total += chunk.len() as u64;
                if *total > SMALL_BODY {
                    return Err(bad("body"));
                }
                out.extend_from_slice(&chunk);
            }
            Ok(None) => return Ok(out),
            Err(e) if e.status() == StatusCode::PAYLOAD_TOO_LARGE => return Err(too_large(cfg)),
            Err(_) => return Err(bad("body")),
        }
    }
}

/// Streams the field `file` to `<job_dir>/input.pdf`. The checks run while the body arrives:
/// the size limit, the PDF mark in the first 1024 bytes, the SHA-256.
/// The file name on the disk is fixed. The name of the client is for display only.
async fn read_file_field(
    cfg: &Config,
    mut field: Field<'_>,
    job_dir: &Path,
) -> Result<Upload, ApiError> {
    let internal = |note: &'static str| {
        move |e: std::io::Error| {
            tracing::error!(target: "upload", error = %e, note, "file system error");
            ApiError::new("internal").with("note", note)
        }
    };
    let file_name = ids::display_file_name(field.file_name().unwrap_or(""));
    tokio::fs::create_dir_all(job_dir)
        .await
        .map_err(internal("job_dir"))?;
    let mut file = tokio::fs::File::create(job_dir.join("input.pdf"))
        .await
        .map_err(internal("upload_file"))?;
    let mut hasher = Sha256::new();
    let mut head: Vec<u8> = Vec::with_capacity(1024);
    let mut mark_checked = false;
    let mut total: u64 = 0;
    loop {
        let chunk = match field.chunk().await {
            Ok(Some(c)) => c,
            Ok(None) => break,
            Err(e) if e.status() == StatusCode::PAYLOAD_TOO_LARGE => return Err(too_large(cfg)),
            Err(_) => return Err(bad("file")),
        };
        total += chunk.len() as u64;
        if total > cfg.max_bytes {
            return Err(too_large(cfg));
        }
        if !mark_checked {
            let take = (1024 - head.len()).min(chunk.len());
            head.extend_from_slice(&chunk[..take]);
            if head.len() == 1024 {
                if !ids::has_pdf_mark(&head) {
                    return Err(ApiError::new("not_pdf"));
                }
                mark_checked = true;
            }
        }
        hasher.update(&chunk);
        file.write_all(&chunk)
            .await
            .map_err(internal("upload_write"))?;
    }
    if !mark_checked && !ids::has_pdf_mark(&head) {
        return Err(ApiError::new("not_pdf"));
    }
    file.flush().await.map_err(internal("upload_write"))?;
    Ok(Upload {
        file_name,
        bytes: total,
        sha256: hex::encode(hasher.finalize()),
    })
}

// ---------------------------------------------------------------------------------------------
// The worker process
// ---------------------------------------------------------------------------------------------

async fn run_job(st: AppState, job: Arc<Job>) {
    let job_dir = st.cfg.jobs_dir().join(&job.id);
    job.data().state = JobState::Running;
    let outcome = execute(&st.cfg, &job, &job_dir).await;
    if let Err(e) = tokio::fs::remove_dir_all(&job_dir).await {
        if e.kind() != std::io::ErrorKind::NotFound {
            tracing::warn!(target: "job", job_id = %job.id, error = %e, "the job folder was not deleted");
        }
    }
    let (word, code) = match &outcome {
        Outcome::Done { valid: true, .. } => ("done", "valid"),
        Outcome::Done { valid: false, .. } => ("done", "not_valid"),
        Outcome::Failed(e) => ("failed", e.code()),
        Outcome::Stopped => ("stopped", "stopped"),
    };
    tracing::info!(
        target: "job",
        job_id = %job.id,
        state = word,
        result = code,
        seconds = job.created.elapsed().as_secs_f64(),
        "job ended"
    );
    // The next job can start before a reader sees the last event.
    st.jobs.clear_active(&job.id);
    job.finish(outcome);
}

enum Ended {
    Lines(Option<Map<String, Value>>),
    Timeout,
    Cancel,
}

async fn execute(cfg: &Config, job: &Job, job_dir: &Path) -> Outcome {
    let internal =
        |note: &'static str| Outcome::Failed(ApiError::new("internal").with("note", note));
    if let Err(e) = tokio::fs::create_dir_all(job_dir).await {
        tracing::error!(target: "job", job_id = %job.id, error = %e, "the job folder was not made");
        return internal("job_dir");
    }
    let out_dir = job_dir.join("out");

    let mut cmd = Command::new(&cfg.worker_cmd[0]);
    cmd.args(&cfg.worker_cmd[1..]);
    match &job.sample {
        Some(doc) => {
            cmd.arg("--sample").arg(doc);
        }
        None => {
            cmd.arg("--pdf").arg(job_dir.join("input.pdf"));
            if let Some(doc) = &job.input.doc_id {
                cmd.arg("--doc-id").arg(doc);
            }
        }
    }
    cmd.arg("--mode")
        .arg(&job.mode)
        .arg("--out")
        .arg(&out_dir)
        .arg("--data-dir")
        .arg(&cfg.data_dir);
    cmd.env("PARLPDFECH_PROFILE", &cfg.profile)
        .env("PARLPDFECH_MAX_PAGES", cfg.max_pages.to_string())
        .env("PARLPDFECH_DATA_DIR", &cfg.data_dir)
        .env("PYTHONUNBUFFERED", "1");
    if let Some(cwd) = &cfg.worker_cwd {
        cmd.current_dir(cwd);
    }
    // The worker gets its own process group. A stop reaches the worker and the processes that it started.
    cmd.stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .kill_on_drop(true)
        .process_group(0);

    let mut child = match cmd.spawn() {
        Ok(c) => c,
        Err(e) => {
            tracing::error!(target: "job", job_id = %job.id, error = %e, "the worker did not start");
            return Outcome::Failed(ApiError::new("converter_stopped").with("note", "spawn"));
        }
    };
    let (Some(stdout), Some(stderr)) = (child.stdout.take(), child.stderr.take()) else {
        let group = child_group(&child);
        stop_child(&mut child, &group, cfg.kill_grace).await;
        return internal("pipes");
    };
    // The id of the process group. `Child::id` gives no value after the wait, so the value is read now.
    let group = child_group(&child);
    tracing::info!(target: "job", job_id = %job.id, pid = child.id().unwrap_or(0), "worker started");

    // Standard error of the worker goes to the log of the server only.
    let log_id = job.id.clone();
    let stderr_task = tokio::spawn(async move {
        let mut reader = BufReader::new(stderr);
        let mut buf = Vec::new();
        while let Ok(read) = read_line(&mut reader, &mut buf).await {
            match read {
                LineRead::Eof => break,
                LineRead::TooLong => {
                    tracing::warn!(target: "worker", job_id = %log_id, "a long line was dropped")
                }
                LineRead::Line => {
                    // No control character of the worker reaches a terminal that shows the log.
                    let text = String::from_utf8_lossy(&buf);
                    let line: String = text
                        .trim_end()
                        .chars()
                        .take(MAX_LOG_LINE)
                        .map(|c| {
                            if c.is_control() && c != '\t' {
                                '\u{fffd}'
                            } else {
                                c
                            }
                        })
                        .collect();
                    tracing::info!(target: "worker", job_id = %log_id, line = %line)
                }
            }
        }
    });

    let deadline = tokio::time::sleep(cfg.job_timeout);
    tokio::pin!(deadline);

    let lines = read_worker_lines(job, stdout);
    let first = tokio::select! {
        last = lines => Ended::Lines(last),
        _ = &mut deadline => Ended::Timeout,
        _ = job.cancel.wait() => Ended::Cancel,
    };
    let (last, status) = match first {
        Ended::Lines(last) => {
            let waited = tokio::select! {
                status = child.wait() => Ok(status),
                _ = &mut deadline => Err(Ended::Timeout),
                _ = job.cancel.wait() => Err(Ended::Cancel),
            };
            match waited {
                Ok(status) => (last, Ok(status)),
                Err(e) => (last, Err(e)),
            }
        }
        other => (None, Err(other)),
    };

    let status = match status {
        Ok(Ok(status)) => status,
        Ok(Err(e)) => {
            tracing::error!(target: "job", job_id = %job.id, error = %e, "wait for the worker failed");
            stop_child(&mut child, &group, cfg.kill_grace).await;
            return Outcome::Failed(ApiError::new("converter_stopped").with("note", "wait"));
        }
        Err(ended) => {
            stop_child(&mut child, &group, cfg.kill_grace).await;
            let _ = tokio::time::timeout(Duration::from_secs(1), stderr_task).await;
            return match ended {
                Ended::Cancel => Outcome::Stopped,
                _ => Outcome::Failed(
                    ApiError::new("timeout").with("seconds", cfg.job_timeout.as_secs()),
                ),
            };
        }
    };
    let _ = tokio::time::timeout(Duration::from_secs(1), stderr_task).await;
    // A process of the group that still runs after the end of the worker is stopped too.
    signal_group(&group, rustix::process::Signal::KILL);

    let code = status.code();
    tracing::info!(target: "job", job_id = %job.id, exit_code = code.unwrap_or(-1), "worker ended");
    let stopped =
        |note: String| Outcome::Failed(ApiError::new("converter_stopped").with("note", note));
    let exit_note = || match code {
        Some(c) => format!("exit_{c}"),
        None => "exit_signal".to_string(),
    };
    let Some(last) = last else {
        return stopped(exit_note());
    };
    match (last.get("event").and_then(Value::as_str), code) {
        (Some("done"), Some(0 | 2)) => {
            let valid = code == Some(0);
            if last.get("valid").and_then(Value::as_bool) != Some(valid) {
                return stopped("protocol".into());
            }
            if last.get("record_id").and_then(Value::as_str) != Some(job.record_id.as_str()) {
                tracing::error!(target: "job", job_id = %job.id, "the record id of the worker is not the expected id");
                return stopped("record_id".into());
            }
            if let Err(note) = install_record(cfg, job, &out_dir).await {
                return stopped(note.to_string());
            }
            let apertus = last
                .get("apertus")
                .and_then(Value::as_str)
                .filter(|a| matches!(*a, "none" | "stored"))
                .map(str::to_string);
            Outcome::Done { valid, apertus }
        }
        (Some("failed"), Some(exit @ (3 | 4))) => {
            let worker_code = last.get("code").and_then(Value::as_str).unwrap_or("");
            let allowed = if exit == 3 {
                REFUSED.contains(&worker_code)
            } else {
                worker_code == "converter_stopped"
            };
            if !allowed {
                return stopped("protocol".into());
            }
            Outcome::Failed(
                ApiError::new(worker_code).with_detail(clean_detail(last.get("detail"))),
            )
        }
        _ => stopped(exit_note()),
    }
}

/// Reads the standard output of the worker. A stage line goes to the job. The answer is the
/// last line with the event `done` or `failed`. A line that is not a JSON object of the
/// protocol goes to the log only.
async fn read_worker_lines(
    job: &Job,
    stdout: tokio::process::ChildStdout,
) -> Option<Map<String, Value>> {
    let mut reader = BufReader::new(stdout);
    let mut buf = Vec::new();
    let mut last = None;
    let mut dropped: u64 = 0;
    loop {
        match read_line(&mut reader, &mut buf).await {
            Ok(LineRead::Eof) | Err(_) => break,
            Ok(LineRead::TooLong) => dropped += 1,
            Ok(LineRead::Line) => {
                let parsed = std::str::from_utf8(&buf)
                    .ok()
                    .map(|t| t.trim_end_matches(['\r', '\n']))
                    .and_then(|t| serde_json::from_str::<Value>(t).ok());
                let Some(Value::Object(map)) = parsed else {
                    dropped += 1;
                    continue;
                };
                let is = |key: &str, allowed: &[&str]| {
                    map.get(key)
                        .and_then(Value::as_str)
                        .is_some_and(|v| allowed.contains(&v))
                };
                match map.get("event").and_then(Value::as_str) {
                    Some("stage")
                        if last.is_none() && is("id", &STAGES) && is("state", &STAGE_STATES) =>
                    {
                        if !job.push_stage(&map) {
                            dropped += 1;
                        }
                    }
                    Some("done" | "failed") => last = Some(map),
                    _ => dropped += 1,
                }
            }
        }
    }
    if dropped > 0 {
        tracing::warn!(target: "job", job_id = %job.id, lines = dropped, "lines of the worker were dropped (not a line of the protocol)");
    }
    last
}

enum LineRead {
    Line,
    TooLong,
    Eof,
}

/// Reads one line into `buf`. A line above `MAX_LINE` is read to its end and not stored.
async fn read_line<R: AsyncBufRead + Unpin>(
    reader: &mut R,
    buf: &mut Vec<u8>,
) -> std::io::Result<LineRead> {
    buf.clear();
    let n = (&mut *reader)
        .take(MAX_LINE as u64 + 1)
        .read_until(b'\n', buf)
        .await?;
    if n == 0 {
        return Ok(LineRead::Eof);
    }
    if buf.last() == Some(&b'\n') || buf.len() <= MAX_LINE {
        return Ok(LineRead::Line);
    }
    loop {
        buf.clear();
        let n = (&mut *reader)
            .take(64 * 1024)
            .read_until(b'\n', buf)
            .await?;
        if n == 0 || buf.last() == Some(&b'\n') {
            buf.clear();
            return Ok(LineRead::TooLong);
        }
    }
}

fn child_group(child: &Child) -> Option<rustix::process::Pid> {
    child
        .id()
        .and_then(|id| i32::try_from(id).ok())
        .and_then(rustix::process::Pid::from_raw)
}

fn signal_group(group: &Option<rustix::process::Pid>, signal: rustix::process::Signal) {
    if let Some(pid) = group {
        // An error says that the group has no process. This is the wanted state.
        let _ = rustix::process::kill_process_group(*pid, signal);
    }
}

/// Stops the worker: the signal TERM to its process group, then the signal KILL after the grace time.
async fn stop_child(child: &mut Child, group: &Option<rustix::process::Pid>, grace: Duration) {
    signal_group(group, rustix::process::Signal::TERM);
    if tokio::time::timeout(grace, child.wait()).await.is_err() {
        signal_group(group, rustix::process::Signal::KILL);
        let _ = child.kill().await;
    } else {
        signal_group(group, rustix::process::Signal::KILL);
    }
}

/// Moves `jobs/<job_id>/out` to `records/<record_id>/`. An old record with the id is replaced
/// by a rename of the full folder. The error value is a short word.
async fn install_record(cfg: &Config, job: &Job, out_dir: &Path) -> Result<(), &'static str> {
    if !ids::is_record_id(&job.record_id) {
        return Err("record_id");
    }
    let mut entries = tokio::fs::read_dir(out_dir)
        .await
        .map_err(|_| "no_output")?;
    let mut has_view = false;
    let mut kept: Vec<String> = Vec::new();
    while let Ok(Some(entry)) = entries.next_entry().await {
        let name = entry.file_name();
        let allowed = name
            .to_str()
            .is_some_and(|n| ids::file_media_type(n).is_some());
        let is_file = entry
            .file_type()
            .await
            .map(|t| t.is_file())
            .unwrap_or(false);
        if allowed && is_file {
            has_view |= name.to_str() == Some("view.json");
            kept.extend(name.to_str().map(str::to_string));
        } else {
            // The record folder holds only the files of the contract.
            tracing::warn!(target: "job", job_id = %job.id, "an entry of the output that is not a record file was deleted");
            let path = entry.path();
            if tokio::fs::remove_dir_all(&path).await.is_err() {
                let _ = tokio::fs::remove_file(&path).await;
            }
        }
    }
    if !has_view {
        return Err("no_view");
    }
    // A record is the 11 files of CONTRACT.md chapter 3 with one document prefix, and no other file.
    if !ids::is_complete_record(&kept) {
        tracing::error!(target: "job", job_id = %job.id, files = kept.len(), "the output of the worker is not a complete record");
        return Err("output");
    }
    let records = cfg.records_dir();
    tokio::fs::create_dir_all(&records)
        .await
        .map_err(|_| "records_dir")?;
    let target = records.join(&job.record_id);
    let old = records.join(format!(".old-{}", job.id));
    let had_old = tokio::fs::rename(&target, &old).await.is_ok();
    if let Err(e) = tokio::fs::rename(out_dir, &target).await {
        tracing::error!(target: "job", job_id = %job.id, error = %e, "the record was not moved");
        if had_old {
            let _ = tokio::fs::rename(&old, &target).await;
        }
        return Err("record_move");
    }
    if had_old {
        let _ = tokio::fs::remove_dir_all(&old).await;
    }
    Ok(())
}

// ---------------------------------------------------------------------------------------------
// GET and DELETE /api/jobs/{id}, the event stream
// ---------------------------------------------------------------------------------------------

fn find_job(st: &AppState, id: &str) -> Result<Arc<Job>, ApiError> {
    if !ids::is_job_id(id) {
        return Err(ApiError::new("job_unknown"));
    }
    st.jobs.find(id).ok_or_else(|| ApiError::new("job_unknown"))
}

/// `GET /api/jobs/{id}`
pub async fn get_job(
    State(st): State<AppState>,
    UrlPath(id): UrlPath<String>,
) -> Result<Response, ApiError> {
    Ok(json_response(&find_job(&st, &id)?.to_json()))
}

/// `DELETE /api/jobs/{id}`: stops a running job. A job that ended is not changed. No record is deleted.
pub async fn delete_job(
    State(st): State<AppState>,
    UrlPath(id): UrlPath<String>,
) -> Result<Response, ApiError> {
    let job = find_job(&st, &id)?;
    if !job.state().ended() {
        tracing::info!(target: "job", job_id = %job.id, "stop requested");
        job.cancel.set();
        job.wait_end(st.cfg.kill_grace + Duration::from_secs(5))
            .await;
    }
    Ok(json_response(&job.to_json()))
}

/// `GET /api/jobs/{id}/events`: all earlier events of the job, then the new events, a ping
/// comment in each interval with no event. The stream ends after `done`, `failed` or `stopped`.
pub async fn job_events(
    State(st): State<AppState>,
    UrlPath(id): UrlPath<String>,
) -> Result<Response, ApiError> {
    let job = find_job(&st, &id)?;
    let ping = st.cfg.ping_interval;
    let (tx, rx) = mpsc::channel::<Result<Bytes, Infallible>>(32);
    let mut changed = job.changed.subscribe();
    tokio::spawn(async move {
        let mut sent = 0usize;
        loop {
            let (batch, ended) = job.events_from(sent);
            for (name, data) in batch {
                let frame = format!("event: {name}\ndata: {data}\n\n");
                if tx.send(Ok(Bytes::from(frame))).await.is_err() {
                    return;
                }
                sent += 1;
            }
            if ended {
                return;
            }
            tokio::select! {
                waited = tokio::time::timeout(ping, changed.changed()) => match waited {
                    Ok(Ok(())) => {}
                    Ok(Err(_)) => return,
                    Err(_) => {
                        if tx.send(Ok(Bytes::from_static(b": ping\n\n"))).await.is_err() {
                            return;
                        }
                    }
                },
                _ = tx.closed() => return,
            }
        }
    });
    let mut res = Body::from_stream(ReceiverStream::new(rx)).into_response();
    let h = res.headers_mut();
    h.insert(
        header::CONTENT_TYPE,
        HeaderValue::from_static("text/event-stream"),
    );
    h.insert("x-accel-buffering", HeaderValue::from_static("no"));
    Ok(res)
}
