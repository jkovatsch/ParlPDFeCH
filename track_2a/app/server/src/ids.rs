//! Strict patterns for each value that a client sends and that becomes part of a path
//! (CONTRACT.md chapter 3). No handler joins a client value to a path before one of these checks.

/// Converter files with the document prefix, in the sequence of CONTRACT.md chapter 3: (suffix, media type).
pub const DOC_FILES: [(&str, &str); 7] = [
    (".gesamt.trig", "application/trig"),
    (".ech.ttl", "text/turtle; charset=utf-8"),
    (".gesamt.rdf.xml", "application/rdf+xml"),
    (".ech.rdf.xml", "application/rdf+xml"),
    (".ech.yaml", "application/yaml"),
    (".labels.yaml", "application/yaml"),
    (".provenance.yaml", "application/yaml"),
];

/// Files with a fixed name, in the sequence of CONTRACT.md chapter 3.
pub const FIXED_FILES: [&str; 4] = [
    "manifest.json",
    "validation.json",
    "view.json",
    "convert.json",
];

/// Optional files of a record with values from the PDF (14.10.2026): the file of the values with the document
/// prefix, the PDF and one image of each page. The worker writes them; a record of the earlier form has none.
pub const VALUES_FILE: (&str, &str) = (".values.ttl", "text/turtle; charset=utf-8");
pub const SOURCE_PDF: &str = "source.pdf";
/// The highest page number of a page image (`page-<n>.png`, `n` from 1 to 999 with no leading zero).
pub const MAX_PAGE_IMAGE: usize = 999;

/// The page number of a page image name `page-<n>.png`, or `None`.
pub fn page_image_number(name: &str) -> Option<usize> {
    let digits = name.strip_prefix("page-")?.strip_suffix(".png")?;
    if digits.is_empty()
        || digits.len() > 3
        || digits.starts_with('0')
        || !digits.bytes().all(|b| b.is_ascii_digit())
    {
        return None;
    }
    let n: usize = digits.parse().ok()?;
    (1..=MAX_PAGE_IMAGE).contains(&n).then_some(n)
}

/// True if the name is one of the optional files: `<prefix>.values.ttl`, `source.pdf` or `page-<n>.png`.
fn is_optional_file(name: &str) -> bool {
    name == SOURCE_PDF
        || page_image_number(name).is_some()
        || name
            .strip_suffix(VALUES_FILE.0)
            .is_some_and(|p| p == "local" || is_doc_number(p))
}

/// A document number: 1 to 12 decimal digits.
pub fn is_doc_number(s: &str) -> bool {
    (1..=12).contains(&s.len()) && s.bytes().all(|b| b.is_ascii_digit())
}

/// `^(s-[0-9]{1,12}|u-[0-9a-f]{16})(-rules)?$`
pub fn is_record_id(s: &str) -> bool {
    let base = s.strip_suffix("-rules").unwrap_or(s);
    if let Some(doc) = base.strip_prefix("s-") {
        return is_doc_number(doc);
    }
    if let Some(hash) = base.strip_prefix("u-") {
        return hash.len() == 16
            && hash
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b));
    }
    false
}

/// A UUID in lower case with hyphens (8-4-4-4-12).
pub fn is_job_id(s: &str) -> bool {
    s.len() == 36
        && s.bytes().enumerate().all(|(i, b)| match i {
            8 | 13 | 18 | 23 => b == b'-',
            _ => b.is_ascii_digit() || (b'a'..=b'f').contains(&b),
        })
}

/// The media type of a record file, or `None` if the name is not one of the allowed names.
/// The prefix of a converter file is a document number or the word `local`.
pub fn file_media_type(name: &str) -> Option<&'static str> {
    if FIXED_FILES.contains(&name) {
        return Some("application/json");
    }
    if name == SOURCE_PDF {
        return Some("application/pdf");
    }
    if page_image_number(name).is_some() {
        return Some("image/png");
    }
    if let Some(prefix) = name.strip_suffix(VALUES_FILE.0) {
        return (prefix == "local" || is_doc_number(prefix)).then_some(VALUES_FILE.1);
    }
    DOC_FILES.iter().find_map(|(suffix, media)| {
        let prefix = name.strip_suffix(suffix)?;
        (prefix == "local" || is_doc_number(prefix)).then_some(*media)
    })
}

/// The position of a file name in the sequence of CONTRACT.md chapter 3 (0 to 10), then the optional files:
/// the file of the values (11), the PDF (12) and the page images (13 + page number).
pub fn file_rank(name: &str) -> Option<usize> {
    if let Some(i) = FIXED_FILES.iter().position(|f| *f == name) {
        return Some(DOC_FILES.len() + i);
    }
    let base = DOC_FILES.len() + FIXED_FILES.len();
    if name == SOURCE_PDF {
        return Some(base + 1);
    }
    if let Some(n) = page_image_number(name) {
        return Some(base + 2 + n);
    }
    if is_optional_file(name) {
        return Some(base);
    }
    file_media_type(name)?;
    DOC_FILES
        .iter()
        .position(|(suffix, _)| name.ends_with(suffix))
}

/// True if the names are the 11 files of a record: the 4 fixed names and the 7 converter files with
/// one document prefix. The only other names are the optional files: the file of the values with the same
/// prefix, the PDF and the page images.
pub fn is_complete_record(names: &[String]) -> bool {
    let has = |n: &str| names.iter().any(|x| x == n);
    let Some(prefix) = names.iter().find_map(|n| n.strip_suffix(DOC_FILES[0].0)) else {
        return false;
    };
    let optional = names
        .iter()
        .filter(|n| {
            n.as_str() == SOURCE_PDF
                || page_image_number(n).is_some()
                || n.strip_suffix(VALUES_FILE.0) == Some(prefix)
        })
        .count();
    names.len() == FIXED_FILES.len() + DOC_FILES.len() + optional
        && FIXED_FILES.iter().all(|f| has(f))
        && DOC_FILES
            .iter()
            .all(|(suffix, _)| has(&format!("{prefix}{suffix}")))
}

/// A character that changes the direction or the form of a text and shows nothing itself.
fn is_format_char(c: char) -> bool {
    matches!(c, '\u{ad}' | '\u{61c}' | '\u{200b}'..='\u{200f}' | '\u{202a}'..='\u{202e}' | '\u{2060}'..='\u{206f}' | '\u{feff}')
}

/// The name that the browser sent: no path, no control character, no format character (for example the
/// right-to-left override), at most 120 characters. The server shows this name only. It never uses it as a file name.
pub fn display_file_name(raw: &str) -> String {
    let last = raw.rsplit(['/', '\\']).next().unwrap_or("");
    let name: String = last
        .chars()
        .filter(|c| !c.is_control() && !is_format_char(*c))
        .take(120)
        .collect();
    if name.chars().all(|c| c == '.') {
        return String::new();
    }
    name
}

/// True if the mark `%PDF-` is in the first 1024 bytes.
pub fn has_pdf_mark(head: &[u8]) -> bool {
    let head = &head[..head.len().min(1024)];
    head.windows(5).any(|w| w == b"%PDF-")
}

/// True if a static file name holds a content hash: a part of 8 or more hex digits between `.` or `-`
/// and the next `.`, with 1 or more of the letters a to f or with 16 or more characters. A part of
/// decimal digits only (a date) is not a content hash.
pub fn is_hashed_name(path: &str) -> bool {
    let name = path.rsplit('/').next().unwrap_or("");
    let parts: Vec<&str> = name.split(['.', '-']).collect();
    parts.len() >= 3
        && parts[1..parts.len() - 1].iter().any(|p| {
            p.len() >= 8
                && p.bytes()
                    .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
                && (p.len() >= 16 || p.bytes().any(|b| (b'a'..=b'f').contains(&b)))
        })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn record_ids() {
        for ok in [
            "s-26171",
            "s-26171-rules",
            "u-0123456789abcdef",
            "u-0123456789abcdef-rules",
        ] {
            assert!(is_record_id(ok), "{ok}");
        }
        for bad in [
            "",
            "s-",
            "s-abc",
            "s-1/..",
            "../s-1",
            "s-1-rules-rules",
            "u-0123456789ABCDEF",
            "u-0123",
            "s-1 ",
            "s-1\0",
            "x-1",
            "s-1234567890123",
            "s-1-rule",
            ".",
            "..",
            "s-1%2f",
            "u-0123456789abcdeg",
        ] {
            assert!(!is_record_id(bad), "{bad:?}");
        }
    }

    #[test]
    fn job_ids() {
        assert!(is_job_id("0b7c1c0e-5a3f-4d0e-9b1a-2f6c8f1d7e42"));
        for bad in [
            "",
            "0B7C1C0E-5A3F-4D0E-9B1A-2F6C8F1D7E42",
            "0b7c1c0e5a3f4d0e9b1a2f6c8f1d7e42",
            "../../etc/passwd",
            "0b7c1c0e-5a3f-4d0e-9b1a-2f6c8f1d7e4/",
        ] {
            assert!(!is_job_id(bad), "{bad:?}");
        }
    }

    #[test]
    fn file_names() {
        assert_eq!(
            file_media_type("26171.gesamt.trig"),
            Some("application/trig")
        );
        assert_eq!(
            file_media_type("26171.ech.ttl"),
            Some("text/turtle; charset=utf-8")
        );
        assert_eq!(
            file_media_type("local.ech.rdf.xml"),
            Some("application/rdf+xml")
        );
        assert_eq!(
            file_media_type("26171.labels.yaml"),
            Some("application/yaml")
        );
        assert_eq!(file_media_type("view.json"), Some("application/json"));
        for bad in [
            "",
            "..",
            "../view.json",
            "view.json/",
            "x/view.json",
            ".gesamt.trig",
            "a.gesamt.trig",
            "26171.gesamt.trig.bak",
            "input.pdf",
            "SHA256SUMS",
            "..gesamt.trig",
            "26171/../1.gesamt.trig",
            "view.json\0",
            "VIEW.JSON",
        ] {
            assert_eq!(file_media_type(bad), None, "{bad:?}");
            assert_eq!(file_rank(bad), None, "{bad:?}");
        }
        assert_eq!(file_rank("26171.gesamt.trig"), Some(0));
        assert_eq!(file_rank("26171.gesamt.rdf.xml"), Some(2));
        assert_eq!(file_rank("26171.ech.rdf.xml"), Some(3));
        assert_eq!(file_rank("26171.provenance.yaml"), Some(6));
        assert_eq!(file_rank("manifest.json"), Some(7));
        assert_eq!(file_rank("convert.json"), Some(10));
        // the optional files of a record with values from the PDF
        assert_eq!(
            file_media_type("26171.values.ttl"),
            Some("text/turtle; charset=utf-8")
        );
        assert_eq!(
            file_media_type("local.values.ttl"),
            Some("text/turtle; charset=utf-8")
        );
        assert_eq!(file_media_type("source.pdf"), Some("application/pdf"));
        assert_eq!(file_media_type("page-1.png"), Some("image/png"));
        assert_eq!(file_media_type("page-25.png"), Some("image/png"));
        assert_eq!(file_rank("26171.values.ttl"), Some(11));
        assert_eq!(file_rank("source.pdf"), Some(12));
        assert_eq!(file_rank("page-2.png"), Some(15));
        for bad in [
            "page-0.png",
            "page-01.png",
            "page-1000.png",
            "page-.png",
            "page-1.PNG",
            "page-1.png/",
            "../page-1.png",
            "page-1a.png",
            "a.values.ttl",
            ".values.ttl",
            "source.PDF",
            "x/source.pdf",
        ] {
            assert_eq!(file_media_type(bad), None, "{bad:?}");
            assert_eq!(file_rank(bad), None, "{bad:?}");
        }
    }

    #[test]
    fn complete_records() {
        let mut names: Vec<String> = DOC_FILES.iter().map(|(s, _)| format!("local{s}")).collect();
        names.extend(FIXED_FILES.iter().map(|f| f.to_string()));
        assert!(is_complete_record(&names));
        assert!(!is_complete_record(&names[1..]));
        let mut other = names.clone();
        other[1] = "888.ech.ttl".into();
        assert!(!is_complete_record(&other));
        assert!(!is_complete_record(&["view.json".to_string()]));
        let mut values = names.clone();
        values.extend(
            ["local.values.ttl", "source.pdf", "page-1.png", "page-2.png"].map(String::from),
        );
        assert!(is_complete_record(&values));
        let mut wrong_prefix = names.clone();
        wrong_prefix.push("888.values.ttl".into());
        assert!(!is_complete_record(&wrong_prefix));
    }

    #[test]
    fn display_names() {
        assert_eq!(display_file_name("C:\\dir\\a b.pdf"), "a b.pdf");
        assert_eq!(display_file_name("/etc/../x.pdf"), "x.pdf");
        assert_eq!(display_file_name("a\r\nb.pdf"), "ab.pdf");
        assert_eq!(display_file_name(&"x".repeat(300)).chars().count(), 120);
        assert_eq!(display_file_name("\u{202e}gnp.exe.pdf"), "gnp.exe.pdf");
        assert_eq!(display_file_name(".."), "");
    }

    #[test]
    fn pdf_mark() {
        assert!(has_pdf_mark(b"%PDF-1.7\n"));
        assert!(has_pdf_mark(b"\xef\xbb\xbf\n%PDF-1.4"));
        assert!(!has_pdf_mark(b"PK\x03\x04"));
        assert!(!has_pdf_mark(b""));
        let mut late = vec![b' '; 1020];
        late.extend_from_slice(b"%PDF-1.4");
        assert!(!has_pdf_mark(&late));
    }

    #[test]
    fn hashed_names() {
        assert!(is_hashed_name("/app/app.3f9a2b1c.js"));
        assert!(is_hashed_name("pkg/mod-0123456789abcdef.wasm"));
        assert!(!is_hashed_name("/app/app.js"));
        assert!(!is_hashed_name("/app/deadbeef.js"));
        assert!(!is_hashed_name("/app/pkg/parlpdfech_rdfcheck_bg.wasm"));
        assert!(!is_hashed_name("/app/report-20261013.html"));
    }
}
