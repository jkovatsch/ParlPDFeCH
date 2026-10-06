# SPDX-License-Identifier: Apache-2.0
"""Korpus-Profil Teil 1-4 (Teilfrage 2.2): Parlamente, Geschäfte pro Jahr,
lokale und harmonisierte Geschäftstypen, Status.

Quelle: <data>/roh/exports/affairs.ndjson.gz, bodies.ndjson.gz (Stand 2026-10-04T13:26Z).
Ausgabe: <data>/analyse/korpus/*.csv, Kennzahlen auf stdout.

Aufruf (im Ordner track_2a): uv run python src/m02_korpus_geschaefte.py
"""

from __future__ import annotations

import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True  # kein __pycache__ im Projekt
sys.path.insert(0, str(Path(__file__).resolve().parent))

from m02_korpus_basis import (  # noqa: E402
    EBENEN,
    anteil,
    bodies,
    ebene,
    erster,
    leer,
    schreibe_csv,
    zeilen,
)

STICHTAG = "2026-10-04"
SPRACHEN = ["de", "fr", "it", "rm"]


def main() -> None:
    if {"-h", "--help"} & set(sys.argv[1:]):
        print(__doc__)
        return
    B = bodies()

    # Pro Parlament
    n = Counter()
    beg_min: dict[str, str] = {}
    beg_max: dict[str, str] = {}
    ohne_beg = Counter()
    beg_zukunft = Counter()
    titel_sprache = defaultdict(Counter)
    ohne_lok_typ = Counter()
    ohne_harm_typ = Counter()
    mit_lok_status = Counter()
    mit_harm_status = Counter()

    # Global
    jahr_ebene = Counter()
    body_jahr = Counter()
    lok_typ = Counter()  # (body, de, fr, it, rm, harm_id) -> n
    harm_typ_namen: dict = {}
    harm_typ_n = Counter()
    harm_typ_bodies = defaultdict(set)
    harm_typ_labels = defaultdict(set)
    status_harm_namen: dict = {}
    status_harm_n = Counter()
    status_harm_bodies = defaultdict(set)
    status_lok = Counter()  # (body, label) -> n
    kreuz_typ = Counter()  # (lokal vorhanden, harmonisiert vorhanden)
    ids = set()
    doppelt = 0

    for a in zeilen("affairs"):
        if a["id"] in ids:
            doppelt += 1
        ids.add(a["id"])
        k = a["body_key"]
        e = ebene(B[k])
        n[k] += 1

        d = a.get("begin_date")
        if leer(d):
            ohne_beg[k] += 1
            jahr_ebene[("ohne Datum", e)] += 1
        else:
            d10 = d[:10]
            beg_min[k] = min(beg_min.get(k, d10), d10)
            beg_max[k] = max(beg_max.get(k, d10), d10)
            if d10 > STICHTAG:
                beg_zukunft[k] += 1
            jahr_ebene[(d[:4], e)] += 1
            body_jahr[(k, d[:4])] += 1

        for s in SPRACHEN:
            if not leer(a.get(f"title_{s}")):
                titel_sprache[k][s] += 1

        lt = tuple(a.get(f"type_name_{s}") for s in SPRACHEN)
        hid = a.get("type_harmonized_id")
        lok_vorhanden = any(not leer(x) for x in lt)
        if not lok_vorhanden:
            ohne_lok_typ[k] += 1
        if hid is None:
            ohne_harm_typ[k] += 1
        kreuz_typ[(lok_vorhanden, hid is not None)] += 1
        lok_typ[(k, *lt, hid)] += 1
        if hid is not None:
            harm_typ_namen[hid] = (
                a.get("type_harmonized_de"),
                a.get("type_harmonized_fr"),
                a.get("type_harmonized_it"),
                a.get("type_harmonized_en"),
                a.get("type_harmonized_wikidata_id"),
            )
            harm_typ_n[hid] += 1
            harm_typ_bodies[hid].add(k)
            if lok_vorhanden:
                harm_typ_labels[hid].add((k, erster(*lt)))

        sl = erster(*(a.get(f"state_name_{s}") for s in SPRACHEN))
        if sl is not None:
            mit_lok_status[k] += 1
            status_lok[(k, sl)] += 1
        sid = a.get("state_name_harmonized_id")
        status_harm_n[sid] += 1
        if sid is not None:
            mit_harm_status[k] += 1
            status_harm_bodies[sid].add(k)
            status_harm_namen[sid] = tuple(
                a.get(f"state_name_harmonized_{s}") for s in SPRACHEN
            )

    total = sum(n.values())

    # ---------- 1. Parlamente ----------
    lok_labels_pro_body = defaultdict(set)
    for (k, de, fr, it, rm, hid), c in lok_typ.items():
        lab = erster(de, fr, it, rm)
        if lab is not None:
            lok_labels_pro_body[k].add(lab)

    harm_pro_body = defaultdict(set)
    for (k, de, fr, it, rm, hid), c in lok_typ.items():
        if hid is not None:
            harm_pro_body[k].add(hid)

    zeilen_p = []
    for k in sorted(n, key=lambda x: (EBENEN.index(ebene(B[x])), -n[x])):
        b = B[k]
        ts = titel_sprache[k]
        titelsprachen = ",".join(s.upper() for s in SPRACHEN if ts[s] / n[k] >= 0.01)
        zeilen_p.append(
            [
                k,
                b.get("name_de"),
                ebene(b),
                b.get("type_name_de"),
                b.get("canton_key") or "",
                b.get("lang") or "",
                b.get("languages") or "",
                titelsprachen,
                n[k],
                beg_min.get(k, ""),
                beg_max.get(k, ""),
                ohne_beg[k],
                beg_zukunft[k],
                *(anteil(ts[s], n[k]) for s in SPRACHEN),
                len(lok_labels_pro_body[k]),
                len(harm_pro_body[k]),
                anteil(ohne_lok_typ[k], n[k]),
                anteil(ohne_harm_typ[k], n[k]),
                anteil(mit_lok_status[k], n[k]),
                anteil(mit_harm_status[k], n[k]),
            ]
        )
    schreibe_csv(
        "parlamente.csv",
        [
            "body_key", "name_de", "ebene", "typ_name_de", "canton_key", "lang",
            "languages", "titelsprachen_ab_1pct", "anzahl_geschaefte",
            "begin_date_min", "begin_date_max", "ohne_begin_date",
            f"begin_date_nach_{STICHTAG}", "anteil_title_de", "anteil_title_fr",
            "anteil_title_it", "anteil_title_rm", "anzahl_lokale_typbezeichnungen",
            "anzahl_harmonisierte_typen", "anteil_ohne_lokalen_typ", "anteil_ohne_harmonisierten_typ",
            "anteil_mit_lokalem_status", "anteil_mit_harmonisiertem_status",
        ],
        zeilen_p,
    )

    # Ebene x Sprache
    es = Counter()
    es_n = Counter()
    for k in n:
        b = B[k]
        sch = (ebene(b), b.get("lang") or "keine Angabe", b.get("languages") or "keine Angabe")
        es[sch] += 1
        es_n[sch] += n[k]
    schreibe_csv(
        "parlamente_ebene_sprache.csv",
        ["ebene", "lang", "languages", "anzahl_parlamente", "anzahl_geschaefte"],
        [[*s, es[s], es_n[s]] for s in sorted(es, key=lambda s: (EBENEN.index(s[0]), s[1], s[2]))],
    )

    # Kontext: Parlamente laut bodies (has_parliament) gegenüber Parlamenten mit Geschäften
    hp = Counter()
    hp_mit = Counter()
    mit = Counter()
    for k, b in B.items():
        e = ebene(b)
        if b.get("has_parliament") is True:
            hp[e] += 1
            if k in n:
                hp_mit[e] += 1
        if k in n:
            mit[e] += 1
    schreibe_csv(
        "parlamente_abdeckung.csv",
        ["ebene", "bodies_has_parliament_true", "davon_mit_geschaeften", "bodies_mit_geschaeften", "geschaefte"],
        [
            [e, hp[e], hp_mit[e], mit[e], sum(n[k] for k in n if ebene(B[k]) == e)]
            for e in EBENEN
        ],
    )

    # ---------- 2. Geschäfte pro Jahr ----------
    parl_jahr = defaultdict(set)
    for (k, j) in body_jahr:
        parl_jahr[j].add(k)
    for k in ohne_beg:
        if ohne_beg[k]:
            parl_jahr["ohne Datum"].add(k)
    jahre = sorted({j for j, _ in jahr_ebene}, key=lambda j: (j == "ohne Datum", j))
    schreibe_csv(
        "geschaefte_pro_jahr.csv",
        ["jahr", "gesamt", *[e.lower() for e in EBENEN], "parlamente_mit_geschaeften",
         *[f"parlamente_{e.lower()}" for e in EBENEN]],
        [[j, sum(jahr_ebene[(j, e)] for e in EBENEN), *[jahr_ebene[(j, e)] for e in EBENEN],
          len(parl_jahr[j]), *[sum(1 for k in parl_jahr[j] if ebene(B[k]) == e) for e in EBENEN]] for j in jahre],
    )
    schreibe_csv(
        "geschaefte_pro_parlament_jahr.csv",
        ["body_key", "ebene", "jahr", "anzahl_geschaefte"],
        [[k, ebene(B[k]), j, c] for (k, j), c in sorted(body_jahr.items())],
    )

    # ---------- 3. Geschäftstypen ----------
    schreibe_csv(
        "typen_lokal.csv",
        [
            "body_key", "ebene", "type_name_de", "type_name_fr", "type_name_it", "type_name_rm",
            "type_harmonized_id", "type_harmonized_de", "type_harmonized_en", "anzahl_geschaefte",
        ],
        [
            [
                k, ebene(B[k]), de or "", fr or "", it or "", rm or "",
                hid if hid is not None else "",
                harm_typ_namen.get(hid, ("",) * 5)[0] or "",
                harm_typ_namen.get(hid, ("",) * 5)[3] or "",
                c,
            ]
            for (k, de, fr, it, rm, hid), c in sorted(
                lok_typ.items(), key=lambda x: (x[0][0], -x[1])
            )
        ],
    )
    zeilen_h = []
    for hid in sorted(harm_typ_n, key=lambda h: -harm_typ_n[h]):
        de, fr, it, en, wd = harm_typ_namen[hid]
        zeilen_h.append(
            [hid, de, fr, it, en, wd, harm_typ_n[hid], anteil(harm_typ_n[hid], total),
             len(harm_typ_bodies[hid]), len(harm_typ_labels[hid])]
        )
    ohne_h = sum(ohne_harm_typ.values())
    zeilen_h.append(["", "(kein harmonisierter Typ)", "", "", "", "", ohne_h, anteil(ohne_h, total),
                     sum(1 for k in n if ohne_harm_typ[k]), ""])
    schreibe_csv(
        "typen_harmonisiert.csv",
        [
            "type_harmonized_id", "type_harmonized_de", "type_harmonized_fr", "type_harmonized_it",
            "type_harmonized_en", "wikidata_id", "anzahl_geschaefte", "anteil_geschaefte",
            "anzahl_parlamente", "anzahl_lokale_bezeichnungen_body_label",
        ],
        zeilen_h,
    )

    # Kennzahlen lokale Bezeichnungen
    paare = {(k, lab) for k, labs in lok_labels_pro_body.items() for lab in labs}
    strings = {lab for _, lab in paare}
    norm = {" ".join(lab.lower().split()) for lab in strings}
    kombis = {key[:5] for key in lok_typ if any(not leer(x) for x in key[1:5])}
    paare_ohne_harm = {
        (key[0], erster(*key[1:5])) for key in lok_typ
        if key[5] is None and any(not leer(x) for x in key[1:5])
    }
    paare_mit_harm = {
        (key[0], erster(*key[1:5])) for key in lok_typ
        if key[5] is not None and any(not leer(x) for x in key[1:5])
    }
    abbildung = defaultdict(set)
    abbildung_n = Counter()
    for key, c in lok_typ.items():
        lab = erster(*key[1:5])
        if lab is not None:
            abbildung[(key[0], lab)].add(key[5])
            abbildung_n[(key[0], lab)] += c
    uneinheitlich = [p for p, hs in abbildung.items() if len(hs) > 1]
    uneinheitlich_n = sum(abbildung_n[p] for p in uneinheitlich)
    schreibe_csv(
        "typen_lokal_uneinheitlich.csv",
        ["body_key", "lokale_bezeichnung", "type_harmonized_ids", "anzahl_geschaefte"],
        [[p[0], p[1], ";".join("leer" if h is None else str(h) for h in sorted(abbildung[p], key=lambda h: -1 if h is None else h)),
          abbildung_n[p]] for p in sorted(uneinheitlich)],
    )
    gesch_lok_ohne_harm = sum(
        c for key, c in lok_typ.items() if key[5] is None and any(not leer(x) for x in key[1:5])
    )

    # ---------- 4. Status ----------
    zeilen_s = []
    for sid in sorted(status_harm_n, key=lambda s: -status_harm_n[s]):
        if sid is None:
            zeilen_s.append(["", "(kein harmonisierter Status)", "", "", "", status_harm_n[sid],
                             anteil(status_harm_n[sid], total), ""])
        else:
            de, fr, it, rm = status_harm_namen[sid]
            zeilen_s.append([sid, de, fr, it, rm, status_harm_n[sid], anteil(status_harm_n[sid], total),
                             ";".join(sorted(status_harm_bodies[sid]))])
    schreibe_csv(
        "status_harmonisiert.csv",
        ["state_name_harmonized_id", "de", "fr", "it", "rm", "anzahl_geschaefte", "anteil_geschaefte", "body_keys"],
        zeilen_s,
    )
    schreibe_csv(
        "status_lokal.csv",
        ["body_key", "ebene", "state_name_lokal", "anzahl_geschaefte"],
        [[k, ebene(B[k]), lab, c] for (k, lab), c in sorted(status_lok.items(), key=lambda x: (x[0][0], -x[1]))],
    )

    # ---------- Kennzahlen ----------
    pe = Counter(ebene(B[k]) for k in n)
    ge = Counter()
    for k in n:
        ge[ebene(B[k])] += n[k]
    print(f"Geschäfte gesamt: {total} (doppelte IDs: {doppelt})")
    print(f"Parlamente mit Geschäften: {len(n)}")
    for e in EBENEN:
        print(f"  {e}: {pe[e]} Parlamente, {ge[e]} Geschäfte ({ge[e] / total:.1%})")
    gem_sub = Counter(B[k]["type_name_de"] for k in n if ebene(B[k]) == "Gemeinde")
    print(f"  Gemeinde-Untertypen: {dict(gem_sub)}")
    print("Ebene x lang:", {f"{s[0]}|{s[1]}|{s[2]}": (es[s], es_n[s]) for s in es})
    print(f"ohne begin_date: {sum(ohne_beg.values())}; begin_date nach Stichtag: {sum(beg_zukunft.values())}")
    print("frueheste Jahre:", jahre[:6], "| je Anzahl:", [sum(jahr_ebene[(j, e)] for e in EBENEN) for j in jahre[:6]])
    j_ab = [j for j in jahre if j != "ohne Datum"]
    for e in EBENEN:
        vor = sum(jahr_ebene[(j, e)] for j in j_ab if j < "2000")
        print(f"  vor 2000 {e}: {vor}")
    print(f"  vor 2000 gesamt: {sum(jahr_ebene[(j, e)] for j in j_ab if j < '2000' for e in EBENEN)}")
    for e in EBENEN:
        ks = [k for k in n if ebene(B[k]) == e]
        print(f"  Median Geschäfte pro Parlament {e}: {statistics.median(n[k] for k in ks)} "
              f"(min {min(n[k] for k in ks)}, max {max(n[k] for k in ks)})")
    print(f"  Median Geschäfte pro Parlament gesamt: {statistics.median(n.values())}")
    print(f"  lokale Typbezeichnungen pro Parlament: Median {statistics.median(len(lok_labels_pro_body[k]) for k in n)}, "
          f"max {max((len(lok_labels_pro_body[k]), k) for k in n)}")
    print(f"  harmonisierte Typen pro Parlament: Median {statistics.median(len(harm_pro_body[k]) for k in n)}")
    print(f"  Parlamente ohne lokalen Status: {sorted(k for k in n if not mit_lok_status[k])}")
    for e in EBENEN:
        ks = [k for k in n if ebene(B[k]) == e]
        ge_ = sum(n[k] for k in ks)
        print(f"  {e}: ohne lokalen Typ {sum(ohne_lok_typ[k] for k in ks) / ge_:.1%}, ohne harm. Typ "
              f"{sum(ohne_harm_typ[k] for k in ks) / ge_:.1%}, mit lokalem Status {sum(mit_lok_status[k] for k in ks) / ge_:.1%}")
    print(f"  Geschäfte ohne lokalen Typ nach Parlament: {[(k, ohne_lok_typ[k]) for k in sorted(n, key=lambda x: -ohne_lok_typ[x]) if ohne_lok_typ[k]][:8]}")
    print(f"Geschäfte 2015-2025: {sum(jahr_ebene[(j, e)] for j in j_ab if '2015' <= j <= '2025' for e in EBENEN)}")
    print(f"Lokale Typen: Paare (Parlament, Bezeichnung) = {len(paare)}; unterschiedliche Zeichenketten = {len(strings)}; "
          f"normalisiert (Kleinschreibung, Leerraum) = {len(norm)}; Kombinationen de/fr/it/rm pro Parlament = {len(kombis)}")
    print(f"  Paare ohne harmonisierten Typ (mind. einmal): {len(paare_ohne_harm)}; Paare mit harm. Typ: {len(paare_mit_harm)}")
    print(f"  Paare mit uneinheitlicher Zuordnung (mehr als ein harm. Wert inkl. leer): {len(uneinheitlich)}, "
          f"Geschäfte mit diesen Bezeichnungen: {uneinheitlich_n}")
    print(f"Harmonisierte Typen: {len(harm_typ_n)}")
    print(f"Ohne harmonisierten Typ: {ohne_h} ({ohne_h / total:.1%}); davon mit lokalem Typ: {gesch_lok_ohne_harm}")
    print(f"Ohne lokalen Typ: {sum(ohne_lok_typ.values())} ({sum(ohne_lok_typ.values()) / total:.1%})")
    print(f"Kreuz (lokal vorhanden, harmonisiert vorhanden): {dict(kreuz_typ)}")
    print(f"Parlamente ohne jeden harmonisierten Typ: {[k for k in n if ohne_harm_typ[k] == n[k]]}")
    print(f"Parlamente mit >=50% ohne harm. Typ: {[(k, round(ohne_harm_typ[k] / n[k], 3), n[k]) for k in n if ohne_harm_typ[k] / n[k] >= 0.5]}")
    nh = status_harm_n[None]
    print(f"Ohne harmonisierten Status: {nh} ({nh / total:.2%}); Parlamente mit harm. Status: "
          f"{sorted({k for s in status_harm_bodies.values() for k in s})}")
    ml = sum(mit_lok_status.values())
    print(f"Mit lokalem Status: {ml} ({ml / total:.1%}); Parlamente mit lokalem Status: "
          f"{sum(1 for k in n if mit_lok_status[k])}; unterschiedliche (Parlament, Status)-Paare: {len(status_lok)}; "
          f"unterschiedliche Zeichenketten: {len({lab for _, lab in status_lok})}")


if __name__ == "__main__":
    main()
