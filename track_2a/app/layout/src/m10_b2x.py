"""Gate GJ (status EXCEPTION), addendum B (B1-L) and addendum C (PROPOSED): B2 forms for one document, the
analysis of the dev switch boundaries, and the dev table of the forms.

Written in English to the STE rules (ASD-STE100, Issue 9). Actor: workflow sub-agent (Claude Opus 5.5), stream D1,
for the main agent. No human checked this file. This file changes no existing file. It imports the frozen
functions of src/m10_design.py and src/m10_score.py. Status of all outputs: EXCEPTION (process rule 10), NOT
RELEASED. This file is an addition after the design freeze (criteria chapter 10.2 item 2).

1 Scope and seal
  Each command of this file reads dev material only. Before a file of a document is read, each document must be
  in the key dev of daten/gj/sets.json and src/m10_guard.py must allow it with the split dev only
  (m10_design.assert_fit_ids). This file never opens daten/gj/validation, a decision file or a states file.

2 B2 forms (function b2x_document)
  Input of each form: Q [n, 6], the calibrated block posterior of the 6 options of one document in reading order;
  the HMM (start, trans, prior) of m10_design.hmm_fit with the 10 states of m10_design.STATES.
  free, joint    Exactly the frozen design: m10_design.b2_document(Q, hmm, form, pd1). No other code path.
  The 3 new forms use the rule chain. Their inputs are the rule options and the certain blocks of the rule view
  (m10_design.rule_view; a block is certain if its (tier, option) is a certain pair of the tier table).
  Rule gap: a gap of m10_design.switch_gaps(rule options). This is the gap directly before the first block of
  the new author family in the rule output (criteria chapter 2.5 on the rule options).
  Switch transition at gap t: block t has a last text family S or R and block t + 1 has a text option of the
  other family (m10_design.SWITCH_PAIR).
  Emission of a new form: as the frozen design, max(Q, 1e-300) / prior. For a certain block, each state with
  another option than the rule option of the block has the emission 0. Thus the path and the marginals of a
  new form agree with the written labels of the certain blocks.
  switch_rule    A switch transition is permitted only at a rule gap. At each other gap its weight is 0.
  switch_soft    One strength value w of SOFT_GRID. The weight of a switch transition is multiplied by exp(w) at
                 a rule gap and by exp(-w) at each other gap.
  switch_anchor  At a rule gap only a switch transition is permitted. At each other gap no switch transition is
                 permitted. Thus the path has a switch at each rule gap and at no other gap.
  The transition weights are not normalized again (as the joint form of the frozen design). In each new form the
  posterior decides the option inside a family, the title and none blocks, and the family of a document without
  a rule gap.
  Outputs of each form: the Viterbi path (exact MAP path of the form), the block marginals [n, 6] and the switch
  probability of each gap [n - 1] by forward-backward, the log likelihood, and the written path. Written path:
  the path, with the rule option at each certain block (as the frozen design writes a certain block).

3 Strength value (function choose_strength; criteria chapter 5 item 5 applied to the strength)
  Only switch_soft has a strength value. For the held-out fold f, each value of SOFT_GRID is applied to the dev
  documents of the other folds. A document of fold g gets the HMM of the folds without f and g and its own
  out-of-fold posterior. Order of the values: the higher count of switch documents exact, then the higher count
  of L9 exact documents, then the higher 6-option accuracy on the non-certain blocks, then the smaller value.
  The first value in this order is applied to fold f with the HMM of the folds without f. The value for a final
  model uses the same order on the out-of-fold results of all dev documents.

4 Dev table (function forms_table; command dev-heads) and selection rule (function select_form; addendum C)
  For each form, on the out-of-fold written paths of all dev documents: the 6-option accuracy on the non-certain
  blocks; L9 exact documents, switch documents exact (key switch_sr) and labelled boundary F1 on all documents
  (no abstention) through m10_score.measure_level; the written switch boundaries that are correct. The rule row:
  the plain rule output of daten/gj/rules through m10_score.load_answer_set (as src/m10_validation_run.py).
  Selection rule: a form is permitted if its count of switch documents exact is not lower than the count of the
  rules minus 1 and its count of L9 exact documents is not lower than the count of the rules minus 1. Among the
  permitted forms, the form with the highest accuracy wins; each form with an accuracy of 0.005 or less below
  the highest value is equal to it, and of these the first form in the order of FORMS wins. If no form is
  permitted: the forms with the highest count of switch documents exact, then the same accuracy rule.

5 Order of the records (GJ.2)
  The commands analysis and dev-heads write the SHA-256 of this file into their run record
  (<out>/<name>_run.json) before they calculate the first value.

6 Commands (from the project folder; one command on one line)
  uv run --offline --frozen --no-sync python src/m10_b2x.py analysis
  uv run --offline --frozen --no-sync python src/m10_b2x.py dev-heads
  Check script: uv run --offline --frozen --no-sync python src/m10_b2x_test.py
  Outputs: daten/gj/design_lora/dev_switch_analysis.json and .md; daten/gj/design_lora/b2_forms_dev_heads.json
  and .md. A command refuses an output file that exists, unless --replace is given.
"""

from __future__ import annotations

import argparse
import datetime as dt
import math
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m10_design as md  # noqa: E402  (frozen design functions; not changed)

VERSION = "m10-b2x-1"
SCRIPT = Path(__file__).resolve()
OUT = md.GJ / "design_lora"
STATUS = md.STATUS
FROZEN_FORMS = ("free", "joint")
NEW_FORMS = ("switch_rule", "switch_soft", "switch_anchor")
FORMS = FROZEN_FORMS + NEW_FORMS                       # the order of the selection rule
SOFT_GRID = (1.0, 2.0, 4.0, 8.0)                       # strength values of switch_soft
STRENGTH_GRID = {"switch_soft": SOFT_GRID}
ENTRY_MARGIN = 1                                       # "not lower than the count of the rules minus 1"
TIE_ACCURACY = 0.005
SHORT_CHARS = 60                                       # a short block has fewer characters (analysis only)
NS = len(md.STATES)
TEXT_STATE = np.array([o in md.FAMILY for o, _ in md.STATES])


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


# ---------------------------------------------------------------- forms (chapter 2)

def rule_gaps(rule_options) -> list[int]:
    """The rule gaps of a document: gap t is the gap after block t (0-based)."""
    return md.switch_gaps(list(rule_options))


def certain_mask(rule_options, rule_tiers, certain_pairs) -> np.ndarray:
    """True for each block whose (tier, option) of the rule view is a certain pair of the tier table."""
    cp = {tuple(x) for x in certain_pairs}
    return np.array([(t, o) in cp for o, t in zip(rule_options, rule_tiers, strict=True)], dtype=bool)


def gap_weights(form: str, strength: float | None) -> tuple[np.ndarray, np.ndarray]:
    """(factor at a rule gap, factor at each other gap) [10, 10] for the transition weights of a new form."""
    sp = md.SWITCH_PAIR
    one = np.ones((NS, NS))
    if form == "switch_rule":
        return one, np.where(sp, 0.0, 1.0)
    if form == "switch_anchor":
        return np.where(sp, 1.0, 0.0), np.where(sp, 0.0, 1.0)
    if form == "switch_soft":
        if strength is None or not (float(strength) >= 0.0 and math.isfinite(float(strength))):
            raise ValueError("switch_soft needs one finite strength value of 0 or more")
        w = float(strength)
        return np.where(sp, math.exp(w), 1.0), np.where(sp, math.exp(-w), 1.0)
    raise ValueError(f"{form!r} is not a new form")


def emissions(Q: np.ndarray, prior: np.ndarray, rule_options=None, certain=None) -> np.ndarray:
    """E [n, 10]: the frozen emission; for a certain block, 0 for each state with another option."""
    E = np.maximum(np.asarray(Q, dtype=np.float64), md.P_FLOOR)[:, md.S_OPT] / np.asarray(prior)[md.S_OPT]
    if certain is not None and rule_options is not None:
        for t in np.flatnonzero(np.asarray(certain, dtype=bool)):
            E[t] = np.where(md.S_OPT == md.OPTIONS.index(rule_options[t]), E[t], 0.0)
    return E


def forward_backward_gaps(E: np.ndarray, start: np.ndarray, trans_of_gap) -> dict:
    """Scaled forward-backward with one transition matrix for each gap. trans_of_gap(t) [10, 10] is the weight
    matrix of the gap after block t. Returns gamma [n, 10], switch [n - 1] and the log likelihood."""
    n = E.shape[0]
    bad = {"gamma": np.zeros((n, NS)), "switch": np.zeros(max(n - 1, 0)), "loglik": -math.inf}
    alpha, c = np.zeros((n, NS)), np.zeros(n)
    a = start * E[0]
    c[0] = a.sum()
    if not c[0] > 0:
        return bad
    alpha[0] = a / c[0]
    for t in range(1, n):
        a = (alpha[t - 1] @ trans_of_gap(t - 1)) * E[t]
        c[t] = a.sum()
        if not c[t] > 0:
            return bad
        alpha[t] = a / c[t]
    beta = np.ones((n, NS))
    for t in range(n - 2, -1, -1):
        beta[t] = trans_of_gap(t) @ (E[t + 1] * beta[t + 1]) / c[t + 1]
    gamma = alpha * beta
    gamma /= gamma.sum(1, keepdims=True)
    sw = np.zeros(max(n - 1, 0))
    for t in range(n - 1):
        sw[t] = float(alpha[t] @ (trans_of_gap(t) * md.SWITCH_PAIR) @ (E[t + 1] * beta[t + 1])) / c[t + 1]
    return {"gamma": gamma, "switch": np.clip(sw, 0.0, 1.0), "loglik": float(np.log(c).sum())}


def viterbi_gaps(logE: np.ndarray, logstart: np.ndarray, logtrans_of_gap) -> tuple[list[int], float]:
    """Exact MAP state path with one log transition matrix for each gap."""
    n = logE.shape[0]
    delta = logstart + logE[0]
    back = np.zeros((n, NS), dtype=np.int64)
    for t in range(1, n):
        cand = delta[:, None] + logtrans_of_gap(t - 1)
        back[t] = cand.argmax(0)
        delta = cand.max(0) + logE[t]
    s = int(delta.argmax())
    score = float(delta[s])
    path = [s]
    for t in range(n - 1, 0, -1):
        s = int(back[t, s])
        path.append(s)
    return path[::-1], score


def written_path(path, rule_options=None, certain=None) -> list[str]:
    """The path with the rule option at each certain block (as the frozen design writes a certain block)."""
    if certain is None or rule_options is None:
        return list(path)
    return [rule_options[j] if certain[j] else o for j, o in enumerate(path)]


def b2x_document(Q: np.ndarray, hmm: dict, form: str, pd1: np.ndarray | None = None, rule_options=None,
                 certain=None, strength: float | None = None) -> dict:
    """One B2 form on one document (chapter 2).

    Q [n, 6]: calibrated block posteriors (options in the order of m10_design.OPTIONS). hmm: dict with start
    [10], trans [10, 10] and prior [6]. pd1 [4]: calibrated D1 posterior, only for the form joint.
    rule_options [n], certain [n] (bool): the rule view; needed for a new form, optional for free and joint.
    strength: one value of SOFT_GRID, only for switch_soft.
    Returns: form, strength, path (n options, Viterbi), written (n options: the path with the rule option at
    each certain block), marg [n, 6], switch [n - 1] (switch probability of each gap), loglik, weights (joint:
    the 4 D1 weights; else None), rule_gaps (list or None) and switch_gaps (the switch gaps of the written path).
    """
    if form not in FORMS:
        raise ValueError(f"unknown B2 form {form!r}")
    Q = np.asarray(Q, dtype=np.float64)
    if Q.ndim != 2 or Q.shape[1] != len(md.OPTIONS) or Q.shape[0] == 0:
        raise ValueError("Q must be [n, 6] with n > 0")
    n = Q.shape[0]
    if rule_options is not None:
        rule_options = list(rule_options)
        if len(rule_options) != n or any(o not in md.OPTIONS for o in rule_options):
            raise ValueError("rule_options must give one of the 6 options for each block")
    if certain is not None:
        certain = np.asarray(certain, dtype=bool)
        if certain.shape != (n,) or rule_options is None:
            raise ValueError("certain must be [n] and needs rule_options")
    gaps = None if rule_options is None else rule_gaps(rule_options)
    if form in FROZEN_FORMS:
        if strength is not None:
            raise ValueError(f"the form {form} has no strength value")
        r = md.b2_document(Q, hmm, form, pd1)
        path, marg, sw, ll, w = list(r["path"]), r["marg"], r["switch"], r["loglik"], r["weights"]
    else:
        if rule_options is None or certain is None:
            raise ValueError(f"the form {form} needs rule_options and certain")
        if form != "switch_soft" and strength is not None:
            raise ValueError(f"the form {form} has no strength value")
        at_rule, at_other = gap_weights(form, strength)
        trans = np.asarray(hmm["trans"], dtype=np.float64)
        t_rule, t_other = trans * at_rule, trans * at_other
        lt_rule, lt_other = md._log0(t_rule), md._log0(t_other)
        is_rule = np.zeros(max(n - 1, 0), dtype=bool)
        is_rule[gaps] = True
        E = emissions(Q, hmm["prior"], rule_options, certain)
        fb = forward_backward_gaps(E, np.asarray(hmm["start"]), lambda t: t_rule if is_rule[t] else t_other)
        sp, score = viterbi_gaps(md._log0(E), md._log0(np.asarray(hmm["start"])),
                                 lambda t: lt_rule if is_rule[t] else lt_other)
        if not (math.isfinite(fb["loglik"]) and math.isfinite(score)):
            raise ValueError(f"B2 form {form}: no path with a weight above 0")
        path = [md.OPTIONS[md.S_OPT[s]] for s in sp]
        marg, sw, ll, w = fb["gamma"] @ md.OPT_OF_STATE, fb["switch"], fb["loglik"], None
    wr = written_path(path, rule_options, certain)
    return {"form": form, "strength": None if strength is None else float(strength), "path": path, "written": wr,
            "marg": marg, "switch": sw, "loglik": ll, "weights": w, "rule_gaps": gaps,
            "switch_gaps": md.switch_gaps(wr)}


# ---------------------------------------------------------------- selection rule (chapter 4; addendum C)

def select_form(rows: dict, rules: dict, order=FORMS) -> dict:
    """The selection rule of addendum C. rows: {form: {"switch_exact", "l9_exact", "accuracy_non_certain"}} with
    dev out-of-fold values; rules: {"switch_exact", "l9_exact"} of the rule output on the same documents.
    Returns the form, the permitted forms and the reason."""
    forms = [f for f in order if f in rows]
    if not forms:
        raise ValueError("no form")
    ok = [f for f in forms if rows[f]["switch_exact"] >= rules["switch_exact"] - ENTRY_MARGIN
          and rows[f]["l9_exact"] >= rules["l9_exact"] - ENTRY_MARGIN]
    if ok:
        pool, reason = ok, "permitted forms"
    else:
        top = max(rows[f]["switch_exact"] for f in forms)
        pool, reason = [f for f in forms if rows[f]["switch_exact"] == top], "no form is permitted; highest switch count"
    best = max(rows[f]["accuracy_non_certain"] for f in pool)
    equal = [f for f in pool if best - rows[f]["accuracy_non_certain"] <= TIE_ACCURACY + 1e-9]
    return {"form": equal[0], "permitted": ok, "pool": pool, "equal_within_0.005": equal, "reason": reason,
            "highest_accuracy": best, "limits": {"switch_exact": rules["switch_exact"] - ENTRY_MARGIN,
                                                "l9_exact": rules["l9_exact"] - ENTRY_MARGIN}}


# ---------------------------------------------------------------- dev data (chapter 1)

@dataclass
class Dev:
    ids: list[str]
    fold: dict[str, int]
    refs: dict[str, list[str]]
    ref_d1: dict[str, str]
    rules: dict[str, dict]
    view: dict[str, tuple[list[str], list[str]]]      # rule view (options, tiers) of each document
    certain: dict[str, np.ndarray]
    certain_pairs: list
    inputs: dict = field(default_factory=dict)


def load_dev(pd1: dict[str, np.ndarray], design_dir: Path = md.DESIGN) -> Dev:
    """The dev documents with their folds, labels, rule views and certain blocks. pd1: {doc: D1 posterior [4]};
    a document with the S1 rule id R1 gets the rule variant of the highest D1 option (as the frozen design).
    The guard runs before a file of a document is read (GJ.10)."""
    sets = md.load_sets()
    ids = sorted({str(d) for d in sets["dev"]}, key=int)
    md.assert_fit_ids(ids, sets)
    folds = md.read_json(Path(design_dir) / "folds.json")
    again = md.make_folds(ids, md.body_keys(ids))
    if again["fold_of_doc"] != folds["fold_of_doc"]:
        raise ValueError("folds.json of the design differs from the fold rule of criteria chapter 5")
    tt = md.read_json(Path(design_dir) / "tier_table.json")
    labels = {d: md.load_label(d) for d in ids}
    rules = {d: md.load_rule(d) for d in ids}
    refs = {d: [b["option"] for b in labels[d]["blocks"]] for d in ids}
    view, cert = {}, {}
    for d in ids:
        if [b["block"] for b in rules[d]["blocks"]] != [b["block"] for b in labels[d]["blocks"]]:
            raise ValueError(f"{d}: the rule file and the label file have other blocks")
        r1 = bool(rules[d]["document"]["d1"].get("needs_apertus"))
        view[d] = md.rule_view(rules[d], md.D1_OPTIONS[int(np.argmax(pd1[d]))] if r1 else None)
        cert[d] = certain_mask(view[d][0], view[d][1], tt["certain_pairs"])
    inputs = {md.rel(md.SETS): md.sha256_file(md.SETS),
              md.rel(Path(design_dir) / "folds.json"): md.sha256_file(Path(design_dir) / "folds.json"),
              md.rel(Path(design_dir) / "tier_table.json"): md.sha256_file(Path(design_dir) / "tier_table.json"),
              "labels_digest": md.digest_lines({md.rel(md.LABELS / f"{d}.json"): md.sha256_file(md.LABELS / f"{d}.json")
                                                for d in ids}),
              "rules_digest": md.digest_lines({md.rel(md.RULES / f"{d}.json"): md.sha256_file(md.RULES / f"{d}.json")
                                               for d in ids})}
    return Dev(ids, {d: int(folds["fold_of_doc"][d]) for d in ids}, refs, {d: labels[d]["d1"] for d in ids}, rules,
               view, cert, tt["certain_pairs"], inputs)


def load_head_oof(design_dir: Path = md.DESIGN) -> tuple[dict, dict, dict]:
    """The stored out-of-fold posteriors of the B1 head and the D1 head of the dev design: ({doc: Q [n, 6]},
    {doc: pd1 [4]}, info). The stored Viterbi path of the frozen free form is in info["viterbi"]."""
    sets = md.load_sets()
    md.assert_fit_ids([str(d) for d in sets["dev"]], sets)
    pb, p2, pd = (Path(design_dir) / "oof" / f"{n}_oof.npz" for n in ("b1", "b2", "d1"))
    with np.load(pb, allow_pickle=False) as z:
        ids = [str(x) for x in z["doc_ids"]]
        bdoc, Qall, fold_blk = np.array(z["block_doc"]), np.array(z["probs_after_t"]), np.array(z["fold"])
    with np.load(p2, allow_pickle=False) as z:
        vit = [str(x) for x in z["viterbi"]]
        mfree, mjoint, form, T2 = np.array(z["marg_free"]), np.array(z["marg_joint"]), str(z["form"]), float(z["T2"])
    with np.load(pd, allow_pickle=False) as z:
        if [str(x) for x in z["doc_ids"]] != ids:
            raise ValueError("d1_oof.npz and b1_oof.npz have other documents")
        pd1all = np.array(z["probs_after_t"])
    if ids != sorted({str(d) for d in sets["dev"]}, key=int):
        raise ValueError("the stored out-of-fold values are not the dev documents of sets.json")
    Q, pd1, info = {}, {}, {"viterbi": {}, "marg_free": {}, "marg_joint": {}, "fold": {}, "form": form, "T2": T2}
    for i, d in enumerate(ids):
        m = bdoc == i
        Q[d], pd1[d] = Qall[m], pd1all[i]
        info["viterbi"][d] = [v for v, k in zip(vit, m) if k]
        info["marg_free"][d], info["marg_joint"][d] = mfree[m], mjoint[m]
        info["fold"][d] = int(fold_blk[m][0])
    info["files"] = {md.rel(p): md.sha256_file(p) for p in (pb, p2, pd)}
    return Q, pd1, info


def fold_hmms(dev: Dev) -> tuple[dict, dict]:
    """({f: HMM of the folds without f}, {(f, g): HMM of the folds without f and g}), fitted with
    m10_design.hmm_fit on the reference sequences (criteria chapter 5 items 5 and 11)."""
    fs = sorted(set(dev.fold.values()))
    one = {f: md.hmm_fit([dev.refs[d] for d in dev.ids if dev.fold[d] != f]) for f in fs}
    two = {(f, g): md.hmm_fit([dev.refs[d] for d in dev.ids if dev.fold[d] not in (f, g)])
           for f in fs for g in fs if f != g}
    return one, two


# ---------------------------------------------------------------- scores through src/m10_score.py

class Scorer:
    """L9 values through the functions of src/m10_score.py, as score_sets of src/m10_validation_run.py does:
    the document table, the atom reference with the pilot overrides, and measure_level on all documents."""

    def __init__(self, ids: list[str]):
        import m10_score as ms  # noqa: PLC0415  (frozen scorer; not changed)

        self.ms, self.ids = ms, list(ids)
        bodies = ms.parliaments(self.ids)
        split = {d: ms.split_of(d, bodies.get(d), allow_group7=False) for d in self.ids}
        if set(split.values()) != {"dev"}:
            raise ValueError("m10_score.split_of gives another split than dev")
        self.table = {d: ms.doc_entry(d) for d in self.ids}
        self.atom_ref, self.sources = {}, Counter()
        for d in self.ids:
            self.atom_ref[d], s, _ = ms.atom_reference(self.table[d], pilots=True)
            self.sources[s] += 1
        self.lv = ms.ladder()["level"]
        self.switch_docs = [d for d in self.ids if ms.switch_sr(self.atom_ref[d])]

    def atoms_of(self, d: str, options: list[str]) -> list[str]:
        e = self.table[d]
        return self.ms.expand(e, dict(zip(e.block_order, options, strict=True)))

    def exact(self, d: str, atoms: list[str]) -> bool:
        """L9 exact of one document (no abstention)."""
        r = self.ms.measure_level(self.lv, [d], {d: atoms}, {d: True}, self.atom_ref, self.table)
        return bool(r["per_document"][d]["exact"])

    def level(self, docs: list[str], atoms: dict) -> dict:
        r = self.ms.measure_level(self.lv, docs, atoms, {d: True for d in docs}, self.atom_ref, self.table)
        return {"documents": r["documents"], "l9_exact": r["exact"], "switch_documents": r["switch_sr"]["documents"],
                "switch_exact": r["switch_sr"]["exact"], "labelled_boundary_f1": md.r6(r["labelled_f1"]),
                "boundaries_ref": r["boundaries_ref"], "boundaries_method": r["boundaries_hyp"],
                "boundaries_correct": r["correct"], "text_intrusion": md.r6(r["text_intrusion"]),
                "exact_documents": r["exact_documents"], "switch_sr_documents": r["switch_sr_documents"]}

    def rules(self) -> tuple[dict, dict]:
        aset, shas = self.ms.load_answer_set("rules", md.RULES, self.ids, self.table)
        return {d: aset[d]["atoms"] for d in self.ids}, shas


def block_counts(dev: Dev, docs, written: dict) -> dict:
    """6-option counts of the written paths: non-certain blocks, all blocks, written switch boundaries."""
    c = Counter()
    for d in docs:
        ref, cm = dev.refs[d], dev.certain[d]
        for j, o in enumerate(written[d]):
            c["blocks"] += 1
            c["correct"] += o == ref[j]
            if not cm[j]:
                c["non_certain"] += 1
                c["non_certain_correct"] += o == ref[j]
        rg, wg = set(md.switch_gaps(ref)), md.switch_gaps(written[d])
        c["switch_ref"] += len(rg)
        c["switch_written"] += len(wg)
        c["switch_written_correct"] += sum(1 for t in wg if t in rg)
    return dict(c)


def summary(dev: Dev, sc: Scorer, docs, written: dict) -> dict:
    c = block_counts(dev, docs, written)
    lv = sc.level(list(docs), {d: sc.atoms_of(d, written[d]) for d in docs})
    return {"documents": len(list(docs)), "non_certain_blocks": c.get("non_certain", 0),
            "non_certain_correct": c.get("non_certain_correct", 0),
            "accuracy_non_certain": md.r6(c.get("non_certain_correct", 0) / max(c.get("non_certain", 0), 1)),
            "blocks": c.get("blocks", 0), "accuracy_all_blocks": md.r6(c.get("correct", 0) / max(c.get("blocks", 0), 1)),
            "l9_exact": lv["l9_exact"], "switch_documents": lv["switch_documents"], "switch_exact": lv["switch_exact"],
            "labelled_boundary_f1": lv["labelled_boundary_f1"], "boundaries_ref": lv["boundaries_ref"],
            "boundaries_method": lv["boundaries_method"], "boundaries_correct": lv["boundaries_correct"],
            "text_intrusion": lv["text_intrusion"],
            "written_switch_boundaries": c.get("switch_written", 0),
            "written_switch_boundaries_correct": c.get("switch_written_correct", 0),
            "reference_switch_boundaries": c.get("switch_ref", 0)}


# ---------------------------------------------------------------- strength and dev table (chapters 3 and 4)

def strength_key(row: dict, value: float) -> tuple:
    """The order of chapter 3: the first value of sorted(..., key) wins."""
    return (-row["switch_exact"], -row["l9_exact"], -row["accuracy_non_certain_unrounded"], value)


def _fast_row(dev: Dev, sc: Scorer, docs, written: dict, exact: dict) -> dict:
    c = block_counts(dev, docs, written)
    sw = set(sc.switch_docs)
    return {"switch_exact": sum(1 for d in docs if exact[d] and d in sw), "l9_exact": sum(1 for d in docs if exact[d]),
            "accuracy_non_certain_unrounded": c.get("non_certain_correct", 0) / max(c.get("non_certain", 0), 1),
            "accuracy_non_certain": md.r6(c.get("non_certain_correct", 0) / max(c.get("non_certain", 0), 1)),
            "documents": len(list(docs))}


def choose_strength(dev: Dev, sc: Scorer, Q: dict, form: str, hmm2: dict, hmm1: dict) -> dict:
    """Chapter 3. Returns {"by_fold": {f: value}, "final": value, "tables": ...} for a form with a strength grid."""
    grid = STRENGTH_GRID[form]
    fs = sorted(set(dev.fold.values()))
    cache: dict[tuple, tuple[list[str], bool]] = {}

    def run(d: str, hmm_key, value: float):
        k = (d, hmm_key, value)
        if k not in cache:
            h = hmm1[hmm_key] if isinstance(hmm_key, int) else hmm2[hmm_key]
            w = b2x_document(Q[d], h, form, None, dev.view[d][0], dev.certain[d], value)["written"]
            cache[k] = (w, sc.exact(d, sc.atoms_of(d, w)))
        return cache[k]

    by_fold, tables = {}, {}
    for f in fs:
        train = [d for d in dev.ids if dev.fold[d] != f]
        rows = {}
        for v in grid:
            res = {d: run(d, (f, dev.fold[d]), v) for d in train}
            rows[v] = _fast_row(dev, sc, train, {d: r[0] for d, r in res.items()}, {d: r[1] for d, r in res.items()})
        by_fold[f] = sorted(grid, key=lambda v: strength_key(rows[v], v))[0]
        tables[str(f)] = {str(v): {k: x for k, x in rows[v].items() if k != "accuracy_non_certain_unrounded"}
                          for v in grid}
    rows = {}
    for v in grid:
        res = {d: run(d, dev.fold[d], v) for d in dev.ids}
        rows[v] = _fast_row(dev, sc, dev.ids, {d: r[0] for d, r in res.items()}, {d: r[1] for d, r in res.items()})
    final = sorted(grid, key=lambda v: strength_key(rows[v], v))[0]
    tables["all_dev_out_of_fold"] = {str(v): {k: x for k, x in rows[v].items() if k != "accuracy_non_certain_unrounded"}
                                     for v in grid}
    return {"grid": list(grid), "by_fold": {str(f): by_fold[f] for f in fs}, "final": final,
            "training_fold_tables": tables,
            "rule": "higher switch documents exact, then higher L9 exact documents, then higher 6-option accuracy "
                    "on the non-certain blocks, then the smaller value"}


def forms_table(Q: dict, pd1: dict, design_dir: Path = md.DESIGN, forms=FORMS, log=None) -> dict:
    """Chapter 4: the dev table of the forms for one set of out-of-fold posteriors.

    Q: {doc: [n, 6]} calibrated out-of-fold block posteriors of all dev documents. pd1: {doc: [4]} calibrated
    out-of-fold D1 posteriors (the joint form and the rule view of an R1 document use them).
    Returns {"forms": {form: row}, "rules": row, "selection": select_form(...), "strength": {...},
    "written": {form: {doc: options}}, "marginals": {form: {doc: [n, 6]}}, "switch": {form: {doc: [n - 1]}},
    "counts": {...}}. The caller writes the files."""
    log = log or (lambda m: None)
    dev = load_dev(pd1, design_dir)
    if set(Q) != set(dev.ids) or any(len(Q[d]) != len(dev.refs[d]) for d in dev.ids):
        raise ValueError("Q must give each block of each dev document")
    sc = Scorer(dev.ids)
    hmm1, hmm2 = fold_hmms(dev)
    out = {"forms": {}, "written": {}, "marginals": {}, "switch": {}, "strength": {}}
    for form in forms:
        st = None
        if form in STRENGTH_GRID:
            st = choose_strength(dev, sc, Q, form, hmm2, hmm1)
            out["strength"][form] = st
        wr, mg, sw = {}, {}, {}
        for d in dev.ids:
            f = dev.fold[d]
            r = b2x_document(Q[d], hmm1[f], form, pd1[d] if form == "joint" else None, dev.view[d][0], dev.certain[d],
                             None if st is None else st["by_fold"][str(f)])
            wr[d], mg[d], sw[d] = r["written"], r["marg"], r["switch"]
        row = summary(dev, sc, dev.ids, wr)
        y = np.array([md.OPTIONS.index(o) for d in dev.ids for o in dev.refs[d]])
        M = np.concatenate([mg[d] for d in dev.ids])
        nc = ~np.concatenate([dev.certain[d] for d in dev.ids])
        row["nll_block_marginals"] = md.r6(md.nll_probs(M, y))
        row["nll_block_marginals_non_certain"] = md.r6(md.nll_probs(M[nc], y[nc]))
        t2 = md.fit_temperature(np.log(np.maximum(M, md.P_FLOOR)), y)
        row["t2_pooled_information"] = md.r6(t2["T"])
        row["ece_block_marginals_after_t2_information"] = md.measures(md.temper(M, t2["T"]), y)["ece"]
        row["strength_by_fold"] = None if st is None else st["by_fold"]
        out["forms"][form], out["written"][form], out["marginals"][form], out["switch"][form] = row, wr, mg, sw
        log(f"{form}: accuracy {row['accuracy_non_certain']}, L9 exact {row['l9_exact']}, switch exact "
            f"{row['switch_exact']} of {row['switch_documents']}")
    rule_atoms, rule_shas = sc.rules()
    rule_opts = {d: dev.view[d][0] for d in dev.ids}
    rr = sc.level(dev.ids, rule_atoms)
    rc = block_counts(dev, dev.ids, rule_opts)
    out["rules"] = {"documents": len(dev.ids), "non_certain_blocks": rc["non_certain"],
                    "non_certain_correct": rc["non_certain_correct"],
                    "accuracy_non_certain": md.r6(rc["non_certain_correct"] / rc["non_certain"]),
                    "blocks": rc["blocks"], "accuracy_all_blocks": md.r6(rc["correct"] / rc["blocks"]),
                    "l9_exact": rr["l9_exact"], "switch_documents": rr["switch_documents"],
                    "switch_exact": rr["switch_exact"], "labelled_boundary_f1": rr["labelled_boundary_f1"],
                    "boundaries_ref": rr["boundaries_ref"], "boundaries_method": rr["boundaries_method"],
                    "boundaries_correct": rr["boundaries_correct"], "text_intrusion": rr["text_intrusion"],
                    "written_switch_boundaries": rc["switch_written"],
                    "written_switch_boundaries_correct": rc["switch_written_correct"],
                    "reference_switch_boundaries": rc["switch_ref"],
                    "source": "L9 values: the nos4 answers of daten/gj/rules (plain rule output, m10_score."
                              "load_answer_set); block values: the rule view",
                    "rule_files_sha256_canonical": sc.ms.canonical_sha(rule_shas)}
    out["selection"] = select_form(out["forms"], out["rules"], forms)
    out["counts"] = {"documents": len(dev.ids), "blocks": int(sum(len(dev.refs[d]) for d in dev.ids)),
                     "certain_blocks": int(sum(int(dev.certain[d].sum()) for d in dev.ids)),
                     "reference_sources": dict(sc.sources), "switch_documents_score": len(sc.switch_docs)}
    out["inputs"] = dev.inputs
    out["_dev"], out["_scorer"] = dev, sc
    return out


# ---------------------------------------------------------------- analysis of the dev switch boundaries (command analysis)

def match_gaps(ref_gaps: list[int], got: list[int]) -> tuple[list[dict], list[int]]:
    """Each reference gap gets the nearest method gap (exact ones first; a method gap is used one time).
    Returns the rows {ref, got, offset} (got None: missed) and the extra method gaps."""
    free = sorted(got)
    rows = {r: None for r in ref_gaps}
    for r in ref_gaps:
        if r in free:
            rows[r] = r
            free.remove(r)
    for r in ref_gaps:
        if rows[r] is None and free:
            g = min(free, key=lambda x: (abs(x - r), x))
            rows[r] = g
            free.remove(g)
    return [{"ref": r, "got": g, "offset": None if g is None else g - r} for r, g in rows.items()], free


def outcome(offset) -> str:
    if offset is None:
        return "missed"
    if offset == 0:
        return "exact"
    a = abs(offset)
    return f"shifted {'early' if offset < 0 else 'late'} by {'1' if a == 1 else '2' if a == 2 else '3 to 5' if a <= 5 else '6 or more'}"


def s2_record_gaps(rule: dict, block_ids: list[str]) -> list[int]:
    """The gaps before the block of the first atom of each S2 run after the first run, when the run changes
    between SPONSOR and EXECUTIVE (the S2 switch of the rule record, before the assembly)."""
    pos = {b: i for i, b in enumerate(block_ids)}
    out, last = [], None
    for atom, fam in rule["document"]["s2"]["runs"]:
        if fam not in ("SPONSOR", "EXECUTIVE"):
            continue
        b = pos.get(str(atom).split(".")[0])
        if last is not None and fam != last and b is not None and b > 0:
            out.append(b - 1)
        last = fam
    return out


def block_facts(doc: dict, j: int) -> dict:
    b = doc["blocks"][j]
    n = len(b.get("text") or "")
    return {"docling_label": b.get("docling_label"), "chars": n, "short": n < SHORT_CHARS}


def analysis(design_dir: Path = md.DESIGN) -> dict:
    """The tables of the dev switch analysis (chapter 6 of the output file names the definitions)."""
    Q, pd1, info = load_head_oof(design_dir)
    dev = load_dev(pd1, design_dir)
    hmm1, _ = fold_hmms(dev)
    sc = Scorer(dev.ids)
    docs = {d: md.load_doc(d) for d in dev.ids}
    res, per_doc = {}, []
    n_equal_path = 0
    for d in dev.ids:
        r = b2x_document(Q[d], hmm1[dev.fold[d]], "free", None, dev.view[d][0], dev.certain[d])
        n_equal_path += r["path"] == info["viterbi"][d]
        res[d] = r
    tot = Counter()
    switch_rows, cross, shift_blocks, extra_rows = [], Counter(), Counter(), []
    off_b2, off_rule, out_b2, out_rule = Counter(), Counter(), Counter(), Counter()
    first_block, s2_agree, missed_fam = Counter(), Counter(), Counter()
    rule_exact_atoms, _ = sc.rules()
    b2_l9 = {d: sc.exact(d, sc.atoms_of(d, res[d]["written"])) for d in dev.ids}
    rule_l9 = {d: sc.exact(d, rule_exact_atoms[d]) for d in dev.ids}
    for d in dev.ids:
        ref, wr, ro = dev.refs[d], res[d]["written"], dev.view[d][0]
        bids = [b["block"] for b in docs[d]["blocks"]]
        R, W, G = md.switch_gaps(ref), md.switch_gaps(wr), md.switch_gaps(ro)
        S2 = s2_record_gaps(dev.rules[d], bids)
        tot["reference_switches"] += len(R)
        tot["b2_written_switches"] += len(W)
        tot["rule_switches"] += len(G)
        tot["b2_written_correct"] += len(set(W) & set(R))
        tot["rule_correct"] += len(set(G) & set(R))
        tot["s2_record_switches"] += len(S2)
        tot["s2_record_correct"] += len(set(S2) & set(R))
        s2_agree["equal to the rule gaps" if sorted(S2) == sorted(G) else "not equal to the rule gaps"] += bool(S2 or G)
        tot["documents_with_reference_switch"] += bool(R)
        tot["documents_with_b2_switch"] += bool(W)
        tot["documents_with_rule_switch"] += bool(G)
        if not (R or W or G):
            continue
        mb, extra_b = match_gaps(R, W)
        mr, extra_r = match_gaps(R, G)
        for xb, xr in zip(mb, mr, strict=True):
            ob, orr = outcome(xb["offset"]), outcome(xr["offset"])
            out_b2[ob] += 1
            out_rule[orr] += 1
            off_b2[str(xb["offset"])] += 1
            off_rule[str(xr["offset"])] += 1
            cross[("exact" if ob == "exact" else "not exact", "exact" if orr == "exact" else "not exact")] += 1
            r = xb["ref"]
            fb = block_facts(docs[d], r + 1)
            q = Q[d][r + 1]
            row = {"doc_id": d, "reference_gap": r, "b2_gap": xb["got"], "b2_offset": xb["offset"], "b2_outcome": ob,
                   "rule_gap": xr["got"], "rule_offset": xr["offset"], "rule_outcome": orr,
                   "first_block_of_new_family": {**fb, "reference_option": ref[r + 1], "b2_option": wr[r + 1],
                                                 "rule_option": ro[r + 1],
                                                 "b1_posterior_of_reference_option": md.r6(q[md.OPTIONS.index(ref[r + 1])]),
                                                 "b1_top_option": md.OPTIONS[int(q.argmax())]},
                   "switch_probability_at_reference_gap": md.r6(res[d]["switch"][r]),
                   "switch_probability_within_2_gaps": md.r6(float(res[d]["switch"][max(0, r - 2): r + 3].sum())),
                   "blocks_before_reference_gap_none_or_title": 0}
            k = r
            while k >= 0 and ref[k] not in md.FAMILY:
                row["blocks_before_reference_gap_none_or_title"] += 1
                k -= 1
            if ob == "missed":
                fams = sorted({md.FAMILY[x] for x in wr if x in md.FAMILY})
                missed_fam["S only" if fams == ["S"] else "R only" if fams == ["R"] else "no text family"] += 1
            if ob != "exact":
                key = ob.split(" by ")[0]
                first_block[(key, fb["docling_label"], "short" if fb["short"] else "long",
                             f"B2 option {wr[r + 1]}", f"B1 top {md.OPTIONS[int(q.argmax())]}")] += 1
            if xb["offset"] not in (None, 0):
                lo, hi = (xb["got"] + 1, r) if xb["offset"] < 0 else (r + 1, xb["got"])
                span = []
                for j in range(lo, hi + 1):
                    f2 = block_facts(docs[d], j)
                    kind = "certain" if dev.certain[d][j] else "non-certain"
                    shift_blocks[("early" if xb["offset"] < 0 else "late", f"reference {ref[j]}", f"B2 {wr[j]}", kind,
                                  "short" if f2["short"] else "long")] += 1
                    span.append({"block": j, "reference": ref[j], "b2": wr[j], "rule": ro[j], "certain": bool(dev.certain[d][j]),
                                 **f2})
                row["blocks_between_the_two_gaps"] = span
                row["shift_in_non_certain_blocks"] = sum(1 for x in span if not x["certain"])
            switch_rows.append(row)
        for g in extra_b:
            j = g + 1
            run = 0
            fam = md.FAMILY.get(wr[j])
            while j + run < len(wr) and (wr[j + run] not in md.FAMILY or md.FAMILY[wr[j + run]] == fam):
                run += 1
            n_text = sum(1 for x in wr[j: j + run] if x in md.FAMILY)
            refc = Counter(ref[x] for x in range(j, j + run) if wr[x] in md.FAMILY)
            extra_rows.append({"doc_id": d, "b2_gap": g, "document_has_reference_switch": bool(R),
                               "reference_d1": dev.ref_d1[d], "head_d1": md.D1_OPTIONS[int(np.argmax(pd1[d]))],
                               "direction": f"to {fam}", "text_blocks_of_the_new_family": n_text,
                               "reference_options_of_these_blocks": dict(refc),
                               "switch_probability": md.r6(res[d]["switch"][g]),
                               "rule_has_a_switch_in_the_document": bool(G), **block_facts(docs[d], g + 1)})
        per_doc.append({"doc_id": d, "blocks": len(ref), "fold": dev.fold[d], "reference_d1": dev.ref_d1[d],
                        "reference_gaps": R, "b2_gaps": W, "rule_gaps": G, "s2_record_gaps": S2,
                        "b2_extra_gaps": extra_b, "rule_extra_gaps": extra_r,
                        "b2_l9_exact": b2_l9[d], "rule_l9_exact": rule_l9[d],
                        "switch_document_of_the_scorer": d in set(sc.switch_docs)})
    sw = set(sc.switch_docs)
    l9 = {"switch_documents_of_the_scorer": len(sw),
          "b2_exact": sum(1 for d in sw if b2_l9[d]), "rule_exact": sum(1 for d in sw if rule_l9[d]),
          "both_exact": sum(1 for d in sw if b2_l9[d] and rule_l9[d]),
          "rule_exact_b2_not": sum(1 for d in sw if rule_l9[d] and not b2_l9[d]),
          "b2_exact_rule_not": sum(1 for d in sw if b2_l9[d] and not rule_l9[d]),
          "none_exact": sum(1 for d in sw if not b2_l9[d] and not rule_l9[d]),
          "all_documents": len(dev.ids), "b2_exact_all": sum(b2_l9.values()), "rule_exact_all": sum(rule_l9.values())}
    ex_ns = [x for x in extra_rows if not x["document_has_reference_switch"]]
    ex_sw = [x for x in extra_rows if x["document_has_reference_switch"]]
    extra = {"b2_extra_switches": len(extra_rows),
             "in_documents_without_a_reference_switch": len(ex_ns),
             "documents_without_a_reference_switch_with_a_b2_switch": len({x["doc_id"] for x in ex_ns}),
             "of_these_documents_the_rules_have_a_switch": len({x["doc_id"] for x in ex_ns
                                                              if x["rule_has_a_switch_in_the_document"]}),
             "in_documents_with_a_reference_switch_(doubled)": len(ex_sw),
             "by_reference_d1": dict(Counter(x["reference_d1"] for x in ex_ns)),
             "by_head_d1": dict(Counter(x["head_d1"] for x in ex_ns)),
             "by_direction": dict(Counter(x["direction"] for x in ex_ns)),
             "reference_options_of_the_blocks_of_the_new_family": dict(sum((Counter(x["reference_options_of_these_blocks"])
                                                                           for x in ex_ns), Counter())),
             "text_blocks_of_the_new_family": {"1": sum(1 for x in ex_ns if x["text_blocks_of_the_new_family"] == 1),
                                               "2 to 5": sum(1 for x in ex_ns if 2 <= x["text_blocks_of_the_new_family"] <= 5),
                                               "6 or more": sum(1 for x in ex_ns if x["text_blocks_of_the_new_family"] >= 6)},
             "rule_extra_switches_in_documents_without_a_reference_switch": sum(
                 len(p["rule_gaps"]) for p in per_doc if not p["reference_gaps"]),
             "rows": extra_rows}
    return {"frozen_free_path_equal_to_the_stored_path": {"documents": len(dev.ids), "equal": n_equal_path},
            "totals": dict(tot), "outcome_of_each_reference_switch": {"b2": dict(out_b2), "rules": dict(out_rule)},
            "offset_of_each_reference_switch_in_blocks": {"b2": dict(off_b2), "rules": dict(off_rule),
                                                          "note": "method gap minus reference gap; None: missed"},
            "b2_against_rules_for_each_reference_switch": {f"b2 {a}, rules {b}": n for (a, b), n in sorted(cross.items())},
            "blocks_between_the_b2_gap_and_the_reference_gap": [
                {"direction": a, "reference": b, "b2": c, "tier": e, "length": f, "blocks": n}
                for (a, b, c, e, f), n in sorted(shift_blocks.items(), key=lambda x: -x[1])],
            "first_block_of_the_new_family_when_b2_is_not_exact": [
                {"b2_outcome": a, "docling_label": b, "length": c, "b2": e, "b1": f, "switches": n}
                for (a, b, c, e, f), n in sorted(first_block.items(), key=lambda x: -x[1])],
            "s2_record_gaps_against_rule_gaps": dict(s2_agree),
            "text_families_of_the_b2_path_when_it_misses_the_switch": dict(missed_fam),
            "l9_exact_through_the_scorer": l9, "extra_b2_switches": extra,
            "reference_switches": switch_rows, "documents": per_doc, "inputs": {**dev.inputs, **info["files"]}}


# ---------------------------------------------------------------- output files

def _table(head: list[str], rows: list[list]) -> list[str]:
    return ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(str(x) for x in r) + " |"
                                                                       for r in rows]


def analysis_markdown(a: dict, rec: dict) -> str:
    t, L = a["totals"], []
    add = L.append
    add("# Gate GJ: analysis of the switch boundaries of B2 on `dev` (out-of-fold values of the heads)")
    add("")
    add(f"Made {rec['finished']} (time from the clock) by `src/m10_b2x.py analysis` (SHA-256 `{rec['script']['sha256']}`). "
        "Status: EXCEPTION, NOT RELEASED. Actor: workflow sub-agent (Claude Opus 5.5), stream D1. No human checked this file.")
    add("")
    add("All values are `dev` out-of-fold values of the frozen design (B1 head, free form). They are information. "
        "No file of a validation document was read.")
    add("")
    add("## 1 Definitions")
    add("")
    add("1. Gap t is the gap after block t. Block numbers start at 0.")
    add("2. Reference gap: a switch boundary of the label file (criteria chapter 2.5).")
    add("3. B2 gap: a switch boundary of the written path of the frozen free form, with the rule option at each certain block.")
    add("4. Rule gap: a switch boundary of the rule options of the rule view.")
    add("5. Each reference gap gets the nearest method gap of its document. Exact gaps come first. A method gap is used one time.")
    add("6. Offset: method gap minus reference gap, in blocks. Early is a negative offset.")
    add(f"7. A short block has fewer than {SHORT_CHARS} characters.")
    add("")
    add("## 2 Totals")
    add("")
    e = a["frozen_free_path_equal_to_the_stored_path"]
    add(f"The path of this file is equal to the stored path of the design in {e['equal']} of {e['documents']} documents.")
    add("")
    L += _table(["Value", "Reference", "B2", "Rules"],
                [["Switch boundaries", t["reference_switches"], t["b2_written_switches"], t["rule_switches"]],
                 ["Correct switch boundaries", "–", t["b2_written_correct"], t["rule_correct"]],
                 ["Documents with a switch", t["documents_with_reference_switch"], t["documents_with_b2_switch"],
                  t["documents_with_rule_switch"]]])
    add("")
    add("## 3 Outcome of each reference switch")
    add("")
    keys = ["exact", "shifted early by 1", "shifted early by 2", "shifted early by 3 to 5", "shifted early by 6 or more",
            "shifted late by 1", "shifted late by 2", "shifted late by 3 to 5", "shifted late by 6 or more", "missed"]
    ob, orr = a["outcome_of_each_reference_switch"]["b2"], a["outcome_of_each_reference_switch"]["rules"]
    L += _table(["Outcome", "B2", "Rules"], [[k, ob.get(k, 0), orr.get(k, 0)] for k in keys])
    add("")
    add("B2 against the rules for each reference switch:")
    add("")
    L += _table(["Case", "Reference switches"], [[k, v] for k, v in a["b2_against_rules_for_each_reference_switch"].items()])
    add("")
    add("## 4 Blocks between the B2 gap and the reference gap (shifted switches)")
    add("")
    L += _table(["Direction", "Reference option", "B2 option", "Tier", "Length", "Blocks"],
                [[r["direction"], r["reference"].replace("reference ", ""), r["b2"].replace("B2 ", ""), r["tier"],
                  r["length"], r["blocks"]] for r in a["blocks_between_the_b2_gap_and_the_reference_gap"]])
    add("")
    add("First block of the new family in the reference, for each reference switch that B2 does not give exactly:")
    add("")
    L += _table(["B2 outcome", "Docling label", "Length", "B2 option", "B1 top option", "Switches"],
                [[r["b2_outcome"], r["docling_label"], r["length"], r["b2"].replace("B2 option ", ""),
                  r["b1"].replace("B1 top ", ""), r["switches"]]
                 for r in a["first_block_of_the_new_family_when_b2_is_not_exact"]])
    add("")
    add(f"Text families of the written B2 path of a document with a missed switch: "
        f"`{a['text_families_of_the_b2_path_when_it_misses_the_switch']}`.")
    add("")
    add("## 5 Extra switches of B2")
    add("")
    x = a["extra_b2_switches"]
    L += _table(["Value", "Count"],
                [["Extra B2 switches", x["b2_extra_switches"]],
                 ["In documents without a reference switch", x["in_documents_without_a_reference_switch"]],
                 ["Documents without a reference switch that have a B2 switch",
                  x["documents_without_a_reference_switch_with_a_b2_switch"]],
                 ["Of these documents, the rules have a switch", x["of_these_documents_the_rules_have_a_switch"]],
                 ["In documents with a reference switch (doubled)", x["in_documents_with_a_reference_switch_(doubled)"]],
                 ["Rule switches in documents without a reference switch",
                  x["rule_extra_switches_in_documents_without_a_reference_switch"]]])
    add("")
    add(f"Reference D1 of the document, for each extra B2 switch in a document without a reference switch: "
        f"`{x['by_reference_d1']}`. D1 of the head: `{x['by_head_d1']}`.")
    add("")
    add(f"Reference options of the text blocks of the new family: `{x['reference_options_of_the_blocks_of_the_new_family']}`. "
        f"Count of these text blocks for each extra switch: `{x['text_blocks_of_the_new_family']}`.")
    add("")
    add("## 6 L9 exact through the scorer (all documents, no abstention)")
    add("")
    q = a["l9_exact_through_the_scorer"]
    L += _table(["Value", "Count"],
                [["Switch documents of the scorer", q["switch_documents_of_the_scorer"]],
                 ["B2 exact", q["b2_exact"]], ["Rules exact", q["rule_exact"]], ["Both exact", q["both_exact"]],
                 ["Rules exact, B2 not", q["rule_exact_b2_not"]], ["B2 exact, rules not", q["b2_exact_rule_not"]],
                 ["None exact", q["none_exact"]],
                 [f"B2 exact on all {q['all_documents']} documents", q["b2_exact_all"]],
                 [f"Rules exact on all {q['all_documents']} documents", q["rule_exact_all"]]])
    add("")
    add("## 7 The S2 switch of the rule record")
    add("")
    add(f"S2 record gaps: {t['s2_record_switches']}; correct: {t['s2_record_correct']}. "
        f"Documents with a rule gap or an S2 record gap: `{a['s2_record_gaps_against_rule_gaps']}`.")
    add("")
    add("## 8 Findings")
    add("")
    for i, s in enumerate(rec["findings"], 1):
        add(f"{i}. {s}")
    add("")
    add("## 9 Each reference switch")
    add("")
    L += _table(["Document", "Reference gap", "B2 gap", "Rule gap", "First block: Docling label", "Characters",
                 "Reference", "B2", "B1 posterior of the reference option", "Switch probability at the reference gap",
                 "Within 2 gaps"],
                [[r["doc_id"], r["reference_gap"], r["b2_gap"], r["rule_gap"], r["first_block_of_new_family"]["docling_label"],
                  r["first_block_of_new_family"]["chars"], r["first_block_of_new_family"]["reference_option"],
                  r["first_block_of_new_family"]["b2_option"], r["first_block_of_new_family"]["b1_posterior_of_reference_option"],
                  r["switch_probability_at_reference_gap"], r["switch_probability_within_2_gaps"]]
                 for r in a["reference_switches"]])
    add("")
    add("## 10 Inputs")
    add("")
    L += _table(["File or digest", "SHA-256"], [[f"`{k}`", f"`{v}`"] for k, v in a["inputs"].items()])
    add("")
    return "\n".join(L)


def findings(a: dict) -> list[str]:
    t = a["totals"]
    ob, orr = a["outcome_of_each_reference_switch"]["b2"], a["outcome_of_each_reference_switch"]["rules"]
    near = sum(v for k, v in ob.items() if k.endswith("by 1") or k.endswith("by 2"))
    far = sum(v for k, v in ob.items() if k.startswith("shifted")) - near
    x, q = a["extra_b2_switches"], a["l9_exact_through_the_scorer"]
    cr = a["b2_against_rules_for_each_reference_switch"]
    rows = a["reference_switches"]
    nb = [r for r in rows if r["b2_outcome"] != "exact"]
    low = sum(1 for r in nb if r["first_block_of_new_family"]["b1_top_option"] != r["first_block_of_new_family"]["reference_option"])
    win = sum(1 for r in nb if r["switch_probability_within_2_gaps"] is not None and r["switch_probability_within_2_gaps"] >= 0.5)
    return [
        f"B2 writes {t['b2_written_switches']} switch boundaries; {t['b2_written_correct']} are correct. "
        f"The rules write {t['rule_switches']}; {t['rule_correct']} are correct.",
        f"Of the {t['reference_switches']} reference switches, B2 gives {ob.get('exact', 0)} exactly, "
        f"{near} with a shift of 1 or 2 blocks, {far} with a larger shift, and it misses {ob.get('missed', 0)}.",
        f"The rules give {orr.get('exact', 0)} exactly and miss {orr.get('missed', 0)}.",
        f"The rules mark the right gap for {cr.get('b2 not exact, rules exact', 0)} reference switches that B2 does not "
        f"give exactly. B2 is exact and the rules are not for {cr.get('b2 exact, rules not exact', 0)}.",
        f"For {low} of the {len(nb)} reference switches that B2 does not give exactly, the top option of B1 for the "
        "first block of the new family is not the reference option.",
        f"For {win} of these {len(nb)} switches, the switch probability within 2 gaps of the reference gap is 0.5 or more. "
        "Thus B2 often finds the area, but not the exact gap.",
        f"B2 writes a switch in {x['documents_without_a_reference_switch_with_a_b2_switch']} documents without a reference "
        f"switch. The rules write {x['rule_extra_switches_in_documents_without_a_reference_switch']} switches in such documents.",
        f"L9 exact on the {q['switch_documents_of_the_scorer']} switch documents of the scorer: B2 {q['b2_exact']}, "
        f"rules {q['rule_exact']}. On all {q['all_documents']} documents: B2 {q['b2_exact_all']}, rules {q['rule_exact_all']}.",
    ]


def heads_markdown(tab: dict, rec: dict) -> str:
    L = []
    add = L.append
    add("# Gate GJ: B2 forms on `dev` with the out-of-fold posteriors of the B1 head")
    add("")
    add(f"Made {rec['finished']} (time from the clock) by `src/m10_b2x.py dev-heads` (SHA-256 `{rec['script']['sha256']}`). "
        "Status: EXCEPTION, NOT RELEASED. Actor: workflow sub-agent (Claude Opus 5.5), stream D1. No human checked this file.")
    add("")
    add("All values are `dev` out-of-fold values (information). The posteriors are the stored values of the B1 head. "
        "They are not values of B1-L. No file of a validation document was read.")
    add("")
    add("## 1 Table")
    add("")
    c = tab["counts"]
    add(f"Units: {c['documents']} documents, {c['blocks']} blocks, {c['blocks'] - c['certain_blocks']} non-certain blocks, "
        f"{tab['rules']['switch_documents']} switch documents of the scorer. L9 values: all documents, no abstention.")
    add("")
    rows = []
    for name, r in [("rules", tab["rules"])] + list(tab["forms"].items()):
        rows.append([f"`{name}`", f"{r['accuracy_non_certain']:.4f}", r["non_certain_correct"], r["l9_exact"],
                     f"{r['switch_exact']} of {r['switch_documents']}", f"{r['labelled_boundary_f1']:.4f}",
                     f"{r['boundaries_correct']} / {r['boundaries_method']} / {r['boundaries_ref']}",
                     f"{r['written_switch_boundaries_correct']} of {r['written_switch_boundaries']}",
                     "–" if r.get("nll_block_marginals") is None else f"{r['nll_block_marginals']:.4f}",
                     "–" if not r.get("strength_by_fold") else ", ".join(f"{v:g}" for v in r["strength_by_fold"].values())])
    L += _table(["Form", "6-option accuracy, non-certain blocks", "Correct blocks", "L9 exact documents",
                 "Switch documents exact", "Labelled boundary F1", "Boundaries correct / method / reference",
                 "Written switch boundaries correct", "NLL of the block marginals", "Strength for folds 1 to 5"], rows)
    add("")
    add("## 2 Selection rule on these values (information; the rule applies to B1-L values only)")
    add("")
    s = tab["selection"]
    add(f"Limits: switch documents exact {s['limits']['switch_exact']} or more; L9 exact documents {s['limits']['l9_exact']} or more. "
        f"Permitted forms: `{s['permitted']}`. Forms within 0.005 of the highest accuracy: `{s['equal_within_0.005']}`. "
        f"Result on the head values: `{s['form']}` ({s['reason']}).")
    add("")
    add("## 3 Strength value of `switch_soft`")
    add("")
    for form, st in tab["strength"].items():
        add(f"Grid: `{st['grid']}`. Value for each held-out fold: `{st['by_fold']}`. Value on all `dev` out-of-fold results: "
            f"`{st['final']}`. Order: {st['rule']}.")
        add("")
        L += _table(["Value", "Switch documents exact", "L9 exact documents", "6-option accuracy, non-certain blocks"],
                    [[v, r["switch_exact"], r["l9_exact"], f"{r['accuracy_non_certain']:.4f}"]
                     for v, r in st["training_fold_tables"]["all_dev_out_of_fold"].items()])
        add("")
    add("## 4 Checks")
    add("")
    for k, v in rec["checks"].items():
        add(f"- {k}: {v}")
    add("")
    add("## 5 Limits")
    add("")
    for i, s2 in enumerate(rec["limits"], 1):
        add(f"{i}. {s2}")
    add("")
    add("## 6 Inputs")
    add("")
    L += _table(["File or digest", "SHA-256"], [[f"`{k}`", f"`{v}`"] for k, v in rec["inputs"].items()])
    add("")
    return "\n".join(L)


# ---------------------------------------------------------------- commands

def _start(name: str, out: Path, replace: bool) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    files = [out / f"{name}.json", out / f"{name}.md", out / f"{name}_run.json"]
    if not replace and any(p.exists() for p in files):
        raise SystemExit(f"{md.rel(out)}: an output of {name} exists; give --replace to write it again")
    import m10_score as ms  # noqa: PLC0415

    rec = {"version": VERSION, "status": STATUS, "command": name, "started": now(),
           "script": {"path": md.rel(SCRIPT), "sha256": md.sha256_file(SCRIPT)},
           "modules": {md.rel(md.SCRIPT): md.sha256_file(md.SCRIPT), md.rel(Path(ms.__file__)): md.sha256_file(ms.__file__),
                       md.rel(Path(md.guard.__file__)): md.sha256_file(md.guard.__file__)},
           "forms": list(FORMS), "strength_grid": {k: list(v) for k, v in STRENGTH_GRID.items()},
           "state": "the script SHA-256 is recorded; no value exists"}
    md.write_json(out / f"{name}_run.json", rec)
    print(f"{now()} script SHA-256 {rec['script']['sha256']} recorded in {md.rel(out / f'{name}_run.json')}", flush=True)
    return rec


def cmd_analysis(args) -> int:
    out = Path(args.out)
    rec = _start("dev_switch_analysis", out, args.replace)
    a = analysis()
    rec.update({"finished": now(), "state": "finished", "findings": findings(a), "inputs": a["inputs"]})
    body = {"version": VERSION, "status": STATUS, "made": rec["finished"], "script": rec["script"],
            "values": "dev out-of-fold values of the frozen design (information)", "findings": rec["findings"], **a}
    h1 = md.write_json(out / "dev_switch_analysis.json", body)
    (out / "dev_switch_analysis.md").write_text(analysis_markdown(a, rec), encoding="utf-8")
    rec["outputs"] = {md.rel(out / "dev_switch_analysis.json"): h1,
                      md.rel(out / "dev_switch_analysis.md"): md.sha256_file(out / "dev_switch_analysis.md")}
    md.write_json(out / "dev_switch_analysis_run.json", rec)
    for s in rec["findings"]:
        print(s)
    print(rec["outputs"])
    return 0


def cmd_dev_heads(args) -> int:
    out = Path(args.out)
    rec = _start("b2_forms_dev_heads", out, args.replace)
    Q, pd1, info = load_head_oof()
    tab = forms_table(Q, pd1, log=lambda m: print(f"{now()} {m}", flush=True))
    dev = tab.pop("_dev")
    tab.pop("_scorer")
    des = md.read_json(md.DESIGN / "design.json")
    acc = des["measures_information"]["accuracy"]
    wr = des["measures_information"]["written"]
    free = tab["forms"]["free"]
    eq_path = sum(1 for d in dev.ids if written_path(info["viterbi"][d], dev.view[d][0], dev.certain[d]) == tab["written"]["free"][d])
    dmax = {f: max(float(np.abs(tab["marginals"][f][d] - info[f"marg_{f}"][d]).max()) for d in dev.ids) for f in FROZEN_FORMS}
    rec["checks"] = {
        "free form: written path equal to the stored path of the design (documents)": f"{eq_path} of {len(dev.ids)}",
        "free form: largest difference of a block marginal to b2_oof.npz": f"{dmax['free']:.3g}",
        "joint form: largest difference of a block marginal to b2_oof.npz": f"{dmax['joint']:.3g}",
        "free form: accuracy on the non-certain blocks against design.json":
            f"{free['accuracy_non_certain']} against {acc['noncertain_b2_viterbi']} ({free['non_certain_blocks']} against "
            f"{acc['noncertain_blocks']} blocks)",
        "rules: accuracy on the non-certain blocks against design.json":
            f"{tab['rules']['accuracy_non_certain']} against {acc['noncertain_rule_view']}",
        "free form: written switch boundaries against design.json":
            f"{free['written_switch_boundaries_correct']} of {free['written_switch_boundaries']} against "
            f"{round(wr['switch_b12_entered']['accuracy'] * wr['switch_b12_entered']['n'])} of {wr['switch_b12_entered']['n']}",
        "rules: written switch boundaries against design.json":
            f"{tab['rules']['written_switch_boundaries_correct']} of {tab['rules']['written_switch_boundaries']} against "
            f"{round(wr['switch_b12_not_entered']['accuracy'] * wr['switch_b12_not_entered']['n'])} of "
            f"{wr['switch_b12_not_entered']['n']}",
        "free form: NLL of the block marginals against design.json":
            f"{free['nll_block_marginals']} against {des['b2']['nll_out_of_fold']['free']}; joint "
            f"{tab['forms']['joint']['nll_block_marginals']} against {des['b2']['nll_out_of_fold']['joint']}",
    }
    rec["limits"] = [
        "The posteriors come from the B1 head, not from B1-L. The order of the forms can be different for B1-L.",
        "The 3 new forms were designed after the `dev` switch analysis of the same posteriors. Thus their `dev` values are too good.",
        "The rules saw 145 of the 193 `dev` documents in their design. This favours the rules and each form that uses the rule gaps.",
        "The strength value of a fold uses posteriors of heads that saw the labels of that fold. Each HMM of the choice excludes the fold.",
        "The switch counts are small. A difference of 1 or 2 documents is not a sure difference.",
        "The reference is an AI reference without a human acceptance.",
    ]
    rec.update({"finished": now(), "state": "finished", "inputs": {**tab["inputs"], **info["files"]}})
    body = {"version": VERSION, "status": STATUS, "made": rec["finished"], "script": rec["script"],
            "values": "dev out-of-fold values with the posteriors of the B1 head (information)",
            "forms_order": list(FORMS), "counts": tab["counts"], "rules": tab["rules"], "forms": tab["forms"],
            "selection_information": tab["selection"], "strength": tab["strength"], "checks": rec["checks"],
            "limits": rec["limits"], "inputs": rec["inputs"],
            "written_switch_gaps": {f: {d: md.switch_gaps(tab["written"][f][d]) for d in dev.ids
                                        if md.switch_gaps(tab["written"][f][d]) or md.switch_gaps(dev.refs[d])}
                                    for f in tab["forms"]}}
    h1 = md.write_json(out / "b2_forms_dev_heads.json", body)
    (out / "b2_forms_dev_heads.md").write_text(heads_markdown(tab, rec), encoding="utf-8")
    rec["outputs"] = {md.rel(out / "b2_forms_dev_heads.json"): h1,
                      md.rel(out / "b2_forms_dev_heads.md"): md.sha256_file(out / "b2_forms_dev_heads.md")}
    md.write_json(out / "b2_forms_dev_heads_run.json", rec)
    for k, v in rec["checks"].items():
        print(f"{k}: {v}")
    print(tab["selection"])
    print(rec["outputs"])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="B2 forms of gate GJ for B1-L (dev only)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("analysis", "dev-heads"):
        s = sub.add_parser(name)
        s.add_argument("--out", default=str(OUT))
        s.add_argument("--replace", action="store_true")
    a = ap.parse_args()
    try:
        return cmd_analysis(a) if a.cmd == "analysis" else cmd_dev_heads(a)
    except md.DesignRefusal as e:
        print(f"refused: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
