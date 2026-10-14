//! Records: the view, the files and the archive (CONTRACT.md chapters 3 and 5.2).

use std::io::Write;
use std::path::PathBuf;

use axum::extract::{Path as UrlPath, RawQuery, State};
use axum::http::{header, HeaderValue, StatusCode};
use axum::response::{IntoResponse, Response};
use sha2::{Digest, Sha256};

use crate::errors::ApiError;
use crate::{bytes_response, ids, AppState};

/// Checks the record id against the pattern and gives the record folder. No file access before the check.
fn record_dir(st: &AppState, record_id: &str) -> Result<PathBuf, ApiError> {
    if !ids::is_record_id(record_id) {
        // The value of the client does not go into the answer.
        return Err(ApiError::new("record_unknown").with("record_id", ""));
    }
    Ok(st.cfg.records_dir().join(record_id))
}

fn unknown(record_id: &str) -> ApiError {
    ApiError::new("record_unknown").with("record_id", record_id)
}

fn internal(note: &'static str) -> impl Fn(std::io::Error) -> ApiError {
    move |e| {
        tracing::error!(target: "records", error = %e, note, "file system error");
        ApiError::new("internal").with("note", note)
    }
}

/// `GET /api/records/{record_id}`: the bytes of `view.json`.
pub async fn get_view(
    State(st): State<AppState>,
    UrlPath(record_id): UrlPath<String>,
) -> Result<Response, ApiError> {
    let dir = record_dir(&st, &record_id)?;
    match tokio::fs::read(dir.join("view.json")).await {
        Ok(bytes) => Ok(bytes_response(bytes, "application/json; charset=utf-8")),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Err(unknown(&record_id)),
        Err(e) => Err(internal("record_read")(e)),
    }
}

/// `GET /api/records/{record_id}/files/{name}`: the bytes of one file, not changed.
pub async fn get_file(
    State(st): State<AppState>,
    UrlPath((record_id, name)): UrlPath<(String, String)>,
    RawQuery(query): RawQuery,
) -> Result<Response, ApiError> {
    let dir = record_dir(&st, &record_id)?;
    let Some(media_type) = ids::file_media_type(&name) else {
        return Err(ApiError::new("file_unknown")
            .with("record_id", record_id)
            .with("name", ""));
    };
    let bytes = match tokio::fs::read(dir.join(&name)).await {
        Ok(bytes) => bytes,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
            let has_record = tokio::fs::metadata(&dir)
                .await
                .map(|m| m.is_dir())
                .unwrap_or(false);
            return Err(if has_record {
                ApiError::new("file_unknown")
                    .with("record_id", record_id)
                    .with("name", name)
            } else {
                unknown(&record_id)
            });
        }
        Err(e) => return Err(internal("file_read")(e)),
    };
    let mut res = bytes_response(bytes, media_type);
    let download = query
        .as_deref()
        .is_some_and(|q| q.split('&').any(|p| p == "download=1"));
    if download {
        // The name passed the pattern check. It holds only digits, letters and dots. The PDF of a record gets the
        // name of the record (finding F5 of 14.10.2026: each PDF was saved as source.pdf).
        let save_as = if name == "source.pdf" {
            format!("parlpdfech-{record_id}.pdf")
        } else {
            name.clone()
        };
        if let Ok(value) = HeaderValue::from_str(&format!("attachment; filename=\"{save_as}\"")) {
            res.headers_mut().insert(header::CONTENT_DISPOSITION, value);
        }
    }
    Ok(res)
}

/// `DELETE /api/records/{record_id}`: deletes the record folder. Answer 204.
pub async fn delete_record(
    State(st): State<AppState>,
    UrlPath(record_id): UrlPath<String>,
) -> Result<Response, ApiError> {
    let dir = record_dir(&st, &record_id)?;
    // A rename first: no reader sees a half deleted record.
    let trash = st
        .cfg
        .records_dir()
        .join(format!(".del-{}", uuid::Uuid::new_v4()));
    match tokio::fs::rename(&dir, &trash).await {
        Ok(()) => {}
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Err(unknown(&record_id)),
        Err(e) => return Err(internal("record_delete")(e)),
    }
    tokio::fs::remove_dir_all(&trash)
        .await
        .map_err(internal("record_delete"))?;
    tracing::info!(target: "records", record_id = %record_id, "record deleted");
    Ok(StatusCode::NO_CONTENT.into_response())
}

/// `GET /api/records/{record_id}/bundle.zip`: the files of the record in the sequence of the
/// contract, then `SHA256SUMS`, all below the folder `parlpdfech-<record_id>/`.
pub async fn get_bundle(
    State(st): State<AppState>,
    UrlPath(record_id): UrlPath<String>,
) -> Result<Response, ApiError> {
    let dir = record_dir(&st, &record_id)?;
    let mut names: Vec<(usize, String)> = Vec::new();
    let mut entries = match tokio::fs::read_dir(&dir).await {
        Ok(entries) => entries,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Err(unknown(&record_id)),
        Err(e) => return Err(internal("record_read")(e)),
    };
    while let Some(entry) = entries
        .next_entry()
        .await
        .map_err(internal("record_read"))?
    {
        if let Some(name) = entry.file_name().to_str() {
            if let Some(rank) = ids::file_rank(name) {
                names.push((rank, name.to_string()));
            }
        }
    }
    if !names.iter().any(|(_, n)| n == "view.json") {
        return Err(unknown(&record_id));
    }
    names.sort();
    let mut files: Vec<(String, Vec<u8>)> = Vec::with_capacity(names.len());
    for (_, name) in names {
        let bytes = tokio::fs::read(dir.join(&name))
            .await
            .map_err(internal("file_read"))?;
        files.push((name, bytes));
    }
    let folder = format!("parlpdfech-{record_id}");
    let archive = tokio::task::spawn_blocking(move || make_zip(&folder, &files))
        .await
        .map_err(|_| ApiError::new("internal").with("note", "bundle"))?
        .map_err(|e| {
            tracing::error!(target: "records", error = %e, "the archive was not made");
            ApiError::new("internal").with("note", "bundle")
        })?;
    let mut res = bytes_response(archive, "application/zip");
    if let Ok(value) = HeaderValue::from_str(&format!(
        "attachment; filename=\"parlpdfech-{record_id}.zip\""
    )) {
        res.headers_mut().insert(header::CONTENT_DISPOSITION, value);
    }
    Ok(res)
}

/// The text of `SHA256SUMS`: one line for each file, `<sha256>  <name>`, sorted by name.
pub fn sha256sums(files: &[(String, Vec<u8>)]) -> String {
    let mut lines: Vec<(&str, String)> = files
        .iter()
        .map(|(name, bytes)| (name.as_str(), hex::encode(Sha256::digest(bytes))))
        .collect();
    lines.sort();
    lines
        .iter()
        .map(|(name, sum)| format!("{sum}  {name}\n"))
        .collect()
}

fn make_zip(folder: &str, files: &[(String, Vec<u8>)]) -> zip::result::ZipResult<Vec<u8>> {
    let options = zip::write::SimpleFileOptions::default()
        .compression_method(zip::CompressionMethod::Deflated)
        .unix_permissions(0o644);
    let mut writer = zip::ZipWriter::new(std::io::Cursor::new(Vec::new()));
    for (name, bytes) in files {
        writer.start_file(format!("{folder}/{name}"), options)?;
        writer.write_all(bytes)?;
    }
    writer.start_file(format!("{folder}/SHA256SUMS"), options)?;
    writer.write_all(sha256sums(files).as_bytes())?;
    Ok(writer.finish()?.into_inner())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sums_are_sorted_by_name() {
        let files = vec![
            ("view.json".to_string(), b"{}".to_vec()),
            ("1.ech.ttl".to_string(), b"".to_vec()),
        ];
        let text = sha256sums(&files);
        let lines: Vec<&str> = text.lines().collect();
        assert_eq!(
            lines[0],
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  1.ech.ttl"
        );
        assert_eq!(
            lines[1],
            "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a  view.json"
        );
    }

    #[test]
    fn zip_has_the_files_and_the_sums() {
        let files = vec![
            ("1.gesamt.trig".to_string(), b"a".to_vec()),
            ("view.json".to_string(), b"{}".to_vec()),
        ];
        let bytes = make_zip("parlpdfech-s-1", &files).unwrap();
        let mut archive = zip::ZipArchive::new(std::io::Cursor::new(bytes)).unwrap();
        let names: Vec<String> = (0..archive.len())
            .map(|i| archive.by_index(i).unwrap().name().to_string())
            .collect();
        assert_eq!(
            names,
            [
                "parlpdfech-s-1/1.gesamt.trig",
                "parlpdfech-s-1/view.json",
                "parlpdfech-s-1/SHA256SUMS"
            ]
        );
    }
}
