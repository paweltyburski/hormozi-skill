#!/usr/bin/env python3
"""Wyszukiwarka po notatkach (atomach wiedzy) z materiałów Alexa Hormoziego.

Czysty Python 3.8+, sama biblioteka standardowa. Przy pierwszym użyciu buduje indeks
(SQLite FTS5) z plików w ../ekstrakcje/ i zapisuje go w katalogu podręcznym; gdy FTS5 albo
zapis nie są dostępne, szuka w pamięci po plikach. Zapytania najlepiej po angielsku,
w słowach, jakich użyłby Hormozi albo jego rozmówca. Dwa-trzy krótkie warianty dają więcej
niż jedno długie.

Przykłady (z katalogu skilla):
    python3 scripts/szukaj.py "raise prices existing customers" --k 6
    python3 scripts/szukaj.py "one client most of revenue" --konsultacje
    python3 scripts/szukaj.py "capacity constraint" --typ DECISION_RULE
    python3 scripts/szukaj.py "manufacturer reseller" --typ CASE --od 2022
    python3 scripts/szukaj.py --doc YT-Gy-RmpRif-I                 # wszystkie atomy nagrania
    python3 scripts/szukaj.py --doc YT-Gy-RmpRif-I --around 00:01:30   # atomy wokół chwili
    python3 scripts/szukaj.py --info                                # liczby, tematy, typy

Wynik: cytowanie ID@hh:mm:ss, typ i temat atomu, tytuł nagrania, krótka teza i szczegół,
liczby, link do właściwej minuty (dla YouTube i podcastu) albo „materiał kursu, bez linku".
W paczce nie ma transkrypcji: atomy to notatki własnymi słowami.
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EKS = ROOT / "ekstrakcje"
META = EKS / "_dokumenty.tsv"
FIELDS = ("claim", "detail", "numbers", "applies_to", "business", "speakers", "questions", "quote")
STOP = set("""a an the and or but of to in on for with at by from as is are was were be been being it its this that
these those i you he she we they me my your our their do does did have has had not no so if then than too very can will
just about into over how what why when which who whom there here also get got more most some any""".split())
SCHEMA_VERSION = "2"


def hms(s):
    s = int(s)
    return "%02d:%02d:%02d" % (s // 3600, s % 3600 // 60, s % 60)


def parse_hms(text):
    try:
        parts = [int(x) for x in text.strip().split(":")]
    except ValueError:
        return 0
    while len(parts) < 3:
        parts.insert(0, 0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


# ---------------------------------------------------------------- wczytywanie

def load_meta():
    meta = {}
    if not META.exists():
        return meta
    with open(META, encoding="utf-8") as f:
        next(f, None)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 7:
                p += [""] * (7 - len(p))
            meta[p[0]] = {"kolekcja": p[1], "rodzaj": p[2], "data": p[3], "tytul": p[4], "link": p[5],
                          "konsultacja": 1 if p[6].strip() == "1" else 0}
    return meta


def unquote(v):
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        try:
            return json.loads(v)
        except ValueError:
            return v[1:-1]
    return v


def parse_doc(path):
    """Zwraca (nagłówek dokumentu, lista atomów) z jednego pliku .md."""
    head, atoms, cur, last = {}, [], None, None
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line.startswith("### "):
                parts = line[4:].split(" | ")
                cur = {"aid": parts[0].strip(), "typ": parts[1].strip() if len(parts) > 1 else "", "topic": "",
                       "also": "", "fw": "", "novelty": "", "ts": "00:00:00"}
                for p in parts[2:]:
                    k, _, v = p.partition(":")
                    if k.strip() in cur:
                        cur[k.strip()] = v.strip()
                for k in FIELDS:
                    cur[k] = ""
                atoms.append(cur)
                last = None
                continue
            m = re.match(r"^(\w+):\s?(.*)$", line)
            if cur is None:
                if m:
                    head[m.group(1)] = unquote(m.group(2).strip())
                continue
            if m and m.group(1) in FIELDS:
                last = m.group(1)
                cur[last] = m.group(2)
            elif line.strip() and last:
                cur[last] += "\n" + line
    return head, atoms


def read_all():
    meta = load_meta()
    docs, atoms = {}, []
    for p in sorted(EKS.glob("*.md")):
        head, at = parse_doc(p)
        did = head.get("doc_id") or p.stem
        m = meta.get(did, {})
        docs[did] = {"doc_id": did, "tytul": head.get("title") or m.get("tytul", ""), "gist": head.get("gist", ""),
                     "frameworks": head.get("frameworks_mentioned", ""), "kolekcja": m.get("kolekcja", ""),
                     "rodzaj": m.get("rodzaj", ""), "data": m.get("data", ""), "link": m.get("link", ""),
                     "konsultacja": m.get("konsultacja", 0)}
        for a in at:
            a["doc_id"] = did
            a["ts_s"] = parse_hms(a["ts"])
            atoms.append(a)
    return docs, atoms


# ---------------------------------------------------------------- indeks

def signature():
    files = list(EKS.glob("*.md")) + [META]
    n = size = mt = 0
    for p in files:
        if p.exists():
            st = p.stat()
            n += 1
            size += st.st_size
            mt = max(mt, int(st.st_mtime))
    return "%s:%d:%d:%d" % (SCHEMA_VERSION, n, size, mt)


def cache_paths():
    cands = []
    env = os.environ.get("HORMOZI_CACHE")
    if env:
        cands.append(Path(env))
    cands += [ROOT / ".cache", Path(tempfile.gettempdir()) / "hormozi_skill_cache"]
    return cands


def fts5_ok():
    try:
        c = sqlite3.connect(":memory:")
        c.execute("CREATE VIRTUAL TABLE t USING fts5(a)")
        c.close()
        return True
    except sqlite3.Error:
        return False


def build(con, docs, atoms):
    con.executescript("""
        CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT);
        CREATE TABLE docs (doc_id TEXT PRIMARY KEY, tytul TEXT, gist TEXT, frameworks TEXT, kolekcja TEXT,
                           rodzaj TEXT, data TEXT, link TEXT, konsultacja INTEGER);
        CREATE TABLE atoms (id INTEGER PRIMARY KEY, aid TEXT, doc_id TEXT, typ TEXT, topic TEXT, also TEXT,
                            fw TEXT, novelty TEXT, ts TEXT, ts_s INTEGER, claim TEXT, detail TEXT, numbers TEXT,
                            applies_to TEXT, business TEXT, speakers TEXT, questions TEXT, quote TEXT);
        CREATE VIRTUAL TABLE fts USING fts5(claim, detail, numbers, applies_to, business, questions, quote, fw,
                                            tytul, tokenize='porter unicode61');
    """)
    con.executemany("INSERT INTO docs VALUES (?,?,?,?,?,?,?,?,?)",
                    [(d["doc_id"], d["tytul"], d["gist"], d["frameworks"], d["kolekcja"], d["rodzaj"], d["data"],
                      d["link"], d["konsultacja"]) for d in docs.values()])
    for i, a in enumerate(atoms, 1):
        con.execute("INSERT INTO atoms VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (i, a["aid"], a["doc_id"], a["typ"], a["topic"], a["also"], a["fw"], a["novelty"], a["ts"],
                     a["ts_s"], a["claim"], a["detail"], a["numbers"], a["applies_to"], a["business"],
                     a["speakers"], a["questions"], a["quote"]))
        con.execute("INSERT INTO fts(rowid, claim, detail, numbers, applies_to, business, questions, quote, fw, tytul)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (i, a["claim"], a["detail"], a["numbers"], a["applies_to"], a["business"], a["questions"],
                     a["quote"], a["fw"], docs[a["doc_id"]]["tytul"]))
    con.execute("INSERT INTO meta VALUES ('sig', ?)", (signature(),))
    con.commit()


def open_index():
    """Zwraca (połączenie SQLite, None) albo (None, (docs, atoms)) w trybie awaryjnym bez FTS5."""
    if not fts5_ok():
        return None, read_all()
    sig = signature()
    for d in cache_paths():
        try:
            d.mkdir(parents=True, exist_ok=True)
            dbp = d / "atomy.sqlite"
            if dbp.exists():
                try:
                    con = sqlite3.connect(str(dbp))
                    con.row_factory = sqlite3.Row
                    if con.execute("SELECT v FROM meta WHERE k='sig'").fetchone()["v"] == sig:
                        return con, None
                    con.close()
                except sqlite3.Error:
                    pass
                dbp.unlink()
            print("Buduję indeks (jednorazowo, kilka sekund)...", file=sys.stderr)
            docs, atoms = read_all()
            tmp = d / ("atomy.%d.tmp" % os.getpid())
            con = sqlite3.connect(str(tmp))
            build(con, docs, atoms)
            con.close()
            os.replace(str(tmp), str(dbp))
            con = sqlite3.connect(str(dbp))
            con.row_factory = sqlite3.Row
            return con, None
        except (OSError, sqlite3.Error):
            continue
    # żaden katalog niezapisywalny: indeks w pamięci
    docs, atoms = read_all()
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    build(con, docs, atoms)
    return con, None


# ---------------------------------------------------------------- zapytania

def terms_of(text):
    return [t for t in re.findall(r"[A-Za-z0-9$%']+", text) if t.lower() not in STOP]


def fts_query(text):
    if re.search(r'"| AND | OR | NOT |NEAR\(', text):
        return text
    tokens = re.findall(r"[A-Za-z0-9$%']+", text)
    terms = [t for t in tokens if t.lower() not in STOP]
    parts = ['"%s"' % t.replace("'", " ") for t in terms]
    parts += ['"%s %s"' % (a, b) for a, b in zip(tokens, tokens[1:]) if a.lower() not in STOP and b.lower() not in STOP]
    return " OR ".join(dict.fromkeys(parts)) or '"%s"' % text.replace('"', " ")


def year_of(d):
    m = re.match(r"(\d{4})", d or "")
    return int(m.group(1)) if m else None


def filters_ok(row, a):
    if a.typ and row["typ"].upper() != a.typ.upper():
        return False
    if a.temat and a.temat.lower() not in (row["topic"] + "," + row["also"]).lower():
        return False
    if a.konsultacje and not row["konsultacja"]:
        return False
    if a.kolekcja and a.kolekcja.lower() not in row["kolekcja"].lower():
        return False
    y = year_of(row["data"])
    if a.od and (y is None or y < a.od):
        return False
    if a.do and (y is None or y > a.do):
        return False
    return True


def search_fts(con, a):
    q = fts_query(" ".join(a.query))
    sql = ("SELECT atoms.*, docs.tytul, docs.data, docs.kolekcja, docs.rodzaj, docs.link, docs.konsultacja,"
           " bm25(fts, 10, 4, 3, 2, 2, 2, 3, 2, 1) AS r FROM fts JOIN atoms ON atoms.id = fts.rowid"
           " JOIN docs ON docs.doc_id = atoms.doc_id WHERE fts MATCH ? ORDER BY r LIMIT 3000")
    try:
        rows = con.execute(sql, (q,)).fetchall()
    except sqlite3.Error as e:
        sys.exit("Błąd składni zapytania: %s" % e)
    return [r for r in rows if filters_ok(r, a)][: a.k]


def search_mem(docs, atoms, a):
    terms = [t.lower() for t in terms_of(" ".join(a.query))]
    if not terms:
        return []
    scored = []
    for at in atoms:
        d = docs[at["doc_id"]]
        row = dict(at)
        row.update({"tytul": d["tytul"], "data": d["data"], "kolekcja": d["kolekcja"], "rodzaj": d["rodzaj"],
                    "link": d["link"], "konsultacja": d["konsultacja"]})
        if not filters_ok(row, a):
            continue
        head = (at["claim"] + " " + at["fw"]).lower()
        body = (at["detail"] + " " + at["numbers"] + " " + at["applies_to"] + " " + at["business"] + " "
                + at["questions"] + " " + at["quote"] + " " + d["tytul"]).lower()
        s = sum(3 * head.count(t) + body.count(t) for t in terms)
        if s:
            row["r"] = -s
            scored.append(row)
    scored.sort(key=lambda r: r["r"])
    return scored[: a.k]


# ---------------------------------------------------------------- wydruk

def link_for(r):
    kind, url, ts = r["rodzaj"], r["link"], r["ts_s"]
    if kind in ("youtube", "livestream", "moremozi") and url:
        return "%s&t=%ds" % (url, ts)
    if kind == "podcast" and url:
        return "%s#t=%d (odcinek audio)" % (url, ts)
    if kind == "course":
        return "materiał kursu, bez linku"
    return "brak publicznego linku"


def clip(text, words):
    w = text.split()
    return text if len(w) <= words else " ".join(w[:words]) + " […]"


def show(r, n, full):
    flags = []
    if r["konsultacja"]:
        flags.append("rozmowa")
    if r["novelty"]:
        flags.append(r["novelty"])
    print("%s[%s@%s] %s | %s%s" % ("%d. " % n if n else "", r["doc_id"], r["ts"], r["typ"], r["topic"],
                                   (" | " + ", ".join(flags)) if flags else ""))
    meta = " | ".join(x for x in (r["tytul"], r["data"], r["kolekcja"]) if x)
    print("   " + meta)
    print("   " + r["claim"].strip())
    det = r["detail"].strip()
    if det:
        print("   " + (det if full else clip(det, 70)).replace("\n", "\n   "))
    for key, label in (("numbers", "liczby"), ("applies_to", "dotyczy"), ("business", "firma"),
                       ("quote", "cytat")):
        if r[key].strip():
            print("   %s: %s" % (label, (r[key].strip() if full else clip(r[key].strip(), 40)).replace("\n", " ")))
    if full:
        for key, label in (("speakers", "mówcy"), ("questions", "pytania")):
            if r[key].strip():
                print("   %s: %s" % (label, r[key].strip().replace("\n", "\n   ")))
    print("   " + link_for(r))
    print()


def get_doc(con, mem, did):
    """Zwraca (wiersz dokumentu, atomy) z indeksu albo z pamięci."""
    if con is not None:
        d = con.execute("SELECT * FROM docs WHERE doc_id=?", (did,)).fetchone()
        if not d:
            like = [r[0] for r in con.execute("SELECT doc_id FROM docs WHERE doc_id LIKE ? LIMIT 8", ("%" + did + "%",))]
            sys.exit("Nie ma nagrania %s.%s" % (did, (" Podobne: " + ", ".join(like)) if like else ""))
        rows = con.execute("SELECT atoms.*, docs.tytul, docs.data, docs.kolekcja, docs.rodzaj, docs.link,"
                           " docs.konsultacja FROM atoms JOIN docs ON docs.doc_id=atoms.doc_id"
                           " WHERE atoms.doc_id=? ORDER BY atoms.id", (did,)).fetchall()
        return d, rows
    docs, atoms = mem
    if did not in docs:
        sys.exit("Nie ma nagrania %s." % did)
    d = docs[did]
    rows = []
    for at in atoms:
        if at["doc_id"] == did:
            r = dict(at)
            r.update({k: d[k] for k in ("tytul", "data", "kolekcja", "rodzaj", "link", "konsultacja")})
            rows.append(r)
    return d, rows


def cmd_doc(con, mem, a):
    d, rows = get_doc(con, mem, a.doc)
    print("%s | %s | %s | %s" % (d["doc_id"], d["tytul"], d["data"], d["kolekcja"]))
    if d["gist"]:
        print("Streszczenie: " + d["gist"])
    if d["frameworks"] and d["frameworks"] != "-":
        print("Frameworki: " + d["frameworks"])
    print("Atomów: %d. W paczce nie ma transkrypcji, tylko notatki; pełne brzmienie jest pod linkiem (jeśli jest).\n"
          % len(rows))
    if a.around:
        ts = parse_hms(a.around)
        rows = sorted(rows, key=lambda r: abs(r["ts_s"] - ts))[: max(a.k, 5)]
        rows.sort(key=lambda r: r["ts_s"])
    for r in rows:
        show(r, 0, True)


def cmd_info(con, mem):
    if con is not None:
        n = con.execute("SELECT COUNT(*) FROM atoms").fetchone()[0]
        nd = con.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
        coll = con.execute("SELECT kolekcja, COUNT(*) FROM docs GROUP BY 1 ORDER BY 2 DESC").fetchall()
        typ = con.execute("SELECT typ, COUNT(*) FROM atoms GROUP BY 1 ORDER BY 2 DESC").fetchall()
        top = con.execute("SELECT topic, COUNT(*) FROM atoms GROUP BY 1 ORDER BY 2 DESC").fetchall()
    else:
        docs, atoms = mem
        from collections import Counter
        n, nd = len(atoms), len(docs)
        coll = Counter(d["kolekcja"] for d in docs.values()).most_common()
        typ = Counter(x["typ"] for x in atoms).most_common()
        top = Counter(x["topic"] for x in atoms).most_common()
    print("Nagrań i lekcji: %d, atomów: %d" % (nd, n))
    print("Kolekcje: " + ", ".join("%s (%d)" % (k or "?", c) for k, c in coll))
    print("Typy (--typ): " + ", ".join("%s (%d)" % (k, c) for k, c in typ))
    print("Tematy (--temat): " + ", ".join("%s (%d)" % (k, c) for k, c in top))


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Wyszukiwarka po atomach wiedzy Hormoziego (bez transkrypcji).")
    ap.add_argument("query", nargs="*", help="zapytanie, najlepiej po angielsku")
    ap.add_argument("--k", type=int, default=8, help="liczba wyników (domyślnie 8)")
    ap.add_argument("--typ", help="FRAMEWORK DEFINITION PRINCIPLE DECISION_RULE BENCHMARK TACTIC SCRIPT CASE "
                                  "DIAGNOSTIC_Q EXAMPLE EVOLUTION")
    ap.add_argument("--temat", help="np. pricing, offers, retention-ltv (patrz --info)")
    ap.add_argument("--konsultacje", action="store_true", help="tylko nagrania z rozmowami z właścicielami firm")
    ap.add_argument("--kolekcja", help='np. "Offers Course", Podcast, Filmy, Livestreamy, MoreMozi')
    ap.add_argument("--od", type=int, help="od roku")
    ap.add_argument("--do", type=int, help="do roku")
    ap.add_argument("--doc", help="pokaż atomy jednego nagrania, np. YT-Gy-RmpRif-I")
    ap.add_argument("--around", help="z --doc: atomy najbliższe chwili hh:mm:ss")
    ap.add_argument("--pelne", action="store_true", help="pełny szczegół atomu zamiast skrótu")
    ap.add_argument("--atomy", action="store_true", help="(zgodność) wszystko i tak szuka w atomach")
    ap.add_argument("--info", action="store_true", help="liczby, typy i tematy w bazie")
    a = ap.parse_args()

    con, mem = open_index()
    if a.info:
        return cmd_info(con, mem)
    if a.doc:
        return cmd_doc(con, mem, a)
    if not a.query:
        ap.print_help()
        return
    rows = search_fts(con, a) if con is not None else search_mem(mem[0], mem[1], a)
    if not rows:
        print("Brak wyników. Spróbuj innych słów (po angielsku), krótszego zapytania albo bez filtrów.")
        return
    for i, r in enumerate(rows, 1):
        show(r, i, a.pelne)


if __name__ == "__main__":
    main()
