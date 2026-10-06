# SPDX-License-Identifier: Apache-2.0
"""Teilfragen 2.5 und 2.6 (thema ech): Abgleich OpenParlData -> eCH-0295.

Streamt die Exporte unter <data>/roh/exports/ zeilenweise (affairs, bodies, events,
contributors, texts/*, votings, agendas) und liest den PDF-Index aus 2.7
(<data>/analyse/pdf/docs_pdf_index.csv.gz, erzeugt von src/m02_pdf_index.py), um
die Verfuegbarkeit von PDF-Volltext pro Geschaeft festzustellen. Die Zuordnungsregeln
stehen in src/m02_ech_regeln.py.

Ausgaben (<data>/analyse/ech/):
  matrix_felder.csv                eCH-Feld x Quelle x Abdeckung x Silber x PDF
  matrix_felder_je_parlament.csv   dieselben Felder je Parlament (Anteil)
  matrix_felder_je_ebene.csv       dieselben Felder je Ebene (Bund, Kanton, Gemeinde, Liechtenstein)
  typ_ech_verteilung.csv           Geschaefte je eCH-Typ, Match-Art und Ebene
  rolle_klassen.csv                Beteiligte je role_harmonized und Sponsor-Klasse (Regel)
  silber_mit_pdf.csv               Silber-Label und PDF mit Text am selben Geschaeft (Trainingskandidaten)
  geschaefte_merkmale.csv.gz       ein Datensatz pro Geschaeft mit 0/1-Merkmalen (nur IDs)
  typ_harmonisiert.csv             type_harmonized -> AffairTypeEnum
  typ_lokal.csv                    lokale Typbezeichnungen -> Vorschlag AffairTypeEnum
  typ_ohne_entsprechung.csv        Kategorien ohne (exakte) eCH-Entsprechung
  typ_konflikt.csv                 lokale Regel vs. Harmonisierung (abweichende Paare)
  rolle_sponsor.csv                role_harmonized + lokale Rolle -> SponsorRoleEnum / eCH-Ort
  ereignis_harmonisiert.csv        title_harmonized -> eCH-Schritt / Etappe / Entscheid
  ereignis_lokal_ohne_harmonisierung.csv  haeufige lokale Titel ohne Harmonisierung (>= 100)
  status_lokal.csv                 state_name (lokal/harmonisiert) -> StatusEnum / Entscheid
  texttyp.csv                      Texttypen aus exports/texts -> TextTypeEnum
  entscheid_verteilung.csv         letzter Entscheid je Geschaeft nach eCH-Typ
  empfehlung_verteilung.csv        Empfehlung der Exekutive nach eCH-Typ und Quelle
  kennzahlen.csv                   Einzelkennzahlen (Konsistenzpruefungen)

Aufruf (im Ordner track_2a): uv run python src/m02_ech_abgleich.py
"""

from __future__ import annotations

import collections
import csv
import glob
import gzip
import json
import re
import statistics
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m02_ech_regeln as R  # noqa: E402
from m03_iso_paths import DATA, rel  # noqa: E402,F401
EXPORTE = DATA / "roh/exports"
PDF_INDEX = DATA / "analyse/pdf/docs_pdf_index.csv.gz"
AUS = DATA / "analyse/ech"

# The script does its work at module level (also on import). Stop before the first read.
if {"-h", "--help"} & set(sys.argv[1:]):
    print(__doc__)
    sys.exit(0)
if not (EXPORTE / "bodies.ndjson.gz").exists():
    raise SystemExit(f"no exports below {rel(EXPORTE)}: run src/m02_exporte_holen.sh first")

MIN_LABEL = 5          # seltenere Bezeichnungen werden zusammengefasst (Namensschutz)
MIN_LOKAL_TITEL = 100  # lokale Ereignistitel ohne Harmonisierung erst ab dieser Haeufigkeit
MIN_BEZUG_PARL = 20    # Parlament zaehlt fuer "ab 50 %" erst ab so vielen Bezugsgeschaeften
PDF_TEXT_MIN = 200     # Zeichen ohne Leerraum, ab denen ein PDF als "mit Text" gilt

T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - T0:6.0f}s] {msg}", file=sys.stderr, flush=True)


def zeilen(pfad: Path):
    with gzip.open(pfad, "rt", encoding="utf-8") as f:
        for z in f:
            if z.strip():
                yield json.loads(z)


def schreibe(name: str, kopf: list[str], reihen) -> None:
    pfad = AUS / name
    oeffne = gzip.open if name.endswith(".gz") else open
    with oeffne(pfad, "wt", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(kopf)
        n = 0
        for r in reihen:
            w.writerow(r)
            n += 1
    log(f"geschrieben {name}: {n} Zeilen")


def tag(s: str | None) -> str:
    return (s or "")[:10]


# ======================================================================= Daten sammeln

F: dict[str, set[int]] = collections.defaultdict(set)   # Merkmal -> Geschaefts-IDs
GESCH: dict[int, tuple[str, str, str]] = {}             # id -> (body_key, ech_typ, match)
BEGIN: dict[int, str] = {}
STATUS_G: dict[int, str] = {}                            # Status aus affairs (state/active)
KZ: list[tuple[str, str, str]] = []                      # Kennzahlen (name, wert, wie)


def kz(name: str, wert, wie: str) -> None:
    KZ.append((name, str(wert), wie))


# ---------------------------------------------------------------- bodies
BODY: dict[str, dict] = {}
for b in zeilen(EXPORTE / "bodies.ndjson.gz"):
    BODY[b["body_key"]] = b


def eb(bk: str) -> str:
    return R.ebene(bk, (BODY.get(bk) or {}).get("type"))


# ---------------------------------------------------------------- affairs
log("affairs")
typ_harm = collections.Counter()
typ_harm_b = collections.defaultdict(set)
typ_harm_en: dict[int, tuple[str, str]] = {}
typ_lok = collections.Counter()
typ_lok_b = collections.defaultdict(set)
typ_lok_info: dict[tuple, tuple] = {}
konflikt = collections.Counter()
konflikt_b = collections.defaultdict(set)
ohne = collections.Counter()
ohne_b = collections.defaultdict(set)
ohne_bsp = collections.defaultdict(collections.Counter)
stat_lok = collections.Counter()
stat_lok_b = collections.defaultdict(set)
che_nummern: set[str] = set()
state_harm_b: set[str] = set()
che_nr_von: dict[int, str] = {}
titel_anomalie = collections.Counter()

for a in zeilen(EXPORTE / "affairs.ndjson.gz"):
    aid = a["id"]
    bk = a["body_key"]
    hid = a.get("type_harmonized_id")
    lok, lok_sprache = None, ""
    for sp in ("de", "fr", "it", "rm"):
        if a.get(f"type_name_{sp}"):
            lok, lok_sprache = a[f"type_name_{sp}"].strip(), sp
            break
    wert, art, kat, quelle = R.typ_ech(hid, lok)
    GESCH[aid] = (bk, wert, art)
    F["alle"].add(aid)

    # Typen
    typ_harm[hid] += 1
    typ_harm_b[hid].add(bk)
    if hid is not None and hid not in typ_harm_en:
        typ_harm_en[hid] = (a.get("type_harmonized_en") or "", a.get("type_harmonized_wikidata_id") or "")
    key = (lok or "", lok_sprache, a.get("type_harmonized_de") or "")
    typ_lok[key] += 1
    typ_lok_b[key].add(bk)
    typ_lok_info[key] = (hid, R.typ_lokal(lok), (wert, art, kat, quelle))
    if hid is not None:
        F["typ_harmonisiert"].add(aid)
    if wert and art in ("exakt", "nah"):
        F["typ_ech_exakt_nah"].add(aid)
    if wert:
        F["typ_ech_irgendein"].add(aid)
    lw, la, _ = R.typ_lokal(lok)
    hw = R.TYP_HARMONISIERT.get(hid, R.TYP_HARMONISIERT[None])[0]
    if la != "unbestimmt" and hid is not None and lw != hw:
        k2 = (a.get("type_harmonized_de") or "", hw, lok or "", lw)
        konflikt[k2] += 1
        konflikt_b[k2].add(bk)
    if art in ("keine", "unbestimmt") or (art == "weiter" and kat) or wert == "draft_decree":
        kat2 = kat or ("Regierungsgeschaeft/Vorlage (nur draft_decree, weiter)" if wert == "draft_decree"
                       else "ohne Typangabe/unbestimmt")
        ohne[kat2] += 1
        ohne_b[kat2].add(bk)
        ohne_bsp[kat2][lok or "(leer)"] += 1

    # Nummer
    if (a.get("number") or "").strip():
        F["nummer_vorhanden"].add(aid)
    if R.nummer_plausibel(a.get("number"), a.get("external_id")):
        F["nummer_plausibel"].add(aid)
    if bk == "CHE" and a.get("number"):
        che_nummern.add(a["number"].strip())
        che_nr_von[aid] = a["number"].strip()

    # Titel
    sprachen = [sp for sp in ("de", "fr", "it", "rm") if (a.get(f"title_{sp}") or "").strip()]
    if sprachen:
        F["titel"].add(aid)
    if len(sprachen) >= 2:
        F["titel_mehrsprachig"].add(aid)
    for sp in sprachen:
        t = a[f"title_{sp}"]
        if "###" in t:
            titel_anomalie["titel_mit_###"] += 1
            F["titel_anomalie"].add(aid)
            break
        if len(t) > 500:
            titel_anomalie["titel_ueber_500_zeichen"] += 1
            F["titel_anomalie"].add(aid)
            break

    # Daten
    if a.get("begin_date"):
        F["begin_date"].add(aid)
        BEGIN[aid] = tag(a["begin_date"])
    if a.get("end_date"):
        F["end_date"].add(aid)

    # Status
    sname = None
    for sp in ("de", "fr", "it", "rm"):
        if a.get(f"state_name_{sp}"):
            sname = a[f"state_name_{sp}"].strip()
            break
    if sname:
        F["state_lokal"].add(aid)
    st, et, en = R.status_lokal(sname)
    sh = a.get("state_name_harmonized_id")
    if sh is not None:
        state_harm_b.add(bk)
        F["state_harmonisiert"].add(aid)
        st = st or {1: "open", 2: "open", 3: "closed"}.get(sh, "")
    if a.get("active") is not None:
        st = st or ("open" if a["active"] else "closed")
        F["active"].add(aid)
    stat_lok[(sname or "", a.get("state_name_harmonized_de") or "")] += 1
    stat_lok_b[(sname or "", a.get("state_name_harmonized_de") or "")].add(bk)
    if st:
        F["status_aus_geschaeft"].add(aid)
        STATUS_G[aid] = st
    if et:
        F["etappe_aus_geschaeft"].add(aid)
    if en and not en.startswith("keine"):
        F["entscheid_aus_geschaeft"].add(aid)

    # Dringlichkeit aus Typ/Titel
    txt = " ".join(x for x in (lok, a.get("title_long_de"), a.get("title_long_fr"),
                                a.get("title_long_it")) if x)
    if lok and R.DRINGLICH.search(lok):
        F["dringlich_typ"].add(aid)
    elif R.DRINGLICH.search(txt):
        F["dringlich_titel"].add(aid)

N_ALLE = len(F["alle"])
log(f"affairs: {N_ALLE}")
_m = collections.Counter("weiter" if (art == "weiter") else ("exakt_nah" if art in ("exakt", "nah") else art)
                         for _, _, art in GESCH.values())
for k in ("exakt_nah", "weiter", "keine", "unbestimmt"):
    kz(f"typ_match_{k}", _m[k], "Geschaefte nach Match-Art der kombinierten Typzuordnung (typ_ech)")
kz("state_harmonisiert_parlamente", ",".join(sorted(state_harm_b)), "body_key mit state_name_harmonized_id")

TYP_VON = {aid: g[1] for aid, g in GESCH.items()}
VORSTOSS = {aid for aid, t in TYP_VON.items() if t in R.VORSTOSS_TYPEN}
ANTRAG = {aid for aid, t in TYP_VON.items() if t in R.ANTRAG_TYPEN}
ANTWORT = {aid for aid, t in TYP_VON.items() if t in R.ANTWORT_TYPEN}

# ---------------------------------------------------------------- events
log("events")
ev_harm = collections.Counter()
ev_harm_aff = collections.defaultdict(set)
ev_harm_b = collections.defaultdict(set)
ev_harm_abw = collections.Counter()
ev_lok = collections.Counter()
ev_lok_b = collections.defaultdict(set)
ev_lok_info: dict[str, tuple] = {}
ev_cache: dict[tuple, tuple] = {}
eingereicht_datum: dict[int, str] = {}
letzter_entscheid: dict[int, tuple] = {}
letzte_empf: dict[int, tuple] = {}
letzter_status: dict[int, tuple] = {}
typkorrektur = collections.Counter()
buero_als_bundesrat = 0
che_type_it_franz = 0
beantw_actor = collections.Counter()
rx_che_nr = re.compile(r"(?<![\d.])(\d{2}\.\d{3,4})(?![\d.])")

for e in zeilen(EXPORTE / "events.ndjson.gz"):
    aid = e.get("affair_id")
    if not aid or aid not in GESCH:
        continue
    bk = e["body_key"]
    hid = e.get("title_harmonized_id")
    titel = (e.get("title_de") or e.get("title_fr") or e.get("title_it") or "").strip()
    ck = (hid, titel)
    if ck not in ev_cache:
        ev_cache[ck] = R.ereignis(hid, titel)
    roh = ev_cache[ck]
    schritt, etappe, entscheid, status, empf, quelle = R.ereignis_fuer_typ(roh, TYP_VON[aid])
    datum = tag(e.get("date"))
    pos = e.get("position") or 0

    if hid is not None:
        ev_harm[hid] += 1
        ev_harm_aff[hid].add(aid)
        ev_harm_b[hid].add(bk)
        hs = R.EREIGNIS_HARM.get(hid)
        if hs and roh[5] == "lokal" and (roh[1], roh[2].split(":")[0]) != (hs[1], hs[2].split(":")[0]):
            ev_harm_abw[hid] += 1
    else:
        k = titel[:80]
        ev_lok[k] += 1
        ev_lok_b[k].add(bk)
        ev_lok_info[k] = roh[:5]

    if roh[1] == "forwarded_to_executive" and etappe != roh[1]:
        typkorrektur[hid] += 1
    if schritt or etappe or entscheid or status:
        F["ereignis_zugeordnet"].add(aid)
    if etappe:
        F["etappe_aus_ereignis"].add(aid)
        if etappe != "submission":
            F["etappe_nach_einreichung"].add(aid)
    if status:
        k = (datum, pos)
        if aid not in letzter_status or k >= letzter_status[aid][0]:
            letzter_status[aid] = (k, status)
    if entscheid and not entscheid.startswith("keine") and entscheid != "none":
        F["entscheid_aus_ereignis"].add(aid)
    if status:
        F["status_aus_ereignis"].add(aid)
    if etappe == "submission" and datum:
        F["eingereicht_ereignis"].add(aid)
        if aid not in eingereicht_datum or datum < eingereicht_datum[aid]:
            eingereicht_datum[aid] = datum
    if schritt.startswith("ResponseStep") or etappe == "executive_response":
        F["antwort_ereignis"].add(aid)
        actor = e.get("actor_de") or e.get("actor_fr") or e.get("actor_it") or ""
        if bk == "CHE" and re.search(r"B[üu]ro", titel) and "beantragt" in titel and actor == "Bundesrat":
            buero_als_bundesrat += 1
        if hid == 6:
            beantw_actor[actor or "(leer)"] += 1
        if actor and R.EXEKUTIVE.search(actor):
            F["responder_ereignis"].add(aid)
    if empf:
        F["empfehlung_ereignis"].add(aid)
        if quelle == "harmonisiert":
            F["empfehlung_ereignis_harm"].add(aid)
        else:
            F["empfehlung_ereignis_lokal"].add(aid)
        k = (datum, pos)
        if aid not in letzte_empf or k >= letzte_empf[aid][0]:
            letzte_empf[aid] = (k, empf, quelle)
    if entscheid in ("urgency_granted",):
        F["dringlich_gewaehrt"].add(aid)
    if entscheid in ("urgency_denied",):
        F["dringlich_abgelehnt"].add(aid)
    if etappe == "urgency_review":
        F["dringlich_ereignis"].add(aid)
    if etappe == "withdrawal" and datum:
        F["rueckzug_datum"].add(aid)
    if schritt.startswith("AssignmentStep.deadline") or (hid in (4, 9, 18)):
        F["frist"].add(aid)
    if schritt.startswith("AssignmentStep(committee_referral)") or etappe == "committee":
        F["kommission_ereignis"].add(aid)
    if schritt.startswith("AssignmentStep(agenda_placement)"):
        F["traktandiert_ereignis"].add(aid)
    if schritt.startswith("AssignmentStep(executive_routing)"):
        F["zuweisung_exekutive_ereignis"].add(aid)
    if schritt == "Submission.sponsorship(transferred)":
        F["sponsor_uebernommen"].add(aid)
    if entscheid and entscheid not in ("none", "recommended_for", "recommended_against",
                                       "urgency_granted", "urgency_denied", "validated",
                                       "failed_validation") and not entscheid.startswith("keine:empfehlung"):
        k = (datum, pos)
        if aid not in letzter_entscheid or k >= letzter_entscheid[aid][0]:
            letzter_entscheid[aid] = (k, entscheid)
        F["schlussentscheid_irgendein"].add(aid)
    if bk == "CHE" and titel:
        for m in rx_che_nr.findall(titel):
            if m in che_nummern and m != che_nr_von.get(aid):
                F["verweis_ereignis"].add(aid)
                break

log(f"events: {len(ev_cache)} verschiedene Titel")
kz("ereignisse_mit_geschaeft", sum(ev_harm.values()) + sum(ev_lok.values()), "events mit affair_id in affairs")
kz("ereignisse_ohne_harmonisierung", sum(ev_lok.values()), "davon ohne title_harmonized_id")
kz("ereignisse_ohne_harmonisierung_bund", sum(n for k, n in ev_lok.items() if "CHE" in ev_lok_b[k] and len(ev_lok_b[k]) == 1),
   "davon Titel, die nur im Bund vorkommen")
kz("ereignisse_ohne_harmonisierung_parlamente", ",".join(sorted(set().union(*ev_lok_b.values()))) if ev_lok_b else "",
   "body_key mit Ereignissen ohne title_harmonized_id")
kz("ueberwiesen_bei_auskunftstypen", sum(typkorrektur.values()),
   "Ereignisse 'Ueberwiesen' bei Interpellation/Anfrage/Frage, umgedeutet zu executive_routing")
kz("ueberwiesen_bei_auskunftstypen_harm26", typkorrektur[26], "davon title_harmonized_id 26")
kz("bund_bueroantrag_mit_actor_bundesrat", buero_als_bundesrat,
   "Bund: Antrags-Ereignisse des Bueros ('Das Buero ... beantragt') mit actor_de 'Bundesrat'")

# Einreichungsdatum: begin_date vs. Ereignis
gleich = abw = 0
diffs = []
for aid, d in eingereicht_datum.items():
    b = BEGIN.get(aid)
    if not b:
        continue
    if b == d:
        gleich += 1
    else:
        abw += 1
        try:
            diffs.append(abs((date.fromisoformat(b) - date.fromisoformat(d)).days))
        except ValueError:
            pass
kz("einreichung_begin_date_gleich_ereignisdatum", gleich,
   "Geschaefte mit begin_date und Einreichungs-Ereignis, Datum identisch (m02_ech_abgleich.py)")
kz("einreichung_begin_date_abweichend", abw, "dito, Datum verschieden")
if diffs:
    kz("einreichung_abweichung_median_tage", statistics.median(diffs), "Median |begin_date - Ereignisdatum| bei Abweichung")
    kz("einreichung_abweichung_ueber_30_tage", sum(1 for x in diffs if x > 30), "Anzahl Abweichungen > 30 Tage")
for k, v in titel_anomalie.items():
    kz(k, v, "affairs.title_*: Geschaefte mit Anomalie (erste Sprache mit Befund)")

# Konsistenz Beantwortet-Ereignisse (title_harmonized_id 6) nach actor
for actor, n in beantw_actor.most_common(8):
    kz(f"beantwortet_ereignis_actor:{actor}", n, "events mit title_harmonized_id 6 nach actor_de")

# ---------------------------------------------------------------- contributors
log("contributors")
rolle = collections.Counter()
rolle_aff = collections.defaultdict(set)
rolle_b = collections.defaultdict(set)
rolle_info: dict[tuple, str] = {}
spons: dict[int, dict] = {}
for c in zeilen(EXPORTE / "contributors.ndjson.gz"):
    aid = c.get("affair_id")
    if not aid or aid not in GESCH:
        continue
    rh = c.get("role_harmonized")
    key = (rh or "", c.get("role_de") or "", c.get("role_fr") or "", c.get("role_it") or "",
           c.get("type") or "")
    klasse = R.rolle_sponsor(rh, c.get("role_de"), c.get("role_fr"), c.get("role_it"))
    rolle[key] += 1
    rolle_aff[key].add(aid)
    rolle_b[key].add(c["body_key"])
    rolle_info[key] = klasse
    if rh == "responder":
        F["responder_rolle"].add(aid)
    elif rh in ("leading_department", "departement"):
        F["federfuehrung"].add(aid)
    elif rh in ("assigned_committee", "committee"):
        F["kommission_rolle"].add(aid)
    elif rh == "council_initial":
        F["erstrat"].add(aid)
    elif rh in ("speaker", "rapporteur"):
        F["sprecher"].add(aid)
    if klasse in ("sponsor", "cosponsor", "transferred", "unbestimmt"):
        s = spons.setdefault(aid, {"k": set(), "unb": set(), "alle": set(), "pid": False, "spon": set(),
                                   "grp": False})
        ident = c.get("person_id") or c.get("group_id") or c.get("fullname") or c.get("id")
        s["alle"].add(ident)
        s["k"].add(klasse)
        if klasse == "unbestimmt":
            s["unb"].add(ident)
        if klasse == "sponsor":
            s["spon"].add(ident)
            if c.get("type") == "group":
                s["grp"] = True
        if c.get("person_id") or c.get("group_id"):
            s["pid"] = True

mehrere_sponsoren = gruppen_sponsor = 0
for aid, s in spons.items():
    F["urheber_irgendein"].add(aid)
    mehrere_sponsoren += len(s["spon"]) >= 2
    gruppen_sponsor += s["grp"]
    if s["pid"]:
        F["urheber_mit_id"].add(aid)
    if "sponsor" in s["k"] or (len(s["alle"]) == 1 and s["k"] <= {"unbestimmt"}):
        F["sponsor_sicher"].add(aid)
    if "sponsor" in s["k"] or s["unb"]:
        F["sponsor_vermutet"].add(aid)
    if "cosponsor" in s["k"]:
        F["cosponsor_sicher"].add(aid)
    if "cosponsor" in s["k"] or len(s["unb"]) >= 2:
        F["cosponsor_vermutet"].add(aid)
    if "transferred" in s["k"]:
        F["sponsor_uebernommen"].add(aid)
    if s["unb"] and len(s["alle"]) >= 2 and "sponsor" not in s["k"]:
        F["sponsor_nur_position"].add(aid)
del spons
kz("geschaefte_mit_mehreren_sponsor_akteuren", mehrere_sponsoren,
   "Geschaefte mit >= 2 verschiedenen Akteuren der Klasse sponsor (lokale Rolle eindeutig Urheber/Erstunterzeichner)")
kz("geschaefte_mit_gruppe_als_sponsor", gruppen_sponsor, "Geschaefte mit contributors.type=group in Klasse sponsor")
F["responder"] = F["responder_rolle"] | F["responder_ereignis"]
F["responder_inkl_federfuehrung"] = F["responder"] | F["federfuehrung"]

# ---------------------------------------------------------------- texts
log("texts")
texttyp = collections.Counter()
texttyp_aff = collections.defaultdict(set)
texttyp_len = collections.defaultdict(list)
texttyp_info: dict[tuple, tuple] = {}
rx_tag = re.compile(r"<[^>]+>")
rx_datum = re.compile(r"\b(vom|du|del)\s+\d.*$", re.I)
che_text_empf: dict[int, str] = {}
for pfad in sorted(glob.glob(str(EXPORTE / "texts/texts_*.ndjson.gz"))):
    for t in zeilen(Path(pfad)):
        aid = t.get("affair_id")
        bk = t["body_key"]
        tde, tfr, tit = t.get("type_de"), t.get("type_fr"), t.get("type_it")
        wert, art = R.texttyp(tde, tfr, tit)
        label = rx_datum.sub(r"\1 <Datum>", (tde or tfr or tit or "").strip())
        key = (bk, label)
        inhalt = ""
        for sp in ("de", "fr", "it", "rm"):
            if (t.get(f"text_{sp}") or "").strip():
                inhalt = t[f"text_{sp}"]
                break
        texttyp[key] += 1
        if bk == "CHE" and tit and tfr and tit == tfr:
            che_type_it_franz += 1
        if aid:
            texttyp_aff[key].add(aid)
        texttyp_info[key] = (wert, art)
        roh = rx_tag.sub(" ", inhalt)
        if len(texttyp_len[key]) < 20000:
            texttyp_len[key].append(len(roh.strip()))
        if not aid or aid not in GESCH or not roh.strip():
            continue
        F["text_irgendein"].add(aid)
        if wert:
            F[f"text_{wert}"].add(aid)
        if bk == "CHE":
            ganz = " ".join(rx_tag.sub(" ", t.get(f"text_{sp}") or "") for sp in ("de", "fr", "it"))
            if wert == "response":
                m = re.search(r"(Der Bundesrat|Das B[üu]ro)[^.]{0,120}(beantragt|ist bereit)[^.]{0,160}\.",
                              ganz)
                if m:
                    emp = R.empfehlung_aus_titel(m.group(0))
                    if emp:
                        che_text_empf[aid] = emp
                        F["empfehlung_text"].add(aid)
            own = che_nr_von.get(aid)
            for m in rx_che_nr.findall(ganz):
                if m in che_nummern and m != own:
                    F["verweis_text"].add(aid)
                    break

kz("bund_texte_type_it_gleich_type_fr", che_type_it_franz,
   "Bund: texts mit identischem type_it und type_fr (franzoesisches Label im italienischen Feld)")
# Abgleich Empfehlung Text vs. Ereignis (Bund)
beide = gleich_e = 0
for aid, emp in che_text_empf.items():
    if aid in letzte_empf:
        beide += 1
        if letzte_empf[aid][1] == emp:
            gleich_e += 1
kz("empfehlung_bund_text_und_ereignis", beide, "Bund: Geschaefte mit Empfehlung aus Antworttext und aus Ereignis")
kz("empfehlung_bund_text_gleich_ereignis", gleich_e, "dito, gleicher RecommendationEnum-Wert (letztes Ereignis)")

F["empfehlung"] = F["empfehlung_ereignis"] | F["empfehlung_text"]
F["verweis"] = F["verweis_text"] | F["verweis_ereignis"]
F["dringlich_positiv"] = F["dringlich_typ"] | F["dringlich_titel"] | F["dringlich_gewaehrt"]

# ---------------------------------------------------------------- votings, agendas
log("votings")
for v in zeilen(EXPORTE / "votings.ndjson.gz"):
    aid = v.get("affair_id")
    if aid in GESCH:
        F["abstimmung"].add(aid)
        if v.get("results_yes") is not None and v.get("results_no") is not None:
            F["abstimmung_zahlen"].add(aid)
log("agendas")
for g in zeilen(EXPORTE / "agendas.ndjson.gz"):
    aid = g.get("item_affair_id")
    if aid in GESCH:
        F["traktandum"].add(aid)

# ---------------------------------------------------------------- PDF-Index (aus 2.7)
log("pdf-index")
if not PDF_INDEX.exists():
    sys.exit(f"PDF-Index fehlt: {PDF_INDEX} (erst src/m02_pdf_index.py laufen lassen)")
with gzip.open(PDF_INDEX, "rt", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        try:
            aid = int(r["affair_id"]) if r["affair_id"] else None
        except ValueError:
            aid = None
        if aid not in GESCH:
            continue
        F["pdf"].add(aid)
        mit_text = int(r["text_nonws"] or 0) >= PDF_TEXT_MIN
        if mit_text:
            F["pdf_text"].add(aid)
            if r["name_klasse"] == "antwort":
                F["pdf_antwort_hinweis"].add(aid)
            if r["name_klasse"] == "vorstoss":
                F["pdf_vorstoss_hinweis"].add(aid)

# ---------------------------------------------------------------- Kombinationen
F["status"] = F["status_aus_geschaeft"] | F["status_aus_ereignis"]
STATUS_AKT: dict[int, str] = {}
for aid in GESCH:
    st = STATUS_G.get(aid) or (letzter_status[aid][1] if aid in letzter_status else "")
    if st:
        STATUS_AKT[aid] = st
        F["status_aktuell"].add(aid)
for wert in ("open", "closed"):
    kz(f"status_aktuell_{wert}", sum(1 for v in STATUS_AKT.values() if v == wert),
       "Status aus affairs.state_name/active, sonst letztes Ereignis mit Status")
kz("status_aktuell_aus_geschaeft", len(STATUS_G), "davon aus affairs (state_name_*, state_name_harmonized, active)")
F["etappe_ausser_einreichung"] = F["etappe_aus_geschaeft"] | F["etappe_nach_einreichung"]
F["etappe"] = F["etappe_aus_geschaeft"] | F["etappe_aus_ereignis"]
F["entscheid"] = F["entscheid_aus_geschaeft"] | F["entscheid_aus_ereignis"]
F["einreichungsdatum"] = F["begin_date"] | F["eingereicht_ereignis"]
F["zuweisung_kommission"] = F["kommission_rolle"] | F["kommission_ereignis"]
F["zuweisung_exekutive"] = F["federfuehrung"] | F["zuweisung_exekutive_ereignis"]
F["text_submitted_oder_pdf"] = F["text_submitted"] | F["pdf_text"]
F["text_response_oder_pdf"] = F["text_response"] | F["pdf_antwort_hinweis"]

# ======================================================================= Matrix

BEZUG = {"alle": F["alle"], "vorstoesse": VORSTOSS, "antrag": ANTRAG, "antwort": ANTWORT}
for name, menge in BEZUG.items():
    kz(f"bezugsmenge_{name}", len(menge), "Anzahl Geschaefte; Typ nach m02_ech_regeln.typ_ech")

# (feld_id, eCH-Pfad, Quelle OpenParlData, Bezug, Merkmal, Qualitaet, Bemerkung)
# Merkmalsart: siehe SELTEN (natuerlich seltene Ereignisse) und PDF_BASIS (Quelle ist das PDF selbst)
# Qualitaet: hoch = Wert direkt uebernehmbar; mittel = Regel/Abbildung noetig;
#            niedrig = nur Hinweis/Naeherung
ZEILEN = [
    ("affair_type", "Affair.affair_type", "affairs.type_harmonized_id", "alle", "typ_harmonisiert", "mittel",
     "harmonisierter Typ vorhanden (Zuordnung siehe typ_harmonisiert.csv)"),
    ("affair_type", "Affair.affair_type", "affairs.type_harmonized_id + type_name_* (Regel)", "alle",
     "typ_ech_exakt_nah", "hoch", "AffairTypeEnum-Wert mit Match exakt/nah"),
    ("affair_number", "Affair.affair_number", "affairs.number", "alle", "nummer_vorhanden", "mittel",
     "Feld immer gefuellt, teils System-ID oder mit Typpraefix"),
    ("affair_number", "Affair.affair_number", "affairs.number (Plausibilitaetsheuristik)", "alle",
     "nummer_plausibel", "mittel", "Schaetzung: keine Hex-/reine System-ID"),
    ("title", "Affair.title[TextBlock]", "affairs.title_de/fr/it/rm", "alle", "titel", "hoch",
     "text_origin (Original/Uebersetzung) nicht kodiert"),
    ("title", "Affair.title[TextBlock] (>=2 Sprachen)", "affairs.title_*", "alle", "titel_mehrsprachig",
     "hoch", ""),
    ("submission_date", "Submission.submission_date", "affairs.begin_date", "vorstoesse", "begin_date",
     "mittel", "Semantik von begin_date nicht dokumentiert; Abgleich mit Ereignis siehe kennzahlen.csv"),
    ("submission_date", "Submission.submission_date", "events (Einreichung)", "vorstoesse",
     "eingereicht_ereignis", "hoch", ""),
    ("sponsorship.sponsor", "Submission.sponsorship(sponsor)", "contributors (Rolle, Regel)", "vorstoesse",
     "sponsor_sicher", "mittel", "lokale Rolle eindeutig oder nur eine Urheberperson"),
    ("sponsorship.sponsor", "Submission.sponsorship(sponsor)", "contributors (inkl. Position 1, Vermutung)",
     "vorstoesse", "sponsor_vermutet", "niedrig", "role_harmonized=author ohne lokale Unterscheidung"),
    ("sponsorship.cosponsor", "Submission.sponsorship(cosponsor)", "contributors (Rolle, Regel)",
     "vorstoesse", "cosponsor_sicher", "mittel", ""),
    ("sponsorship.cosponsor", "Submission.sponsorship(cosponsor)", "contributors (inkl. Vermutung)",
     "vorstoesse", "cosponsor_vermutet", "niedrig", ""),
    ("sponsorship.actor", "Sponsorship.actor (global_uri)", "contributors.person_id/group_id", "vorstoesse",
     "urheber_mit_id", "hoch", "Personen-/Gruppen-ID fuer Akteursverweis"),
    ("sponsorship.transferred", "Sponsorship(transferred)", "contributors assuming + events 'Wird uebernommen'",
     "vorstoesse", "sponsor_uebernommen", "hoch", "nur Bund"),
    ("responder", "ResponseStep.responder", "contributors responder + events Antwort mit Exekutive als actor",
     "antwort", "responder", "mittel", "actor meist generisch ('Regierung'); Name aus bodies.executive_name"),
    ("responder", "ResponseStep.responder (inkl. Federfuehrung)", "+ contributors leading_department",
     "antwort", "responder_inkl_federfuehrung", "niedrig", "Federfuehrung = vorbereitende Stelle"),
    ("recommendation", "ResponseStep.recommendation", "events (Antrag der Exekutive, Regel)", "antrag",
     "empfehlung_ereignis", "mittel", ""),
    ("recommendation", "ResponseStep.recommendation", "events + texts (Bund, Antwortsatz)", "antrag",
     "empfehlung", "mittel", ""),
    ("texts.submitted", "Submission.texts(submitted)", "exports/texts", "vorstoesse", "text_submitted", "hoch",
     ""),
    ("texts.reasoning", "Submission.texts(reasoning)", "exports/texts", "vorstoesse", "text_reasoning", "hoch",
     ""),
    ("texts.response", "ResponseStep.texts(response)", "exports/texts", "antwort", "text_response", "hoch", ""),
    ("texts.summary", "TextBlock(summary)", "exports/texts (Lead, Kurzbeschrieb, Beschreibung)", "alle",
     "text_summary", "mittel", ""),
    ("texts (PDF)", "Submission/ResponseStep.texts", "docs (PDF mit Tika-Text, Index 2.7)", "vorstoesse",
     "pdf_text", "niedrig", "Rohtext; Gliederung in submitted/reasoning/response erst durch Extraktion"),
    ("texts.response (PDF-Hinweis)", "ResponseStep.texts(response)", "docs: Name/Kategorie 'Antwort' (Index 2.7)",
     "antwort", "pdf_antwort_hinweis", "niedrig", "Schaetzung ueber Dateinamen/Kategorie"),
    ("texts.submitted (Text oder PDF)", "Submission.texts(submitted)", "exports/texts oder docs", "vorstoesse",
     "text_submitted_oder_pdf", "niedrig", ""),
    ("procedure_states.status", "ProcedureState.status", "affairs.state_name_* / active / events", "alle",
     "status", "mittel", ""),
    ("procedure_states.stage", "ProcedureState.stage", "events (Regel) / affairs.state_name_*", "alle",
     "etappe", "mittel", ""),
    ("procedure_states.stage", "ProcedureState.stage (ohne submission)", "events (Regel) / affairs.state_name_*",
     "alle", "etappe_ausser_einreichung", "mittel", "nur Etappen nach der Einreichung"),
    ("procedure_states.decision", "ProcedureState.decision", "events (Regel) / affairs.state_name_*", "antrag",
     "entscheid", "mittel", "ohne 'none' und ohne Entscheide ausserhalb des Enums"),
    ("procedure_states.decision", "ProcedureState.decision (inkl. Werte ausserhalb Enum)", "events (Regel)",
     "antrag", "schlussentscheid_irgendein", "niedrig", "inkl. abgeschrieben, als Postulat ueberwiesen usw."),
    ("current_state.status", "Affair.current_state.status", "affairs.state_name_*/active, sonst letztes Ereignis",
     "alle", "status_aktuell", "mittel", ""),
    ("current_state", "Affair.current_state", "affairs.state_name_* (lokal)", "alle", "state_lokal", "mittel",
     "nur lokaler Freitext; state_name_harmonized fast leer"),
    ("linked_affairs", "Affair.linked_affairs", "kein Feld; Nummernverweise in texts/events (nur Bund)", "alle",
     "verweis", "niedrig", "Schaetzung ueber Regex auf Bundesnummern"),
    ("lifecycle_flags.urgent", "LifecycleFlags.urgent", "type_name_*/title_long_* + events Dringlichkeit",
     "vorstoesse", "dringlich_positiv", "mittel", "nur positive Faelle belegbar; 'false' nicht ableitbar"),
    ("submission_validation (urgency)", "SubmissionValidationStep(urgency_request)", "events (Regel)",
     "vorstoesse", "dringlich_ereignis", "mittel", ""),
    ("withdrawn_date", "Submission.withdrawn_date", "events (Rueckzug)", "vorstoesse", "rueckzug_datum", "hoch", ""),
    ("deadline", "AssignmentStep.deadline", "events (Frist)", "vorstoesse", "frist", "niedrig",
     "Fristart nicht kodiert"),
    ("assignment.committee_referral", "AssignmentStep(committee_referral)",
     "contributors assigned_committee/committee + events", "alle", "zuweisung_kommission", "mittel", ""),
    ("assignment.executive_routing", "AssignmentStep(executive_routing)", "contributors leading_department + events",
     "alle", "zuweisung_exekutive", "mittel", ""),
    ("assignment.chamber_assignment", "AssignmentStep(chamber_assignment)", "contributors council_initial",
     "alle", "erstrat", "hoch", "nur Bund"),
    ("assignment.agenda_placement", "AssignmentStep(agenda_placement)", "events Traktandiert", "alle",
     "traktandiert_ereignis", "mittel", ""),
    ("committee_deliberation.spokesperson", "CommitteeDeliberationStep.spokesperson",
     "contributors speaker/rapporteur", "alle", "sprecher", "mittel", ""),
    ("plenary_debates.vote", "PlenaryDebateEvent.vote", "votings", "alle", "abstimmung", "hoch", ""),
    ("plenary_debates.meeting_ref", "PlenaryDebate.meeting_ref", "agendas.item_affair_id", "alle", "traktandum",
     "hoch", ""),
]


SELTEN = {"sponsor_uebernommen", "dringlich_positiv", "dringlich_ereignis", "rueckzug_datum", "frist",
          "verweis"}
PDF_BASIS = {"pdf_text", "pdf_antwort_hinweis", "text_submitted_oder_pdf"}


def bewertung(anteil: float, qual: str, n_parl_50: int, n_parl_bezug: int, n_parl_mit: int = 0,
              merkmal: str = "") -> tuple[str, str]:
    """Regel fuer Silber und PDF-Bedarf.

    Normalfall: Silber nach Anteil und Qualitaet; PDF-Bedarf nach Anteil der Parlamente
    (mit >= MIN_BEZUG_PARL Bezugsgeschaeften), die das Feld zu mindestens 50 % abdecken.
    Seltene Merkmale (SELTEN): Anteil misst Vorkommen, nicht Abdeckung; bewertet wird,
    in wie vielen Parlamenten das Merkmal ueberhaupt belegt ist.
    PDF_BASIS: Quelle ist das PDF selbst, Extraktion daher immer noetig.
    """
    if merkmal in SELTEN:
        if n_parl_mit == 0:
            return "nein", "ja"
        silber = "ja" if (qual == "hoch" and n_parl_mit >= 0.5 * n_parl_bezug) else "teilweise"
        if n_parl_mit >= 0.8 * n_parl_bezug:
            pdf = "nein"
        elif n_parl_mit < 0.2 * n_parl_bezug:
            pdf = "ja"
        else:
            pdf = "teilweise"
        return silber, pdf
    if anteil < 0.02:
        silber = "nein"
    elif qual == "hoch" and anteil >= 0.5:
        silber = "ja"
    else:
        silber = "teilweise"
    if n_parl_bezug == 0:
        pdf = "ja"
    elif n_parl_50 >= 0.8 * n_parl_bezug:
        pdf = "nein"
    elif n_parl_50 < 0.2 * n_parl_bezug:
        pdf = "ja"
    else:
        pdf = "teilweise"
    if merkmal in PDF_BASIS:
        pdf = "ja"
    return silber, pdf


def je_parlament(menge: set[int]) -> collections.Counter:
    c = collections.Counter()
    for aid in menge:
        c[GESCH[aid][0]] += 1
    return c


BEZUG_PARL = {k: je_parlament(v) for k, v in BEZUG.items()}
matrix = []
je_parl = []
for feld, pfad, quelle, bezug, merkmal, qual, bem in ZEILEN:
    menge = F[merkmal] & BEZUG[bezug]
    nb = len(BEZUG[bezug])
    anteil = len(menge) / nb if nb else 0.0
    pc = je_parlament(menge)
    bp = BEZUG_PARL[bezug]
    n_parl_bezug = sum(1 for b, n in bp.items() if n >= MIN_BEZUG_PARL)
    n_parl_50 = sum(1 for b, n in bp.items() if n >= MIN_BEZUG_PARL and pc[b] / n >= 0.5)
    silber, pdf = bewertung(anteil, qual, n_parl_50, n_parl_bezug, len(pc), merkmal)
    matrix.append([feld, pfad, quelle, bezug, nb, len(menge), f"{anteil:.4f}", len(pc), n_parl_50,
                   n_parl_bezug, qual, silber, pdf, merkmal, bem])
    for b, n in sorted(bp.items()):
        je_parl.append([merkmal, feld, b, eb(b), n, pc[b], f"{pc[b] / n:.4f}"])

# je Ebene
je_ebene = []
for feld, pfad, quelle, bezug, merkmal, qual, bem in ZEILEN:
    menge = F[merkmal] & BEZUG[bezug]
    nb = collections.Counter(eb(GESCH[a][0]) for a in BEZUG[bezug])
    nm = collections.Counter(eb(GESCH[a][0]) for a in menge)
    pb = collections.defaultdict(set)
    for a in menge:
        pb[eb(GESCH[a][0])].add(GESCH[a][0])
    for e in ("Bund", "Kanton", "Gemeinde", "Liechtenstein"):
        je_ebene.append([merkmal, feld, e, nb[e], nm[e], f"{nm[e] / nb[e]:.4f}" if nb[e] else "", len(pb[e])])

AUS.mkdir(parents=True, exist_ok=True)
schreibe("matrix_felder_je_ebene.csv", ["merkmal", "ech_feld", "ebene", "n_bezug", "n_mit_wert", "anteil",
                                        "n_parlamente_mit_wert"], je_ebene)
tv = collections.Counter()
tv_b = collections.defaultdict(set)
for aid, (bk, typ, art) in GESCH.items():
    k = (typ or "(kein Wert)", art, eb(bk))
    tv[k] += 1
    tv_b[k].add(bk)
schreibe("typ_ech_verteilung.csv", ["ech_affair_type", "match_art", "ebene", "n_geschaefte", "n_parlamente"],
         [[t, a, e, n, len(tv_b[(t, a, e)])] for (t, a, e), n in sorted(tv.items(), key=lambda x: -x[1])])
# Silber-Label x PDF mit Text (Schaetzung moeglicher Trainingsbeispiele fuer PDF-Extraktion)
sp_reihen = []
SP_MERKMALE = ["typ_ech_exakt_nah", "nummer_plausibel", "eingereicht_ereignis", "begin_date", "sponsor_sicher",
               "cosponsor_sicher", "urheber_mit_id", "responder", "empfehlung", "entscheid",
               "schlussentscheid_irgendein", "status_aktuell", "dringlich_positiv", "rueckzug_datum",
               "text_submitted", "text_response"]
typ_mengen = collections.defaultdict(set)
for aid, (bk, typ, art) in GESCH.items():
    if typ and art in ("exakt", "nah"):
        typ_mengen[f"typ:{typ}"].add(aid)
for m in SP_MERKMALE + sorted(typ_mengen):
    menge = typ_mengen[m] if m.startswith("typ:") else F[m]
    mit = menge & F["pdf_text"]
    pc = je_parlament(mit)
    sp_reihen.append([m, len(menge), len(mit), len(pc), sum(1 for v in pc.values() if v >= MIN_BEZUG_PARL),
                      sum(1 for b in pc if eb(b) == "Kanton"), sum(1 for b in pc if eb(b) == "Gemeinde")])
schreibe("silber_mit_pdf.csv", ["merkmal", "n_geschaefte_mit_label", "n_davon_mit_pdf_text",
                                "n_parlamente", "n_parlamente_ab_20", "n_kantone", "n_gemeinden"], sp_reihen)
schreibe("matrix_felder.csv",
         ["ech_feld", "ech_pfad", "quelle_openparldata", "bezugsmenge", "n_bezug", "n_mit_wert", "anteil",
          "n_parlamente_mit_wert", "n_parlamente_ab_50pct", "n_parlamente_bezug_ab_20", "qualitaet",
          "silber_label", "pdf_extraktion_noetig", "merkmal", "bemerkung"], matrix)
schreibe("matrix_felder_je_parlament.csv",
         ["merkmal", "ech_feld", "body_key", "ebene", "n_bezug", "n_mit_wert", "anteil"], je_parl)

# Merkmale pro Geschaeft
MERKMALE = sorted({z[4] for z in ZEILEN} | {"pdf", "text_irgendein", "dringlich_gewaehrt",
                                            "dringlich_abgelehnt", "empfehlung_text"})


def merkmal_reihen():
    for aid in sorted(GESCH):
        bk, typ, art = GESCH[aid]
        emp = letzte_empf.get(aid)
        ent = letzter_entscheid.get(aid)
        yield [aid, bk, eb(bk), typ, art, emp[1] if emp else "", che_text_empf.get(aid, ""),
               ent[1] if ent else "", STATUS_AKT.get(aid, "")] + [1 if aid in F[m] else 0 for m in MERKMALE]


schreibe("geschaefte_merkmale.csv.gz",
         ["affair_id", "body_key", "ebene", "ech_affair_type", "typ_match", "empfehlung_ereignis",
          "empfehlung_text_bund", "letzter_entscheid", "status_aktuell"] + MERKMALE, merkmal_reihen())

# ======================================================================= Typ-Tabellen
lbl = R.TYP_HARMONISIERT
harm_label: dict = {}
for (lok, sp, hde), (hid, _, _) in typ_lok_info.items():
    harm_label[hid] = hde
reihen = []
for hid, n in typ_harm.most_common():
    w, art, kat, bem = lbl.get(hid, lbl[None])
    en_, wd = typ_harm_en.get(hid, ("", ""))
    reihen.append([hid if hid is not None else "", harm_label.get(hid, ""), repr(en_) if en_ else "", wd, w, art,
                   kat, n, f"{n / N_ALLE:.4f}", len(typ_harm_b[hid]), bem])
schreibe("typ_harmonisiert.csv", ["type_harmonized_id", "type_harmonized_de", "type_harmonized_en",
                                  "wikidata_id", "ech_affair_type", "match_art",
                                  "kategorie_ohne_entsprechung", "n_geschaefte", "anteil", "n_parlamente",
                                  "bemerkung"], reihen)

# englische Labels/Wikidata aus affairs fuer Befunde (nur Kontrolle)
reihen = []
selten = collections.Counter()
selten_b = collections.defaultdict(set)
for key, n in typ_lok.most_common():
    lok, sp, hde = key
    hid, (lw, la, lk), (cw, ca, ck, cq) = typ_lok_info[key]
    if n < MIN_LABEL and lok:
        k = (hde, cw, ca)
        selten[k] += n
        selten_b[k] |= typ_lok_b[key]
        continue
    reihen.append([lok or "(leer)", sp, hde, n, len(typ_lok_b[key]), lw, la, lk, cw, ca, ck, cq])
for (hde, cw, ca), n in selten.most_common():
    reihen.append([f"(seltene Bezeichnungen < {MIN_LABEL})", "", hde, n, len(selten_b[(hde, cw, ca)]), "", "",
                   "", cw, ca, "", "kombiniert"])
schreibe("typ_lokal.csv", ["lokale_bezeichnung", "sprache", "type_harmonized_de", "n_geschaefte",
                           "n_parlamente", "vorschlag_lokal", "match_lokal", "kategorie_lokal",
                           "ech_affair_type_kombiniert", "match_kombiniert", "kategorie_kombiniert",
                           "quelle_kombiniert"], reihen)

reihen = []
for kat, n in ohne.most_common():
    bsp = "; ".join(f"{k} ({v})" for k, v in ohne_bsp[kat].most_common(6) if v >= MIN_LABEL)
    reihen.append([kat, n, f"{n / N_ALLE:.4f}", len(ohne_b[kat]), bsp])
schreibe("typ_ohne_entsprechung.csv", ["kategorie", "n_geschaefte", "anteil", "n_parlamente",
                                       "haeufigste_lokale_bezeichnungen"], reihen)

reihen = [[hde, hw, lok, lw, n, len(konflikt_b[(hde, hw, lok, lw)])]
          for (hde, hw, lok, lw), n in konflikt.most_common() if n >= MIN_LABEL]
schreibe("typ_konflikt.csv", ["type_harmonized_de", "ech_aus_harmonisierung", "lokale_bezeichnung",
                              "ech_aus_lokaler_regel", "n_geschaefte", "n_parlamente"], reihen)

# ======================================================================= Rollen
reihen = []
selten = collections.Counter()
selten_aff = collections.defaultdict(set)
selten_b = collections.defaultdict(set)
for key, n in rolle.most_common():
    rh, rde, rfr, rit, typ = key
    ort, vorschlag, art, bem = R.ROLLE_HARMONISIERT.get(rh, ("", "", "unbestimmt", ""))
    klasse = rolle_info[key]
    if n < MIN_LABEL and (rde or rfr or rit):
        k = (rh, klasse)
        selten[k] += n
        selten_aff[k] |= rolle_aff[key]
        selten_b[k] |= rolle_b[key]
        continue
    reihen.append([rh, rde, rfr, rit, typ, n, len(rolle_aff[key]), len(rolle_b[key]), ort, vorschlag, art,
                   klasse, bem])
for (rh, klasse), n in selten.most_common():
    reihen.append([rh, f"(seltene Bezeichnungen < {MIN_LABEL})", "", "", "", n, len(selten_aff[(rh, klasse)]),
                   len(selten_b[(rh, klasse)]), "", "", "", klasse, "kombiniert"])
rk = collections.Counter()
rk_aff = collections.defaultdict(set)
rk_b = collections.defaultdict(set)
for key, n in rolle.items():
    k = (key[0], rolle_info[key])
    rk[k] += n
    rk_aff[k] |= rolle_aff[key]
    rk_b[k] |= rolle_b[key]
schreibe("rolle_klassen.csv", ["role_harmonized", "sponsor_role_lokal_regel", "n_eintraege", "n_geschaefte",
                               "n_parlamente"],
         [[rh, k, n, len(rk_aff[(rh, k)]), len(rk_b[(rh, k)])] for (rh, k), n in rk.most_common()])
schreibe("rolle_sponsor.csv", ["role_harmonized", "role_de", "role_fr", "role_it", "type", "n_eintraege",
                               "n_geschaefte", "n_parlamente", "ech_ort", "sponsor_role_harmonisiert",
                               "match_harmonisiert", "sponsor_role_lokal_regel", "bemerkung"], reihen)

# ======================================================================= Ereignisse
harm_de: dict[int, tuple] = {}
for e in zeilen(EXPORTE / "events.ndjson.gz"):
    hid = e.get("title_harmonized_id")
    if hid is not None and hid not in harm_de:
        harm_de[hid] = (e.get("title_harmonized_de") or "", e.get("title_harmonized_en") or "")
    if len(harm_de) >= len(ev_harm):
        break
reihen = []
for hid, n in ev_harm.most_common():
    s, et, en, st, art, bem = R.EREIGNIS_HARM.get(hid, ("", "", "", "", "unbestimmt", "nicht zugeordnet"))
    emp = R.EMPFEHLUNG_HARM.get(hid, "")
    de, en_ = harm_de.get(hid, ("", ""))
    reihen.append([hid, de, en_, n, len(ev_harm_aff[hid]), len(ev_harm_b[hid]), s, et, en, st, emp, art,
                   ev_harm_abw[hid], f"{ev_harm_abw[hid] / n:.3f}", bem])
schreibe("ereignis_harmonisiert.csv", ["title_harmonized_id", "title_harmonized_de", "title_harmonized_en",
                                       "n_ereignisse", "n_geschaefte", "n_parlamente", "ech_schritt",
                                       "procedure_stage", "procedure_decision", "status", "recommendation",
                                       "match_art", "n_lokal_abweichend", "anteil_lokal_abweichend",
                                       "bemerkung"], reihen)
reihen = []
for k, n in ev_lok.most_common():
    if n < MIN_LOKAL_TITEL:
        break
    s, et, en, st, emp = ev_lok_info[k]
    reihen.append([k, n, len(ev_lok_b[k]), ",".join(sorted(ev_lok_b[k])), s, et, en, st, emp])
schreibe("ereignis_lokal_ohne_harmonisierung.csv", ["lokaler_titel", "n_ereignisse", "n_parlamente",
                                                    "parlamente", "ech_schritt", "procedure_stage",
                                                    "procedure_decision", "status", "recommendation"], reihen)

# ======================================================================= Status
reihen = []
for (sname, sh), n in stat_lok.most_common():
    if n < MIN_LABEL:
        continue
    st, et, en = R.status_lokal(sname)
    reihen.append([sname or "(leer)", sh, n, len(stat_lok_b[(sname, sh)]), st, et, en])
schreibe("status_lokal.csv", ["state_name_lokal", "state_name_harmonized_de", "n_geschaefte", "n_parlamente",
                              "status_vorschlag", "procedure_stage", "procedure_decision"], reihen)

# ======================================================================= Texttypen
reihen = []
for key, n in sorted(texttyp.items(), key=lambda x: (-x[1])):
    bk, label = key
    w, art = texttyp_info[key]
    ls = texttyp_len[key]
    reihen.append([bk, eb(bk), label, n, len(texttyp_aff[key]), w, art, int(statistics.median(ls)) if ls else 0])
schreibe("texttyp.csv", ["body_key", "ebene", "texttyp_lokal", "n_texte", "n_geschaefte", "text_type",
                         "match_art", "median_zeichen"], reihen)

# ======================================================================= Verteilungen
ent = collections.Counter()
ent_b = collections.defaultdict(set)
for aid, (_, e) in letzter_entscheid.items():
    k = (TYP_VON[aid] or "(kein eCH-Typ)", e)
    ent[k] += 1
    ent_b[k].add(GESCH[aid][0])
schreibe("entscheid_verteilung.csv", ["ech_affair_type", "letzter_entscheid", "n_geschaefte", "n_parlamente"],
         [[t, e, n, len(ent_b[(t, e)])] for (t, e), n in sorted(ent.items(), key=lambda x: (x[0][0], -x[1]))])
emp = collections.Counter()
emp_b = collections.defaultdict(set)
for aid, (_, wert, quelle) in letzte_empf.items():
    k = (TYP_VON[aid] or "(kein eCH-Typ)", wert, "ereignis_" + quelle)
    emp[k] += 1
    emp_b[k].add(GESCH[aid][0])
for aid, wert in che_text_empf.items():
    k = (TYP_VON[aid] or "(kein eCH-Typ)", wert, "text_bund")
    emp[k] += 1
    emp_b[k].add(GESCH[aid][0])
schreibe("empfehlung_verteilung.csv", ["ech_affair_type", "recommendation", "quelle", "n_geschaefte",
                                       "n_parlamente"],
         [[t, w, q, n, len(emp_b[(t, w, q)])] for (t, w, q), n in sorted(emp.items(),
                                                                       key=lambda x: (x[0][0], x[0][2], -x[1]))])

kz("parlamente_mit_geschaeften", len({g[0] for g in GESCH.values()}), "verschiedene body_key in affairs")
schreibe("kennzahlen.csv", ["kennzahl", "wert", "wie_berechnet"], KZ)
log("fertig")
