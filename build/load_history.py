"""load_history.py - turn the Teknosys/Tender Desk export (tenders_full.csv) into engine-ready rows.

The export holds every tender EPADS (federal) and Punjab e-PADS published from 1 Jan to 14 Oct 2026.
Usage: python build/load_history.py path/to/tenders_full.csv
Writes build/out/history_rows.json. Only fields the engine and the market view need are kept.
"""
import csv, json, os, re, sys
csv.field_size_limit(10**8)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scraper"))
from classify import normalize_buyer

METHOD = [(r"petty purchase", "PP"), (r"quotation", "RFQ"), (r"two stage", "TS"), (r"two.?envelope", "OCB2"), (r"one.?envelope", "OCB1"), (r"framework", "FW"), (r"quality", "RFP")]
def method_of(p):
    p = (p or "").lower()
    for rx, c in METHOD:
        if re.search(rx, p):
            return c
    return ""
CAT = {"goods": "G", "works": "W", "non-consultancy services": "S", "services": "S", "consultancy services": "C"}
DESIG = re.compile(r"\b(officer|director|executive|secretary|manager|engineer|principal|registrar|chairman|deputy|assistant|head|incharge|in-charge|xen|sdo|superintendent|commandant|controller|administrator|dean|vice chancellor|project director)\b", re.I)
def org_of(s, b):
    if s == "EPADS":
        b0 = b.split(" , ")[0].strip()
        depth = 0; start = -1; groups = []
        for i, ch in enumerate(b0):
            if ch == "(":
                if depth == 0: start = i
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and start >= 0: groups.append((start, i)); start = -1
        if groups:
            st, en = groups[-1]
            inner = re.split(r"\s+/\s+", b0[st + 1:en].strip())[0].strip()
            outer = b0[:st].strip(" ,-")
            if len(inner.split()) >= 2 or re.search(r"\([A-Z]{2,8}\)", inner):
                return inner
            return outer or b0
        return b0
    parts = [p.strip() for p in b.split(",") if p.strip()]
    keep = [p for p in parts if not DESIG.search(p)] or parts
    return ", ".join(keep[:2])
SRC = {"EPADS-Federal": "EPADS", "Punjab-ePADS": "PUNJAB", "KPITB": "KPITB"}

src = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads/tenders_full.csv"
rows = []
with open(src, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        try:
            raw = json.loads(r.get("raw") or "{}")
        except Exception:
            raw = {}
        s = SRC.get(r["source"], r["source"])
        ref = r["ref"] or ""
        tid = ("EPADS-" + ref[1:]) if s == "EPADS" and re.match(r"^P\d+$", ref) else s + "-" + re.sub(r"[^A-Za-z0-9]+", "-", ref).strip("-")
        cat = CAT.get(re.sub(r"\s*\(inferred\)", "", r["category"] or "").strip().lower(), "")
        proc = raw.get("procedure", "")
        t = (r["title"] or "").strip()
        d = re.sub(r"\s+", " ", r["description"] or "").strip()
        nt = "EOI" if re.search(r"expression of interest|\beoi\b", t + " " + d[:200], re.I) else ("PQ" if re.search(r"pre-?qualification", t + " " + proc, re.I) else "")
        b = (r["buyer"] or "").strip()
        bn = normalize_buyer(r["buyer_norm"] or b) or b
        rows.append({"id": tid, "s": s, "j": r["jurisdiction"], "ref": ref, "t": t, "d": d[:900], "b": b, "bn": bn, "cat": cat,
                     "mth": method_of(proc), "nt": nt, "pub": (r["advertised"] or "")[:10], "cl": (r["closing"] or "")[:10],
                     "org": org_of(s, b), "u": r["url"] or "", "sect": r["buyer_sector"] or "", "ttype": r["tender_type"] or ""})
seen, out = set(), []
for x in rows:
    if x["id"] in seen:
        continue
    seen.add(x["id"]); out.append(x)
json.dump(out, open(os.path.join(HERE, "out", "history_rows.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("history rows", len(out), "from", len(rows))
