"""Measurement of the complexity ladder of the isolation (step Measure, 08.10.2026).

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5).
Status: measurement on stored outputs. This script gives no gate result.

Context: gate 3a (E20 version 4.2) is NOT MET. Jonathan decided on 08.10.2026 to reduce the complexity of the
task until a gate can be passed. The ladder `daten/iso/ladder/ladder.json` defines the isolation levels L0 to
L10. This script applies each isolation level to answer folders and measures it with the metric definitions of
the isolation level.

Rules of an isolation level (read from ladder.json, never changed here):
  collapse map  the same map on the reference and on the converter answers (rule_library.collapse_maps)
  scope rule    from the converter answers of the document and the stored S1 outputs (field `role` only)
  zones         from the converter answers, the Docling block id of each atom and the fixed answers
  unit          atom   m03_iso_v4.compare_docs on the transformed answers (each value is asserted equal)
                block  block form: the converter claims the class sequence, the switch points and the
                       existence of each block, but no extent. Each atom without a fixed answer gets the text
                       answer of the converter run before it (before the first run: the first run). For the
                       output `nos4` this changes no atom (checked). Exact rule: exact_block.
                document  the set of coarse text classes (exact_document)
Neither the scope rule nor a zone reads a reference.

Reference reliability: the coder pairs of daten/iso/ladder/MAP.md chapter 2.1 on the 41 group documents of dev
and eval, with the scope and the zones of the canonical converter of the isolation level (`assembled`, or
`nos4` at the block unit; the convention of the ladder step). The AI reference `ref41` against the human gold
set records: 3 dev records, 2 eval records (validation). The record 877101 is not a gold set record.

Methods: rule composite `assembled` and `best` (dev in-sample), `nos4` (block variant of the ladder, dev
in-sample), whole-document readout Apertus-v1.5-8B with LoRA `hyp_oof_a1` (out of fold; dev part = groups 1
to 3, eval part = groups 4 and 5; `oof_a1_with_pool` also has the pool documents of dev), in-context readout
Apertus-v1.5-70B `hyp_cscs70_k4_e20`, `hyp_cscs70_k4`, `hyp_cscs70_k0` (E20 version 3.1 outputs, converted
to E20 version 4 answers), and the eval-only feasibility variants `combined` and `apertus`. The ladder defines
no method combination.

Gate limits: criteria version 3.1 (gate-3a-negative-result-draft.md chapter 3.3). Three verdict sets:
  V1  criteria version 3.1 with the metric definitions of the isolation level (no criterion change)
  V2  V1 with the criterion changes CC1, CC2, CC3, CC5 of ladder.json for the isolation level (CC4: reported)
  V3  V2 with the limit change LC1 (omission limit 0.003). LC1 is a limit change, not a reduction.
Reference limit (process rule 2.3): the blind pair blind_X | blind_Y at the isolation level, worst direction.

Integrity:
  1. guard() refuses each group 7 document (m03_iso_v4.final_docs()) and each document that
     m03_sub_common._check_allowed_doc refuses (test document, test parliament, unknown document). It runs
     before a file of the document is opened. guard_dir() refuses final_* folders, hyp_g7_final_a1,
     report_g7_final_a1.json and daten/gold/test.
  2. No CSCS request, no network request, no training, no GPU. Stored outputs only.
  3. Each dev value of the rule composite is in-sample. Each eval value is a validation value.

Checks (exit code 2 if one fails, before any output file is written):
  identity  L0: hyp_assembled_dev F1 0.6993, hyp_assembled_eval F1 0.6, and the pooled OOF values of
            daten/iso/v4/report_oof_a1_viterbi.json (39 documents of groups 1 to 5 with triage PASS)
  compare   each atom-unit value equal to m03_iso_v4.compare_docs (skip with --no-compare)
  ladder    the canonical converter values equal to daten/iso/ladder/scratch/ladder_values.json

Version 2 (step Report, 08.10.2026): changes after the verification lenses (verify_reproduce.md,
verify_integrity.md, verify_final.md). No change to a rule of the ladder, a method output or a reference.
  1. Primary method: the method that the ladder named before the measurement (`assembled`; `nos4` at the block
     unit). The verdicts of the primary method are the result. The best of all outputs is "exploratory".
  2. Sensitivity reference: group documents against consensus_XY (blind X where X and Y agree, else ref41).
  3. Strata: reference blocks (0, 1, 2 or more), language, metadata role, reference role, group or pool.
  4. Block unit: G3a.6 has no object (omission 0 by construction); frame share of the TextBlocks reported.
  5. G3a.3 analog: blind X | Y in the decisive value of the isolation level (reported only).
  6. Apertus share and export rule ids in the claimed documents of the primary method.
  7. LC1 only at the isolation levels that ladder.json lists. Gate comparisons use unrounded rates.
  8. Zones never hold an atom with a fixed answer (ladder-spec 5.3, item 4). The ladder check uses the count
     with fixed atoms, the definition of the ladder step.

Run:    uv run --no-project --with pyyaml python src/m03_ladder.py
Output: daten/iso/ladder/results.json, daten/iso/ladder/results.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import m03_iso_v4 as v4  # noqa: E402

# speed only (same values): compare_docs reads the atom file and the carried atoms again for each atom
v4.atoms_of = lru_cache(maxsize=None)(v4.atoms_of)
_CARRIED_ORIG = v4.carried_ids
_CARRIED_CACHE: dict[int, tuple] = {}


def _carried_cached(atoms):
    k = id(atoms)
    if k not in _CARRIED_CACHE:
        _CARRIED_CACHE[k] = (atoms, _CARRIED_ORIG(atoms))
    return _CARRIED_CACHE[k][1]


v4.carried_ids = _carried_cached
import m03_sub_common as sc  # noqa: E402

VERSION = "ladder-measure-2"
LADDER = ROOT / "daten/iso/ladder"
SCRATCH = LADDER / "scratch"
V4 = ROOT / "daten/iso/v4"
SUB = ROOT / "daten/iso/sub"
ASM = SUB / "assemble"
OUT_JSON = LADDER / "results.json"
OUT_MD = LADDER / "results.md"
TEXT = set(v4.TEXT)

# ------------------------------------------------------------------ gate limits (criteria version 3.1)
LIMITS = {
    "G3a.3": {"labelled_f1": (">=", 0.95)},
    "G3a.5": {"labelled_f1": (">=", 0.95), "labelled_f1_lower": (">=", 0.90)},
    "G3a.6": {"text_omission": ("<=", 0.002), "documents_with_omission_share": ("<=", 0.05)},
    "G3a.6b": {"text_intrusion": ("<=", 0.01)},
    "G3a.9": {"exact_rate": (">=", 0.80)},
}
LC1_OMISSION = 0.003
CC3_CLASS_ERROR = 0.01

# ------------------------------------------------------------------ guard
G7 = frozenset(v4.final_docs())
REFUSED_PARTS = ("hyp_g7_final_a1", "report_g7_final_a1.json")
GUARD = Counter()


def guard(d) -> str:
    """Refuse group 7 documents, test documents, documents of a test parliament and unknown documents."""
    d = str(d)
    if d in G7:
        raise SystemExit("guard: a group 7 document was refused (final group)")
    sc._check_allowed_doc(d)
    GUARD["calls"] += 1
    return d


def guard_dir(p: Path) -> Path:
    rel = Path(p).resolve().relative_to(ROOT.resolve())
    if any(x.startswith("final_") for x in rel.parts) or any(x in REFUSED_PARTS for x in rel.parts):
        raise SystemExit(f"guard: folder {rel.as_posix()} refused (final measurement material)")
    if rel.as_posix().startswith("daten/gold/test"):
        raise SystemExit(f"guard: folder {rel.as_posix()} refused (test set, process rule 6)")
    return Path(p)


def guard_selftest() -> dict:
    """Probes of the guard. No probe opens a file."""
    out = {}
    try:
        guard(sorted(G7)[0])
        out["group_7_document"] = "NOT REFUSED"
    except SystemExit:
        out["group_7_document"] = "refused"
    try:
        guard("0")
        out["unknown_document"] = "NOT REFUSED"
    except ValueError:
        out["unknown_document"] = "refused"
    for name, p in (("final_folder", V4 / "final_probe"), ("hyp_g7_final_a1", V4 / "hyp_g7_final_a1"),
                    ("report_g7_final_a1", V4 / "report_g7_final_a1.json"), ("test_set_folder", ROOT / "daten/gold/test/probe")):
        try:
            guard_dir(p)
            out[name] = "NOT REFUSED"
        except SystemExit:
            out[name] = "refused"
    out["group_7_documents_known"] = len(G7)
    return out


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ------------------------------------------------------------------ documents and splits
SP = sc.splits()
DOCS = sc.load()
SPLIT_OF = {guard(d): s for s in ("dev", "eval") for d in SP[s]}
GOLD_IDS = sc.gold_record_ids()
if "877101" in GOLD_IDS:
    raise SystemExit("877101 is a tool record, not a gold set record")
GOLD = {"dev": [guard(d) for d in GOLD_IDS if SPLIT_OF.get(d) == "dev"],
        "eval": [guard(d) for d in GOLD_IDS if SPLIT_OF.get(d) == "eval"]}
GROUP_DOCS = {s: [d for d in SP[s] if DOCS[d].kind == "group"] for s in ("dev", "eval")}

# ------------------------------------------------------------------ ladder rules
LADDER_JSON = json.loads((LADDER / "ladder.json").read_text(encoding="utf-8"))
MAPS = LADDER_JSON["rule_library"]["collapse_maps"]
CC = {c["id"]: set(c["applies_to"]) for c in LADDER_JSON["criterion_changes"]}
LC = {c["id"]: set(c["applies_to"]) for c in LADDER_JSON["limit_changes"]}
LEVELS = []
for _l in LADDER_JSON["levels"]:
    LEVELS.append({"id": _l["id"], "name": _l["name"], "parent": _l["parent"], "path": _l["path"],
                   "map": _l["collapse_map_id"], "scope": _l["scope_rule"]["id"],
                   "zones": [z["id"] for z in _l["abstention_rule"]["zones"]], "unit": _l["unit_rule"]["id"],
                   "exact_rule": _l["metrics"]["exact_rule"],
                   "canonical": "nos4" if "nos4" in _l["method_output"] else "assembled",
                   "reduction": _l["reduction_or_limit_change"]})


def cmap(name: str, a: list[str]) -> list[str]:
    m = MAPS[name]
    return [m[x] for x in a]


# ------------------------------------------------------------------ converter signals (no reference fields)
def _load_signal(rel: str, fields: tuple) -> dict:
    out = {}
    for split in ("dev", "eval"):
        p = guard_dir(SUB / rel.format(s=split))
        for d, rec in json.loads(p.read_text(encoding="utf-8"))["documents"].items():
            if d in SPLIT_OF:
                out[guard(d)] = {f: rec.get(f) for f in fields}   # the fields reference and correct are dropped
    return out


SIG: dict[str, dict] = {}
for _name, _rel in (("s1_rule", "s1_role/rule_{s}.json"), ("s1_apertus", "s1_role/apertus_{s}.json"),
                    ("s1_combined", "s1_role/combined_{s}.json")):
    for _d, _x in _load_signal(_rel, ("role",)).items():
        SIG.setdefault(_d, {})[_name] = _x["role"]
# information only (version 2): who decided the S1 combined role, and the S1 rule id (P2 and R1 read export fields)
for _d, _x in _load_signal("s1_role/combined_{s}.json", ("source",)).items():
    SIG[_d]["s1_combined_source"] = _x["source"]
for _d, _x in _load_signal("s1_role/rule_{s}.json", ("reason",)).items():
    SIG[_d]["s1_rule_id"] = str(_x["reason"]).split(":")[0]
EXPORT_RULE_IDS = ("P2", "R1")
AUTHOR = ("proposal", "response", "combined")


def role(h: list[str]) -> str:
    return sc.role_of(sc.FAMILY[x] for x in h if x in TEXT)


def scope_all(d, h):
    return True


def scope_written_affair(d, h):
    return role(h) in AUTHOR and SIG[d]["s1_combined"] in AUTHOR


def scope_role_agreement(d, h):
    return scope_written_affair(d, h) and role(h) == SIG[d]["s1_rule"]


def scope_single_author_agreement(d, h):
    r = role(h)
    return scope_role_agreement(d, h) and r in ("proposal", "response") and SIG[d]["s1_apertus"] == r


SCOPES = {"all": scope_all, "written_affair": scope_written_affair, "role_agreement": scope_role_agreement,
          "single_author_agreement": scope_single_author_agreement}


# ------------------------------------------------------------------ abstention zones (converter answers only)
def sections(hm):
    out, cur = [], None
    for i, x in enumerate(hm):
        if x in TEXT:
            if cur and cur[2] == x:
                cur[1] = i
            else:
                if cur:
                    out.append(tuple(cur))
                cur = [i, i, x]
    if cur:
        out.append(tuple(cur))
    return out


def z_interior(d, hm):
    z = set()
    for a, b, _ in sections(hm):
        z |= {i for i in range(a, b + 1) if hm[i] not in TEXT}
    return z


def z_edge_blocks(k):
    def f(d, hm):
        at, fx = v4.atoms_of(d), DOCS[d].fixed
        blk = [x["block"] for x in at]
        order = []
        for i, b in enumerate(blk):
            if at[i]["id"] in fx:
                continue
            if not order or order[-1] != b:
                order.append(b)
        pos = {b: n for n, b in enumerate(order)}
        zb = set()
        for a, b, _ in sections(hm):
            ba, bb = pos.get(blk[a]), pos.get(blk[b])
            if ba is None or bb is None:
                continue
            for n in range(ba - k, ba + k):
                if 0 <= n < len(order):
                    zb.add(order[n])
            for n in range(bb - k + 1, bb + k + 1):
                if 0 <= n < len(order):
                    zb.add(order[n])
        return {i for i, b in enumerate(blk) if b in zb and at[i]["id"] not in fx}
    return f


def z_run_band(m):
    def f(d, hm):
        out, i = set(), 0
        while i < len(hm):
            if hm[i] in TEXT:
                j = i
                while j + 1 < len(hm) and hm[j + 1] in TEXT:
                    j += 1
                run = list(range(i, j + 1))
                out.update(run[:m])
                out.update(run[-m:])
                i = j + 1
            else:
                i += 1
        return out
    return f


def zone_fn(zid: str):
    if zid == "interior":
        return z_interior
    if zid.startswith("edge_blocks_"):
        return z_edge_blocks(int(zid.rsplit("_", 1)[1]))
    if zid.startswith("run_band_"):
        return z_run_band(int(zid.rsplit("_", 1)[1]))
    raise SystemExit(f"unknown zone {zid}")


def block_form(hm: list[str], d: str) -> list[str]:
    """Block unit: the converter claims no extent. Each atom without a fixed answer gets the text answer of the
    converter run before it; before the first run, the answer of the first run."""
    fx, ids = DOCS[d].fixed, DOCS[d].ids
    first = next((i for i, x in enumerate(hm) if x in TEXT), None)
    if first is None:
        return list(hm)
    out, prev = list(hm), hm[first]
    for i, x in enumerate(hm):
        if x in TEXT:
            prev = x
        elif ids[i] not in fx:
            out[i] = prev
    return out


@lru_cache(maxsize=None)
def fixed_idx(d: str) -> frozenset:
    fx = DOCS[d].fixed
    return frozenset(i for i, a in enumerate(DOCS[d].ids) if a in fx)


def converter_view(lv: dict, d: str, h_raw: list[str], bf: bool = True, with_raw: bool = False):
    """(claimed, converter answers after the map and the unit form, zone). No reference is read.
    bf=False: no block form at the block unit (information only).
    Version 2: the zone holds no atom with a fixed answer (ladder-spec 5.3, item 4). A fixed answer is never a
    text answer, so the mask gives the same answers. with_raw=True also gives the zone size with fixed atoms
    (definition of the ladder step, for the ladder check)."""
    claimed = SCOPES[lv["scope"]](d, h_raw)
    hm = cmap(lv["map"], h_raw)
    if lv["unit"] == "block" and bf:
        hm = block_form(hm, d)
    zone = set()
    for z in lv["zones"]:
        zone |= zone_fn(z)(d, hm)
    raw_size = len(zone)
    zone -= fixed_idx(d)
    if with_raw:
        return claimed, hm, zone, raw_size
    return claimed, hm, zone


def mask(a: list[str], zone: set) -> list[str]:
    return ["none" if i in zone and x in TEXT else x for i, x in enumerate(a)]


# ------------------------------------------------------------------ counts (same formulas as compare_docs)
@lru_cache(maxsize=None)
def carried(d):
    c = v4.carried_ids(v4.atoms_of(d))
    return frozenset(i for i, a in enumerate(DOCS[d].ids) if a in c)


def blocks(a):
    out, cur, cls = [], [], None
    for i, x in enumerate(a):
        if x in TEXT:
            if cls is not None and x != cls:
                out.append((cls, cur))
                cur = []
            cls = x
            cur.append(i)
    if cur:
        out.append((cls, cur))
    return out


def doc_counts(d, r, h):
    br, bh, good, inner = v4.boundaries(r, h, set(carried(d)))
    om = sum(1 for x, y in zip(r, h) if x in TEXT and y not in TEXT)
    it = sum(1 for x, y in zip(r, h) if y in TEXT and x not in TEXT)
    both = sum(1 for x, y in zip(r, h) if x in TEXT and y in TEXT)
    ce = sum(1 for x, y in zip(r, h) if x in TEXT and y in TEXT and x != y)
    rt = {i for i, x in enumerate(r) if x in TEXT}
    ht = {i for i, x in enumerate(h) if x in TEXT}
    bo = sum(1 for _, b in blocks(r) if not (set(b) & ht))
    bi = sum(1 for _, b in blocks(h) if not (set(b) & rt))
    bnd_ok = good == br and bh == br
    return dict(br=len(br), bh=len(bh), good=len(good), inner=len(inner), om=om, it=it, both=both, ce=ce,
                tr=len(rt), th=len(ht), bo=bo, bi=bi,
                exact_atom=bnd_ok and om == 0 and it == 0 and ce == 0,
                exact_block=bnd_ok and om == 0 and ce == 0 and bo == 0 and bi == 0,
                exact_document={x for x in r if x in TEXT} == {x for x in h if x in TEXT})


def f1(tp, nh, nr, nd=4):
    p = tp / nh if nh else 0.0
    q = tp / nr if nr else 0.0
    if not p + q:
        return 0.0
    v = 2 * p * q / (p + q)
    return round(v, nd) if nd is not None else v


def lower_f1(tp, nh, nr):
    lp, lr = v4.jeffreys_lower(tp, nh) or 0.0, v4.jeffreys_lower(tp, nr) or 0.0
    return round(2 * lp * lr / (lp + lr), 4) if lp and lr else 0.0


def aggregate(rows: list[dict], exact_rule: str) -> dict:
    c = Counter()
    for x in rows:
        for k, v in x.items():
            c[k] += int(v)
    n = len(rows)
    ex = c[exact_rule]
    dom = sum(1 for x in rows if x["om"] > 0)
    return {"documents": n, "boundaries_ref": c["br"], "boundaries_hyp": c["bh"], "correct": c["good"],
            "labelled_f1": f1(c["good"], c["bh"], c["br"]), "labelled_f1_lower": lower_f1(c["good"], c["bh"], c["br"]),
            "inner_boundaries_ref": c["inner"],
            "text_omission": round(c["om"] / c["tr"], 4) if c["tr"] else None,
            "documents_with_omission": dom,
            "documents_with_omission_share": round(dom / n, 4) if n else None,
            "text_intrusion": round(c["it"] / c["th"], 4) if c["th"] else None,
            "text_class_error": round(c["ce"] / c["both"], 4) if c["both"] else None,
            "block_omission": c["bo"], "block_intrusion": c["bi"],
            "documents_with_block_intrusion": sum(1 for x in rows if x["bi"] > 0),
            "exact_rule": exact_rule, "exact": ex, "exact_rate": round(ex / n, 4) if n else None,
            "exact_lower": v4.jeffreys_lower(ex, n) if n else None, "exact_atom_rule": c["exact_atom"],
            "text_ref": c["tr"], "text_hyp": c["th"], "omitted": c["om"], "intruded": c["it"],
            "class_err_atoms": c["ce"], "both_text": c["both"],
            # version 2: unrounded rates for the gate comparison (verify_reproduce.md finding 5)
            "unrounded": {"labelled_f1": f1(c["good"], c["bh"], c["br"], None),
                          "text_omission": c["om"] / c["tr"] if c["tr"] else None,
                          "documents_with_omission_share": dom / n if n else None,
                          "text_intrusion": c["it"] / c["th"] if c["th"] else None,
                          "text_class_error": c["ce"] / c["both"] if c["both"] else None,
                          "exact_rate": ex / n if n else None}}


COMPARE_RUNS = Counter()


def check_compare_docs(R: dict, H: dict, docs: list[str], mine: dict, what: str) -> None:
    if not docs:
        return
    with tempfile.TemporaryDirectory() as t:
        rd, hd = Path(t) / "r", Path(t) / "h"
        for d in docs:
            v4.write(rd, d, R[d], "ref", "ladder")
            v4.write(hd, d, H[d], "hyp", "ladder")
        cd = v4.compare_docs(rd, hd, list(docs))
    for k in ("documents", "labelled_f1", "labelled_f1_lower", "boundaries_ref", "boundaries_hyp", "text_omission",
              "documents_with_omission", "text_intrusion", "text_class_error"):
        if cd[k] != mine[k]:
            raise SystemExit(f"check compare FAILED {what}: {k} compare_docs {cd[k]} script {mine[k]}")
    if cd["counts"]["exact"] != mine["exact_atom_rule"]:
        raise SystemExit(f"check compare FAILED {what}: exact")
    COMPARE_RUNS["runs"] += 1
    COMPARE_RUNS["documents"] += len(docs)


# ------------------------------------------------------------------ answer folders
def folder_reader(folder: Path):
    folder = guard_dir(folder)

    def read(d):
        guard(d)
        p = folder / f"{d}.json"
        if not p.exists():
            return None
        return list(v4.load_answers(p, d, DOCS[d].ids))
    read.source = folder.relative_to(ROOT).as_posix()
    return read


def json_reader(paths: list[Path]):
    data = {}
    for p in paths:
        p = guard_dir(p)
        for d, a in json.loads(p.read_text(encoding="utf-8")).items():
            guard(d)
            if len(a) != len(DOCS[d].ids) or not set(a) <= set(v4.ANSWERS):
                raise SystemExit(f"{p}: bad answers for {d}")
            data[d] = list(a)

    def read(d):
        return data.get(guard(d))
    read.source = ", ".join(p.relative_to(ROOT).as_posix() for p in paths)
    return read


def trivial_role(d: str) -> list[str]:
    """Trivial converter 'role only': each atom without a fixed answer gets the default answer of the S1
    combined role."""
    fam = sc.ROLE_DEFAULT_FAMILY.get(SIG[d]["s1_combined"], "SPONSOR")
    fill = sc.DEFAULT_TYPE[fam]
    return [DOCS[d].fixed.get(a, fill) for a in DOCS[d].ids]


IN_SAMPLE = "in-sample: AI agents wrote the rules on dev"
VALIDATION = "validation: eval was measured several times before"
G13 = lambda d: DOCS[d].kind == "group" and DOCS[d].group in ("1", "2", "3")  # noqa: E731
G45 = lambda d: DOCS[d].group in ("4", "5")  # noqa: E731
ANY = lambda d: True  # noqa: E731
_oof = folder_reader(V4 / "hyp_oof_a1")
METHODS = [
    {"id": "assembled", "name": "rule composite assembled (S1 combined, S2 to S5 rules, assembly options)",
     "reader": {"dev": folder_reader(ASM / "hyp_assembled_dev"), "eval": folder_reader(ASM / "hyp_assembled_eval")},
     "filter": {"dev": ANY, "eval": ANY}, "label_dev": IN_SAMPLE},
    {"id": "best", "name": "rule composite best (no assembly options)",
     "reader": {"dev": folder_reader(ASM / "hyp_best_dev"), "eval": folder_reader(ASM / "hyp_best_eval")},
     "filter": {"dev": ANY, "eval": ANY}, "label_dev": IN_SAMPLE},
    {"id": "nos4", "name": "rule composite, block variant nos4 of the ladder (S3 all text, S4 not used)",
     "reader": {s: json_reader([SCRATCH / f"err_recompose_nos4_{s}.json"]) for s in ("dev", "eval")},
     "filter": {"dev": ANY, "eval": ANY}, "label_dev": IN_SAMPLE},
    {"id": "oof_a1", "name": "whole-document readout, Apertus-v1.5-8B with LoRA, out of fold (dev: groups 1 to 3)",
     "reader": {"dev": _oof, "eval": _oof}, "filter": {"dev": G13, "eval": G45},
     "label_dev": "out of fold (groups 1 to 3); the S1 scope signals are in-sample on dev"},
    {"id": "oof_a1_with_pool", "name": "as oof_a1, dev part with the out-of-fold pool documents",
     "reader": {"dev": _oof, "eval": _oof}, "filter": {"dev": ANY, "eval": G45},
     "label_dev": "out of fold (groups 1 to 3 and pool); the S1 scope signals are in-sample on dev"},
    {"id": "cscs70_k4_e20", "name": "in-context readout, Apertus-v1.5-70B, 4 examples, E20 in the system message",
     "reader": {s: folder_reader(V4 / "hyp_cscs70_k4_e20") for s in ("dev", "eval")},
     "filter": {"dev": ANY, "eval": ANY},
     "label_dev": "not fitted (examples from pool documents of other parliaments); the S1 scope signals are in-sample on dev"},
    {"id": "cscs70_k4", "name": "in-context readout, Apertus-v1.5-70B, 4 examples",
     "reader": {s: folder_reader(V4 / "hyp_cscs70_k4") for s in ("dev", "eval")},
     "filter": {"dev": ANY, "eval": ANY},
     "label_dev": "not fitted (examples from pool documents of other parliaments); the S1 scope signals are in-sample on dev"},
    {"id": "cscs70_k0", "name": "in-context readout, Apertus-v1.5-70B, 0 examples",
     "reader": {s: folder_reader(V4 / "hyp_cscs70_k0") for s in ("dev", "eval")},
     "filter": {"dev": ANY, "eval": ANY},
     "label_dev": "not fitted; the S1 scope signals are in-sample on dev"},
    {"id": "combined_eval_only", "name": "feasibility variant combined (S1 to S4 combined), eval only",
     "reader": {"eval": folder_reader(ASM / "hyp_combined_eval")}, "filter": {"eval": ANY}, "label_dev": None},
    {"id": "apertus_eval_only", "name": "feasibility variant apertus (S1 to S4 Apertus-v1.5-8B), eval only",
     "reader": {"eval": folder_reader(ASM / "hyp_apertus_eval")}, "filter": {"eval": ANY}, "label_dev": None},
]
ANS: dict[str, dict[str, dict[str, list[str]]]] = {}
for _m in METHODS:
    ANS[_m["id"]] = {}
    for _s, _rd in _m["reader"].items():
        got = {}
        for _d in SP[_s]:
            if not _m["filter"][_s](_d):
                continue
            a = _rd(_d)
            if a is not None:
                got[_d] = a
        ANS[_m["id"]][_s] = got
CANON = {k: {**ANS[k]["dev"], **ANS[k]["eval"]} for k in ("assembled", "nos4")}

CODERS = {name: folder_reader(V4 / name) for name in
          ("blind_X", "blind_Y", "native_N", "ref_A", "ref_B", "review_R1", "review_R2", "ref", "ref_rev", "ref41",
           "consensus_XY")}
PAIRS = [("blind_X", "blind_Y", "blind"), ("native_N", "blind_X", "blind"), ("native_N", "blind_Y", "blind"),
         ("ref_A", "ref_B", "separate"),
         ("blind_X", "ref41", "blind coder against the anchored reference"),
         ("blind_Y", "ref41", "blind coder against the anchored reference"),
         ("native_N", "ref41", "blind coder against the anchored reference"),
         ("review_R1", "review_R2", "anchored"), ("ref", "ref_rev", "anchored"), ("ref_rev", "ref41", "anchored"),
         ("ref_A", "ref", "anchored"), ("ref_B", "ref", "anchored"),
         ("consensus_XY", "ref41", "derived, not a coder pair")]


def claim_changes_without_apertus(lv: dict, answers: dict, docs: list[str]) -> dict:
    """Version 2: documents whose claim changes if the S1 rule role replaces the S1 combined role (the only
    Apertus decision in the rule composite). verify_final.md finding 1."""
    changed = []
    for d in docs:
        c1 = SCOPES[lv["scope"]](d, answers[d])
        saved = SIG[d]["s1_combined"]
        SIG[d]["s1_combined"] = SIG[d]["s1_rule"]
        try:
            c2 = SCOPES[lv["scope"]](d, answers[d])
        finally:
            SIG[d]["s1_combined"] = saved
        if c1 != c2:
            changed.append(d)
    return {"documents": len(docs), "claim_changes": len(changed),
            "note": "claim changes if the S1 rule role replaces the S1 combined role (Apertus only for rule id R1)"}


def consensus_ref(d: str) -> list[str]:
    """Sensitivity reference (version 2): consensus_XY for a group document (blind X where X and Y agree, else
    ref41), pool_ref41 for a pool document (no blind pair exists)."""
    if DOCS[d].kind == "group":
        a = CODERS["consensus_XY"](d)
        if a is not None:
            return a
    return sc.reference(d)


# ------------------------------------------------------------------ measurement
def measure(lv: dict, answers: dict[str, list[str]], docs: list[str], ref=None, compare=False, what="",
            trivial=True, bf=True) -> dict:
    """Converter answers against the reference at one isolation level; with the trivial check on the same scope."""
    ref = ref or (lambda d: sc.reference(d))
    rows, trows, R, H, claimed_docs = [], [], {}, {}, []
    t = Counter()
    info = []          # version 2: one record for each available document (strata, frame share, Apertus share)
    for d in docs:
        guard(d)
        r0 = ref(d)
        claimed, hm, zone, raw_zone = converter_view(lv, d, answers[d], bf, with_raw=True)
        rm = cmap(lv["map"], r0)
        t["atoms_available"] += len(rm)
        t["ref_text_available"] += sum(x in TEXT for x in rm)
        rz, hz = mask(rm, zone), mask(hm, zone)
        rec = {"doc": d, "claimed": bool(claimed), "ref_blocks": min(len(blocks(rz)), 2),
               "kind": DOCS[d].kind, "language": DOCS[d].language or "unknown",
               "meta_role": DOCS[d].meta_role or "unknown", "reference_role": role(r0)}
        if not claimed:
            info.append(rec)
            continue
        dc = doc_counts(d, rz, hz)
        rows.append(dc)
        R[d], H[d] = rz, hz
        claimed_docs.append(d)
        rec["exact"] = bool(dc[lv["exact_rule"]])
        rec["frame_atoms_in_text"], rec["text_atoms"] = dc["it"], dc["th"]
        if trivial:
            tv = cmap(lv["map"], trivial_role(d))
            if lv["unit"] == "block":
                tv = block_form(tv, d)
            tc = doc_counts(d, rz, mask(tv, zone))
            trows.append(tc)
            rec["trivial_exact"] = bool(tc[lv["exact_rule"]])
        info.append(rec)
        t["atoms_claimed"] += len(rz)
        t["unsure_atoms"] += len(zone)
        t["unsure_atoms_incl_fixed"] += raw_zone
        t["ref_text_claimed"] += sum(x in TEXT for x in rz)
    m = aggregate(rows, lv["exact_rule"])
    if compare and lv["unit"] == "atom":
        check_compare_docs(R, H, claimed_docs, m, what)
    tr = aggregate(trows, lv["exact_rule"])
    n_av = len(docs)
    m.update({
        "documents_available": n_av,
        "coverage_documents": round(len(claimed_docs) / n_av, 4) if n_av else None,
        "atoms_available": t["atoms_available"], "atoms_claimed": t["atoms_claimed"], "unsure_atoms": t["unsure_atoms"],
        "coverage_atoms": round((t["atoms_claimed"] - t["unsure_atoms"]) / t["atoms_available"], 4) if t["atoms_available"] else None,
        "unsure_share_of_claimed_atoms": round(t["unsure_atoms"] / t["atoms_claimed"], 4) if t["atoms_claimed"] else None,
        "ref_text_available": t["ref_text_available"], "ref_text_claimed": t["ref_text_claimed"],
        "coverage_ref_text": round(t["ref_text_claimed"] / t["ref_text_available"], 4) if t["ref_text_available"] else None,
        "trivial_role_same_scope": {"exact": tr["exact"], "documents": tr["documents"], "exact_rate": tr["exact_rate"]},
        "claimed_documents": claimed_docs,
        "exact_documents": [d for d, x in zip(claimed_docs, rows) if x[lv["exact_rule"]]],
        "unsure_atoms_incl_fixed": t["unsure_atoms_incl_fixed"],
        "strata": strata(info),
        "frame_in_text_of_exact_documents": frame_share(info),
        "converter_inputs_of_claimed_documents": input_share(info),
    })
    return m


STRATA_KEYS = (("ref_blocks", "reference blocks after the map and the zones (0, 1, 2 = 2 or more)"),
               ("language", "language of the document (metadata)"),
               ("meta_role", "document role of the metadata"),
               ("reference_role", "role of the reference answers (reporting only, never a converter input)"),
               ("kind", "group document (ref41) or pool document (pool_ref41)"))


def strata(info: list[dict]) -> dict:
    """Coverage and exact documents for each stratum (version 2; verify_integrity.md findings 4 and 11,
    verify_final.md findings 5 to 7). The strata use the reference only for the report, never for a claim."""
    out = {}
    for key, _ in STRATA_KEYS:
        s = {}
        for rec in info:
            v = s.setdefault(str(rec[key]), Counter())
            v["available"] += 1
            if rec["claimed"]:
                v["claimed"] += 1
                v["exact"] += rec.get("exact", False)
                v["trivial_exact"] += rec.get("trivial_exact", False)
        out[key] = {k: {**v, "exact_lower": v4.jeffreys_lower(v["exact"], v["claimed"]) if v["claimed"] else None}
                    for k, v in sorted(s.items())}
    return out


def frame_share(info: list[dict]) -> dict:
    """Converter text atoms that are no reference text, in the exact documents (verify_integrity.md finding 3).
    At the block unit, these frame lines are in the TextBlock text of an exact document."""
    ex = [r for r in info if r.get("exact")]
    fr = sum(r["frame_atoms_in_text"] for r in ex)
    tx = sum(r["text_atoms"] for r in ex)
    shares = [r["frame_atoms_in_text"] / r["text_atoms"] for r in ex if r["text_atoms"]]
    return {"exact_documents": len(ex), "exact_documents_with_frame_atoms": sum(1 for r in ex if r["frame_atoms_in_text"]),
            "frame_atoms": fr, "text_atoms": tx, "share": round(fr / tx, 4) if tx else None,
            "max_share_one_document": round(max(shares), 4) if shares else None}


def input_share(info: list[dict]) -> dict:
    """Part of Apertus and of the export fields in the S1 signals of the claimed documents (verify_final.md
    finding 1, verify_integrity.md findings 12 and 17)."""
    cl = [r["doc"] for r in info if r["claimed"] and r["doc"] in SIG]   # identity check: readout-only documents
    return {"claimed": len(cl),
            "s1_combined_from_apertus": sum(1 for d in cl if SIG[d].get("s1_combined_source") == "apertus"),
            "s1_combined_differs_from_s1_rule": sum(1 for d in cl if SIG[d]["s1_combined"] != SIG[d]["s1_rule"]),
            "s1_rule_id_reads_export_fields": sum(1 for d in cl if SIG[d].get("s1_rule_id") in EXPORT_RULE_IDS),
            "export_rule_ids": list(EXPORT_RULE_IDS)}


def measure_pair(lv: dict, a_read, b_read, docs: list[str]) -> dict:
    """Coder A as the first coder (reference), coder B as the second, with the scope and zones of the canonical
    converter of the isolation level."""
    canon = CANON[lv["canonical"]]
    ra, rb, used = [], [], []
    for d in docs:
        guard(d)
        A0, B0 = a_read(d), b_read(d)
        if A0 is None or B0 is None:
            continue
        claimed, _, zone = converter_view(lv, d, canon[d])
        if not claimed:
            continue
        A, B = mask(cmap(lv["map"], A0), zone), mask(cmap(lv["map"], B0), zone)
        ra.append(doc_counts(d, A, B))
        rb.append(doc_counts(d, B, A))
        ra[-1]["sw"] = len(blocks(A)) >= 2
        rb[-1]["sw"] = len(blocks(B)) >= 2
        used.append(d)
    sw = [(x["sw"], x[lv["exact_rule"]], y["sw"], y[lv["exact_rule"]]) for x, y in zip(ra, rb)]
    switch = {"documents": [sum(1 for a, _, _, _ in sw if a), sum(1 for _, _, c, _ in sw if c)],
              "exact": [sum(1 for a, e, _, _ in sw if a and e), sum(1 for _, _, c, f in sw if c and f)],
              "note": "documents where the first coder of the direction has 2 or more blocks"}
    for x in ra + rb:
        x.pop("sw")
    ga, gb = aggregate(ra, lv["exact_rule"]), aggregate(rb, lv["exact_rule"])
    n = len(used)

    def pick(k):
        return [ga[k], gb[k]]

    def pick_f1(k):   # no boundary on both sides: F1 has no object (compare_docs gives 0.0)
        return [g[k] if g["boundaries_ref"] + g["boundaries_hyp"] else None for g in (ga, gb)]
    f1s = pick_f1("labelled_f1")
    ex_lower = [v4.jeffreys_lower(g["exact"], n) if n else None for g in (ga, gb)]
    return {"documents": n, "boundaries": pick("boundaries_ref"), "exact_lower": ex_lower,
            "labelled_f1": f1s, "labelled_f1_lower": pick_f1("labelled_f1_lower"),
            "f1_sym": round((f1s[0] + f1s[1]) / 2, 4) if n and None not in f1s else None,
            "text_omission": pick("text_omission"), "omitted_atoms": [ga["omitted"], gb["omitted"]],
            "text_atoms": [ga["text_ref"], gb["text_ref"]],
            "documents_with_omission_share": pick("documents_with_omission_share"),
            "text_intrusion": pick("text_intrusion"), "text_class_error": pick("text_class_error"),
            "block_intrusion": pick("block_intrusion"), "exact": pick("exact"), "exact_rate": pick("exact_rate"),
            "switch_stratum": switch, "used_documents": used,
            "direction": "first value: first coder as the reference; second value: second coder as the reference"}


def _worst(vals, higher_is_better):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return min(vals) if higher_is_better else max(vals)


def reference_limit(xy: dict) -> dict:
    """Process rule 2.3: the blind pair at the isolation level, worst direction."""
    return {"source": "blind_X | blind_Y, worst of the two directions", "documents": xy["documents"],
            "boundaries": xy["boundaries"][0],
            "labelled_f1": _worst(xy["labelled_f1"], True), "labelled_f1_sym": xy["f1_sym"],
            "labelled_f1_lower": _worst(xy["labelled_f1_lower"], True),
            "text_omission": _worst(xy["text_omission"], False),
            "documents_with_omission_share": _worst(xy["documents_with_omission_share"], False),
            "text_intrusion": _worst(xy["text_intrusion"], False),
            "text_class_error": _worst(xy["text_class_error"], False),
            "exact_rate": _worst(xy["exact_rate"], True),
            "exact": min(xy["exact"]) if xy["documents"] else None,
            "exact_lower": _worst(xy["exact_lower"], True)}


def _cmp(value, op, limit):
    if value is None:
        return None, False
    margin = round(value - limit, 4) if op == ">=" else round(limit - value, 4)
    return margin, margin >= 0


def gate(lv: dict, m: dict, kind: str) -> dict:
    """kind V1 (criteria 3.1), V2 (V1 with CC1, CC2, CC3, CC5), V3 (V2 with LC1)."""
    L, unit = lv["id"], lv["unit"]
    if unit == "document" and kind == "V1":
        return {"applicable": False, "met": None, "failed": [],
                "note": "the document unit makes no atom claim; criteria version 3.1 has no object"}
    if m["documents"] == 0:
        return {"applicable": True, "met": False, "failed": ["no claimed document"], "criteria": {}}
    crit = {}
    unr = m.get("unrounded", {})

    def add(cid, items, decisive, note=""):
        parts, ok = {}, True
        for key, (op, lim) in items.items():
            # version 2: the verdict uses the unrounded rate; the margin is rounded for the report
            raw = unr.get(key, m.get(key))
            margin, _ = _cmp(m.get(key), op, lim)
            met = None if raw is None else (raw >= lim if op == ">=" else raw <= lim)
            parts[key] = {"value": m.get(key), "unrounded": raw, "op": op, "limit": lim, "margin": margin,
                          "met": bool(met)}
            ok = ok and bool(met)
        crit[cid] = {"decisive": decisive, "met": ok, "parts": parts, "note": note}

    if unit in ("atom", "block"):
        cc1 = kind != "V1" and L in CC["CC1"]
        add("G3a.5", LIMITS["G3a.5"], not cc1, "reported only (CC1)" if cc1 else "")
        lim6 = dict(LIMITS["G3a.6"])
        lc1 = kind == "V3" and L in LC["LC1"]          # version 2: LC1 only where ladder.json lists it
        if lc1:
            lim6["text_omission"] = ("<=", LC1_OMISSION)
        if unit == "block":
            # version 2: the block form gives a text answer to each atom without a fixed answer, so the omission
            # is 0 by construction (verify_integrity.md finding 6). Block omission is part of exact_block.
            add("G3a.6", lim6, False, "no object at the block unit: omission is 0 by construction; block "
                                      "omission is in the exact rule")
            crit["G3a.6"]["met"] = None
        else:
            add("G3a.6", lim6, True, "LC1: omission limit 0.003" if lc1 else "")
        cc2 = kind != "V1" and L in CC["CC2"]
        add("G3a.6b", LIMITS["G3a.6b"], not cc2, "replaced by block intrusion in the exact rule (CC2)" if cc2 else "")
    add("G3a.9", LIMITS["G3a.9"], True, f"exact rule {lv['exact_rule']}")
    crit["G3a.9"]["exact"] = m["exact"]
    crit["G3a.9"]["documents"] = m["documents"]
    crit["G3a.9"]["needed_for_limit"] = -(-4 * m["documents"] // 5)
    crit["G3a.9"]["spare_documents"] = m["exact"] - crit["G3a.9"]["needed_for_limit"]
    crit["G3a.9"]["exact_lower"] = m["exact_lower"]
    if kind != "V1" and L in CC["CC3"]:
        add("CC3", {"text_class_error": ("<=", CC3_CLASS_ERROR)}, True)
    if kind != "V1" and L in CC["CC5"]:
        t = m["trivial_role_same_scope"]["exact"]
        crit["CC5"] = {"decisive": True, "met": m["exact"] > t,
                       "parts": {"exact": {"value": m["exact"], "op": ">", "limit": t, "margin": m["exact"] - t,
                                           "met": m["exact"] > t}},
                       "note": "method exact documents above the trivial converter 'role only' on the same scope"}
    if L in CC["CC4"]:
        crit["CC4"] = {"decisive": False, "met": None,
                       "parts": {"coverage_documents": {"value": m["coverage_documents"]},
                                 "coverage_ref_text": {"value": m["coverage_ref_text"]}},
                       "note": "coverage floor not set by Jonathan: reported only"}
    failed = [k for k, c in crit.items() if c["decisive"] and not c["met"]]
    return {"applicable": True, "met": not failed, "failed": failed, "criteria": crit,
            "decisive_met": sum(1 for c in crit.values() if c["decisive"] and c["met"]),
            "decisive_total": sum(1 for c in crit.values() if c["decisive"])}


# ------------------------------------------------------------------ checks
def run_identity(compare: bool) -> dict:
    """L0 must reproduce the known values. Stop if it does not."""
    out, fail = {}, []
    expected = {"dev": {"labelled_f1": 0.6993, "labelled_f1_lower": 0.6525, "text_omission": 0.0191,
                        "text_intrusion": 0.2268, "text_class_error": 0.145, "document_exact_rate": 0.0437},
                "eval": {"labelled_f1": 0.6, "labelled_f1_lower": 0.4614, "text_omission": 0.0241,
                         "text_intrusion": 0.2924, "text_class_error": 0.0618, "document_exact_rate": 0.0909}}
    L0 = next(lv for lv in LEVELS if lv["id"] == "L0")
    for split in ("dev", "eval"):
        docs = SP[split]
        with tempfile.TemporaryDirectory() as t:
            for d in docs:
                guard(d)
                src = sc.REF41 if DOCS[d].kind == "group" else sc.POOL41
                (Path(t) / f"{d}.json").symlink_to(src / f"{d}.json")
            cd = v4.compare_docs(Path(t), guard_dir(ASM / f"hyp_assembled_{split}"), docs)
        mine = measure(L0, ANS["assembled"][split], docs)
        row = {"documents": cd["documents"], "expected": expected[split],
               "compare_docs": {k: cd[k] for k in expected[split]},
               "script_L0": {k: (mine["exact_rate"] if k == "document_exact_rate" else mine[k]) for k in expected[split]}}
        ok = row["compare_docs"] == expected[split] == row["script_L0"]
        row["status"] = "MET" if ok else "NOT MET"
        if not ok:
            fail.append(f"assembled {split}")
        out[f"hyp_assembled_{split}"] = row
    # OOF: report_oof_a1_viterbi.json, groups 1 to 5 with triage PASS
    rep = json.loads((V4 / "report_oof_a1_viterbi.json").read_text(encoding="utf-8"))
    groups = rep["groups"]
    docs = [guard(d) for d in v4.group_docs(groups, final=False) if sc.triage().get(d) == "PASS"]
    cd = v4.compare_docs(guard_dir(V4 / "ref41"), guard_dir(V4 / "hyp_oof_a1"), docs)
    keys = list(rep["pooled"].keys())
    got = {k: cd[k] for k in keys}
    oof_ans = {d: _oof(d) for d in docs}
    mine = measure(L0, oof_ans, docs, trivial=False)
    mine_v = {k: (mine["exact_rate"] if k == "document_exact_rate" else mine[k]) for k in keys}
    ok = got == rep["pooled"] == mine_v
    out["hyp_oof_a1"] = {"documents": len(docs), "groups": groups, "expected": rep["pooled"], "compare_docs": got,
                         "script_L0": mine_v, "status": "MET" if ok else "NOT MET"}
    if not ok:
        fail.append("oof_a1")
    out["failed"] = fail
    if fail:
        print(json.dumps(out, indent=1))
        raise SystemExit(2)
    return out


LADDER_KEYS = ("documents", "boundaries_ref", "boundaries_hyp", "correct", "labelled_f1", "labelled_f1_lower",
               "text_omission", "documents_with_omission", "text_intrusion", "text_class_error", "block_omission",
               "block_intrusion", "documents_with_block_intrusion", "exact", "exact_rate", "exact_lower",
               "coverage_ref_text", "unsure_atoms")


def ladder_check(results: dict) -> dict:
    """The canonical converter values and the agreement values must be equal to the ladder step values."""
    lvj = json.loads((SCRATCH / "ladder_values.json").read_text(encoding="utf-8"))["levels"]
    diffs, n = [], 0
    for lv in LEVELS:
        L, c = lv["id"], lv["canonical"]
        for split in ("dev", "eval"):
            mine = results[L]["methods"][c][split]
            old = lvj[L]["method"][split]
            for k in LADDER_KEYS:
                n += 1
                mk = "unsure_atoms_incl_fixed" if k == "unsure_atoms" else k   # version 2: zone count of the ladder step
                if mine[mk] != old[k]:
                    diffs.append(f"{L} {c} {split} {k}: {mine[mk]} != {old[k]}")
            n += 1
            if mine["trivial_role_same_scope"]["exact"] != lvj[L]["trivial_role_same_scope"][split]["exact"]:
                diffs.append(f"{L} trivial {split}")
        for pair, old_key in (("blind_X|blind_Y", "X|Y"), ("blind_X|ref41", "X|ref41"), ("blind_Y|ref41", "Y|ref41")):
            mine = results[L]["reference"]["pairs"][pair]["all"]
            old = lvj[L]["agreement"][old_key]
            f1m = 0.0 if mine["f1_sym"] is None else mine["f1_sym"]
            for a, b in ((mine["documents"], old["documents"]), (f1m, old["f1_sym"]),
                         (mine["text_omission"][0], old["omission_first_as_ref"]),
                         (mine["exact"], old["exact_documents"])):
                n += 1
                if a != b:
                    diffs.append(f"{L} {pair}: {a} != {b}")
        g = results[L]["reference"]["ai_reference_vs_gold_set"]["pooled_5"]
        old = lvj[L]["agreement"]["gold|ref41"]
        f1g = 0.0 if g["f1_sym"] is None and g["documents"] else g["f1_sym"]
        for a, b in ((g["documents"], old["documents"]), (f1g, old["f1_sym"]), (g["exact"], old["exact_documents"])):
            n += 1
            if a != b:
                diffs.append(f"{L} gold set: {a} != {b}")
    return {"compared_values": n, "differences": diffs, "status": "MET" if not diffs else "NOT MET",
            "source": "daten/iso/ladder/scratch/ladder_values.json"}


def gold_validate() -> dict:
    """The derived E20 answers of the gold set records pass m03_iso_v4.validate4."""
    out = {}
    with tempfile.TemporaryDirectory() as t:
        for d in GOLD["dev"] + GOLD["eval"]:
            v4.write(Path(t), d, sc.reference(d, "gold"), "gold set record", "m03_gold_record.derive")
            out[d] = {"split": SPLIT_OF[d], "errors": v4.validate4(Path(t) / f"{d}.json")}
    return out


# ------------------------------------------------------------------ main
def run(compare: bool) -> dict:
    started = time.strftime("%d.%m.%Y, %H:%M %Z")
    selftest = guard_selftest()
    if any(v == "NOT REFUSED" for v in selftest.values()):
        raise SystemExit(f"guard self-test FAILED: {selftest}")
    identity = run_identity(compare)
    print("identity check MET", flush=True)
    block_form_changes = {s: sum(1 for d, a in ANS["nos4"][s].items()
                                 for x, y in zip(cmap("SLOT_NOTITLE", a), block_form(cmap("SLOT_NOTITLE", a), d)) if x != y)
                          for s in ("dev", "eval")}
    if any(block_form_changes.values()):
        raise SystemExit(f"block form changes nos4: {block_form_changes}")
    gold_check = gold_validate()
    if any(x["errors"] for x in gold_check.values()):
        raise SystemExit(f"gold set records do not pass validate4: {gold_check}")

    results = {}
    group_all = GROUP_DOCS["dev"] + GROUP_DOCS["eval"]
    for lv in LEVELS:
        L = lv["id"]
        t0 = time.time()
        # reference reliability
        pairs = {}
        for a, b, cls in PAIRS:
            pairs[f"{a}|{b}"] = {"class": cls,
                                 "all": measure_pair(lv, CODERS[a], CODERS[b], group_all),
                                 "dev": measure_pair(lv, CODERS[a], CODERS[b], GROUP_DOCS["dev"]),
                                 "eval": measure_pair(lv, CODERS[a], CODERS[b], GROUP_DOCS["eval"])}
        gold_read = lambda d: DOCS[d].gold  # noqa: E731
        ref_read = lambda d: sc.reference(d)  # noqa: E731
        gold_ref = {"dev": measure_pair(lv, gold_read, ref_read, GOLD["dev"]),
                    "eval_validation": measure_pair(lv, gold_read, ref_read, GOLD["eval"]),
                    "pooled_5": measure_pair(lv, gold_read, ref_read, GOLD["dev"] + GOLD["eval"]),
                    "direction": "first: gold set record (human review); second: ref41 (AI reference)"}
        rl = reference_limit(pairs["blind_X|blind_Y"]["all"])
        conflicts = {}
        for cid in (("G3a.9",) if lv["unit"] == "document" else ("G3a.5", "G3a.6", "G3a.6b", "G3a.9")):
            for key, (op, lim) in LIMITS[cid].items():
                ref_v = rl.get(key)
                if ref_v is None or (lv["unit"] == "block" and cid == "G3a.6"):
                    # version 2: at the block unit, G3a.6 has no object (verify_integrity.md finding 16)
                    conflicts[f"{cid} {key}"] = {"limit": lim, "reference_limit": ref_v, "conflict": None}
                    continue
                stricter = lim > ref_v if op == ">=" else lim < ref_v
                conflicts[f"{cid} {key}"] = {"limit": lim, "reference_limit": ref_v, "conflict": stricter}
        xy_all = pairs["blind_X|blind_Y"]["all"]
        g3a3 = {"value_blind_XY_f1_sym": xy_all["f1_sym"], "limit": 0.95,
                "margin": round(xy_all["f1_sym"] - 0.95, 4) if xy_all["f1_sym"] is not None else None,
                "note": "proxy only: G3a.3 is defined on the native coders of the final documents (0.917 at L0)"}
        # version 2: G3a.3 analog in the decisive value of the isolation level (verify_integrity.md finding 8)
        g3a3_analog = {"value": f"blind X | Y, {lv['exact_rule']} (worst direction)",
                       "exact": min(xy_all["exact"]) if xy_all["documents"] else None,
                       "documents": xy_all["documents"],
                       "exact_rate": _worst(xy_all["exact_rate"], True), "exact_lower": _worst(xy_all["exact_lower"], True),
                       "switch_stratum": xy_all["switch_stratum"],
                       "note": "reported only; same AI model for both coders; group documents only"}
        # methods
        methods = {}
        for meth in METHODS:
            mid = meth["id"]
            row = {"name": meth["name"], "sources": {s: r.source for s, r in meth["reader"].items()}}
            for split in ("dev", "eval"):
                if split not in meth["reader"]:
                    row[split] = None
                    continue
                docs = [d for d in SP[split] if d in ANS[mid][split]]
                m = measure(lv, ANS[mid][split], docs, compare=compare, what=f"{L} {mid} {split}")
                if lv["unit"] == "block":
                    raw = measure(lv, ANS[mid][split], docs, trivial=False, bf=False)
                    m["without_block_form"] = {k: raw[k] for k in ("documents", "exact", "exact_rate", "text_omission",
                                                                   "documents_with_omission", "text_intrusion")}
                m["value_label"] = meth["label_dev"] if split == "dev" else VALIDATION
                m["full_coverage_of_split"] = len(docs) == len(SP[split])
                m["gate"] = {k: gate(lv, m, k) for k in ("V1", "V2", "V3")}
                if mid in ("assembled", "best", "nos4"):
                    # version 2: sensitivity to the known deviations of ref41 (verify_integrity.md finding 2)
                    sm = measure(lv, ANS[mid][split], docs, ref=consensus_ref)
                    m["sensitivity_consensus_XY"] = {
                        "reference": "group documents: consensus_XY (blind X where X and Y agree, else ref41); "
                                     "pool documents: pool_ref41 (no blind pair)",
                        "documents": sm["documents"], "exact": sm["exact"], "exact_rate": sm["exact_rate"],
                        "exact_lower": sm["exact_lower"],
                        "exact_only_with_ref41": sorted(set(m["exact_documents"]) - set(sm["exact_documents"])),
                        "exact_only_with_consensus": sorted(set(sm["exact_documents"]) - set(m["exact_documents"])),
                        "trivial_exact": sm["trivial_role_same_scope"]["exact"],
                        "gate_V2": gate(lv, sm, "V2")["met"]}
                    m["apertus_claim_effect"] = claim_changes_without_apertus(lv, ANS[mid][split], docs)
                row[split] = m
            # against the human gold set records (dev: in-sample for the rule composite; eval: validation)
            for split, key in (("dev", "gold_set_dev"), ("eval", "gold_set_eval_validation")):
                if split in meth["reader"]:
                    docs = [d for d in GOLD[split] if d in ANS[mid][split]]
                    gm = measure(lv, ANS[mid][split], docs, ref=lambda d: DOCS[d].gold)
                    row[key] = {k: gm[k] for k in ("documents_available", "documents", "boundaries_ref", "correct",
                                                   "labelled_f1", "text_omission", "text_intrusion",
                                                   "text_class_error", "exact", "exact_rule", "claimed_documents")}
            methods[mid] = row
        results[L] = {"definition": {k: lv[k] for k in ("name", "parent", "path", "map", "scope", "zones", "unit",
                                                         "exact_rule", "canonical", "reduction")},
                      "criterion_changes": [c for c in ("CC1", "CC2", "CC3", "CC4", "CC5") if L in CC[c]],
                      "limit_change_LC1_listed": L in LC["LC1"],
                      "reference": {"pairs": pairs, "ai_reference_vs_gold_set": gold_ref,
                                    "reference_limit": rl, "process_rule_2_3": conflicts, "G3a.3_proxy": g3a3,
                                    "G3a.3_analog": g3a3_analog,
                                    "scope_and_zones_from": lv["canonical"]},
                      "primary_method": lv["canonical"],
                      "task_kind": ("classification of whole documents (E25), not an isolation"
                                    if lv["unit"] == "document" else "isolation"),
                      "methods": methods}
        print(f"{L} done in {time.time() - t0:.1f} s", flush=True)
    check = ladder_check(results)
    if check["status"] != "MET":
        print("\n".join(check["differences"][:40]))
        raise SystemExit(2)
    summary = summarize(results)
    return {"schema": "parlpdfech-ladder-results/1", "version": VERSION, "status": "NOT RELEASED",
            "run_date": started, "finished": time.strftime("%d.%m.%Y, %H:%M %Z"),
            "actor": "workflow sub-agent (Claude Opus 5.5), step Measure of the complexity ladder; version 2 by the "
                     "workflow sub-agent (Claude Opus 5.5) of the step Report",
            "revision_2": ["primary method = method named by the ladder before the measurement; best of all outputs "
                           "is exploratory",
                           "sensitivity reference consensus_XY for group documents",
                           "strata: reference blocks, language, metadata role, reference role, group or pool",
                           "block unit: G3a.6 no object; frame share in the text of exact documents",
                           "G3a.3 analog: blind X | Y in the exact rule of the isolation level",
                           "Apertus share and export rule ids in the claimed documents",
                           "LC1 only at the listed isolation levels; gate comparisons with unrounded rates",
                           "zones without atoms with a fixed answer"],
            "decision_served": LADDER_JSON["decision_served"],
            "script": {"path": "src/m03_ladder.py", "sha256": sha256(Path(__file__))},
            "inputs": {"ladder.json": sha256(LADDER / "ladder.json"),
                       "ladder_values.json": sha256(SCRATCH / "ladder_values.json"),
                       "report_oof_a1_viterbi.json": sha256(V4 / "report_oof_a1_viterbi.json"),
                       "err_recompose_nos4_dev.json": sha256(SCRATCH / "err_recompose_nos4_dev.json"),
                       "err_recompose_nos4_eval.json": sha256(SCRATCH / "err_recompose_nos4_eval.json"),
                       **{f"s1_role/{n}_{s}.json": sha256(SUB / f"s1_role/{n}_{s}.json")
                          for n in ("rule", "combined", "apertus") for s in ("dev", "eval")}},
            "value_labels": {"dev": "rule composite: in-sample; LoRA readout: out of fold; 70B: not fitted. The S1 "
                                    "scope signals and the L4 scope choice are in-sample on dev.",
                             "eval": VALIDATION, "gold set records": "3 dev and 2 eval (validation) records; 877101 not used"},
            "gate_limits_criteria_3_1": {k: {kk: list(vv) for kk, vv in v.items()} for k, v in LIMITS.items()},
            "verdict_sets": {"V1": "criteria version 3.1 with the metric definitions of the isolation level",
                             "V2": "V1 with the criterion changes CC1, CC2, CC3, CC5 of the isolation level (CC4 reported)",
                             "V3": "V2 with the limit change LC1 (omission limit 0.003) at the isolation levels that "
                                   "ladder.json lists",
                             "note": "the criterion changes and LC1 were written after the dev and eval values were "
                                     "known; a V2 or V3 MET on stored outputs is not a gate result"},
            "checks": {"guard_selftest": selftest, "guard_calls": GUARD["calls"], "identity": identity,
                       "compare_docs": dict(COMPARE_RUNS) if compare else "skipped (--no-compare)",
                       "block_form_changes_on_nos4": block_form_changes, "ladder_reproduction": check,
                       "gold_set_records_validate4": gold_check},
            "splits": {"dev": len(SP["dev"]), "eval": len(SP["eval"]), "dev_group": len(GROUP_DOCS["dev"]),
                       "eval_group": len(GROUP_DOCS["eval"]), "gold_set_dev": GOLD["dev"], "gold_set_eval": GOLD["eval"]},
            "levels": results, "summary": summary}


def _rank_key(m: dict) -> tuple:
    g = m["gate"]["V2"]
    return (bool(g.get("met")), m["exact_rate"] or 0.0, g.get("decisive_met", 0), m["documents"])


def summarize(results: dict) -> dict:
    out = {"best_rule": "EXPLORATORY: methods with an output for each document of the split; rank: V2 met, then "
                        "exact rate, then decisive V2 criteria met, then claimed documents. A selection among 10 "
                        "outputs after the values were known; not a gate result.",
           "primary_rule": "the method that the ladder named before the measurement: assembled; nos4 at the block unit",
           "levels": {}, "met_dev_and_eval": {"V1": [], "V2": [], "V3": []},
           "primary": {}, "primary_met_dev_and_eval": {"V1": [], "V2": [], "V3": []}}
    for L, r in results.items():
        pm = r["primary_method"]
        prow = r["methods"][pm]
        out["primary"][L] = {"method": pm}
        for s in ("dev", "eval"):
            m = prow[s]
            g9 = m["gate"]["V2"].get("criteria", {}).get("G3a.9", {})
            out["primary"][L][s] = {
                "exact": m["exact"], "documents": m["documents"], "exact_rate": m["exact_rate"],
                "exact_lower": m["exact_lower"], "needed_for_0.80": g9.get("needed_for_limit"),
                "spare_documents": g9.get("spare_documents"),
                "trivial": m["trivial_role_same_scope"]["exact"],
                "coverage_documents": m["coverage_documents"], "coverage_ref_text": m["coverage_ref_text"],
                "V1": m["gate"]["V1"]["met"], "V2": m["gate"]["V2"]["met"], "V3": m["gate"]["V3"]["met"],
                "V2_failed": m["gate"]["V2"]["failed"], "V1_failed": m["gate"]["V1"]["failed"],
                "sensitivity_consensus_XY": {k: m["sensitivity_consensus_XY"][k] for k in ("exact", "documents", "gate_V2")},
                "value_label": m["value_label"]}
        for kind in ("V1", "V2", "V3"):
            if prow["dev"]["gate"][kind].get("met") and prow["eval"]["gate"][kind].get("met"):
                out["primary_met_dev_and_eval"][kind].append({"level": L, "method": pm})
        best = {}
        for split in ("dev", "eval"):
            cand = [(mid, row[split]) for mid, row in r["methods"].items()
                    if row.get(split) and row[split]["documents"] and row[split]["full_coverage_of_split"]]
            if cand:
                mid, m = max(cand, key=lambda x: _rank_key(x[1]))
                best[split] = mid
        out["levels"][L] = {"best_dev": best.get("dev"), "best_eval_validation": best.get("eval")}
        for kind in ("V1", "V2", "V3"):
            for mid, row in r["methods"].items():
                if row.get("dev") and row.get("eval") and row["dev"]["gate"][kind].get("met") and row["eval"]["gate"][kind].get("met"):
                    hit = {"level": L, "method": mid, "primary": mid == r["primary_method"],
                           "label": "primary method" if mid == r["primary_method"] else
                           "exploratory: selected after the values were known; not a gate result"}
                    for s in ("dev", "eval"):
                        m = row[s]
                        if "sensitivity_consensus_XY" in m:
                            sx = m["sensitivity_consensus_XY"]
                            hit[f"{s}_consensus_exact"] = f"{sx['exact']}/{sx['documents']}"
                            hit[f"{s}_consensus_V2"] = sx["gate_V2"]
                        need = -(-4 * m["documents"] // 5)          # smallest count with rate >= 0.80
                        hit[f"{s}_exact"] = f"{m['exact']}/{m['documents']}"
                        hit[f"{s}_exact_lower"] = m["exact_lower"]
                        hit[f"{s}_spare_documents"] = m["exact"] - need
                        hit[f"{s}_trivial"] = m["trivial_role_same_scope"]["exact"]
                        hit[f"{s}_coverage_documents"] = m["coverage_documents"]
                        hit[f"{s}_coverage_ref_text"] = m["coverage_ref_text"]
                        hit[f"{s}_value_label"] = m["value_label"]
                    out["met_dev_and_eval"][kind].append(hit)
        for mid, row in r["methods"].items():
            dv, ev = row.get("dev"), row.get("eval")
            if not (dv and ev and dv["documents"] and dv["full_coverage_of_split"]):
                continue
            if ev["gate"]["V2"].get("met") and dv["gate"]["V2"]["failed"] == ["G3a.9"]:
                need = -(-4 * dv["documents"] // 5)
                out.setdefault("near_misses_dev_V2", []).append(
                    {"level": L, "method": mid, "dev_exact": f"{dv['exact']}/{dv['documents']}",
                     "dev_documents_short": need - dv["exact"], "eval_exact": f"{ev['exact']}/{ev['documents']}"})
    return out


# ------------------------------------------------------------------ report
PARTIAL = ("oof_a1", "oof_a1_with_pool", "cscs70_k4_e20", "cscs70_k4", "cscs70_k0")


def fx(v, nd=3):
    if v is None:
        return "–"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def frac(a, b):
    return f"{a} of {b}" if b else "–"


def verdict(g: dict) -> str:
    return "–" if g["met"] is None else ("MET" if g["met"] else "NOT MET")


def write_md(res: dict) -> str:
    L_ = res["levels"]
    lines = []
    w = lines.append
    w("# Measurement of the complexity ladder (step Measure)")
    w("")
    w(f"Version 2, {res['run_date']} (run date from the clock). Status: NOT RELEASED. Actor: workflow sub-agent "
      "(Claude Opus 5.5), step Measure of the complexity ladder. Version 2: workflow sub-agent (Claude Opus 5.5), "
      "step Report. Written in English to the STE rules (ASD-STE100, Issue 9).")
    w("")
    w("Script: `src/m03_ladder.py`. All values: `daten/iso/ladder/results.json`. Ladder: `daten/iso/ladder/ladder.json`.")
    w("")
    w("Changes in version 2 (after the verification lenses `verify_reproduce.md`, `verify_integrity.md` and `verify_final.md`):")
    w("")
    w("1. The primary method of each isolation level is the method that the ladder named before the measurement. Its verdicts are the result.")
    w("2. The best of all outputs is an exploratory value. It is a selection after the values were known.")
    w("3. A sensitivity value measures the group documents against `consensus_XY` (blind X where X and Y agree, else `ref41`).")
    w("4. New strata: reference blocks, language, metadata role and group or pool.")
    w("5. At the block unit, G3a.6 has no object. The frame share in the text of the exact documents is reported.")
    w("6. A G3a.3 analog, the Apertus share and the export rule ids are reported.")
    w("7. LC1 applies only at the isolation levels that `ladder.json` lists. The gate comparisons use unrounded rates.")
    w("8. A zone holds no atom with a fixed answer. No gate value changes. The count of unsure atoms changes.")
    w("")
    w("## 1 Purpose")
    w("")
    w("1. On 08.10.2026, Jonathan decided: \"Das ergibt wenig Sinn etwas nicht zu bestehen wir müssen einfach die "
      "komplexität reduzieren bis wir diese bestehen.\"")
    w("2. The meaning is: reduce the complexity of the isolation task until a gate can be passed.")
    w("3. This file gives the values of each isolation level L0 to L10 on the stored outputs.")
    w("4. This file gives no gate result. Jonathan selects an isolation level and its gate criteria before the measurement (process rule 1.5).")
    w("")
    w("## 2 Limits of this step")
    w("")
    w("1. This step used only stored outputs. It sent no CSCS request and no network request. It trained no model and used no GPU.")
    w("2. The script examines each document id with `m03_sub_common._check_allowed_doc` and against `m03_iso_v4.final_docs()` before it opens a file.")
    w("3. The script refuses `final_*` folders, `hyp_g7_final_a1`, `report_g7_final_a1.json` and `daten/gold/test`. It read no group 7 document and no test document.")
    w("4. Version 1 changed no existing file. Version 2 changed only `src/m03_ladder.py`, `results.json` and this file.")
    w("5. Each `dev` value of the rule composite is in-sample. AI agents wrote the rules on `dev`. The S1 scope signals and the L4 scope choice are also in-sample on `dev`.")
    w("6. The LoRA readout `oof_a1` is out of fold. The 70B readouts had no training. Their examples are pool documents of other parliaments.")
    w("7. Each `eval` value is a validation value. `eval` was measured several times before. No `eval` value is a final measurement.")
    w("8. All references are from AI agents, except the 5 gold set records. A value against an AI reference is agreement, not accuracy.")
    w("9. Version 1 compared 10 method outputs at 11 isolation levels. A method that meets the limits in that comparison was selected on `dev` and `eval`.")
    w("10. The criterion changes CC1 to CC5 and the limit change LC1 were written after the `dev` and `eval` values were known. A V2 or V3 MET on stored outputs is not a gate result.")
    w("")
    ck = res["checks"]
    w("## 3 Checks")
    w("")
    w("| Check | Result | Details |")
    w("|---|---|---|")
    idt = ck["identity"]
    for k in ("hyp_assembled_dev", "hyp_assembled_eval"):
        x = idt[k]
        w(f"| Identity: `{k}` at L0 | {x['status']} | F1 {fx(x['script_L0']['labelled_f1'], 4)}, lower bound "
          f"{fx(x['script_L0']['labelled_f1_lower'], 4)}, exact rate {fx(x['script_L0']['document_exact_rate'], 4)}; "
          f"equal to `compare_docs` and to the expected values |")
    x = idt["hyp_oof_a1"]
    w(f"| Identity: `hyp_oof_a1` at L0, {x['documents']} documents of groups 1 to 5 | {x['status']} | F1 "
      f"{fx(x['script_L0']['labelled_f1'], 4)}, omission {fx(x['script_L0']['text_omission'], 4)}, exact rate "
      f"{fx(x['script_L0']['document_exact_rate'], 4)}; equal to `report_oof_a1_viterbi.json` |")
    cmpd = ck["compare_docs"]
    if isinstance(cmpd, dict):
        w(f"| Atom-unit values against `compare_docs` | MET | {cmpd.get('runs', 0)} measurements, {cmpd.get('documents', 0)} document values |")
    lr = ck["ladder_reproduction"]
    w(f"| Values of the ladder step (`ladder_values.json`) | {lr['status']} | {lr['compared_values']} values, {len(lr['differences'])} differences |")
    w(f"| Block form on `nos4` | MET | {sum(ck['block_form_changes_on_nos4'].values())} changed atoms |")
    w(f"| Gold set records with `validate4` | MET | {len(ck['gold_set_records_validate4'])} records, 0 errors; 877101 not used |")
    gs = ck["guard_selftest"]
    w(f"| Guard probes | MET | group 7 document {gs['group_7_document']}, unknown document {gs['unknown_document']}, "
      f"`final_*` {gs['final_folder']}, test set folder {gs['test_set_folder']} |")
    w("")
    # ---------------------------------------------------------------- primary result (version 2)
    w("## 4 Primary result")
    w("")
    w("The primary method is the method that the ladder named before the measurement: `assembled`, and `nos4` at the block unit (`ladder-spec.md` chapter 3, item 8).")
    w("")
    w("Columns:")
    w("")
    w("1. Exact: exact documents of the claimed documents, with the Jeffreys lower bound. `dev` is in-sample. `eval` is a validation value.")
    w("2. Spare: exact documents above the count that the limit 0.80 needs. A negative value misses the limit.")
    w("3. Trivial: exact documents of \"role only\" on the same documents.")
    w("4. Consensus: exact documents when `consensus_XY` replaces `ref41` for the group documents.")
    w("")
    w("| Isolation level | Method | `dev` exact (lower bound) | `dev` spare | `dev` trivial | `dev` consensus | `eval` exact (lower bound) | `eval` spare | V2 misses `dev`; `eval` | V1, V2, V3 on both splits |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for L, p in res["summary"]["primary"].items():
        dv, ev = p["dev"], p["eval"]
        both = ", ".join(("MET" if (dv[k] and ev[k]) else ("–" if dv[k] is None else "NOT MET")) for k in ("V1", "V2", "V3"))
        w(f"| {L} | `{p['method']}` | {dv['exact']} of {dv['documents']} ({fx(dv['exact_lower'])}) | {dv['spare_documents']} | "
          f"{dv['trivial']} | {dv['sensitivity_consensus_XY']['exact']} | {ev['exact']} of {ev['documents']} ({fx(ev['exact_lower'])}) | "
          f"{ev['spare_documents']} | {', '.join(dv['V2_failed']) or 'none'}; {', '.join(ev['V2_failed']) or 'none'} | {both} |")
    w("")
    w("Facts:")
    w("")
    for i, s in enumerate(primary_facts(res), 1):
        w(f"{i}. {s}")
    w("")
    w("### 4.1 Strata of the primary method")
    w("")
    w("Reference blocks after the map and the zones: 0 (no text field), 1 (one block), 2 (2 or more blocks, thus a switch). Cell: exact documents of claimed documents, then \"role only\" on the same documents. Claimed of available in brackets.")
    w("")
    w("| Isolation level | `dev` 0 blocks | `dev` 1 block | `dev` 2 or more | `eval` 0 blocks | `eval` 1 block | `eval` 2 or more |")
    w("|---|---|---|---|---|---|---|")
    for L, r in L_.items():
        pm = r["primary_method"]
        cells = []
        for s in ("dev", "eval"):
            st = r["methods"][pm][s]["strata"]["ref_blocks"]
            for k in ("0", "1", "2"):
                v = st.get(k)
                cells.append("–" if not v or not v.get("claimed") else
                             f"{v.get('exact', 0)} of {v['claimed']}, trivial {v.get('trivial_exact', 0)} ({v['claimed']} of {v['available']})")
        w(f"| {L} | " + " | ".join(cells) + " |")
    w("")
    w("Language and group or pool. Cell: exact of claimed (claimed of available).")
    w("")
    w("| Isolation level | `dev` de | `dev` fr | `dev` it | `dev` group | `dev` pool | `eval` de | `eval` fr | `eval` it |")
    w("|---|---|---|---|---|---|---|---|---|")
    for L, r in L_.items():
        pm = r["primary_method"]
        cells = []
        for s, dims in (("dev", (("language", "de"), ("language", "fr"), ("language", "it"), ("kind", "group"), ("kind", "pool"))),
                        ("eval", (("language", "de"), ("language", "fr"), ("language", "it")))):
            st = r["methods"][pm][s]["strata"]
            for dim, k in dims:
                v = st[dim].get(k)
                cells.append("–" if not v else f"{v.get('exact', 0)} of {v.get('claimed', 0)} ({v.get('claimed', 0)} of {v['available']})")
        w(f"| {L} | " + " | ".join(cells) + " |")
    w("")
    w("### 4.2 Frame lines, Apertus and export fields in the primary method")
    w("")
    w("Frame share: converter text atoms that are no reference text, in the exact documents. At the block unit, these frame lines are in the TextBlock text. Apertus: claimed documents where Apertus gave the S1 combined role. Export: claimed documents where the S1 rule id is P2 or R1 (export fields).")
    w("")
    w("| Isolation level | `dev` frame share (maximum) | `eval` frame share (maximum) | `dev` Apertus; changed role; claim change without Apertus | `eval` Apertus; changed role; claim change | `dev` export | `eval` export |")
    w("|---|---|---|---|---|---|---|")
    for L, r in L_.items():
        pm = r["primary_method"]
        cells = []
        for s in ("dev", "eval"):
            f = r["methods"][pm][s]["frame_in_text_of_exact_documents"]
            cells.append("no atom claim" if r["definition"]["unit"] == "document" else
                         f"{fx(f['share'])} ({fx(f['max_share_one_document'])})")
        for s in ("dev", "eval"):
            a = r["methods"][pm][s]["converter_inputs_of_claimed_documents"]
            ce = r["methods"][pm][s]["apertus_claim_effect"]
            cells.append(f"{a['s1_combined_from_apertus']}; {a['s1_combined_differs_from_s1_rule']}; {ce['claim_changes']}")
        for s in ("dev", "eval"):
            a = r["methods"][pm][s]["converter_inputs_of_claimed_documents"]
            cells.append(f"{a['s1_rule_id_reads_export_fields']} of {a['claimed']}")
        w(f"| {L} | " + " | ".join(cells) + " |")
    w("")
    # ---------------------------------------------------------------- main table
    w("## 5 Main table (with the exploratory best output)")
    w("")
    w("Columns:")
    w("")
    w("1. Blind X and Y: the pair `blind_X` and `blind_Y` on the group documents of `dev` and `eval` that the isolation level claims.")
    w("2. In that column, F1 is the symmetric mean. Omission and exact rate are the worst of the two directions.")
    w("3. `ref41` and gold set records: exact documents of `ref41` with the human gold set record as the reference. The `eval` records are validation values.")
    w("4. Best output: the best of the methods with an output for each document of the split (chapter 8, item 7). This is an exploratory value, not a gate result.")
    w("5. Coverage: claimed documents and reference text outside the zones, for the best `dev` output.")
    w("")
    w("| Isolation level | Blind X and Y: F1; omission; exact | `ref41` and gold set records: `dev`; `eval` | Best output on `dev` (exploratory) | Best output on `eval` (exploratory, validation) | Coverage `dev`; `eval` |")
    w("|---|---|---|---|---|---|")
    for L, r in L_.items():
        xy = r["reference"]["pairs"]["blind_X|blind_Y"]["all"]
        rl = r["reference"]["reference_limit"]
        g = r["reference"]["ai_reference_vs_gold_set"]
        sb = res["summary"]["levels"][L]
        cells = []
        for split, key in (("dev", "best_dev"), ("eval", "best_eval_validation")):
            mid = sb[key]
            if not mid:
                cells.append("–")
                continue
            m = r["methods"][mid][split]
            v2 = m["gate"]["V2"]
            fail = ", ".join(v2["failed"]) if v2["failed"] else "none"
            cells.append(f"`{mid}`: {m['exact']} of {m['documents']} exact ({fx(m['exact_rate'])}); V2 misses: {fail}")
        md = r["methods"][sb["best_dev"]]
        cov = (f"{fx(md['dev']['coverage_documents'], 2)}, text {fx(md['dev']['coverage_ref_text'], 2)}; "
               f"{fx(md['eval']['coverage_documents'], 2) if md.get('eval') else '–'}, text "
               f"{fx(md['eval']['coverage_ref_text'], 2) if md.get('eval') else '–'}")
        f1c = fx(xy["f1_sym"]) if xy["f1_sym"] is not None else "no boundary"
        w(f"| {L} | {f1c}; {fx(rl['text_omission'], 4)}; {fx(rl['exact_rate'])} ({xy['documents']} documents) | "
          f"{frac(g['dev']['exact'][0], g['dev']['documents'])}; {frac(g['eval_validation']['exact'][0], g['eval_validation']['documents'])} | "
          f"{cells[0]} | {cells[1]} | {cov} |")
    w("")
    w("Methods with an output for only part of a split. Cell: exact documents of claimed documents on `dev`, then on `eval`. The mark (V2) means that V2 is met on that split.")
    w("")
    w("| Isolation level | " + " | ".join(f"`{m}`" for m in PARTIAL) + " |")
    w("|---|" + "---|" * len(PARTIAL))
    for L, r in L_.items():
        cells = []
        for mid in PARTIAL:
            parts = []
            for split in ("dev", "eval"):
                m = r["methods"][mid].get(split)
                if not m or not m["documents"]:
                    parts.append("0 claimed")
                    continue
                mark = " (V2)" if m["gate"]["V2"]["met"] else ""
                parts.append(f"{m['exact']}/{m['documents']}{mark}")
            cells.append("; ".join(parts))
        w(f"| {L} | " + " | ".join(cells) + " |")
    w("")
    # ---------------------------------------------------------------- passes
    w("## 6 Isolation levels where a method meets all gate limits on `dev` and on `eval`")
    w("")
    texts = (("V1", "V1, criteria version 3.1 with the metric definitions of the isolation level"),
             ("V2", "V2, V1 with the criterion changes CC1, CC2, CC3 and CC5 of the isolation level"),
             ("V3", "V3, V2 with the limit change LC1"))
    w("Primary method (named by the ladder before the measurement):")
    w("")
    for kind, text in texts:
        hits = res["summary"]["primary_met_dev_and_eval"][kind]
        items = "; ".join(f"{h['level']} `{h['method']}`" for h in hits) if hits else "no isolation level"
        w(f"- {text}: {items}.")
    w("")
    w("All 10 outputs (exploratory, a selection after the values were known):")
    w("")
    for kind, text in texts:
        hits = res["summary"]["met_dev_and_eval"][kind]
        items = "; ".join(f"{h['level']} `{h['method']}`" for h in hits) if hits else "no isolation level and no method"
        w(f"- {text}: {items}.")
    w("")
    seen = set()
    for kind in ("V1", "V2", "V3"):
        for h in res["summary"]["met_dev_and_eval"][kind]:
            key = (h["level"], h["method"])
            if key in seen:
                continue
            seen.add(key)
            L, mid = key
            r = L_[L]
            w(f"Values of {L} `{mid}` (V2 and V3 met on both splits; {h['label']}):")
            w("")
            w("| Split | Value label | Exact | Jeffreys lower bound | Spare documents | Trivial | Consensus reference | Claimed documents | Text coverage |")
            w("|---|---|---|---|---|---|---|---|---|")
            for s in ("dev", "eval"):
                cons = h.get(s + "_consensus_exact", "–")
                if s + "_consensus_V2" in h:
                    cons += " (V2 " + ("MET" if h[s + "_consensus_V2"] else "NOT MET") + ")"
                w(f"| `{s}` | {h[s + '_value_label']} | {h[s + '_exact']} | {fx(h[s + '_exact_lower'])} | {h[s + '_spare_documents']} | "
                  f"{h[s + '_trivial']} | {cons} | {fx(h[s + '_coverage_documents'], 3)} | {fx(h[s + '_coverage_ref_text'], 3)} |")
            w("")
            w("Facts:")
            w("")
            for i, s in enumerate(pass_facts(res, L, mid), 1):
                w(f"{i}. {s}")
            w("")
    nm = res["summary"].get("near_misses_dev_V2", [])
    if nm:
        w("Methods with an output for each `dev` document that meet V2 on `eval` and miss V2 on `dev` only by G3a.9:")
        w("")
        w("| Isolation level | Method | `dev` exact | `dev` documents short of 0.80 | `eval` exact (validation) |")
        w("|---|---|---|---|---|")
        for x in nm:
            w(f"| {x['level']} | `{x['method']}` | {x['dev_exact']} | {x['dev_documents_short']} | {x['eval_exact']} |")
        w("")
    # ---------------------------------------------------------------- rule 2.3
    w("## 7 Reference limits (process rule 2.3)")
    w("")
    w("The reference limit is the blind pair `blind_X` and `blind_Y` at the isolation level, in the worst direction. A conflict means that the limit of criteria version 3.1 is stricter than the reference limit. At the block unit, G3a.6 has no object.")
    w("")
    w("| Isolation level | Documents | Boundaries | F1 | F1 lower bound | Omission | Documents with omission | Intrusion | Exact rate (lower bound) | Switch documents: exact | Conflicts |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for L, r in L_.items():
        rl = r["reference"]["reference_limit"]
        conf = [k for k, v in r["reference"]["process_rule_2_3"].items() if v["conflict"]]
        nob = [k for k, v in r["reference"]["process_rule_2_3"].items() if v["conflict"] is None]
        c = ", ".join(f"{k.split()[0]} `{k.split()[1]}`" for k in conf) or "none"
        if nob:
            c += "; no object: " + ", ".join(f"{k.split()[0]} `{k.split()[1]}`" for k in nob)
        sw = r["reference"]["G3a.3_analog"]["switch_stratum"]
        w(f"| {L} | {rl['documents']} | {rl['boundaries']} | {fx(rl['labelled_f1'])} | {fx(rl['labelled_f1_lower'])} | "
          f"{fx(rl['text_omission'], 4)} | {fx(rl['documents_with_omission_share'], 3)} | {fx(rl['text_intrusion'], 4)} | "
          f"{fx(rl['exact_rate'])} ({fx(rl['exact_lower'])}) | {sw['exact'][0]} of {sw['documents'][0]}, {sw['exact'][1]} of {sw['documents'][1]} | {c} |")
    w("")
    w("Facts:")
    w("")
    for i, s in enumerate(rule23_facts(res), 1):
        w(f"{i}. {s}")
    w("")
    # ---------------------------------------------------------------- conventions
    w("## 8 Conventions")
    w("")
    w("1. Limits of criteria version 3.1: G3a.5 F1 0.95 or more and lower bound 0.90 or more. G3a.6 omission 0.002 or less. "
      "G3a.6 also needs 5 % or less of the documents with an omission. G3a.6b intrusion 0.01 or less. G3a.9 exact rate 0.80 or more.")
    w("2. Margin: the value minus the limit for a minimum, and the limit minus the value for a maximum. A negative margin misses the limit. The verdict uses the unrounded value.")
    w("3. V1 uses the exact rule of the isolation level. At the block unit, G3a.9 uses `exact_block` and G3a.6 has no object. At the document unit, V1 has no object.")
    w("4. V2 applies the criterion changes of `ladder.json` for the isolation level. CC1: G3a.5 is reported only. CC2: block intrusion in the exact rule replaces G3a.6b.")
    w("5. V2 also applies CC3 (class error 0.01 or less) and CC5 (more exact documents than the trivial converter). CC4 has no floor yet. V2 reports the coverage only.")
    w("6. V3 is V2 with LC1: omission limit 0.003, only at the isolation levels that `ladder.json` lists. LC1 is a limit change, not a reduction of the task.")
    w("7. Best output (exploratory): only methods with an output for each document of the split. Rank: V2 met, then exact rate, then V2 criteria met, then claimed documents.")
    w("8. Scope and zones of a coder pair come from the primary method of the isolation level: `assembled`, or `nos4` at the block unit. The ladder step used the same convention.")
    w("9. Block form: at the block unit, the converter claims no extent. Each atom without a fixed answer gets the answer of the converter run before it.")
    w("10. The block form changes no atom of `nos4`. Version 1 applied the block form to all other outputs. This is a method change after the ladder step. Chapter 9 also gives the exact documents without the block form.")
    w("11. `oof_a1` has 19 `dev` documents (groups 1 to 3) and 15 `eval` documents (groups 4 and 5). The 70B outputs have 17 to 19 `dev` documents.")
    w("12. F1 with no boundary on both sides has no object. The script then gives no F1 for a coder pair. `compare_docs` gives 0.0 for a method.")
    w("13. A zone holds no atom with a fixed answer. The ladder check compares the zone count with fixed atoms, the definition of the ladder step.")
    w("")
    # ---------------------------------------------------------------- details
    w("## 9 Values for each isolation level")
    w("")
    for n, (L, r) in enumerate(L_.items(), 1):
        d = r["definition"]
        w(f"### 9.{n} {L}: {d['name']}")
        w("")
        w(f"Task kind: {r['task_kind']}. Primary method: `{r['primary_method']}`.")
        w("")
        w(f"Rules: map `{d['map']}`, scope `{d['scope']}`, zones {', '.join('`' + z + '`' for z in d['zones']) or 'none'}, "
          f"unit `{d['unit']}`, exact rule `{d['exact_rule']}`. Criterion changes in V2: {', '.join(r['criterion_changes']) or 'none'}.")
        w("")
        w("Reference reliability on the claimed group documents of `dev` and `eval`. First value: the first coder is the reference.")
        w("")
        w("| Pair | Class | Documents | Boundaries | F1 (symmetric) | Omission | Intrusion | Class error | Exact |")
        w("|---|---|---|---|---|---|---|---|---|")
        for pk, p in r["reference"]["pairs"].items():
            a = p["all"]
            pl = " and ".join(f"`{x}`" for x in pk.split("|"))
            if not a["documents"]:
                w(f"| {pl} | {p['class']} | 0 | – | – | – | – | – | – |")
                continue
            w(f"| {pl} | {p['class']} | {a['documents']} | {a['boundaries'][0]} | {fx(a['f1_sym'])} | "
              f"{fx(a['text_omission'][0], 4)}, {fx(a['text_omission'][1], 4)} | {fx(a['text_intrusion'][0], 4)} | "
              f"{fx(a['text_class_error'][0], 4)} | {a['exact'][0]}, {a['exact'][1]} |")
        for gk, glabel in (("dev", "`dev`"), ("eval_validation", "`eval` (validation)")):
            g = r["reference"]["ai_reference_vs_gold_set"][gk]
            if not g["documents"]:
                w(f"| gold set records and `ref41`, {glabel} | human review against the AI reference | 0 | – | – | – | – | – | – |")
                continue
            w(f"| gold set records and `ref41`, {glabel} | human review against the AI reference | {g['documents']} | "
              f"{g['boundaries'][0]} | {fx(g['f1_sym'])} | {fx(g['text_omission'][0], 4)}, {fx(g['text_omission'][1], 4)} | "
              f"{fx(g['text_intrusion'][0], 4)} | {fx(g['text_class_error'][0], 4)} | {g['exact'][0]}, {g['exact'][1]} |")
        w("")
        blk = d["unit"] == "block"
        w("Method values. Boundaries: correct, method, reference. Trivial: exact documents of 'role only' on the same scope."
          + (" Raw: exact documents without the block form." if blk else ""))
        w("")
        w("| Method | Split | Claimed documents | Text coverage | Boundaries | F1 (lower bound) | Omission (documents) | Intrusion | Class error | Exact (lower bound) | Trivial |"
          + (" Raw |" if blk else "") + " V1 | V2 | V3 |")
        w("|---|---|---|---|---|---|---|---|---|---|---|" + ("---|" if blk else "") + "---|---|---|")
        for mid, row in r["methods"].items():
            for split in ("dev", "eval"):
                m = row.get(split)
                if not m:
                    continue
                if not m["documents"]:
                    w(f"| `{mid}` | `{split}` | 0 of {m['documents_available']} | – | – | – | – | – | – | – | – |"
                      + (" – |" if blk else "") + " – | – | – |")
                    continue
                v = [verdict(m["gate"][k]) for k in ("V1", "V2", "V3")]
                bi = f"; block {m['documents_with_block_intrusion']}" if blk else ""
                raw = f" {m['without_block_form']['exact']} |" if blk else ""
                w(f"| `{mid}` | `{split}` | {m['documents']} of {m['documents_available']} | {fx(m['coverage_ref_text'], 2)} | "
                  f"{m['correct']}, {m['boundaries_hyp']}, {m['boundaries_ref']} | {fx(m['labelled_f1'])} ({fx(m['labelled_f1_lower'])}) | "
                  f"{fx(m['text_omission'], 4)} ({m['documents_with_omission']}) | {fx(m['text_intrusion'], 3)}{bi} | "
                  f"{fx(m['text_class_error'], 3)} | {m['exact']} ({fx(m['exact_lower'])}) | {m['trivial_role_same_scope']['exact']} |"
                  f"{raw} {v[0]} | {v[1]} | {v[2]} |")
        w("")
        mid = r["primary_method"]
        row = r["methods"][mid]
        w(f"Margins of the primary method `{mid}` to the limits of criteria version 3.1, with the reference limit:")
        w("")
        w("| Criterion | Limit | Reference limit (blind X and Y) | Rule 2.3 conflict | `dev` value (margin) | `eval` value (margin, validation) |")
        w("|---|---|---|---|---|---|")
        rl = r["reference"]["reference_limit"]
        conf = r["reference"]["process_rule_2_3"]
        for cid in ("G3a.5", "G3a.6", "G3a.6b", "G3a.9"):
            for key, (op, lim) in LIMITS[cid].items():
                if f"{cid} {key}" not in conf:
                    continue
                cells = []
                for split in ("dev", "eval"):
                    m = row.get(split)
                    if not m or not m["documents"]:
                        cells.append("–")
                        continue
                    mg, _ = _cmp(m.get(key), op, lim)
                    cells.append(f"{fx(m.get(key), 4)} ({fx(mg, 4)})")
                c = conf[f"{cid} {key}"]["conflict"]
                w(f"| {cid} `{key}` | {'≥' if op == '>=' else '≤'} {lim} | {fx(rl.get(key), 4)} | "
                  f"{'no object' if c is None else ('yes' if c else 'no')} | {cells[0]} | {cells[1]} |")
        w("")
    w("## 10 Files")
    w("")
    w("| File | Content |")
    w("|---|---|")
    w("| `src/m03_ladder.py` | Script of this step: guard, checks, isolation levels, measurement, this report |")
    w("| `daten/iso/ladder/results.json` | All values: reference pairs, methods, margins, verdicts, checks, input hashes |")
    w("| `daten/iso/ladder/results.md` | This file |")
    w("")
    return "\n".join(lines) + "\n"


def pass_facts(res: dict, L: str, mid: str) -> list[str]:
    """Facts about one method that meets V2 on both splits (generated from the values)."""
    r = res["levels"][L]
    lv = r["definition"]
    out = []
    dev, ev = r["methods"][mid]["dev"], r["methods"][mid]["eval"]
    canon = r["methods"][lv["canonical"]]
    if mid != lv["canonical"]:
        out.append(f"The ladder names `{lv['canonical']}` as the method of {L}. `{lv['canonical']}` gets "
                   f"{canon['dev']['exact']} of {canon['dev']['documents']} on `dev` and "
                   f"{canon['eval']['exact']} of {canon['eval']['documents']} on `eval`.")
    if lv["unit"] == "block" and mid != "nos4":
        out.append(f"The values of `{mid}` use the block form that version 1 of the step Measure applied. The ladder defines it only for `nos4`. Without the block form, "
                   f"`{mid}` gets {dev['without_block_form']['exact']} of {dev['without_block_form']['documents']} on `dev`.")
    need = -(-4 * dev["documents"] // 5)
    out.append(f"On `dev`, the limit 0.80 needs {need} exact documents of {dev['documents']}. "
               f"The method has {dev['exact']}. The Jeffreys lower bound is {fx(dev['exact_lower'])}.")
    out.append(f"The `dev` value is in-sample. The `eval` value is a validation value with {ev['documents']} claimed documents.")
    out.append(f"The method claims {dev['documents']} of {dev['documents_available']} `dev` documents. "
               f"The primary method claims {canon['dev']['documents']}. The scope rule reads the role of the converter answers.")
    if mid != lv["canonical"]:
        cm, mm = set(canon["dev"]["claimed_documents"]), set(dev["claimed_documents"])
        ce, me = set(canon["dev"]["exact_documents"]), set(dev["exact_documents"])
        oc, om_ = cm - mm, mm - cm
        if oc:
            out.append(f"On `dev`, {len(oc)} documents are claimed only by `{lv['canonical']}`. Of these, "
                       f"{len(oc & ce)} are exact for `{lv['canonical']}`.")
            why = Counter((role(ANS[mid]["dev"][d]), SIG[d]["s1_rule"]) for d in oc)
            out.append("Role of the `" + mid + "` answers and S1 rule role of these documents: "
                       + "; ".join(f"{a} and {b}, {n} documents" for (a, b), n in why.most_common()) + ".")
        if om_:
            out.append(f"On `dev`, {len(om_)} documents are claimed only by `{mid}`. Of these, {len(om_ & me)} are exact for `{mid}`.")
        both = cm & mm
        out.append(f"Documents that both claim: {len(both)}. Exact only for `{lv['canonical']}`: {len((both & ce) - me)}. "
                   f"Exact only for `{mid}`: {len((both & me) - ce)}.")
    v1 = dev["gate"]["V1"]
    if v1.get("failed"):
        out.append("V1 is not met on `dev`: " + ", ".join(v1["failed"]) + ".")
    return out


def primary_facts(res: dict) -> list[str]:
    """Facts about the primary methods (version 2), generated from the values."""
    out = []
    pm = res["summary"]["primary_met_dev_and_eval"]
    for kind in ("V1", "V2", "V3"):
        hits = pm[kind]
        out.append(f"{kind}: " + ("no isolation level meets all limits on `dev` and on `eval` with the primary method."
                                  if not hits else "met on both splits at " + ", ".join(h["level"] for h in hits) + "."))
    for L, p in res["summary"]["primary"].items():
        dv, ev = p["dev"], p["eval"]
        if ev["V2"] and dv["V2_failed"] == ["G3a.9"]:
            out.append(f"{L} `{p['method']}` misses V2 on `dev` only by G3a.9: {dv['exact']} of {dv['documents']}, "
                       f"short by {-dv['spare_documents']} {'document' if dv['spare_documents'] == -1 else 'documents'}. `eval` (validation): {ev['exact']} of {ev['documents']}.")
            out.append(f"{L} `{p['method']}` with the consensus reference: `dev` {dv['sensitivity_consensus_XY']['exact']} "
                       f"of {dv['sensitivity_consensus_XY']['documents']}, `eval` {ev['sensitivity_consensus_XY']['exact']} "
                       f"of {ev['sensitivity_consensus_XY']['documents']}.")
    return out


def rule23_facts(res: dict) -> list[str]:
    out = []
    by = {}
    for L, r in res["levels"].items():
        for k, v in r["reference"]["process_rule_2_3"].items():
            if v["conflict"]:
                by.setdefault(k, []).append(L)
    for k, Ls in by.items():
        cid, key = k.split()
        out.append(f"{cid} `{key}`: the limit is stricter than the blind pair at {', '.join(Ls)}.")
    out.append("The 0.917 of the native coders of group 7 (G3a.3) is known only at L0. This step did not calculate it again.")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-compare", action="store_true", help="skip the compare_docs check of each atom-unit value")
    args = ap.parse_args()
    res = run(compare=not args.no_compare)
    OUT_JSON.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    OUT_MD.write_text(write_md(res), encoding="utf-8")
    print("written", OUT_JSON.relative_to(ROOT), OUT_MD.relative_to(ROOT))
    for kind, hits in res["summary"]["met_dev_and_eval"].items():
        print(kind, [(h["level"], h["method"], h["dev_exact"], h["eval_exact"]) for h in hits])


if __name__ == "__main__":
    main()
