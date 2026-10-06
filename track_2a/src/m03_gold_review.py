# SPDX-License-Identifier: Apache-2.0
"""Human gold set (decision E32): local review tool for Jonathan (E20 version 4.1).

A small web server on this Mac only (127.0.0.1). It shows each document of a batch: the PDF pages
as images with a coloured box for each atom (colour = answer), the atoms as blocks, the answer of
the AI coders as a proposal, and the atoms where AI codings do not agree ("strittig", "⚠").
Jonathan confirms or corrects; he answers 4 questions for each document. The tool saves after each
change and every 20 s while he works, and when he leaves a page. It measures his active time (page
visible and an input in the last 90 s) and the wall time from the first opening to "fertig".

Files: <data>/gold/<batch>/decisions/<doc_id>.json (answers, decided atoms, questions, note, times,
proposal and its SHA-256, E20 and freeze SHA-256); a document with the status "fertig" also gets an
answer file of E20 version 4 in <data>/gold/<batch>/answers/<doc_id>.json (checked by validate4). The
fixed answers (page furniture R1/R4/R5, picture atoms R3) cannot be changed.

Batches (lists of `m03_gold_select.py`):
  pilot         20 development documents; proposal: <data>/iso/v4/consensus_XY; other codings: blind_X,
                blind_Y, ref41, native_N. The documents of <data>/gold/pilot_blind.csv show no proposal and
                no other coding: Jonathan codes them from the start (unanchored measurement).
  test          test documents (process rule 6); proposal: <data>/gold/test/ai_ref; other codings ai_A, ai_B.
                Only after the freeze of E20 (<data>/gold/e20_freeze.json, SHA-256 equal to the current file).
  pilot_repeat, test_repeat
                the second check of process rule 2.4 (same proposal; never the first answers). While a
                repeat is open, its documents are locked in the first batch.

Guards: a save must name the batch of the server and the last save that the page loaded (else 409);
"fertig" is never set back; a stored decision whose atom ids differ from the atoms is not loaded.
The server answers only requests with the host 127.0.0.1:<port> or localhost:<port>; it accepts a
save only without an origin or with the origin of the server (no save from another web page).

Known limit: the page images of all batches go to <data>/gold/cache/pages_cropbox, and the batch
test_repeat goes to <data>/gold/test_repeat/. Both are outside <data>/gold/test.

The user interface is in German (for Jonathan); the files and the code are in English.
--coder gives the name of the human coder (default Jonathan). --e20 gives the file of the E20
definition (default: the file of the freeze record); its SHA-256 goes into each decision.

Usage:  uv run python src/m03_gold_review.py --batch pilot --e20 FILE    (then open http://127.0.0.1:8877)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m03_iso_paths import DATA, iso_path, pdf_path, rel  # noqa: E402
import m03_iso_v4 as v4  # noqa: E402

GOLD = DATA / "gold"
E20_FILE: Path | None = None   # file of the E20 definition (--e20; default: the file of the freeze record)
CODER = "Jonathan"             # name of the human coder (--coder)
FREEZE = GOLD / "e20_freeze.json"
VERSION = "gold-review-v2"
E20 = "e20-v4.1"
LOCK = threading.Lock()
FMT = "%Y-%m-%dT%H:%M:%S"

BATCHES = {
    "pilot": {"list": GOLD / "pilot.csv", "proposal": DATA / "iso/v4/consensus_XY",
              "others": {"KI X": DATA / "iso/v4/blind_X", "KI Y": DATA / "iso/v4/blind_Y",
                         "Ref 4.1": DATA / "iso/v4/ref41", "KI N": DATA / "iso/v4/native_N"}},
    "test": {"list": GOLD / "test.csv", "proposal": GOLD / "test/ai_ref",
             "others": {"KI A": GOLD / "test/ai_A", "KI B": GOLD / "test/ai_B"}},
}
BATCHES["pilot_repeat"] = dict(BATCHES["pilot"], list=GOLD / "pilot_repeat.csv")
BATCHES["test_repeat"] = dict(BATCHES["test"], list=GOLD / "test_repeat.csv")

LABELS = {
    "title": ("Titel", "1", "#2563eb"),
    "submitted": ("Vorstoss-Text (eingereicht)", "2", "#16a34a"),
    "reasoning": ("Begründung des Vorstosses", "3", "#84cc16"),
    "response": ("Antwort der Regierung", "4", "#ea580c"),
    "recommendation": ("Formeller Antrag der Regierung", "5", "#dc2626"),
    "none": ("Kein Textfeld", "6", "#9ca3af"),
    "summary": ("Zusammenfassung", "7", "#0891b2"),
    "vote": ("Beschlusstext des Parlaments", "8", "#7c3aed"),
    "speech": ("Votum im Protokoll", "9", "#db2777"),
    "committee_recommendation": ("Antrag der Kommission", "0", "#a16207"),
    "short_title": ("Kurztitel", "k", "#60a5fa"),
    "proposition": ("Antrag in der Debatte", "p", "#c026d3"),
    "furniture": ("Seitenrand (fest)", "", "#e5e7eb"),
}

QUESTIONS = [
    ("titel", "Ist der Titel richtig und vollständig markiert?"),
    ("vorstoss", "Ist der Text des Vorstosses (und eine Begründung) richtig abgegrenzt?"),
    ("antwort", "Ist die Antwort der Regierung (und ein Antrag) richtig abgegrenzt?"),
    ("rahmen", "Sind Anrede, Gruss, Unterschriften, Daten, Verteiler und Beilagen überall «Kein Textfeld»?"),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_ids(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def answers_of(path: Path, ids: list[str]) -> list[str] | None:
    if not path.exists():
        return None
    x = json.loads(path.read_text(encoding="utf-8"))
    return x["answers"] if x.get("ids") == ids else None


def recorded_path(s: str) -> Path:
    """A path of a record: absolute, or relative to the folder that contains the data root (m03_iso_paths.rel)."""
    p = Path(s)
    return p if p.is_absolute() else DATA.parent / p


def freeze_state() -> dict:
    """The freeze of E20 and whether it matches the current file."""
    f = json.loads(FREEZE.read_text(encoding="utf-8")) if FREEZE.exists() else None
    e20 = E20_FILE or (recorded_path(f["file"]) if f and f.get("file") else None)
    cur = sha(e20) if e20 is not None and e20.exists() else None
    if f is None:
        return {"frozen": False, "e20_sha256": cur}
    return {"frozen": True, "valid": cur is not None and f.get("sha256") == cur, "freeze_sha256": f.get("sha256"),
            "e20_sha256": cur}


class Conflict(Exception):
    pass


class Store:
    def __init__(self, batch: str):
        self.batch = batch
        self.is_test = batch.startswith("test")
        self.base = batch[: -len("_repeat")] if batch.endswith("_repeat") else None
        self.docs = read_ids(BATCHES[batch]["list"])
        self.ids = [r["doc_id"] for r in self.docs]
        self.meta = {r["doc_id"]: r for r in self.docs}
        blind = GOLD / f"{batch}_blind.csv"
        self.blind = {r["doc_id"] for r in read_ids(blind)} if blind.exists() and not self.base else set()
        self.dec_dir = GOLD / batch / "decisions"
        self.ans_dir = GOLD / batch / "answers"
        self.page_dir = GOLD / "cache/pages_cropbox"
        self.dec_dir.mkdir(parents=True, exist_ok=True)
        self.ans_dir.mkdir(parents=True, exist_ok=True)
        self.freeze = freeze_state()

    def check_id(self, doc_id: str) -> str:
        if doc_id not in self.meta:
            raise KeyError(doc_id)
        return doc_id

    def locked(self, doc_id: str) -> bool:
        """Process rule 2.4: a document of an open repeat list stays closed in the first batch."""
        if self.base:
            return False
        rep = GOLD / f"{self.batch}_repeat.csv"
        if not rep.exists() or doc_id not in {r["doc_id"] for r in read_ids(rep)}:
            return False
        p = GOLD / f"{self.batch}_repeat" / "decisions" / f"{doc_id}.json"
        return not (p.exists() and json.loads(p.read_text(encoding="utf-8")).get("status") == "fertig")

    def decision(self, doc_id: str) -> dict | None:
        p = self.dec_dir / f"{doc_id}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def doc(self, doc_id: str) -> dict:
        atoms = v4.atoms_of(doc_id)
        ids = [a["id"] for a in atoms]
        fixed = v4.fixed_answers(doc_id)
        cfg = BATCHES[self.batch]
        blind = doc_id in self.blind
        prop_path = cfg["proposal"] / f"{doc_id}.json"
        proposal = None if blind else answers_of(prop_path, ids)
        if proposal is None:
            proposal = [fixed.get(a, "none") for a in ids]
        others = {}
        if not blind:
            for name, d in cfg["others"].items():
                o = answers_of(d / f"{doc_id}.json", ids)
                if o is not None:
                    others[name] = o
        dec = self.decision(doc_id)
        error = None
        if dec is not None and dec.get("ids") != ids:
            error = "Die gespeicherte Entscheidung passt nicht mehr zu den Zeilen dieses Dokuments. Bitte dem Projektteam melden."
        if self.locked(doc_id):
            error = "Dieses Dokument ist gesperrt, bis seine Wiederholung (zweite Prüfung) fertig ist."
        dl = json.loads(iso_path("docling", doc_id).read_text(encoding="utf-8"))
        pages = [{"n": p["seite"], "w": p["breite"], "h": p["hoehe"]} for p in dl["seiten"]]
        out_atoms = [{"id": a["id"], "page": a["seite"], "box": a.get("zeilenrahmen") or a.get("rahmen"),
                      "text": a.get("text") or "", "fixed": fixed.get(a["id"])} for a in atoms]
        m = self.meta[doc_id]
        return {"doc_id": doc_id, "batch": self.batch, "is_test": self.is_test, "blind": blind, "error": error,
                "index": self.ids.index(doc_id), "count": len(self.ids),
                "meta": {k: m.get(k, "") for k in ("body_key", "ebene", "sprache", "scan", "dokumentrolle", "seiten")},
                "atoms": out_atoms, "pages": pages, "proposal": proposal, "others": others,
                "decision": None if error else dec,
                "labels": {k: {"name": v[0], "key": v[1], "color": v[2]} for k, v in LABELS.items()},
                "questions": QUESTIONS}

    def save(self, doc_id: str, body: dict) -> dict:
        if body.get("batch") != self.batch:
            raise Conflict(f"Seite gehört zum Stapel «{body.get('batch')}», der Server zum Stapel «{self.batch}».")
        if self.locked(doc_id):
            raise Conflict("Dokument gesperrt (Wiederholung offen).")
        atoms = v4.atoms_of(doc_id)
        ids = [a["id"] for a in atoms]
        answers = body.get("answers")
        if not isinstance(answers, list) or len(answers) != len(ids):
            raise ValueError("answers: wrong length")
        fixed = v4.fixed_answers(doc_id)
        for a, y in zip(ids, answers):
            if y not in v4.ANSWERS:
                raise ValueError(f"{a}: unknown answer {y}")
            if a in fixed and y != fixed[a]:
                raise ValueError(f"{a}: fixed answer {fixed[a]}")
            if a not in fixed and y == "furniture":
                raise ValueError(f"{a}: furniture only by a fixed rule")
        status = body.get("status", "in Arbeit")
        if status not in ("in Arbeit", "fertig"):
            raise ValueError("status")
        cfg = BATCHES[self.batch]
        blind = doc_id in self.blind
        prop_path = cfg["proposal"] / f"{doc_id}.json"
        proposal = None if blind else answers_of(prop_path, ids)
        with LOCK:
            old = self.decision(doc_id) or {}
            if old and old.get("ids") != ids:
                raise Conflict("Gespeicherte Entscheidung passt nicht zu den Zeilen.")
            if old.get("last_saved") and body.get("base") != old.get("last_saved"):
                raise Conflict("Dieses Dokument wurde inzwischen an anderer Stelle gespeichert. Bitte Seite neu laden.")
            now = datetime.now()
            if old.get("last_saved"):
                elapsed = (now - datetime.strptime(old["last_saved"][:19], FMT)).total_seconds()
            else:
                elapsed = 3600.0
            delta = max(0.0, min(float(body.get("active_delta") or 0), elapsed + 30.0, 3600.0))
            if old.get("status") == "fertig":
                status = "fertig"
            opened = [t for t in (old.get("first_opened"), str(body.get("opened_at") or "")[:19]) if t]
            stamp = now.strftime(FMT)
            if stamp == old.get("last_saved"):
                stamp = now.strftime(FMT) + f".{now.microsecond:06d}"[:4]
            rec = {
                "doc_id": doc_id, "batch": self.batch, "tool": VERSION, "e20": E20, "coder": CODER,
                "e20_sha256": self.freeze["e20_sha256"], "freeze_sha256": self.freeze.get("freeze_sha256"),
                "blind": blind, "status": status, "answers": answers, "ids": ids,
                "questions": body.get("questions") or {}, "resolved": sorted(set(body.get("resolved") or [])),
                "notes": str(body.get("notes") or "")[:5000],
                "active_seconds": round(float(old.get("active_seconds", 0)) + delta, 1),
                "first_opened": min(opened) if opened else None,
                "first_saved": old.get("first_saved") or stamp,
                "last_saved": stamp,
                "last_changed": stamp if (body.get("changed") or not old) else old.get("last_changed"),
                "finished": old.get("finished") or (stamp if status == "fertig" else None),
                "proposal_source": None if blind else rel(prop_path),
                "proposal_sha256": sha(prop_path) if (prop_path.exists() and not blind) else None,
                "changed_vs_proposal": sum(1 for x, y in zip(proposal, answers) if x != y) if proposal else None,
            }
            if status == "fertig":
                v4.write(self.ans_dir, doc_id, answers,
                         CODER + " (gold review, " + ("blind" if blind else "proposal shown") + ")",
                         f"{VERSION}; proposal {rec['proposal_source']}")
                err = v4.validate4(self.ans_dir / f"{doc_id}.json")
                if err:
                    raise ValueError("; ".join(err[:3]))
            (self.dec_dir / f"{doc_id}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=0), encoding="utf-8")
        return {"ok": True, "active_seconds": rec["active_seconds"], "changed": rec["changed_vs_proposal"],
                "last_saved": rec["last_saved"], "status": status}

    def status(self) -> list[dict]:
        out = []
        for d in self.ids:
            x = self.decision(d) or {}
            m = self.meta[d]
            out.append({"doc_id": d, "sprache": m.get("sprache"), "dokumentrolle": m.get("dokumentrolle"),
                        "seiten": m.get("seiten"), "status": "gesperrt" if self.locked(d) else x.get("status", "offen"),
                        "blind": d in self.blind, "minutes": round(x.get("active_seconds", 0) / 60, 1),
                        "changed": x.get("changed_vs_proposal")})
        return out

    def page_png(self, doc_id: str, n: int) -> Path:
        d = self.page_dir / doc_id
        d.mkdir(parents=True, exist_ok=True)
        out = d / f"p{n}.png"
        if not out.exists():
            subprocess.run(["pdftoppm", "-r", "110", "-png", "-cropbox", "-singlefile", "-f", str(n), "-l", str(n),
                            str(pdf_path(doc_id)), str(d / f"p{n}")], check=True, capture_output=True)
        return out


PAGE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gold-Prüfung</title><style>
:root{--bg:#f8fafc;--fg:#0f172a;--mut:#64748b;--card:#fff;--line:#e2e8f0;--warn:#f59e0b;--sel:#0ea5e9}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 -apple-system,system-ui,sans-serif;background:var(--bg);color:var(--fg)}
header{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--line);padding:8px 14px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
header b{font-size:15px}.pill{padding:2px 8px;border-radius:99px;background:#eef2ff;font-size:12px}
button{font:inherit;padding:5px 10px;border:1px solid var(--line);border-radius:6px;background:#fff;cursor:pointer}
button.primary{background:#0f172a;color:#fff;border-color:#0f172a}button:disabled{opacity:.4;cursor:default}
main{display:grid;grid-template-columns:minmax(0,58%) minmax(0,42%);height:calc(100vh - 52px)}
#pages{overflow:auto;padding:12px;border-right:1px solid var(--line)}#side{overflow:auto;padding:12px}
.page{position:relative;margin:0 auto 14px;max-width:900px;box-shadow:0 1px 4px #0002;background:#fff}
.page img{display:block;width:100%}.box{position:absolute;border:2px solid;opacity:.55;cursor:pointer}
.box.sel{outline:3px solid var(--sel);opacity:.9}.box.disp{border-style:dashed;border-width:3px;opacity:.85}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px;margin-bottom:10px}
.ans{display:flex;flex-wrap:wrap;gap:5px}.ans button{display:flex;gap:6px;align-items:center;font-size:12.5px}
.sw{display:inline-block;width:12px;height:12px;border-radius:3px}.key{font-size:11px;color:var(--mut)}
.row{display:grid;grid-template-columns:14px 64px 1fr;gap:6px;padding:3px 4px;border-radius:5px;cursor:pointer;align-items:start}
.row:hover{background:#f1f5f9}.row.sel{background:#e0f2fe}.row.fixed{opacity:.45;cursor:default}
.row .id{font:11px ui-monospace,monospace;color:var(--mut)}.row .t{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.row.disp .t::before{content:"⚠ ";color:var(--warn)}.alt{font-size:11.5px;color:#b45309;grid-column:3}
.blk{border-left:5px solid;padding:4px 6px;margin:6px 0;background:#fff;border-radius:4px}
.blk h4{margin:0 0 2px;font-size:12.5px;display:flex;justify-content:space-between}
.q{margin:6px 0}.q label{margin-right:10px;font-size:13px}textarea{width:100%;min-height:60px;font:inherit}
.mut{color:var(--mut);font-size:12px}details summary{cursor:pointer;font-weight:600}.err{color:#b91c1c;font-weight:600}
.banner{background:#fef3c7;border:1px solid #f59e0b;border-radius:8px;padding:8px 10px;margin-bottom:10px}
.guide li{margin:3px 0}
@media (max-width:900px){main{grid-template-columns:1fr;height:auto}#pages{max-height:60vh}}
</style></head><body><div id="app">Lade …</div><script>
const DOC="__DOC__", BATCH="__BATCH__";
let D=null, ans=[], sel=new Set(), anchor=null, resolved=new Set(), notes="", qs={}, dirty=false, saving=null, stale=false;
let changeSeq=0, base=null, lastInput=Date.now(), activeAcc=0, lastTick=Date.now();
const openedAt=(()=>{const d=new Date(),p=n=>String(n).padStart(2,"0");return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`})();
const $=s=>document.querySelector(s);
function esc(s){return (s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
function L(a){return D.labels[a]||{name:a,color:"#000",key:""}}
function disputed(i){for(const k in D.others){if(D.others[k][i]!==D.proposal[i])return true}return false}
function alts(i){const o=[];for(const k in D.others){if(D.others[k][i]!==ans[i])o.push(k+": "+L(D.others[k][i]).name)}if(D.proposal[i]!==ans[i])o.push("Vorschlag: "+L(D.proposal[i]).name);return o}
function tick(){const now=Date.now();if(document.visibilityState==="visible"&&now-lastInput<90000)activeAcc+=(now-lastTick)/1000;lastTick=now}
setInterval(tick,1000);["mousemove","keydown","scroll","click","wheel"].forEach(e=>addEventListener(e,()=>{lastInput=Date.now()},true));
async function load(){
  const r=await fetch("/api/doc/"+DOC);D=await r.json();
  if(D.error){$("#app").innerHTML=`<main style="display:block;padding:24px"><p class="err">${esc(D.error)}</p><p><a href="/">Zur Übersicht</a></p></main>`;D=null;return}
  const dec=D.decision;ans=(dec&&dec.answers)?dec.answers.slice():D.proposal.slice();base=dec?dec.last_saved:null;
  resolved=new Set(dec?dec.resolved:[]);notes=dec?dec.notes:"";qs=dec?dec.questions:{};render();
}
function blocks(){const b=[];let s=0;for(let i=1;i<=ans.length;i++){if(i===ans.length||ans[i]!==ans[s]){b.push([s,i-1]);s=i}}return b}
function render(){
  const sp=$("#pages")?$("#pages").scrollTop:0, ss=$("#side")?$("#side").scrollTop:0;
  const m=D.meta, nd=D.atoms.filter((a,i)=>disputed(i)).length, open=D.atoms.filter((a,i)=>disputed(i)&&!resolved.has(a.id)).length;
  const qok=D.questions.every(([k])=>qs[k]);
  const askText=D.is_test?"Bei «unklar» bitte kurz notieren, was unklar ist. Testdokumente werden nicht mit dem Projektteam besprochen; die Notiz bleibt in deiner Datei.":"Bei «unklar» bitte kurz notieren, was unklar ist; das Projektteam klärt es danach mit dir.";
  $("#app").innerHTML=`<header><b>Dokument ${D.index+1} / ${D.count}</b><span class="pill">${D.doc_id}</span>
   <span class="pill">${esc(m.body_key)} · ${esc(m.ebene)} · ${esc(m.sprache)} · ${esc(m.dokumentrolle)} · ${esc(m.seiten)} S.${m.scan!=="digital"?" · Scan":""}</span>
   <span class="mut" id="timer"></span><span class="mut" id="save"></span>
   <span style="flex:1"></span><a href="/pdf/${D.doc_id}" target="_blank">PDF öffnen</a>
   <button onclick="go(-1)">← Zurück</button><button onclick="toIndex()">Übersicht</button>
   <button class="primary" ${open||!qok?"disabled":""} onclick="finish()">Fertig ✓</button><button onclick="go(1)">Weiter →</button></header>
   <main><div id="pages"></div><div id="side">
   ${D.blind?`<div class="banner"><b>Ohne Vorschlag:</b> Bei diesem Dokument zeigt das Werkzeug absichtlich keinen KI-Vorschlag. Bitte markiere Titel, Vorstoss, Antwort usw. selbst (Zeile anklicken, mit Shift einen Bereich, dann Taste). Alles andere bleibt «Kein Textfeld».</div>`:""}
   <div class="card"><b>Antwort für die markierten Zeilen</b> <span class="mut">(Zeile anklicken, mit Shift einen Bereich)</span><div class="ans">${
     Object.entries(D.labels).filter(([k])=>k!=="furniture").map(([k,v])=>`<button onclick="assign('${k}')"><span class="sw" style="background:${v.color}"></span>${esc(v.name)} <span class="key">${v.key}</span></button>`).join("")}</div>
     ${D.blind?"":`<div class="mut" style="margin-top:6px">Strittige Zeilen (⚠): ${nd}, davon offen: <b>${open}</b>. Eine strittige Zeile gilt als entschieden, wenn du eine Antwort setzt oder «Vorschlag übernehmen» drückst.
     <button onclick="okSel()">Vorschlag übernehmen (markierte Zeilen)</button></div>`}</div>
   <div class="card"><b>Fragen zu diesem Dokument</b>${D.questions.map(([k,t])=>`<div class="q">${esc(t)}<br>${["stimmt","korrigiert","unklar"].map(v=>`<label><input type="radio" name="q_${k}" ${qs[k]===v?"checked":""} onchange="setQ('${k}','${v}')"> ${v}</label>`).join("")}</div>`).join("")}
     <div class="mut">${askText}</div>
     <textarea placeholder="${D.is_test?"Notiz":"Notiz oder Frage an das Projektteam"}" oninput="notes=this.value;mark()">${esc(notes)}</textarea></div>
   <details class="card"><summary>Kurzanleitung (Regeln)</summary><div class="guide">${GUIDE}</div></details>
   <div class="card"><b>Blöcke</b> <span class="mut">(gleiche Antwort hintereinander)</span><div id="blocks"></div></div></div></main>`;
  renderPages();renderBlocks();updTimer();$("#save").textContent=stale?"VERALTET – bitte Seite neu laden":(dirty?"nicht gespeichert":"");
  $("#pages").scrollTop=sp;$("#side").scrollTop=ss;
}
function renderPages(){
  const el=$("#pages"),sp=el.scrollTop;el.innerHTML=D.pages.map(p=>`<div class="page" id="pg${p.n}"><img loading="lazy" src="/page/${D.doc_id}/${p.n}.png">${
    D.atoms.map((a,i)=>a.page===p.n&&a.box?boxHtml(a,i,p):"").join("")}</div>`).join("");el.scrollTop=sp;
}
function boxHtml(a,i,p){const[l,t,r,b]=a.box,c=L(ans[i]).color;
  return `<div class="box ${sel.has(i)?"sel":""} ${disputed(i)&&!resolved.has(a.id)?"disp":""}" id="bx${i}" title="${esc(a.id+" · "+L(ans[i]).name)}" style="left:${l/p.w*100}%;top:${t/p.h*100}%;width:${(r-l)/p.w*100}%;height:${(b-t)/p.h*100}%;border-color:${c};background:${c}22" onclick="pick(event,${i})"></div>`}
function renderBlocks(){
  const el=$("#blocks"),side=$("#side"),ss=side.scrollTop;el.innerHTML=blocks().map(([s,e])=>{const a=ans[s],c=L(a).color;
    return `<div class="blk" style="border-color:${c}"><h4><span>${esc(L(a).name)}</span><span class="mut">${e-s+1} Zeilen</span></h4>${
      D.atoms.slice(s,e+1).map((at,k)=>{const i=s+k,dp=disputed(i)&&!resolved.has(at.id),al=disputed(i)?alts(i):[];
        return `<div class="row ${sel.has(i)?"sel":""} ${at.fixed?"fixed":""} ${dp?"disp":""}" id="rw${i}" onclick="pick(event,${i})"><span class="sw" style="background:${L(ans[i]).color}"></span><span class="id">${at.id} · S.${at.page}</span><span class="t" title="${esc(at.text)}">${esc(at.text||"(ohne Text)")}</span>${al.length?`<span></span><span></span><span class="alt">${esc(al.join(" · "))}</span>`:""}</div>`}).join("")}</div>`}).join("");side.scrollTop=ss;
}
function pick(ev,i){if(D.atoms[i].fixed)return;
  if(ev.shiftKey&&anchor!==null){sel=new Set();const[a,b]=anchor<i?[anchor,i]:[i,anchor];for(let k=a;k<=b;k++)if(!D.atoms[k].fixed)sel.add(k)}
  else if(ev.metaKey||ev.ctrlKey){sel.has(i)?sel.delete(i):sel.add(i);anchor=i}else{sel=new Set([i]);anchor=i}
  renderPages();renderBlocks();const fromBox=ev.target.classList.contains("box");
  const r=$("#rw"+i);if(fromBox&&r)r.scrollIntoView({block:"nearest"});const b=$("#bx"+i);if(!fromBox&&b)b.scrollIntoView({block:"nearest"})}
function assign(a){if(!sel.size)return;for(const i of sel){if(!D.atoms[i].fixed){ans[i]=a;resolved.add(D.atoms[i].id)}}mark();render()}
function okSel(){for(const i of sel){if(!D.atoms[i].fixed){ans[i]=D.proposal[i];resolved.add(D.atoms[i].id)}}mark();render()}
function setQ(k,v){qs[k]=v;mark();render()}
function mark(){dirty=true;changeSeq++;$("#save")&&($("#save").textContent="nicht gespeichert")}
function payload(status,delta){return {batch:BATCH,base,answers:ans,resolved:[...resolved],notes,questions:qs,status,active_delta:delta,opened_at:openedAt,changed:dirty}}
async function save(status){
  if(stale||!D)return false; if(saving){await saving;if(!status&&!dirty&&activeAcc<1)return true}
  tick();const delta=activeAcc;activeAcc=0;const seq=changeSeq;
  const st=status||((D.decision&&D.decision.status==="fertig")?"fertig":"in Arbeit");
  saving=(async()=>{try{const r=await fetch("/api/save/"+D.doc_id,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload(st,delta))});
    const j=await r.json();if(r.status===409){stale=true;throw new Error(j.error)}if(!r.ok)throw new Error(j.error);
    base=j.last_saved;D.decision=Object.assign(D.decision||{},{status:j.status,active_seconds:j.active_seconds,last_saved:j.last_saved});
    dirty=changeSeq!==seq;$("#save").textContent=(dirty?"nicht gespeichert":"gespeichert")+" ("+new Date().toLocaleTimeString()+")";return true}
   catch(e){activeAcc+=delta;$("#save").innerHTML='<span class="err">FEHLER: '+esc(e.message)+'</span>';return false}finally{updTimer()}})();
  const ok=await saving;saving=null;return ok}
async function finish(){if(await save("fertig")&&!dirty)go(1)}
async function go(d){if(!(await save()))return;const s=await (await fetch("/api/status")).json();const ids=s.map(x=>x.doc_id);const k=ids.indexOf(D.doc_id)+d;location.href=(k>=0&&k<ids.length)?"/doc/"+ids[k]:"/"}
async function toIndex(){if(await save())location.href="/"}
function updTimer(){if(!D)return;const t=((D.decision&&D.decision.active_seconds)||0)+activeAcc;$("#timer")&&($("#timer").textContent="aktive Zeit "+Math.floor(t/60)+":"+String(Math.floor(t%60)).padStart(2,"0"))}
setInterval(()=>{updTimer();if(D&&!stale&&(dirty||activeAcc>=5))save()},20000);
addEventListener("keydown",e=>{if(!D)return;const t=e.target;
  if(t.tagName==="INPUT"&&t.type==="radio"&&e.key.startsWith("Arrow")){e.preventDefault();return}
  if(t.tagName==="TEXTAREA"||t.tagName==="INPUT"||t.tagName==="SELECT"||e.metaKey||e.ctrlKey||e.altKey)return;
  for(const k in D.labels){if(D.labels[k].key&&e.key===D.labels[k].key){assign(k);e.preventDefault();return}}
  if(e.key==="Enter"&&!D.blind){okSel();e.preventDefault()}});
addEventListener("pagehide",()=>{if(!D||stale)return;tick();if(dirty||activeAcc>=1||!D.decision){
  navigator.sendBeacon("/api/save/"+D.doc_id,new Blob([JSON.stringify(payload((D.decision&&D.decision.status==="fertig")?"fertig":"in Arbeit",activeAcc))],{type:"application/json"}))}});
const GUIDE=`__GUIDE__`;
load();
</script></body></html>"""

GUIDE = """<p><b>Deine Aufgabe:</b> Die KI schlägt für jede Zeile eine Antwort vor. Du prüfst vor allem die <b>Grenzen</b>
(wo beginnt und endet der Titel, der Vorstoss, die Antwort) und die <b>strittigen Zeilen (⚠)</b>, bei denen KI-Codierer
verschiedener Meinung sind. Was stimmt, lässt du stehen.</p>
<ul>
<li><b>Titel:</b> die gedruckte Überschrift mit dem Betreff des Geschäfts. Eine Zeile direkt darüber oder darunter, die nur
den Typ («Motion», «Interpellation»), den Dokumenttyp oder eine Nummer enthält, gehört dazu.</li>
<li><b>Vorstoss-Text:</b> der eigentliche Text, den die Ratsmitglieder eingereicht haben: Forderung, Fragen. Ein Satz wie «Ich frage den
Regierungsrat:» gehört dazu.</li>
<li><b>Begründung:</b> nur wenn eine Überschrift oder ein Label «Begründung» (oder gleichbedeutend) sie einleitet.</li>
<li><b>Antwort der Regierung:</b> der eigentliche Antworttext der Exekutive. Einzelne Fragen, die sie vor ihren Antworten wiederholt,
gehören zur Antwort. Wiederholt sie den ganzen Vorstoss am Stück, behält er «Vorstoss-Text».</li>
<li><b>Formeller Antrag der Regierung:</b> nur ein eigener Absatz mit nur dem Antrag («Wir beantragen, die Motion abzulehnen»).</li>
<li><b>Kein Textfeld:</b> alles um den Text herum: Briefkopf, Formularfelder (ausser dem Betreff), Anrede, «folgender Vorstoss wurde
eingereicht», Gruss, Dank, Unterschriften, Mitunterzeichnende, Ort und Datum, Versandzeilen, Verteiler, Beilagen,
«Der Regierungsrat beschliesst:», Hinweise zu Kosten oder Verspätung, Logos, Stempel, Handschrift.</li>
<li><b>Satz am Anfang der Antwort, der sie nur ankündigt</b> («Der Regierungsrat antwortet wie folgt:») → Kein Textfeld.</li>
<li><b>Überschriften</b> gehören zum Text, den sie einleiten («Antwort des Regierungsrates» → Antwort), auch wenn zuerst ein Rahmensatz kommt.</li>
<li><b>Fussnoten</b> gehören zum letzten Text davor auf derselben Seite; <b>Bildlegenden</b> zum Text darum herum.</li>
<li><b>Vorlage oder Erlassentwurf der Regierung an das Parlament</b> → Vorstoss-Text (hier ist die Regierung Urheberin).
Ein Entscheid der Regierung in eigener Kompetenz → Kein Textfeld.</li>
<li><b>Beschlusstext des Parlaments</b> («Der Kantonsrat beschliesst: …», «nimmt Kenntnis …») → Beschlusstext.</li>
<li><b>Protokolle:</b> die mündliche Antwort des Regierungsmitglieds → Antwort; andere Wortmeldungen → Votum.</li>
<li><b>Beilage</b> mit dem ganzen Vorstoss → Kein Textfeld.</li>
</ul><p class="mut">Grau und nicht anklickbar: Seitenzahlen, wiederkehrende Kopf- und Fusszeilen, Dateiangaben (feste Regeln).
Tasten: 1 Titel, 2 Vorstoss, 3 Begründung, 4 Antwort, 5 Antrag, 6 Kein Textfeld, 7 Zusammenfassung, 8 Beschluss,
9 Votum, 0 Kommission, k Kurztitel, p Antrag Debatte, Enter = Vorschlag übernehmen.</p>"""

INDEX = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Gold-Prüfung</title>
<style>body{margin:0;font:14px/1.5 -apple-system,system-ui,sans-serif;background:#f8fafc;color:#0f172a}main{max-width:900px;margin:0 auto;padding:16px}
table{border-collapse:collapse;width:100%;background:#fff}td,th{border-bottom:1px solid #e2e8f0;padding:6px 8px;text-align:left}
.s-fertig{color:#16a34a;font-weight:600}.s-in{color:#ea580c}.mut{color:#64748b}a{color:#2563eb}</style></head><body><main>
<h2>Gold-Prüfung · Stapel «__BATCH__»</h2><p class="mut">__INTRO__</p>
<p id="sum"></p><table><thead><tr><th>#</th><th>Dokument</th><th>Sprache</th><th>Typ</th><th>Seiten</th><th>Status</th><th>Minuten</th><th>Korrigierte Zeilen</th></tr></thead><tbody id="t"></tbody></table>
<script>fetch("/api/status").then(r=>r.json()).then(s=>{let done=0,min=0;document.getElementById("t").innerHTML=s.map((x,i)=>{if(x.status==="fertig"){done++;min+=x.minutes}
const st=x.status+(x.blind?" · ohne Vorschlag":"");return `<tr><td>${i+1}</td><td>${x.status==="gesperrt"?x.doc_id:`<a href="/doc/${x.doc_id}">${x.doc_id}</a>`}</td><td>${x.sprache}</td><td>${x.dokumentrolle}</td><td>${x.seiten}</td><td class="${x.status==="fertig"?"s-fertig":x.status==="in Arbeit"?"s-in":""}">${st}</td><td>${x.minutes||""}</td><td>${x.changed??""}</td></tr>`}).join("");
document.getElementById("sum").textContent=`Fertig: ${done} von ${s.length}`+(done?` · Mittel ${(min/done).toFixed(1)} Minuten pro Dokument`:"")})</script></main></body></html>"""

INTRO = {
    "pilot": "Ein Klick auf eine Zeile öffnet das Dokument. Alles wird automatisch gespeichert. Ziel des Piloten: herausfinden, wie lange ein Dokument dauert und wie oft die KI falsch liegt. Dokumente «ohne Vorschlag» markierst du selbst von Anfang an.",
    "test": "Testdokumente: Hier entsteht der Gold-Standard für die Schlussmessung. Unklare Stellen nur notieren; sie werden nicht mit dem Projektteam besprochen.",
    "pilot_repeat": "Zweite Prüfung (Wiederholung): Bitte prüfe diese Dokumente noch einmal, ohne an deine erste Prüfung zu denken.",
    "test_repeat": "Zweite Prüfung der Testdokumente: Bitte prüfe sie noch einmal, ohne an deine erste Prüfung zu denken.",
}


def make_handler(store: Store):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def local(self, save: bool = False) -> bool:
            """Only requests to this server on this computer; a save only from a page of this server."""
            port = self.server.server_address[1]
            hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
            if self.headers.get("Host") not in hosts:
                return False
            origin = self.headers.get("Origin")
            return not save or origin is None or origin in {f"http://{h}" for h in hosts}

        def json(self, code: int, obj) -> None:
            self.send(code, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

        def do_GET(self):
            if not self.local():
                return self.json(403, {"error": "host not allowed"})
            try:
                p = self.path.split("?")[0]
                if p == "/":
                    html = INDEX.replace("__BATCH__", store.batch).replace("__INTRO__", INTRO[store.batch])
                    return self.send(200, html.encode(), "text/html; charset=utf-8")
                if p == "/api/status":
                    return self.json(200, store.status())
                m = re.fullmatch(r"/doc/(\d+)", p)
                if m:
                    d = store.check_id(m.group(1))
                    page = PAGE.replace("__DOC__", d).replace("__BATCH__", store.batch).replace("__GUIDE__", GUIDE.replace("`", "'"))
                    return self.send(200, page.encode(), "text/html; charset=utf-8")
                m = re.fullmatch(r"/api/doc/(\d+)", p)
                if m:
                    return self.json(200, store.doc(store.check_id(m.group(1))))
                m = re.fullmatch(r"/page/(\d+)/(\d+)\.png", p)
                if m:
                    f = store.page_png(store.check_id(m.group(1)), int(m.group(2)))
                    return self.send(200, f.read_bytes(), "image/png")
                m = re.fullmatch(r"/pdf/(\d+)", p)
                if m:
                    f = pdf_path(store.check_id(m.group(1)))
                    return self.send(200, f.read_bytes(), "application/pdf")
                self.json(404, {"error": "not found"})
            except KeyError:
                self.json(404, {"error": "document not in this batch"})
            except Exception as e:  # noqa: BLE001
                self.json(500, {"error": str(e)})

        def do_POST(self):
            if not self.local(save=True):
                return self.json(403, {"error": "host or origin not allowed"})
            try:
                m = re.fullmatch(r"/api/save/(\d+)", self.path)
                if not m:
                    return self.json(404, {"error": "not found"})
                n = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(n) or b"{}")
                self.json(200, store.save(store.check_id(m.group(1)), body))
            except KeyError:
                self.json(404, {"error": "document not in this batch"})
            except Conflict as e:
                self.json(409, {"error": str(e)})
            except ValueError as e:
                self.json(400, {"error": str(e)})
            except Exception as e:  # noqa: BLE001
                self.json(500, {"error": str(e)})
    return H


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", choices=sorted(BATCHES), default="pilot")
    ap.add_argument("--port", type=int, default=8877)
    ap.add_argument("--coder", default="Jonathan", help="name of the human coder")
    ap.add_argument("--e20", default=None, help="file of the E20 definition (default: the file of the freeze record)")
    args = ap.parse_args()
    global CODER, E20_FILE
    CODER = args.coder
    E20_FILE = Path(args.e20) if args.e20 else None
    if not BATCHES[args.batch]["list"].exists():
        raise SystemExit(f"no list {BATCHES[args.batch]['list']} (m03_gold_select.py)")
    if args.batch.startswith("test"):
        f = freeze_state()
        if not f["frozen"]:
            raise SystemExit("test batch only after the freeze of E20 (<data>/gold/e20_freeze.json; process rule 6)")
        if not f["valid"]:
            raise SystemExit("E20 changed after the freeze: a new freeze is necessary (m03_gold_freeze.py), "
                             "and test documents checked under the old freeze are checked again")
    store = Store(args.batch)
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(store))
    print(f"Gold-Prüfung, Stapel {args.batch}: http://127.0.0.1:{args.port}  ({len(store.ids)} Dokumente; Ctrl-C beendet)",
          flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
