//! The binary `parlpdfech-server`. It reads the configuration from the environment
//! (CONTRACT.md chapter 2.1), serves until the signal TERM or INT, stops the worker and exits.

use std::process::ExitCode;
use std::time::Duration;

use parlpdfech_server::{build_app, AppState, Config, Flag};
use tokio::signal::unix::{signal, SignalKind};

#[tokio::main]
async fn main() -> ExitCode {
    tracing_subscriber::fmt()
        .with_writer(std::io::stderr)
        .with_ansi(false)
        .init();

    let mut cfg = match Config::from_env() {
        Ok(cfg) => cfg,
        Err(text) => {
            tracing::error!(target: "server", error = %text, "invalid configuration");
            return ExitCode::from(2);
        }
    };
    if cfg.drop_absent_site() {
        tracing::warn!(target: "server", "the site folder has no index.html: the address / redirects to /app/");
    }
    let state = AppState::new(cfg);
    // First the port, then the lock of the work folder, then the clean-up of the job folders.
    // A second process with the same port or the same work folder stops before it changes a file.
    let listener = match tokio::net::TcpListener::bind(&state.cfg.bind).await {
        Ok(listener) => listener,
        Err(e) => {
            tracing::error!(target: "server", error = %e, bind = %state.cfg.bind, "bind failed");
            return ExitCode::from(2);
        }
    };
    let _work_lock = match state.lock_work_dir() {
        Ok(file) => file,
        Err(e) => {
            tracing::error!(target: "server", error = %e, dir = %state.cfg.work_dir.display(), "the work folder is not usable (no lock)");
            return ExitCode::from(2);
        }
    };
    if let Err(e) = state.prepare_work_dir() {
        tracing::error!(target: "server", error = %e, dir = %state.cfg.work_dir.display(), "the work folder is not writable");
        return ExitCode::from(2);
    }
    let loopback = listener
        .local_addr()
        .map(|a| a.ip().is_loopback())
        .unwrap_or(false);
    if !loopback {
        tracing::warn!(target: "server", bind = %state.cfg.bind, "the listen address is not a loopback address: the API has no authentication; publish the port on 127.0.0.1 only");
    }
    if !state.cfg.ui_dir.join("index.html").is_file() {
        tracing::warn!(target: "server", "the UI folder has no index.html");
    }
    if !state
        .cfg
        .data_dir
        .join("samples")
        .join("index.json")
        .is_file()
    {
        tracing::warn!(target: "server", "the data folder has no samples/index.json");
    }
    tracing::info!(
        target: "server",
        bind = %state.cfg.bind,
        profile = %state.cfg.profile,
        version = env!("CARGO_PKG_VERSION"),
        commit = %state.cfg.commit,
        ui_dir = %state.cfg.ui_dir.display(),
        data_dir = %state.cfg.data_dir.display(),
        work_dir = %state.cfg.work_dir.display(),
        site = state.cfg.site_dir.is_some(),
        max_bytes = state.cfg.max_bytes,
        max_pages = state.cfg.max_pages,
        job_timeout_seconds = state.cfg.job_timeout.as_secs(),
        readonly = state.cfg.readonly,
        sample_runs = state.cfg.sample_runs,
        hosted = state.cfg.hosted,
        "listening"
    );

    let stop = Flag::default();
    let on_signal = stop.clone();
    tokio::spawn(async move {
        let (Ok(mut term), Ok(mut int)) = (
            signal(SignalKind::terminate()),
            signal(SignalKind::interrupt()),
        ) else {
            tracing::error!(target: "server", "no signal handler");
            return;
        };
        tokio::select! {
            _ = term.recv() => tracing::info!(target: "server", signal = "TERM", "stop requested"),
            _ = int.recv() => tracing::info!(target: "server", signal = "INT", "stop requested"),
        }
        on_signal.set();
    });

    // First the worker stops, then the server takes no new connection and ends.
    let jobs = state.jobs.clone();
    let grace = state.cfg.kill_grace + Duration::from_secs(2);
    let graceful = stop.clone();
    let shutdown = async move {
        graceful.wait().await;
        jobs.stop_active(grace).await;
    };
    let serve = axum::serve(listener, build_app(state)).with_graceful_shutdown(shutdown);
    let limit = async {
        stop.wait().await;
        tokio::time::sleep(grace + Duration::from_secs(5)).await;
    };
    tokio::select! {
        result = serve => {
            if let Err(e) = result {
                tracing::error!(target: "server", error = %e, "server error");
                return ExitCode::from(1);
            }
        }
        _ = limit => tracing::warn!(target: "server", "open connections were closed at the stop"),
    }
    tracing::info!(target: "server", "stopped");
    ExitCode::SUCCESS
}
