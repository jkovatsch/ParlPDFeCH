//! Integration tests of the API with the fake worker `tests/fake_worker.py`.
//! The tests call the router in the process. They open no port.

use std::path::{Path, PathBuf};
use std::time::Duration;

use axum::body::Body;
use axum::http::{header, HeaderMap, Method, Request, StatusCode};
use axum::Router;
use parlpdfech_server::{build_app, AppState, Config};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use tower::ServiceExt;

const CSP: &str =
    "default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self'; img-src 'self'; \
font-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'";

/// The `Host` value of the test requests (the server refuses a request with no loopback host name).
const HOST: &str = "127.0.0.1:8080";

/// The policy of each answer that is not below `/app/` or `/api/` (the static site).
const SITE_CSP: &str =
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; \
base-uri 'none'; form-action 'none'; frame-ancestors 'none'";

struct Env {
    tmp: tempfile::TempDir,
    app: Router,
    state: AppState,
}

impl Env {
    fn work(&self) -> PathBuf {
        self.tmp.path().join("work")
    }
}

fn manifest_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn env_with(case: &str, change: impl FnOnce(&mut Config, &Path)) -> Env {
    let tmp = tempfile::tempdir().unwrap();
    let ui = tmp.path().join("ui");
    std::fs::create_dir_all(ui.join("pkg")).unwrap();
    std::fs::write(
        ui.join("index.html"),
        "<!doctype html><title>test page</title>",
    )
    .unwrap();
    std::fs::write(ui.join("app.js"), "// test script\n").unwrap();
    std::fs::write(ui.join("app.0123abcd.js"), "// test script with a hash\n").unwrap();
    std::fs::write(ui.join("app.css"), "body{}\n").unwrap();
    std::fs::write(
        ui.join("pkg").join("parlpdfech_rdfcheck_bg.wasm"),
        b"\0asm\x01\0\0\0",
    )
    .unwrap();
    std::fs::write(tmp.path().join("secret.txt"), "outside of the UI folder").unwrap();
    let mut cfg = Config {
        profile: "native".into(),
        bind: "127.0.0.1:0".into(),
        ui_dir: ui,
        data_dir: manifest_dir().join("tests/fixtures/data"),
        work_dir: tmp.path().join("work"),
        worker_cmd: vec![
            "python3".into(),
            manifest_dir()
                .join("tests/fake_worker.py")
                .to_string_lossy()
                .into_owned(),
            "--case".into(),
            case.into(),
        ],
        worker_cwd: None,
        site_dir: None,
        max_bytes: 64 * 1024,
        max_pages: 25,
        job_timeout: Duration::from_secs(30),
        commit: "test".into(),
        ping_interval: Duration::from_secs(15),
        kill_grace: Duration::from_millis(500),
        allowed_hosts: Vec::new(),
        upload_timeout: Duration::from_secs(30),
        readonly: false,
        sample_runs: true,
        hosted: false,
    };
    change(&mut cfg, tmp.path());
    let state = AppState::new(cfg);
    state.prepare_work_dir().unwrap();
    Env {
        tmp,
        app: build_app(state.clone()),
        state,
    }
}

fn env(case: &str) -> Env {
    env_with(case, |_, _| {})
}

async fn call(app: &Router, req: Request<Body>) -> (StatusCode, HeaderMap, Vec<u8>) {
    let res = app.clone().oneshot(req).await.unwrap();
    let status = res.status();
    let headers = res.headers().clone();
    let body = axum::body::to_bytes(res.into_body(), 64 * 1024 * 1024)
        .await
        .unwrap();
    (status, headers, body.to_vec())
}

fn request(method: Method, path: &str) -> Request<Body> {
    Request::builder()
        .method(method)
        .uri(path)
        .header(header::HOST, HOST)
        .body(Body::empty())
        .unwrap()
}

async fn get(app: &Router, path: &str) -> (StatusCode, HeaderMap, Vec<u8>) {
    call(app, request(Method::GET, path)).await
}

async fn get_json(app: &Router, path: &str) -> (StatusCode, Value) {
    let (status, _, body) = get(app, path).await;
    (
        status,
        serde_json::from_slice(&body).unwrap_or_else(|_| {
            panic!("no JSON from {path}: {:?}", String::from_utf8_lossy(&body))
        }),
    )
}

async fn post_json(app: &Router, value: Value) -> (StatusCode, Value) {
    let req = Request::builder()
        .method(Method::POST)
        .uri("/api/jobs")
        .header(header::HOST, HOST)
        .header(header::CONTENT_TYPE, "application/json")
        .body(Body::from(value.to_string()))
        .unwrap();
    let (status, _, body) = call(app, req).await;
    (status, serde_json::from_slice(&body).unwrap())
}

const BOUNDARY: &str = "----testboundary7MA4YWxkTrZu0gW";

/// One part of a form: (field name, file name of the client, bytes).
type Part<'a> = (&'a str, Option<&'a str>, &'a [u8]);

/// Builds the request of a form.
fn multipart(parts: &[(&str, Option<&str>, &[u8])]) -> Request<Body> {
    let mut body = Vec::new();
    for (name, file_name, bytes) in parts {
        body.extend_from_slice(format!("--{BOUNDARY}\r\n").as_bytes());
        match file_name {
            Some(f) => body.extend_from_slice(
                format!("Content-Disposition: form-data; name=\"{name}\"; filename=\"{f}\"\r\nContent-Type: application/pdf\r\n\r\n").as_bytes(),
            ),
            None => body.extend_from_slice(format!("Content-Disposition: form-data; name=\"{name}\"\r\n\r\n").as_bytes()),
        }
        body.extend_from_slice(bytes);
        body.extend_from_slice(b"\r\n");
    }
    body.extend_from_slice(format!("--{BOUNDARY}--\r\n").as_bytes());
    Request::builder()
        .method(Method::POST)
        .uri("/api/jobs")
        .header(header::HOST, HOST)
        .header(
            header::CONTENT_TYPE,
            format!("multipart/form-data; boundary={BOUNDARY}"),
        )
        .header(header::CONTENT_LENGTH, body.len())
        .body(Body::from(body))
        .unwrap()
}

async fn post_form(app: &Router, parts: &[(&str, Option<&str>, &[u8])]) -> (StatusCode, Value) {
    let (status, _, body) = call(app, multipart(parts)).await;
    (status, serde_json::from_slice(&body).unwrap())
}

/// A small synthetic PDF. The test writes it. It is not a document of the project.
fn tiny_pdf(text: &str) -> Vec<u8> {
    format!(
        "%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n\
3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>\nendobj\n% {text}\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
    )
    .into_bytes()
}

/// The events of a job as (event name, data). The call returns when the server closes the stream.
async fn events(app: &Router, job_id: &str) -> Vec<(String, String)> {
    let (status, headers, body) = get(app, &format!("/api/jobs/{job_id}/events")).await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(headers[header::CONTENT_TYPE], "text/event-stream");
    parse_events(&String::from_utf8(body).unwrap())
}

fn parse_events(text: &str) -> Vec<(String, String)> {
    text.split("\n\n")
        .filter_map(|frame| {
            let mut name = None;
            let mut data = None;
            for line in frame.lines() {
                if let Some(v) = line.strip_prefix("event: ") {
                    name = Some(v.to_string());
                } else if let Some(v) = line.strip_prefix("data: ") {
                    data = Some(v.to_string());
                }
            }
            Some((name?, data?))
        })
        .collect()
}

async fn start_sample(app: &Router, doc: &str, mode: &str) -> String {
    let (status, body) = post_json(app, json!({"sample": doc, "mode": mode})).await;
    assert_eq!(status, StatusCode::ACCEPTED, "{body}");
    assert_eq!(body["state"], "queued");
    let id = body["job_id"].as_str().unwrap().to_string();
    assert_eq!(body["events"], format!("/api/jobs/{id}/events"));
    assert_eq!(body["status"], format!("/api/jobs/{id}"));
    id
}

fn assert_error(status: StatusCode, body: &Value, code: &str, http: u16) {
    assert_eq!(status.as_u16(), http, "{body}");
    let e = &body["error"];
    assert_eq!(e["code"], code, "{body}");
    for key in ["title", "text", "action"] {
        for lang in ["en", "de"] {
            let text = e[key][lang].as_str().unwrap();
            assert!(
                !text.is_empty() && !text.contains('{'),
                "{code} {key} {lang}: {text}"
            );
        }
    }
    assert!(e["exits"].is_array() && e["detail"].is_object());
}

fn jobs_dir_is_empty(env: &Env) -> bool {
    std::fs::read_dir(env.work().join("jobs"))
        .unwrap()
        .next()
        .is_none()
}

fn pid_runs(pid: u64) -> bool {
    std::process::Command::new("kill")
        .args(["-0", &pid.to_string()])
        .stderr(std::process::Stdio::null())
        .status()
        .unwrap()
        .success()
}

// ------------------------------------------------------------------------------------------

#[tokio::test]
async fn health_and_headers() {
    let env = env("auto");
    let (status, headers, body) = get(&env.app, "/healthz").await;
    assert_eq!(
        (status, body.as_slice()),
        (StatusCode::OK, b"ok".as_slice())
    );
    assert!(headers[header::CONTENT_TYPE]
        .to_str()
        .unwrap()
        .starts_with("text/plain"));

    let (status, headers, body) = get(&env.app, "/api/health").await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(
        headers[header::CONTENT_TYPE],
        "application/json; charset=utf-8"
    );
    assert_eq!(headers[header::CACHE_CONTROL], "no-store");
    assert_eq!(headers["x-content-type-options"], "nosniff");
    assert_eq!(headers["referrer-policy"], "no-referrer");
    assert_eq!(headers["x-frame-options"], "DENY");
    assert_eq!(headers["cross-origin-opener-policy"], "same-origin");
    assert_eq!(headers["cross-origin-resource-policy"], "same-origin");
    assert_eq!(
        headers["permissions-policy"],
        "camera=(), microphone=(), geolocation=()"
    );
    assert!(headers.get(header::SET_COOKIE).is_none());
    let h: Value = serde_json::from_slice(&body).unwrap();
    assert_eq!(h["schema"], "parlpdfech-health/1");
    assert_eq!(h["version"], "0.1.0");
    assert_eq!(h["commit"], "test");
    assert_eq!(h["profile"], "native");
    assert_eq!(h["status"], "EXCEPTION, NOT RELEASED");
    assert_eq!(
        h["modes"],
        json!({"samples": true, "rules": true, "apertus_stored": true, "upload": true, "apertus_gpu": false,
               "read_only": false, "sample_runs": true, "reason": {"upload": null, "apertus_gpu": "not_implemented"}})
    );
    assert_eq!(
        h["ocr"],
        if cfg!(target_os = "macos") {
            "apple"
        } else {
            "none"
        }
    );
    assert_eq!(
        h["limits"],
        json!({"max_bytes": 65536, "max_pages": 25, "job_timeout_seconds": 30})
    );
    assert_eq!(h["busy"], false);
    assert_eq!(h["job_id"], Value::Null);
    assert_eq!(h["wasm"], true);
    assert_eq!(h["site"], false);
    assert_eq!(h["hosted"], false);
    // The same keys as the example of the contract.
    let example: Value = serde_json::from_slice(
        &std::fs::read(manifest_dir().join("../contract/examples/health.json")).unwrap(),
    )
    .unwrap();
    let keys = |v: &Value| v.as_object().unwrap().keys().cloned().collect::<Vec<_>>();
    assert_eq!(keys(&h), keys(&example));
}

#[tokio::test]
async fn health_of_the_profile_slim_and_an_absent_index() {
    let env = env_with("auto", |cfg, tmp| {
        cfg.profile = "slim".into();
        cfg.data_dir = tmp.join("no_data");
        std::fs::remove_dir_all(cfg.ui_dir.join("pkg")).unwrap();
    });
    let (_, h) = get_json(&env.app, "/api/health").await;
    assert_eq!(h["modes"]["upload"], false);
    assert_eq!(h["modes"]["reason"]["upload"], "profile_slim");
    assert_eq!(h["ocr"], "none");
    assert_eq!(h["modes"]["samples"], false);
    assert_eq!(h["modes"]["apertus_stored"], false);
    assert_eq!(h["wasm"], false);
    let (status, s) = get_json(&env.app, "/api/samples").await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(s["samples"], json!([]));
    let (status, body) = post_json(&env.app, json!({"sample": "26171"})).await;
    assert_error(status, &body, "sample_unknown", 404);
}

#[tokio::test]
async fn a_broken_index_gives_internal_and_no_path() {
    let env = env_with("auto", |cfg, tmp| {
        cfg.data_dir = tmp.join("data");
        std::fs::create_dir_all(cfg.data_dir.join("samples")).unwrap();
        std::fs::write(cfg.data_dir.join("samples/index.json"), "{ not json").unwrap();
    });
    let (status, _, body) = get(&env.app, "/api/samples").await;
    let text = String::from_utf8(body).unwrap();
    let value: Value = serde_json::from_str(&text).unwrap();
    assert_error(status, &value, "internal", 500);
    assert_eq!(value["error"]["detail"]["note"], "samples_index");
    assert!(!text.contains(env.tmp.path().to_str().unwrap()));
}

#[tokio::test]
async fn sample_job_valid_then_record_files_bundle_delete() {
    let env = env("auto");
    let (status, s) = get_json(&env.app, "/api/samples").await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(s["schema"], "parlpdfech-samples/1");
    let samples = s["samples"].as_array().unwrap();
    assert_eq!(samples.len(), 3);
    for sample in samples {
        assert_eq!(sample["ready"], json!({"auto": false, "rules": false}));
        assert!(sample["in_sample"].is_boolean());
    }

    let id = start_sample(&env.app, "26171", "auto").await;
    let evs = events(&env.app, &id).await;
    let names: Vec<&str> = evs.iter().map(|(n, _)| n.as_str()).collect();
    assert_eq!(names.len(), 13, "{names:?}");
    assert!(names[..12].iter().all(|n| *n == "stage"));
    assert_eq!(names[12], "done");
    // A stage event holds the checked values of the worker line (the server builds the object again).
    assert_eq!(
        evs[0].1,
        r#"{"event":"stage","id":"read_pdf","state":"running"}"#
    );
    assert_eq!(
        evs[1].1,
        r#"{"counts":{"pages":1},"event":"stage","id":"read_pdf","origin":"stored","seconds":0.001,"state":"done"}"#
    );
    let done: Value = serde_json::from_str(&evs[12].1).unwrap();

    let (status, job) = get_json(&env.app, &format!("/api/jobs/{id}")).await;
    assert_eq!(status, StatusCode::OK);
    let mut a = done.clone();
    let mut b = job.clone();
    a["elapsed_seconds"] = Value::Null;
    b["elapsed_seconds"] = Value::Null;
    assert_eq!(a, b, "the data of the event done is the job object");
    assert_eq!(job["schema"], "parlpdfech-job/1");
    assert_eq!(job["state"], "done");
    assert_eq!(job["valid"], true);
    assert_eq!(job["apertus"], "stored");
    assert_eq!(job["record_id"], "s-26171");
    assert_eq!(job["error"], Value::Null);
    assert_eq!(job["mode"], "auto");
    assert_eq!(
        job["input"],
        json!({"kind": "sample", "doc_id": "26171", "file_name": null, "bytes": null,
               "pdf_sha256": "f2e5fe4ae6747a886d93bc753795611117fe11b4d23f4ae30d53866fcedb1493"})
    );
    let stages = job["stages"].as_array().unwrap();
    let ids: Vec<&str> = stages.iter().map(|s| s["id"].as_str().unwrap()).collect();
    assert_eq!(
        ids,
        ["read_pdf", "lines", "rules", "apertus", "write", "check"]
    );
    assert!(stages
        .iter()
        .all(|s| s["state"] == "done" && s["reason"].is_null()));
    assert_eq!(
        stages[4],
        json!({"id": "write", "state": "done", "origin": "new", "seconds": 0.001,
                                 "counts": {"labels": 4, "triples": 40}, "reason": null})
    );
    let example: Value = serde_json::from_slice(
        &std::fs::read(manifest_dir().join("../contract/examples/job.json")).unwrap(),
    )
    .unwrap();
    let keys = |v: &Value| v.as_object().unwrap().keys().cloned().collect::<Vec<_>>();
    assert_eq!(keys(&job), keys(&example));
    assert!(
        jobs_dir_is_empty(&env),
        "the job folder is deleted at the end of the job"
    );

    // A late client gets the full sequence again.
    assert_eq!(events(&env.app, &id).await, evs);

    let (_, s) = get_json(&env.app, "/api/samples").await;
    let ready: Vec<&Value> = s["samples"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|x| x["doc_id"] == "26171")
        .collect();
    assert_eq!(ready[0]["ready"], json!({"auto": true, "rules": false}));

    // The view and the files: bytes not changed, media types of the contract.
    let dir = env.work().join("records/s-26171");
    let (status, headers, body) = get(&env.app, "/api/records/s-26171").await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(
        headers[header::CONTENT_TYPE],
        "application/json; charset=utf-8"
    );
    assert_eq!(headers[header::CACHE_CONTROL], "no-store");
    assert_eq!(body, std::fs::read(dir.join("view.json")).unwrap());
    let expected = [
        ("26171.gesamt.trig", "application/trig"),
        ("26171.ech.ttl", "text/turtle; charset=utf-8"),
        ("26171.gesamt.rdf.xml", "application/rdf+xml"),
        ("26171.ech.rdf.xml", "application/rdf+xml"),
        ("26171.ech.yaml", "application/yaml"),
        ("26171.labels.yaml", "application/yaml"),
        ("26171.provenance.yaml", "application/yaml"),
        ("manifest.json", "application/json"),
        ("validation.json", "application/json"),
        ("view.json", "application/json"),
        ("convert.json", "application/json"),
    ];
    for (name, media) in expected {
        let (status, headers, body) =
            get(&env.app, &format!("/api/records/s-26171/files/{name}")).await;
        assert_eq!(status, StatusCode::OK, "{name}");
        assert_eq!(headers[header::CONTENT_TYPE], media, "{name}");
        assert_eq!(body, std::fs::read(dir.join(name)).unwrap(), "{name}");
        assert!(headers.get(header::CONTENT_DISPOSITION).is_none());
    }
    let (_, headers, _) = get(
        &env.app,
        "/api/records/s-26171/files/26171.gesamt.trig?download=1",
    )
    .await;
    assert_eq!(
        headers[header::CONTENT_DISPOSITION],
        "attachment; filename=\"26171.gesamt.trig\""
    );

    // The archive: 12 entries in the sequence of the contract, each line of SHA256SUMS is correct.
    let (status, headers, body) = get(&env.app, "/api/records/s-26171/bundle.zip").await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(headers[header::CONTENT_TYPE], "application/zip");
    assert_eq!(
        headers[header::CONTENT_DISPOSITION],
        "attachment; filename=\"parlpdfech-s-26171.zip\""
    );
    let mut archive = zip::ZipArchive::new(std::io::Cursor::new(body)).unwrap();
    assert_eq!(archive.len(), 12);
    let mut contents = Vec::new();
    for i in 0..archive.len() {
        let mut file = archive.by_index(i).unwrap();
        let mut bytes = Vec::new();
        std::io::Read::read_to_end(&mut file, &mut bytes).unwrap();
        contents.push((file.name().to_string(), bytes));
    }
    for (i, (name, _)) in expected.iter().enumerate() {
        assert_eq!(contents[i].0, format!("parlpdfech-s-26171/{name}"));
        assert_eq!(contents[i].1, std::fs::read(dir.join(name)).unwrap());
    }
    assert_eq!(contents[11].0, "parlpdfech-s-26171/SHA256SUMS");
    let sums = String::from_utf8(contents[11].1.clone()).unwrap();
    let lines: Vec<&str> = sums.lines().collect();
    assert_eq!(lines.len(), 11);
    let mut sorted = lines
        .iter()
        .map(|l| l.split_once("  ").unwrap().1)
        .collect::<Vec<_>>();
    let listed = sorted.clone();
    sorted.sort();
    assert_eq!(listed, sorted);
    for line in lines {
        let (sum, name) = line.split_once("  ").unwrap();
        assert_eq!(
            sum,
            hex::encode(Sha256::digest(std::fs::read(dir.join(name)).unwrap())),
            "{name}"
        );
    }

    // DELETE of the record.
    let (status, _, body) = call(&env.app, request(Method::DELETE, "/api/records/s-26171")).await;
    assert_eq!((status, body.len()), (StatusCode::NO_CONTENT, 0));
    assert!(!dir.exists());
    let (status, body) = get_json(&env.app, "/api/records/s-26171").await;
    assert_error(status, &body, "record_unknown", 404);
    assert_eq!(body["error"]["detail"]["record_id"], "s-26171");
    let (status, _, body) = call(&env.app, request(Method::DELETE, "/api/records/s-26171")).await;
    assert_error(
        status,
        &serde_json::from_slice(&body).unwrap(),
        "record_unknown",
        404,
    );
    let (status, body) = get_json(&env.app, "/api/records/s-26171/bundle.zip").await;
    assert_error(status, &body, "record_unknown", 404);
    // The job that ended is not changed by a DELETE.
    let (status, _, body) = call(
        &env.app,
        request(Method::DELETE, &format!("/api/jobs/{id}")),
    )
    .await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(
        serde_json::from_slice::<Value>(&body).unwrap()["state"],
        "done"
    );
}

#[tokio::test]
async fn rules_mode_has_its_own_record_and_a_multipart_sample_works() {
    let env = env("auto");
    let (status, body) = post_form(
        &env.app,
        &[("sample", None, b"879163"), ("mode", None, b"rules")],
    )
    .await;
    assert_eq!(status, StatusCode::ACCEPTED, "{body}");
    let id = body["job_id"].as_str().unwrap();
    let evs = events(&env.app, id).await;
    let job: Value = serde_json::from_str(&evs.last().unwrap().1).unwrap();
    assert_eq!(evs.last().unwrap().0, "done");
    assert_eq!(job["record_id"], "s-879163-rules");
    assert_eq!(job["apertus"], "none");
    assert_eq!(job["mode"], "rules");
    assert_eq!(
        job["stages"][3],
        json!({"id": "apertus", "state": "skipped", "origin": null, "seconds": null,
                                        "counts": {}, "reason": "mode_rules"})
    );
    assert!(env
        .work()
        .join("records/s-879163-rules/view.json")
        .is_file());
    assert!(!env.work().join("records/s-879163").exists());
    let (_, s) = get_json(&env.app, "/api/samples").await;
    let sample = s["samples"]
        .as_array()
        .unwrap()
        .iter()
        .find(|x| x["doc_id"] == "879163")
        .unwrap()
        .clone();
    assert_eq!(sample["ready"], json!({"auto": false, "rules": true}));
}

#[tokio::test]
async fn a_new_conversion_replaces_the_record_folder() {
    let env = env("auto");
    for _ in 0..2 {
        let id = start_sample(&env.app, "714840", "auto").await;
        assert_eq!(events(&env.app, &id).await.last().unwrap().0, "done");
        std::fs::write(
            env.work().join("records/s-714840/manifest.json"),
            "changed by the test",
        )
        .unwrap();
    }
    let id = start_sample(&env.app, "714840", "auto").await;
    events(&env.app, &id).await;
    let (_, _, body) = get(&env.app, "/api/records/s-714840/files/manifest.json").await;
    assert!(String::from_utf8(body).unwrap().contains("\"fake\""));
    let names: Vec<String> = std::fs::read_dir(env.work().join("records"))
        .unwrap()
        .map(|e| e.unwrap().file_name().to_string_lossy().into_owned())
        .collect();
    assert_eq!(names, ["s-714840"]);
}

#[tokio::test]
async fn not_valid_is_a_result() {
    let env = env("not_valid");
    let id = start_sample(&env.app, "26171", "auto").await;
    let evs = events(&env.app, &id).await;
    assert_eq!(evs.last().unwrap().0, "done");
    let (_, job) = get_json(&env.app, &format!("/api/jobs/{id}")).await;
    assert_eq!(
        (job["state"].as_str(), job["valid"].as_bool()),
        (Some("done"), Some(false))
    );
    assert_eq!(job["record_id"], "s-26171");
    assert_eq!(
        get(&env.app, "/api/records/s-26171").await.0,
        StatusCode::OK
    );
}

#[tokio::test]
async fn upload_of_an_unknown_pdf_is_refused_by_the_worker() {
    let env = env("auto");
    let pdf = tiny_pdf("unknown");
    let sha = hex::encode(Sha256::digest(&pdf));
    let (status, body) = post_form(
        &env.app,
        &[
            ("file", Some("C:\\Users\\me\\..\\my file.pdf"), &pdf),
            ("doc_id", None, b"123"),
            ("mode", None, b"auto"),
        ],
    )
    .await;
    assert_eq!(status, StatusCode::ACCEPTED, "{body}");
    let id = body["job_id"].as_str().unwrap();
    let evs = events(&env.app, id).await;
    let names: Vec<&str> = evs.iter().map(|(n, _)| n.as_str()).collect();
    assert_eq!(names, ["stage", "stage", "failed"]);
    let job: Value = serde_json::from_str(&evs[2].1).unwrap();
    assert_eq!(job["state"], "failed");
    assert_eq!(job["record_id"], Value::Null);
    assert_eq!(job["valid"], Value::Null);
    assert_eq!(
        job["input"],
        json!({"kind": "upload", "doc_id": "123", "file_name": "my file.pdf", "bytes": pdf.len(), "pdf_sha256": sha})
    );
    assert_eq!(job["stages"][0]["state"], "failed");
    assert_eq!(job["stages"][0]["reason"], "not_in_package");
    assert_eq!(job["stages"][1]["state"], "pending");
    let error = json!({"error": job["error"]});
    assert_error(
        StatusCode::UNPROCESSABLE_ENTITY,
        &error,
        "not_in_package",
        422,
    );
    assert_eq!(
        job["error"]["detail"],
        json!({"pdf_sha256": sha, "profile": "native"})
    );
    assert!(jobs_dir_is_empty(&env), "input.pdf is deleted");
    assert!(std::fs::read_dir(env.work().join("records"))
        .unwrap()
        .next()
        .is_none());
}

#[tokio::test]
async fn upload_of_a_pdf_of_the_index_gets_the_sample_id() {
    let pdf = tiny_pdf("in the index");
    let sha = hex::encode(Sha256::digest(&pdf));
    let env = env_with("auto", |cfg, tmp| {
        cfg.data_dir = tmp.join("data");
        std::fs::create_dir_all(cfg.data_dir.join("samples")).unwrap();
        let index = json!({"schema": "parlpdfech-samples/1", "samples": [
            {"doc_id": "26171", "record_id": "s-26171", "pdf_sha256": sha, "modes": ["auto"], "apertus": "stored", "in_sample": true}]});
        std::fs::write(cfg.data_dir.join("samples/index.json"), index.to_string()).unwrap();
    });
    let (status, body) = post_form(&env.app, &[("file", Some("a.pdf"), &pdf)]).await;
    assert_eq!(status, StatusCode::ACCEPTED, "{body}");
    let evs = events(&env.app, body["job_id"].as_str().unwrap()).await;
    let job: Value = serde_json::from_str(&evs.last().unwrap().1).unwrap();
    assert_eq!(job["state"], "done", "{job}");
    assert_eq!(job["record_id"], "s-26171");
    assert_eq!(job["input"]["kind"], "upload");
    assert!(jobs_dir_is_empty(&env));
    // The sample has no mode rules in this index.
    let (status, body) = post_json(&env.app, json!({"sample": 26171, "mode": "rules"})).await;
    assert_error(status, &body, "bad_request", 400);
    assert_eq!(body["error"]["detail"]["field"], "mode");
    let (_, h) = get_json(&env.app, "/api/health").await;
    assert_eq!(h["modes"]["rules"], false);
}

#[tokio::test]
async fn upload_with_a_forced_valid_worker_gets_a_u_record() {
    let env = env("valid");
    let pdf = tiny_pdf("forced");
    let sha = hex::encode(Sha256::digest(&pdf));
    let (status, body) = post_form(
        &env.app,
        &[("mode", None, b"rules"), ("file", Some("x.pdf"), &pdf)],
    )
    .await;
    assert_eq!(status, StatusCode::ACCEPTED, "{body}");
    let evs = events(&env.app, body["job_id"].as_str().unwrap()).await;
    let job: Value = serde_json::from_str(&evs.last().unwrap().1).unwrap();
    let record_id = format!("u-{}-rules", &sha[..16]);
    assert_eq!(job["record_id"], record_id.as_str(), "{job}");
    let (status, headers, _) = get(
        &env.app,
        &format!("/api/records/{record_id}/files/local.gesamt.trig"),
    )
    .await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(headers[header::CONTENT_TYPE], "application/trig");
}

#[tokio::test]
async fn crash_gives_converter_stopped_and_no_trace() {
    let env = env("crash");
    let id = start_sample(&env.app, "26171", "auto").await;
    let (_, _, raw) = get(&env.app, &format!("/api/jobs/{id}/events")).await;
    let raw = String::from_utf8(raw).unwrap();
    assert!(
        !raw.contains("Traceback") && !raw.contains("fake crash") && !raw.contains("/fake/"),
        "{raw}"
    );
    let evs = parse_events(&raw);
    assert_eq!(evs.last().unwrap().0, "failed");
    let job: Value = serde_json::from_str(&evs.last().unwrap().1).unwrap();
    assert_eq!(job["state"], "failed");
    assert_eq!(job["error"]["code"], "converter_stopped");
    assert_eq!(job["error"]["detail"], json!({"note": "exit_1"}));
    assert!(job["error"]["text"]["en"]
        .as_str()
        .unwrap()
        .contains("exit_1"));
    assert!(jobs_dir_is_empty(&env));
    assert!(!env.work().join("records/s-26171").exists());
}

#[tokio::test]
async fn an_internal_stop_of_the_worker_passes_only_clean_detail() {
    let env = env("stopped");
    let id = start_sample(&env.app, "26171", "auto").await;
    let (_, _, raw) = get(&env.app, &format!("/api/jobs/{id}/events")).await;
    let raw = String::from_utf8(raw).unwrap();
    assert!(!raw.contains("/fake/"), "{raw}");
    let job: Value = serde_json::from_str(&parse_events(&raw).last().unwrap().1).unwrap();
    assert_eq!(job["error"]["code"], "converter_stopped");
    assert_eq!(job["error"]["detail"], json!({"note": "writer"}));
}

#[tokio::test]
async fn protocol_errors_of_the_worker_give_converter_stopped() {
    for (case, note) in [("wrong_id", "record_id"), ("no_view", "no_view")] {
        let env = env(case);
        let id = start_sample(&env.app, "26171", "auto").await;
        let evs = events(&env.app, &id).await;
        let job: Value = serde_json::from_str(&evs.last().unwrap().1).unwrap();
        assert_eq!(job["state"], "failed", "{case}");
        assert_eq!(job["error"]["code"], "converter_stopped", "{case}");
        assert_eq!(job["error"]["detail"]["note"], note, "{case}");
        assert!(!env.work().join("records/s-26171").exists(), "{case}");
        assert!(!env.work().join("records/s-1").exists(), "{case}");
        assert!(jobs_dir_is_empty(&env), "{case}");
    }
    // A worker command that does not exist.
    let env = env_with("auto", |cfg, _| {
        cfg.worker_cmd = vec!["no-such-command-of-the-test".into()]
    });
    let id = start_sample(&env.app, "26171", "auto").await;
    let evs = events(&env.app, &id).await;
    let job: Value = serde_json::from_str(&evs.last().unwrap().1).unwrap();
    assert_eq!(job["error"]["detail"], json!({"note": "spawn"}));
}

#[tokio::test]
async fn an_entry_that_is_not_a_record_file_does_not_reach_the_record() {
    let env = env("extra_file");
    let id = start_sample(&env.app, "26171", "auto").await;
    assert_eq!(events(&env.app, &id).await.last().unwrap().0, "done");
    let mut names: Vec<String> = std::fs::read_dir(env.work().join("records/s-26171"))
        .unwrap()
        .map(|e| e.unwrap().file_name().to_string_lossy().into_owned())
        .collect();
    names.sort();
    assert_eq!(names.len(), 11);
    assert!(!names.contains(&"notes.txt".to_string()));
}

#[tokio::test]
async fn hang_reaches_the_timeout_and_the_process_is_stopped() {
    for case in ["hang", "hang_hard"] {
        let env = env_with(case, |cfg, _| {
            cfg.job_timeout = Duration::from_secs(2);
            cfg.ping_interval = Duration::from_millis(200);
        });
        let id = start_sample(&env.app, "26171", "auto").await;
        let started = std::time::Instant::now();
        let (_, _, raw) = get(&env.app, &format!("/api/jobs/{id}/events")).await;
        let waited = started.elapsed();
        let raw = String::from_utf8(raw).unwrap();
        assert!(
            raw.matches(": ping\n\n").count() >= 3,
            "{case}: ping comments in the stream: {raw}"
        );
        let evs = parse_events(&raw);
        let job: Value = serde_json::from_str(&evs.last().unwrap().1).unwrap();
        assert_eq!(evs.last().unwrap().0, "failed", "{case}");
        assert_eq!(job["error"]["code"], "timeout", "{case}");
        assert_eq!(job["error"]["detail"], json!({"seconds": 2}), "{case}");
        assert!(job["error"]["text"]["en"].as_str().unwrap().contains('2'));
        assert!(
            waited >= Duration::from_millis(1500) && waited < Duration::from_secs(8),
            "{case}: {waited:?}"
        );
        let pid = job["stages"][0]["counts"]["pid"].as_u64().unwrap();
        assert!(
            !pid_runs(pid),
            "{case}: the worker process {pid} still runs"
        );
        assert!(jobs_dir_is_empty(&env), "{case}");
        let (_, h) = get_json(&env.app, "/api/health").await;
        assert_eq!(h["busy"], false);
    }
}

#[tokio::test]
async fn garbage_on_standard_output_never_reaches_the_client() {
    let env = env("garbage");
    let id = start_sample(&env.app, "26171", "auto").await;
    let (_, _, raw) = get(&env.app, &format!("/api/jobs/{id}/events")).await;
    let raw = String::from_utf8(raw).unwrap();
    for word in [
        "not JSON",
        "binary",
        "/fake/",
        "unknown_event",
        "no_such_stage",
        "no_such_state",
        "garbage",
        "xxxx",
        "JSON string",
        "[1, 2, 3]",
    ] {
        assert!(!raw.contains(word), "{word} is in the stream");
    }
    let evs = parse_events(&raw);
    assert_eq!(evs.len(), 13);
    assert_eq!(evs.last().unwrap().0, "done");
    for (name, data) in &evs {
        let value: Value = serde_json::from_str(data).unwrap();
        assert!(value.is_object(), "{name}");
    }
    let (_, job) = get_json(&env.app, &format!("/api/jobs/{id}")).await;
    assert_eq!(job["state"], "done");
    assert!(!job.to_string().contains("/fake/"));
}

#[tokio::test]
async fn busy_then_stop_then_a_new_job() {
    let env = env_with("hang", |cfg, _| cfg.job_timeout = Duration::from_secs(60));
    let id = start_sample(&env.app, "26171", "auto").await;
    let (_, h) = get_json(&env.app, "/api/health").await;
    assert_eq!(h["busy"], true);
    assert_eq!(h["job_id"], id.as_str());

    let (status, body) = post_json(&env.app, json!({"sample": "879163"})).await;
    assert_error(status, &body, "busy", 409);
    assert_eq!(body["error"]["detail"]["job_id"], id.as_str());
    assert_eq!(body["error"]["exits"], json!(["retry", "sample"]));
    let pdf = tiny_pdf("busy");
    let (status, body) = post_form(&env.app, &[("file", Some("a.pdf"), &pdf)]).await;
    assert_error(status, &body, "busy", 409);

    // Wait for the stage event that holds the process number of the worker.
    let mut pid = None;
    for _ in 0..100 {
        let (_, job) = get_json(&env.app, &format!("/api/jobs/{id}")).await;
        assert_eq!(job["state"], "running");
        pid = job["stages"][0]["counts"]["pid"].as_u64();
        if pid.is_some() {
            break;
        }
        tokio::time::sleep(Duration::from_millis(50)).await;
    }
    let pid = pid.expect("the worker did not start in 5 s");
    assert!(pid_runs(pid));
    assert!(env.work().join("jobs").join(&id).is_dir());

    let (status, _, body) = call(
        &env.app,
        request(Method::DELETE, &format!("/api/jobs/{id}")),
    )
    .await;
    assert_eq!(status, StatusCode::OK);
    let job: Value = serde_json::from_slice(&body).unwrap();
    assert_eq!(job["state"], "stopped");
    assert_eq!(job["error"], Value::Null);
    assert_eq!(job["record_id"], Value::Null);
    assert!(
        !pid_runs(pid),
        "the worker process still runs after the stop"
    );
    assert!(jobs_dir_is_empty(&env));
    let evs = events(&env.app, &id).await;
    assert_eq!(evs.last().unwrap().0, "stopped");
    assert_eq!(
        serde_json::from_str::<Value>(&evs.last().unwrap().1).unwrap()["state"],
        "stopped"
    );

    let (_, h) = get_json(&env.app, "/api/health").await;
    assert_eq!(
        (h["busy"].as_bool(), h["job_id"].is_null()),
        (Some(false), true)
    );
    let id2 = start_sample(&env.app, "879163", "auto").await;
    env.state.jobs.stop_active(Duration::from_secs(5)).await;
    let (_, job) = get_json(&env.app, &format!("/api/jobs/{id2}")).await;
    assert_eq!(job["state"], "stopped");
}

#[tokio::test]
async fn upload_checks() {
    let env = env("auto");
    // too_large: the limit of this test server is 64 KB.
    let mut big = tiny_pdf("big");
    big.resize(64 * 1024 + 1, b' ');
    let (status, body) = post_form(&env.app, &[("file", Some("big.pdf"), &big)]).await;
    assert_error(status, &body, "too_large", 413);
    assert_eq!(body["error"]["detail"]["max_bytes"], 65536);
    assert!(body["error"]["text"]["en"]
        .as_str()
        .unwrap()
        .contains("0.06 MB"));
    // too_large: a body above the limit plus 64 KB (refused from the declared length).
    big.resize(200 * 1024, b' ');
    let (status, body) = post_form(&env.app, &[("file", Some("big.pdf"), &big)]).await;
    assert_error(status, &body, "too_large", 413);
    // too_large with no declared length (the body is counted while it streams).
    let mut req = multipart(&[("file", Some("big.pdf"), &big)]);
    req.headers_mut().remove(header::CONTENT_LENGTH);
    let (status, _, body) = call(&env.app, req).await;
    assert_error(
        status,
        &serde_json::from_slice(&body).unwrap(),
        "too_large",
        413,
    );
    // A file at the limit passes the size check.
    let mut exact = tiny_pdf("exact");
    exact.resize(64 * 1024, b' ');
    let (status, body) = post_form(&env.app, &[("file", Some("exact.pdf"), &exact)]).await;
    assert_eq!(status, StatusCode::ACCEPTED, "{body}");
    events(&env.app, body["job_id"].as_str().unwrap()).await;

    // not_pdf
    for bytes in [
        b"PK\x03\x04 a zip file".to_vec(),
        Vec::new(),
        vec![b'a'; 5000],
        b"<html>%PDF".to_vec(),
    ] {
        let (status, body) = post_form(&env.app, &[("file", Some("x.pdf"), &bytes)]).await;
        assert_error(status, &body, "not_pdf", 415);
    }

    // bad_request
    let pdf = tiny_pdf("bad");
    let cases: Vec<(Vec<Part>, &str)> = vec![
        (vec![], "file"),
        (vec![("mode", None, b"auto")], "file"),
        (
            vec![("file", Some("a.pdf"), &pdf), ("sample", None, b"26171")],
            "sample",
        ),
        (
            vec![("file", Some("a.pdf"), &pdf), ("mode", None, b"fast")],
            "mode",
        ),
        (
            vec![("file", Some("a.pdf"), &pdf), ("doc_id", None, b"12a")],
            "doc_id",
        ),
        (
            vec![("file", Some("a.pdf"), &pdf), ("doc_id", None, b"../../x")],
            "doc_id",
        ),
        (
            vec![("file", Some("a.pdf"), &pdf), ("file", Some("b.pdf"), &pdf)],
            "file",
        ),
        (
            vec![("sample", None, b"26171"), ("doc_id", None, b"26171")],
            "doc_id",
        ),
    ];
    for (parts, field) in cases {
        let (status, body) = post_form(&env.app, &parts).await;
        assert_error(status, &body, "bad_request", 400);
        assert_eq!(body["error"]["detail"]["field"], field, "{body}");
    }
    let filler = vec![b'x'; 70 * 1024];
    let (status, body) = post_form(
        &env.app,
        &[("other", None, &filler), ("sample", None, b"26171")],
    )
    .await;
    assert_error(status, &body, "bad_request", 400);
    for (content_type, text) in [
        ("application/json", "{not json"),
        ("application/json", "[]"),
        ("text/plain", "sample=26171"),
        ("application/json", r#"{"file":"x"}"#),
        ("application/json", r#"{"sample":{"a":1}}"#),
    ] {
        let req = Request::builder()
            .method(Method::POST)
            .uri("/api/jobs")
            .header(header::HOST, HOST)
            .header(header::CONTENT_TYPE, content_type)
            .body(Body::from(text))
            .unwrap();
        let (status, _, body) = call(&env.app, req).await;
        assert_error(
            status,
            &serde_json::from_slice(&body).unwrap(),
            "bad_request",
            400,
        );
    }

    // sample_unknown
    for sample in [json!("1"), json!("../../etc"), json!(99)] {
        let (status, body) = post_json(&env.app, json!({"sample": sample})).await;
        assert_error(status, &body, "sample_unknown", 404);
        assert!(!body.to_string().contains(".."), "{body}");
    }
    assert!(jobs_dir_is_empty(&env), "a refused upload leaves no file");
    let (_, h) = get_json(&env.app, "/api/health").await;
    assert_eq!(h["busy"], false);
}

#[tokio::test]
async fn path_traversal_gives_404_and_no_file() {
    let env = env("auto");
    let id = start_sample(&env.app, "26171", "auto").await;
    events(&env.app, &id).await;
    std::fs::write(
        env.work().join("records/secret.json"),
        "outside of a record",
    )
    .unwrap();
    std::fs::write(
        env.work().join("records/s-26171/input.pdf"),
        "not on the list",
    )
    .unwrap();
    std::fs::create_dir_all(env.work().join("records/other")).unwrap();
    std::fs::write(env.work().join("records/other/view.json"), "{}").unwrap();

    let paths = [
        "/api/records/..",
        "/api/records/%2e%2e",
        "/api/records/..%2f..%2fsecret.txt",
        "/api/records/other",
        "/api/records/s-26171%2f..%2fother",
        "/api/records/s-26171%00",
        "/api/records/S-26171",
        "/api/records/s-26171/files/..%2fsecret.json",
        "/api/records/s-26171/files/%2e%2e%2f%2e%2e%2fsecret.txt",
        "/api/records/s-26171/files/....//secret.json",
        "/api/records/s-26171/files/input.pdf",
        "/api/records/s-26171/files/view.json%00.txt",
        "/api/records/s-26171/files/26171.gesamt.trig%2f..%2fview.json",
        "/api/records/s-26171/files/%2fetc%2fpasswd",
        "/api/records/s-26171/files/999.gesamt.trig",
        "/api/records/..%2fother/files/view.json",
        "/api/records/other/files/view.json",
        "/api/records/other/bundle.zip",
        "/api/records/..%2f..%2fwork/bundle.zip",
        "/api/records/s-26171/files/",
        "/api/records/s-26171/../other",
        "/api/records/s-26171/files/../../other/view.json",
        "/api/jobs/..%2f..%2fsecret.txt",
        "/api/jobs/not-a-job-id/events",
        "/api/jobs/00000000-0000-4000-8000-000000000000",
        "/api/jobs/00000000-0000-4000-8000-000000000000/events",
        "/api/nothing",
        "/api",
    ];
    for path in paths {
        let (status, headers, body) = get(&env.app, path).await;
        let text = String::from_utf8_lossy(&body).to_string();
        assert_eq!(status, StatusCode::NOT_FOUND, "{path}: {text}");
        assert_eq!(
            headers[header::CONTENT_TYPE],
            "application/json; charset=utf-8",
            "{path}"
        );
        let value: Value = serde_json::from_str(&text).unwrap();
        let code = value["error"]["code"].as_str().unwrap();
        assert!(
            ["record_unknown", "file_unknown", "job_unknown", "not_found"].contains(&code),
            "{path}: {code}"
        );
        assert!(
            !text.contains("outside") && !text.contains("not on the list"),
            "{path}"
        );
        assert!(
            !text.contains(env.tmp.path().to_str().unwrap()),
            "{path}: a local path is in the answer"
        );
        assert!(
            !text.contains(".."),
            "{path}: the value of the client is in the answer: {text}"
        );
    }
    for path in [
        "/api/records/..%2fother",
        "/api/records/other",
        "/api/records/s-26171%2f..%2fother",
    ] {
        let (status, _, _) = call(&env.app, request(Method::DELETE, path)).await;
        assert_eq!(status, StatusCode::NOT_FOUND, "{path}");
    }
    assert!(env.work().join("records/other/view.json").is_file());
    assert!(env.work().join("records/secret.json").is_file());
    assert!(env.tmp.path().join("secret.txt").is_file());

    // Static files: no path leaves the UI folder.
    for path in [
        "/app/../secret.txt",
        "/app/..%2fsecret.txt",
        "/app/%2e%2e/secret.txt",
        "/app/pkg/../../secret.txt",
        "/app//etc/passwd",
        "/app/no_such_file.js",
        "/secret.txt",
        "/x",
    ] {
        let (status, _, body) = get(&env.app, path).await;
        assert!(
            status == StatusCode::NOT_FOUND || status == StatusCode::BAD_REQUEST,
            "{path}: {status}"
        );
        assert!(
            !String::from_utf8_lossy(&body).contains("outside"),
            "{path}"
        );
    }

    // A method that an address does not have: the error object, not an empty answer.
    for (method, path) in [
        (Method::PUT, "/api/jobs"),
        (Method::GET, "/api/jobs"),
        (Method::POST, "/api/health"),
        (Method::POST, "/api/records/s-26171"),
    ] {
        let (status, _, body) = call(&env.app, request(method, path)).await;
        assert_error(
            status,
            &serde_json::from_slice(&body).unwrap(),
            "not_found",
            404,
        );
    }
    // A large body on an address that takes none.
    let req = Request::builder()
        .method(Method::DELETE)
        .uri("/api/records/s-26171")
        .header(header::HOST, HOST)
        .header(header::CONTENT_LENGTH, 100_000)
        .body(Body::from(vec![b'x'; 100_000]))
        .unwrap();
    let (status, _, body) = call(&env.app, req).await;
    assert_error(
        status,
        &serde_json::from_slice(&body).unwrap(),
        "bad_request",
        400,
    );
    assert!(env.work().join("records/s-26171").is_dir());
}

#[tokio::test]
async fn static_files_of_the_ui() {
    let env = env("auto");
    let (status, headers, _) = get(&env.app, "/").await;
    assert_eq!(status, StatusCode::TEMPORARY_REDIRECT);
    assert_eq!(headers[header::LOCATION], "/app/");
    let (_, headers, _) = get(&env.app, "/?lang=de").await;
    assert_eq!(headers[header::LOCATION], "/app/?lang=de");
    let (status, headers, _) = get(&env.app, "/app").await;
    assert_eq!(status, StatusCode::PERMANENT_REDIRECT);
    assert_eq!(headers[header::LOCATION], "/app/");

    let (status, headers, body) = get(&env.app, "/app/?lang=de").await;
    assert_eq!(status, StatusCode::OK);
    assert!(headers[header::CONTENT_TYPE]
        .to_str()
        .unwrap()
        .starts_with("text/html"));
    assert_eq!(headers[header::CONTENT_SECURITY_POLICY], CSP);
    assert_eq!(headers[header::CACHE_CONTROL], "no-cache");
    assert_eq!(headers["x-content-type-options"], "nosniff");
    assert_eq!(headers["x-frame-options"], "DENY");
    assert_eq!(headers[header::CONTENT_TYPE], "text/html; charset=utf-8");
    assert!(String::from_utf8(body).unwrap().contains("test page"));

    let media = |h: &HeaderMap| h[header::CONTENT_TYPE].to_str().unwrap().to_string();
    let (status, headers, body) = get(&env.app, "/app/pkg/parlpdfech_rdfcheck_bg.wasm").await;
    assert_eq!(
        (status, media(&headers).as_str()),
        (StatusCode::OK, "application/wasm")
    );
    assert_eq!(body, b"\0asm\x01\0\0\0");
    assert_eq!(headers[header::CACHE_CONTROL], "no-cache");
    let (_, headers, _) = get(&env.app, "/app/app.js").await;
    assert!(
        media(&headers).contains("javascript"),
        "{}",
        media(&headers)
    );
    assert_eq!(headers[header::CACHE_CONTROL], "no-cache");
    let (_, headers, _) = get(&env.app, "/app/app.css").await;
    assert!(media(&headers).starts_with("text/css"));
    let (_, headers, _) = get(&env.app, "/app/app.0123abcd.js").await;
    assert_eq!(
        headers[header::CACHE_CONTROL],
        "public, max-age=31536000, immutable"
    );
    let (status, headers, _) = get(&env.app, "/app/no.0123abcd.js").await;
    assert_eq!(status, StatusCode::NOT_FOUND);
    assert_eq!(headers[header::CACHE_CONTROL], "no-cache");
    assert_eq!(headers[header::CONTENT_SECURITY_POLICY], CSP);
    let (status, _, _) = call(&env.app, request(Method::POST, "/app/app.js")).await;
    assert_eq!(status, StatusCode::METHOD_NOT_ALLOWED);
}

/// A small static site in the form of the project site: pages in two languages, a script, a style
/// sheet, data files and a page for the status 404.
fn write_site(tmp: &Path, with_404: bool) -> PathBuf {
    let site = tmp.join("site");
    for folder in ["de", "about", "static", "data/records/26171", "empty"] {
        std::fs::create_dir_all(site.join(folder)).unwrap();
    }
    std::fs::write(
        site.join("index.html"),
        "<!doctype html><title>site page</title>",
    )
    .unwrap();
    std::fs::write(
        site.join("de/index.html"),
        "<!doctype html><title>Seite</title>",
    )
    .unwrap();
    std::fs::write(
        site.join("about/index.html"),
        "<!doctype html><title>about</title>",
    )
    .unwrap();
    std::fs::write(site.join("static/explorer.js"), "// site script\n").unwrap();
    std::fs::write(site.join("static/site.css"), "body{}\n").unwrap();
    std::fs::write(
        site.join("static/favicon.svg"),
        "<svg xmlns=\"http://www.w3.org/2000/svg\"/>",
    )
    .unwrap();
    std::fs::write(site.join("data/build.json"), "{}").unwrap();
    std::fs::write(site.join("data/records/26171/instance.yaml"), "a: 1\n").unwrap();
    std::fs::write(site.join("robots.txt"), "User-agent: *\n").unwrap();
    std::fs::write(site.join("SHA256SUMS"), "0  index.html\n").unwrap();
    std::fs::write(site.join(".hidden"), "x").unwrap();
    if with_404 {
        std::fs::write(
            site.join("404.html"),
            "<!doctype html><title>no such page</title>",
        )
        .unwrap();
    }
    site
}

#[tokio::test]
async fn the_optional_site_is_below_the_root() {
    let env = env_with("auto", |cfg, tmp| {
        cfg.site_dir = Some(write_site(tmp, true))
    });
    let (status, headers, body) = get(&env.app, "/").await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(headers[header::CONTENT_TYPE], "text/html; charset=utf-8");
    assert_eq!(headers[header::CONTENT_SECURITY_POLICY], SITE_CSP);
    assert_eq!(headers[header::CACHE_CONTROL], "no-cache");
    assert_eq!(headers["x-content-type-options"], "nosniff");
    assert_eq!(headers["x-frame-options"], "DENY");
    assert!(headers.get(header::SET_COOKIE).is_none());
    assert!(String::from_utf8(body).unwrap().contains("site page"));

    // Each file of the site with its media type. The policy of the site, not the policy of the app.
    for (path, media) in [
        ("/index.html", "text/html; charset=utf-8"),
        ("/de/", "text/html; charset=utf-8"),
        ("/about/", "text/html; charset=utf-8"),
        ("/about/index.html", "text/html; charset=utf-8"),
        ("/static/explorer.js", "text/javascript; charset=utf-8"),
        ("/static/site.css", "text/css; charset=utf-8"),
        ("/static/favicon.svg", "image/svg+xml; charset=utf-8"),
        ("/data/build.json", "application/json; charset=utf-8"),
        ("/data/records/26171/instance.yaml", "application/yaml"),
        ("/robots.txt", "text/plain; charset=utf-8"),
        ("/SHA256SUMS", "text/plain; charset=utf-8"),
    ] {
        let (status, headers, _) = get(&env.app, path).await;
        assert_eq!(status, StatusCode::OK, "{path}");
        assert_eq!(headers[header::CONTENT_TYPE], media, "{path}");
        assert_eq!(headers[header::CONTENT_SECURITY_POLICY], SITE_CSP, "{path}");
        assert_eq!(headers[header::CACHE_CONTROL], "no-cache", "{path}");
    }
    // The German page is another file than the start page.
    assert!(String::from_utf8(get(&env.app, "/de/").await.2)
        .unwrap()
        .contains("Seite"));
    // A query does not change the file.
    assert_eq!(get(&env.app, "/de/?x=1").await.0, StatusCode::OK);

    // A folder with no slash at the end redirects to the folder address on this server.
    for (path, target) in [("/de", "/de/"), ("/about", "/about/")] {
        let (status, headers, _) = get(&env.app, path).await;
        assert_eq!(status, StatusCode::TEMPORARY_REDIRECT, "{path}");
        assert_eq!(headers[header::LOCATION], target, "{path}");
    }

    // A path with no file: the page 404.html of the site, with the status 404.
    for path in [
        "/no-such-page",
        "/de/no-such-page/",
        "/empty/",
        "/static/",
        "/../secret.txt",
        "/.hidden",
        "/%2e%2e/secret.txt",
    ] {
        let (status, headers, body) = get(&env.app, path).await;
        assert_eq!(status, StatusCode::NOT_FOUND, "{path}");
        assert_eq!(
            headers[header::CONTENT_TYPE],
            "text/html; charset=utf-8",
            "{path}"
        );
        assert_eq!(headers[header::CONTENT_SECURITY_POLICY], SITE_CSP, "{path}");
        let text = String::from_utf8(body).unwrap();
        assert!(
            text.contains("no such page") && !text.contains("outside of the UI folder"),
            "{path}"
        );
    }

    // The app and the API stay at their addresses, with their own policies.
    let (status, headers, body) = get(&env.app, "/app/").await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(headers[header::CONTENT_SECURITY_POLICY], CSP);
    assert!(String::from_utf8(body).unwrap().contains("test page"));
    assert_eq!(
        get(&env.app, "/app").await.0,
        StatusCode::PERMANENT_REDIRECT
    );
    assert_eq!(
        get(&env.app, "/app/no-such-file.js").await.0,
        StatusCode::NOT_FOUND
    );
    let (status, body) = get_json(&env.app, "/api/health").await;
    assert_eq!(
        (status, body["schema"].as_str()),
        (StatusCode::OK, Some("parlpdfech-health/1"))
    );
    assert_eq!(body["site"], true);
    let (status, body) = get_json(&env.app, "/api/no-such-address").await;
    assert_error(status, &body, "not_found", 404);

    // The host rule applies to the site as to the app. A method that changes something gets no file.
    let foreign = Request::builder()
        .uri("/")
        .header(header::HOST, "evil.example")
        .body(Body::empty())
        .unwrap();
    let (status, _, body) = call(&env.app, foreign).await;
    assert_eq!(
        (status, body.as_slice()),
        (StatusCode::FORBIDDEN, b"forbidden".as_slice())
    );
    for method in [Method::POST, Method::PUT, Method::DELETE] {
        let (status, _, body) = call(&env.app, request(method.clone(), "/")).await;
        assert_eq!(status, StatusCode::METHOD_NOT_ALLOWED, "{method}");
        assert!(
            !String::from_utf8_lossy(&body).contains("site page"),
            "{method}"
        );
    }
    // No request changed the site folder (11 files that the server gives, and the dot file).
    assert_eq!(site_file_count(&env), 12);
}

fn site_file_count(env: &Env) -> usize {
    fn walk(dir: &Path) -> usize {
        std::fs::read_dir(dir)
            .unwrap()
            .flatten()
            .map(|e| {
                if e.path().is_dir() {
                    walk(&e.path())
                } else {
                    1
                }
            })
            .sum()
    }
    walk(&env.tmp.path().join("site"))
}

#[tokio::test]
async fn a_site_with_no_404_page_and_a_server_with_no_site() {
    // A site with no file 404.html: the plain answer.
    let plain = env_with("auto", |cfg, tmp| {
        cfg.site_dir = Some(write_site(tmp, false))
    });
    let (status, headers, body) = get(&plain.app, "/no-such-page").await;
    assert_eq!(
        (status, body.as_slice()),
        (StatusCode::NOT_FOUND, b"not found".as_slice())
    );
    assert_eq!(headers[header::CONTENT_SECURITY_POLICY], SITE_CSP);

    // No site: the address / redirects to the app, each other address is not known, and health says so.
    let env = env("auto");
    let (status, headers, _) = get(&env.app, "/").await;
    assert_eq!(status, StatusCode::TEMPORARY_REDIRECT);
    assert_eq!(headers[header::LOCATION], "/app/");
    let (status, headers, _) = get(&env.app, "/?lang=de").await;
    assert_eq!(
        (status, headers[header::LOCATION].to_str().unwrap()),
        (StatusCode::TEMPORARY_REDIRECT, "/app/?lang=de")
    );
    assert_eq!(get(&env.app, "/de/").await.0, StatusCode::NOT_FOUND);
    assert_eq!(
        get(&env.app, "/static/site.css").await.0,
        StatusCode::NOT_FOUND
    );
    assert_eq!(get_json(&env.app, "/api/health").await.1["site"], false);

    // A site folder with no index.html is dropped: the server behaves as with no site.
    let tmp = tempfile::tempdir().unwrap();
    std::fs::create_dir_all(tmp.path().join("site")).unwrap();
    let mut cfg = (*env.state.cfg).clone();
    cfg.site_dir = Some(tmp.path().join("site"));
    assert!(cfg.drop_absent_site());
    assert!(cfg.site_dir.is_none());
    cfg.site_dir = Some(write_site(tmp.path(), true));
    assert!(!cfg.drop_absent_site());
    assert!(cfg.site_dir.is_some());
}

#[tokio::test]
async fn the_read_only_setting_applies_to_the_site_and_hosted_is_a_health_key() {
    let env = env_with("auto", |cfg, tmp| {
        cfg.site_dir = Some(write_site(tmp, true));
        cfg.readonly = true;
        cfg.hosted = true;
    });
    let (_, h) = get_json(&env.app, "/api/health").await;
    assert_eq!(
        (
            h["site"].clone(),
            h["hosted"].clone(),
            h["modes"]["read_only"].clone()
        ),
        (json!(true), json!(true), json!(true))
    );
    assert_eq!(get(&env.app, "/").await.0, StatusCode::OK);
    // A DELETE of a page address is refused before the file service, as below /app/.
    for path in ["/", "/de/", "/static/site.css", "/app/"] {
        let (status, _, body) = call(&env.app, request(Method::DELETE, path)).await;
        assert_eq!(
            (status, body.as_slice()),
            (StatusCode::FORBIDDEN, b"forbidden".as_slice()),
            "{path}"
        );
    }
    assert!(env.tmp.path().join("site/index.html").is_file());
}

#[tokio::test]
async fn the_server_keeps_the_last_20_jobs() {
    let env = env("refused");
    let mut ids = Vec::new();
    for _ in 0..22 {
        let id = start_sample(&env.app, "26171", "auto").await;
        events(&env.app, &id).await;
        ids.push(id);
    }
    for id in &ids[..2] {
        let (status, body) = get_json(&env.app, &format!("/api/jobs/{id}")).await;
        assert_error(status, &body, "job_unknown", 404);
    }
    for id in &ids[2..] {
        assert_eq!(
            get(&env.app, &format!("/api/jobs/{id}")).await.0,
            StatusCode::OK
        );
    }
}

#[tokio::test]
async fn a_foreign_host_or_origin_is_refused() {
    let env = env("auto");
    let with = |method: Method, path: &str, headers: &[(&str, &str)]| {
        let mut b = Request::builder().method(method).uri(path);
        for (k, v) in headers {
            b = b.header(*k, *v);
        }
        b.body(Body::empty()).unwrap()
    };
    let json = |body: &[u8]| serde_json::from_slice::<Value>(body).unwrap();
    // DNS rebinding: the host name of another site.
    for host in [
        "evil.example",
        "evil.example:8080",
        "127.0.0.1.evil.example",
        "localhost.evil.example:80",
    ] {
        let (status, _, body) = call(
            &env.app,
            with(Method::GET, "/api/samples", &[("host", host)]),
        )
        .await;
        assert_error(status, &json(&body), "forbidden", 403);
        let (status, _, _) = call(&env.app, with(Method::GET, "/app/", &[("host", host)])).await;
        assert_eq!(status, StatusCode::FORBIDDEN, "{host}");
    }
    let (status, _, body) = call(&env.app, with(Method::GET, "/api/samples", &[])).await;
    assert_error(status, &json(&body), "forbidden", 403);
    let (status, _, _) = call(
        &env.app,
        with(
            Method::GET,
            "http://evil.example/api/health",
            &[("host", "127.0.0.1")],
        ),
    )
    .await;
    assert_eq!(status, StatusCode::FORBIDDEN);
    for host in [
        "localhost",
        "localhost:8894",
        "127.0.0.1:1",
        "[::1]:8080",
        "LOCALHOST:8080",
    ] {
        let (status, _, _) = call(
            &env.app,
            with(Method::GET, "/api/samples", &[("host", host)]),
        )
        .await;
        assert_eq!(status, StatusCode::OK, "{host}");
    }
    // The health address of a container check needs no host name.
    assert_eq!(
        call(&env.app, with(Method::GET, "/healthz", &[])).await.0,
        StatusCode::OK
    );

    // A request of another site that changes something (a form POST needs no preflight).
    let cases: [&[(&str, &str)]; 5] = [
        &[("host", HOST), ("origin", "https://evil.example")],
        &[("host", HOST), ("origin", "null")],
        &[("host", HOST), ("origin", "http://127.0.0.1:9999")],
        &[("host", HOST), ("sec-fetch-site", "cross-site")],
        &[("host", HOST), ("sec-fetch-site", "same-site")],
    ];
    for headers in cases {
        let mut req = multipart(&[("sample", None, b"26171")]);
        for (k, v) in headers {
            req.headers_mut()
                .insert(axum::http::HeaderName::from_static(k), v.parse().unwrap());
        }
        let (status, _, body) = call(&env.app, req).await;
        assert_error(status, &json(&body), "forbidden", 403);
        let (status, _, _) = call(
            &env.app,
            with(Method::DELETE, "/api/records/s-26171", headers),
        )
        .await;
        assert_eq!(status, StatusCode::FORBIDDEN);
    }
    assert!(jobs_dir_is_empty(&env));
    // The page of this server: Origin is the own origin.
    let mut req = multipart(&[("sample", None, b"26171")]);
    req.headers_mut()
        .insert(header::ORIGIN, format!("http://{HOST}").parse().unwrap());
    req.headers_mut()
        .insert("sec-fetch-site", "same-origin".parse().unwrap());
    let (status, _, body) = call(&env.app, req).await;
    assert_eq!(
        status,
        StatusCode::ACCEPTED,
        "{}",
        String::from_utf8_lossy(&body)
    );
    let id = json(&body)["job_id"].as_str().unwrap().to_string();
    assert_eq!(events(&env.app, &id).await.last().unwrap().0, "done");

    // A name of the list PARLPDFECH_ALLOWED_HOSTS.
    let listed = env_with("auto", |cfg, _| {
        cfg.allowed_hosts = vec!["parl.test".into()]
    });
    assert_eq!(
        call(
            &listed.app,
            with(Method::GET, "/api/samples", &[("host", "parl.test:8080")])
        )
        .await
        .0,
        StatusCode::OK
    );
}

#[tokio::test]
async fn a_path_that_is_not_utf8_gives_the_error_object() {
    let env = env("auto");
    for path in [
        "/api/records/%ff",
        "/api/jobs/%ff",
        "/api/jobs/%ff/events",
        "/api/records/s-1/files/%ff",
        "/api/records/%ff/bundle.zip",
    ] {
        let (status, body) = get_json(&env.app, path).await;
        assert_error(status, &body, "not_found", 404);
    }
    let (status, _, body) = call(&env.app, request(Method::DELETE, "/api/records/%ff")).await;
    assert_error(
        status,
        &serde_json::from_slice(&body).unwrap(),
        "not_found",
        404,
    );
}

#[tokio::test]
async fn the_server_gives_only_the_page_files_of_the_ui_folder() {
    let env = env_with("auto", |cfg, tmp| {
        let ui = &cfg.ui_dir;
        std::fs::create_dir_all(ui.join("fixtures")).unwrap();
        std::fs::create_dir_all(ui.join("tools")).unwrap();
        std::fs::write(ui.join("README.md"), "notes of the development").unwrap();
        std::fs::write(ui.join("fixtures/view.json"), "{}").unwrap();
        std::fs::write(ui.join("tools/check.mjs"), "//").unwrap();
        std::fs::write(ui.join(".hidden.json"), "{}").unwrap();
        std::os::unix::fs::symlink(tmp.join("secret.txt"), ui.join("link.txt")).unwrap();
        std::fs::write(ui.join("report-20261013.html"), "<title>dated</title>").unwrap();
    });
    for path in [
        "/app/README.md",
        "/app/fixtures/view.json",
        "/app/fixtures/",
        "/app/fixtures",
        "/app/tools/check.mjs",
        "/app/pkg",
        "/app/pkg/",
        "/app/.hidden.json",
        "/app/link.txt",
    ] {
        let (status, headers, _) = get(&env.app, path).await;
        assert_eq!(status, StatusCode::NOT_FOUND, "{path}");
        assert!(headers.get(header::LOCATION).is_none(), "{path}");
    }
    // A name of 256 and more bytes gives 404, not an error of the file system.
    assert_eq!(
        get(&env.app, &format!("/app/{}", "a".repeat(256))).await.0,
        StatusCode::NOT_FOUND
    );
    assert_eq!(
        get(&env.app, &format!("/app/{}.js", "a".repeat(300)))
            .await
            .0,
        StatusCode::NOT_FOUND
    );
    // A file name with a date is not a file with a content hash.
    let (status, headers, _) = get(&env.app, "/app/report-20261013.html").await;
    assert_eq!(
        (status, headers[header::CACHE_CONTROL].to_str().unwrap()),
        (StatusCode::OK, "no-cache")
    );
}

#[tokio::test]
async fn a_stage_line_passes_only_checked_values_and_a_flood_is_cut() {
    let env = env("dirty_stage");
    let id = start_sample(&env.app, "26171", "auto").await;
    let evs = events(&env.app, &id).await;
    let (_, job) = get_json(&env.app, &format!("/api/jobs/{id}")).await;
    let all = format!("{evs:?}{job}");
    assert!(
        !all.contains("/fake/secret") && !all.contains("Traceback") && !all.contains("extra_key"),
        "{all}"
    );
    assert_eq!(
        evs[1].1,
        r#"{"counts":{"pages":1},"event":"stage","id":"read_pdf","note":"view_absent","seconds":0.001,"state":"done"}"#
    );
    assert_eq!(job["stages"][0]["counts"], json!({"pages": 1}));
    assert_eq!(job["stages"][0]["origin"], Value::Null);

    let flood = env_with("flood", |_, _| {});
    let id = start_sample(&flood.app, "26171", "auto").await;
    let evs = events(&flood.app, &id).await;
    assert_eq!(evs.len(), 65, "64 stage events and the end event");
    assert_eq!(evs.last().unwrap().0, "done");
}

#[tokio::test]
async fn an_output_with_absent_files_is_not_a_record() {
    let env = env("few_files");
    let id = start_sample(&env.app, "26171", "auto").await;
    assert_eq!(events(&env.app, &id).await.last().unwrap().0, "failed");
    let (_, job) = get_json(&env.app, &format!("/api/jobs/{id}")).await;
    assert_eq!(job["error"]["code"], "converter_stopped");
    assert_eq!(job["error"]["detail"], json!({"note": "output"}));
    assert!(!env.work().join("records/s-26171").exists());
}

#[tokio::test]
async fn a_second_process_does_not_get_the_work_folder() {
    let env = env("auto");
    let first = env.state.lock_work_dir().unwrap();
    assert!(env.state.lock_work_dir().is_err());
    drop(first);
    assert!(env.state.lock_work_dir().is_ok());
}

#[tokio::test]
async fn the_read_only_setting_takes_no_file_and_refuses_each_delete() {
    let env = env_with("auto", |cfg, _| cfg.readonly = true);
    let (_, h) = get_json(&env.app, "/api/health").await;
    assert_eq!(h["modes"]["upload"], false);
    assert_eq!(h["modes"]["reason"]["upload"], "read_only");
    assert_eq!(h["modes"]["read_only"], true);
    assert_eq!(h["modes"]["sample_runs"], true);
    assert_eq!(h["modes"]["samples"], true);

    // A file is refused before a byte of it is written. No job starts.
    let pdf = tiny_pdf("public");
    for parts in [
        vec![("file", Some("a.pdf"), pdf.as_slice())],
        vec![
            ("mode", None, b"auto".as_slice()),
            ("file", Some("a.pdf"), pdf.as_slice()),
        ],
        vec![
            ("sample", None, b"26171".as_slice()),
            ("file", Some("a.pdf"), pdf.as_slice()),
        ],
    ] {
        let (status, body) = post_form(&env.app, &parts).await;
        assert_error(status, &body, "read_only", 403);
        assert_eq!(body["error"]["detail"], json!({"note": "upload"}));
        assert!(body["error"]["text"]["en"]
            .as_str()
            .unwrap()
            .starts_with("This site shows the samples only."));
        assert!(!body.to_string().contains("localhost"));
        assert!(jobs_dir_is_empty(&env));
    }
    let (_, h) = get_json(&env.app, "/api/health").await;
    assert_eq!(h["busy"], false);

    // The run of a sample stays (form and JSON).
    let id = start_sample(&env.app, "26171", "auto").await;
    assert_eq!(events(&env.app, &id).await.last().unwrap().0, "done");
    let (status, body) = post_form(
        &env.app,
        &[("sample", None, b"26171"), ("mode", None, b"rules")],
    )
    .await;
    assert_eq!(status, StatusCode::ACCEPTED, "{body}");
    let rules = body["job_id"].as_str().unwrap().to_string();
    assert_eq!(events(&env.app, &rules).await.last().unwrap().0, "done");

    // Each DELETE is refused and changes nothing: a record, a job, an unknown id, a page address.
    for path in [
        "/api/records/s-26171",
        "/api/records/s-26171-rules",
        "/api/records/s-1",
        &format!("/api/jobs/{id}"),
        "/api/jobs/x",
    ] {
        let (status, _, body) = call(&env.app, request(Method::DELETE, path)).await;
        let body: Value = serde_json::from_slice(&body).unwrap();
        assert_error(status, &body, "read_only", 403);
        assert_eq!(body["error"]["detail"], json!({"note": "delete"}), "{path}");
    }
    assert_eq!(
        call(&env.app, request(Method::DELETE, "/app/index.html"))
            .await
            .0,
        StatusCode::FORBIDDEN
    );
    assert!(env.work().join("records/s-26171/view.json").is_file());
    assert!(env.work().join("records/s-26171-rules/view.json").is_file());
    assert_eq!(
        get(&env.app, "/api/records/s-26171").await.0,
        StatusCode::OK
    );
    assert_eq!(
        get(&env.app, "/api/records/s-26171/bundle.zip").await.0,
        StatusCode::OK
    );

    // A running job is not stopped by a DELETE.
    let hang = env_with("hang", |cfg, _| cfg.readonly = true);
    let id = start_sample(&hang.app, "26171", "auto").await;
    let (status, _, _) = call(
        &hang.app,
        request(Method::DELETE, &format!("/api/jobs/{id}")),
    )
    .await;
    assert_eq!(status, StatusCode::FORBIDDEN);
    let (_, job) = get_json(&hang.app, &format!("/api/jobs/{id}")).await;
    assert!(
        job["state"] == "running" || job["state"] == "queued",
        "{job}"
    );
    hang.state.jobs.stop_active(Duration::from_secs(3)).await;

    // With no setting the same DELETE works.
    let open = env_with("auto", |_, _| {});
    let id = start_sample(&open.app, "26171", "auto").await;
    assert_eq!(events(&open.app, &id).await.last().unwrap().0, "done");
    assert_eq!(
        call(&open.app, request(Method::DELETE, "/api/records/s-26171"))
            .await
            .0,
        StatusCode::NO_CONTENT
    );
}

#[tokio::test]
async fn sample_runs_off_serves_a_ready_record_and_starts_no_new_run() {
    let env = env_with("auto", |cfg, _| {
        cfg.readonly = true;
        cfg.sample_runs = false;
    });
    let (_, h) = get_json(&env.app, "/api/health").await;
    assert_eq!(h["modes"]["sample_runs"], false);
    assert_eq!(h["modes"]["read_only"], true);

    // No record yet: the run is accepted, so that the site can make the record.
    let id = start_sample(&env.app, "26171", "auto").await;
    assert_eq!(events(&env.app, &id).await.last().unwrap().0, "done");
    assert!(env.work().join("records/s-26171/view.json").is_file());

    // The record is ready: a new run is refused (JSON and form) and no job folder is made.
    let (status, body) = post_json(&env.app, json!({"sample": "26171", "mode": "auto"})).await;
    assert_error(status, &body, "sample_runs_off", 403);
    assert_eq!(body["error"]["detail"], json!({"record_id": "s-26171"}));
    let (status, body) = post_form(&env.app, &[("sample", None, b"26171")]).await;
    assert_error(status, &body, "sample_runs_off", 403);
    assert!(jobs_dir_is_empty(&env));
    let (_, h) = get_json(&env.app, "/api/health").await;
    assert_eq!(h["busy"], false);
    assert_eq!(
        get(&env.app, "/api/records/s-26171").await.0,
        StatusCode::OK
    );

    // The other mode of the same sample has no record: its run is accepted one time.
    let (status, body) = post_json(&env.app, json!({"sample": "26171", "mode": "rules"})).await;
    assert_eq!(status, StatusCode::ACCEPTED, "{body}");
    let rules = body["job_id"].as_str().unwrap().to_string();
    assert_eq!(events(&env.app, &rules).await.last().unwrap().0, "done");
    let (status, body) = post_json(&env.app, json!({"sample": "26171", "mode": "rules"})).await;
    assert_error(status, &body, "sample_runs_off", 403);

    // An unknown sample keeps its own code.
    let (status, body) = post_json(&env.app, json!({"sample": "99999"})).await;
    assert_error(status, &body, "sample_unknown", 404);

    // With the default (on) a ready record is converted again.
    let open = env_with("auto", |_, _| {});
    let id = start_sample(&open.app, "26171", "auto").await;
    assert_eq!(events(&open.app, &id).await.last().unwrap().0, "done");
    let (status, body) = post_json(&open.app, json!({"sample": "26171"})).await;
    assert_eq!(status, StatusCode::ACCEPTED);
    let again = body["job_id"].as_str().unwrap().to_string();
    assert_eq!(events(&open.app, &again).await.last().unwrap().0, "done");

    // Sample runs off with no read-only setting: the refusal has its own code, and its text makes no
    // statement about files or about DELETE (the server still takes a file and deletes a record).
    let env = env_with("auto", |cfg, _| cfg.sample_runs = false);
    let (_, h) = get_json(&env.app, "/api/health").await;
    assert_eq!(
        (
            h["modes"]["sample_runs"].clone(),
            h["modes"]["read_only"].clone(),
            h["modes"]["upload"].clone()
        ),
        (json!(false), json!(false), json!(true))
    );
    let id = start_sample(&env.app, "26171", "auto").await;
    assert_eq!(events(&env.app, &id).await.last().unwrap().0, "done");
    let (status, body) = post_json(&env.app, json!({"sample": "26171"})).await;
    assert_error(status, &body, "sample_runs_off", 403);
    for lang in ["en", "de"] {
        let text = format!(
            "{} {}",
            body["error"]["title"][lang], body["error"]["text"][lang]
        )
        .to_lowercase();
        for word in [
            "file",
            "datei",
            "delete",
            "lösch",
            "samples only",
            "nur die beispiele",
        ] {
            assert!(!text.contains(word), "{lang}: {text}");
        }
    }
    let (status, _, _) = call(&env.app, request(Method::DELETE, "/api/records/s-26171")).await;
    assert_eq!(status, StatusCode::NO_CONTENT);
}
