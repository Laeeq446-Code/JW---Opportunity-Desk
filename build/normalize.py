"""
normalize.py - turn the raw pulls (raw/*.json) into one clean tender list.

No relevance logic lives here. This step only cleans: dates, buyer names,
procurement method, duplicates across portals. Output: build/out/tenders_open.json
and build/out/tenders_hist.json.
"""
import json, re, sys, hashlib, os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scraper"))
from classify import normalize_buyer  # buyer clean-up proven on 3,181 federal tenders

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "raw")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def clean(s):
    return re.sub(r"\s+", " ", str(s or "")).replace("&#039;", "'").replace("&amp;", "&").replace("&quot;", '"').strip()


def parse_dt(s):
    """'Thursday, November 5, 2026 03:42 PM' | 'Nov 12, 2026' | 'Dec 09, 2026 10:30 AM' -> ISO"""
    s = clean(s)
    if not s:
        return ""
    m = re.search(r"([A-Za-z]{3})[a-z]*\.? (\d{1,2}),? (\d{4})(?:\s+(\d{1,2}):(\d{2})\s*([AP]M))?", s)
    if not m:
        return ""
    mon = MONTHS.get(m.group(1).lower())
    if not mon:
        return ""
    d = f"{int(m.group(3)):04d}-{mon:02d}-{int(m.group(2)):02d}"
    if m.group(4):
        h = int(m.group(4)) % 12 + (12 if m.group(6) == "PM" else 0)
        d += f"T{h:02d}:{m.group(5)}"
    return d


def load(name):
    p = os.path.join(RAW, name + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def epads_buyer(b):
    """EPADS writes 'Unit (Parent Org (ACR))' or 'Org (Unit)'. Keep the raw string; derive a short account name."""
    b = clean(b)
    # last top-level parenthetical
    depth = 0; start = -1; groups = []
    for i, ch in enumerate(b):
        if ch == "(":
            if depth == 0: start = i
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and start >= 0:
                groups.append((start, i)); start = -1
    if groups:
        s, e = groups[-1]
        inner = b[s + 1:e].strip(); outer = b[:s].strip(" ,-")
        inner = re.split(r"\s+/\s+", inner)[0].strip()
        if "/" in inner and len(inner.split("/")[-1].strip()) > 12:
            inner = inner.split("/")[-1].strip()
        unit = re.match(r"^(directorate|department|division|wing|section|office|member|branch|cell|unit|engineering|procurement|admin|hq|head ?quarter|campus|zone|region|circle|project|pmu)", inner, re.I)
        looks_org = (len(inner.split()) >= 3 or re.search(r"\([A-Z]{2,8}\)", inner) or inner.lower() == outer.lower()) and not unit
        if looks_org and e >= len(b) - 2:
            return inner
        return outer or b
    return b


METHOD = [
    (r"petty purchase", "PP"), (r"quotation", "RFQ"), (r"two stage", "TS"), (r"two envelope", "OCB2"),
    (r"one envelope", "OCB1"),
]


def method_of(proc):
    p = proc.lower()
    for rx, code in METHOD:
        if re.search(rx, p):
            return code
    return ""


CAT = {"goods": "G", "works": "W", "non-consultancy services": "S", "consultancy services": "C",
       "non consultancy services": "S"}

out_open, out_hist = [], []
meta = {"sources": {}}
TODAY = None

# ── EPADS (federal e-procurement, epads.gov.pk) ─────────────────────────────
e = load("epads2")
if e:
    now = datetime.fromisoformat(e["now"].replace("Z", "+00:00")) + timedelta(hours=5)  # PKT
    TODAY = now.strftime("%Y-%m-%d")
    det = e.get("det", {})
    n = 0
    for (pid, title, buyer, pub, cl, typ, proc, flags, extra) in e["rows"]:
        cl_iso = parse_dt(cl)
        if not cl_iso:
            m = re.search(r"(?:(\d+)d\s*)?(\d+)h\s*(\d+)m\s*Left", cl)
            if m:
                cl_iso = (now + timedelta(days=int(m.group(1) or 0), hours=int(m.group(2)), minutes=int(m.group(3)))).strftime("%Y-%m-%dT%H:%M")
        d = det.get(str(pid)) or ["", None, None]
        rec = {
            "id": f"EPADS-{pid}", "s": "EPADS", "ref": f"P{pid}", "t": clean(title), "d": "",
            "b": clean(buyer), "bn": epads_buyer(buyer),
            "cat": CAT.get(typ.lower(), ""), "mth": method_of(proc), "nt": "PQ" if "prequal" in (extra or "").lower() else "",
            "pub": parse_dt(pub)[:10], "cl": cl_iso,
            "u": f"https://epads.gov.pk/opportunities/federal/procurements/{pid}",
            "st": ("C" if "Corrigendum" in flags else "") + ("G" if "Grievance" in flags else ""),
            "v": d[1], "sbd": d[0] or "",
        }
        out_open.append(rec); n += 1
    meta["sources"]["EPADS"] = {"name": "EPADS 2.0 federal e-procurement", "url": "https://epads.gov.pk", "pulled": e["now"], "rows": n,
                               "note": "Every open federal procurement on the public board (10 listing pages)."}

# ── PPRA EPMS active tenders (epms.ppra.gov.pk) ─────────────────────────────
p = load("epms")
if p:
    n = 0
    NT = {"Request for Proposal (RFP)": "RFP", "Pre-qualification Notice (PQ)": "PQ", "Expression of Interest (EOI)": "EOI"}
    for (no, kind, title, desc, sec, status, adv, cl, org, ttype, cat, nature) in p["rows"]:
        ref = f"TS{int(no):010d}E" if str(no).isdigit() else f"{no}E"
        orgraw = clean(p["orgs"][org])
        st = ""
        if status and "Cancel" in str(status): st += "X"
        if status and "Corrigendum" in str(status): st += "C"
        desc = clean(desc)
        if re.match(r"^(single|two) stage", desc, re.I) or desc.lower() in ("pre-qualification", "prequalification"):
            mth_hint, desc = desc, ""
        else:
            mth_hint = ""
        rec = {
            "id": f"EPMS-{no}", "s": "EPMS", "ref": ref, "t": clean(title), "d": desc.rstrip(".").rstrip("…") if desc else "",
            "b": orgraw, "bn": normalize_buyer(orgraw),
            "cat": CAT.get(str(cat).lower(), ""), "mth": method_of(mth_hint), "nt": NT.get(ttype, "") if ttype else "",
            "pub": parse_dt(adv)[:10], "cl": parse_dt(cl),
            "u": f"https://epms.ppra.gov.pk/public/tenders/tender-details/{ref}",
            "st": st, "sec": p["sec"][sec],
            "kind": {"Disposal": "D", "Framework Agreement": "F"}.get(kind, "") if kind else "",
            "intl": 1 if nature == "International" else 0,
        }
        out_open.append(rec); n += 1
    meta["sources"]["EPMS"] = {"name": "PPRA EPMS active tenders", "url": "https://epms.ppra.gov.pk/public/tenders/active-tenders", "pulled": p["now"], "rows": n,
                              "note": "Every active federal tender notice on the PPRA board (38 listing pages)."}

# ── World Bank procurement notices API, Pakistan ─────────────────────────────
w = load("wb")
if w:
    def wbrec(o, closed=False):
        pm = o.get("pm", "") or ""
        nt = {"Invitation for Bids": "", "Request for Expression of Interest": "EOI"}.get(o.get("nt", ""), "")
        mth = "ICS" if re.search(r"individual", pm, re.I) else ("RFP" if re.search(r"proposal|quality|cost", pm, re.I) else ("RFQ" if re.search(r"quotation", pm, re.I) else "OCB1"))
        tx = clean(o.get("tx", ""))
        # keep the scope part of the notice; drop standing World Bank boilerplate sentences
        tx = re.sub(r"(has received|has applied for) (financing|a credit|a loan)[^.]*\.", " ", tx, flags=re.I)
        tx = re.sub(r"(Bidding will be conducted|Interested eligible bidders|The bidding document|Bids must be delivered|All bids must be accompanied|Attention is drawn|Expressions of interest must be)[^.]*\.", " ", tx, flags=re.I)
        nd = o.get("nd", "")
        m = re.match(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", nd)
        pub = f"{m.group(3)}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}" if m else ""
        return {
            "id": f"WB-{o['id']}", "s": "WB", "ref": o.get("ref") or o["id"], "t": clean(o.get("bd", "")),
            "d": clean(tx)[:1200], "b": clean(o.get("org", "")) or "World Bank financed project",
            "bn": clean(o.get("org", "")) or "World Bank financed project",
            "cat": {"GO": "G", "CW": "W", "CS": "C", "NC": "S"}.get(o.get("pg", ""), ""), "mth": mth, "nt": nt,
            "pub": pub, "cl": (o.get("dl") or "")[:10],
            "u": f"https://projects.worldbank.org/en/projects-operations/procurement-detail/{o['id']}",
            "st": "", "proj": clean(o.get("pn", "")), "intl": 1,
        }
    for o in w["open"]:
        out_open.append(wbrec(o))
    for o in w.get("recentClosed", []):
        out_hist.append(wbrec(o, True))
    meta["sources"]["WB"] = {"name": "World Bank procurement notices API (Pakistan)", "url": "https://search.worldbank.org/api/v2/procnotices?format=json&project_ctry_name_exact=Pakistan",
                            "pulled": w["now"], "rows": len(w["open"]), "note": f"Last {w['counts']['all']} Pakistan notices read; open ones kept, ICT-related closed ones kept as history."}
    json.dump([{"id": a["id"], "date": a["nd"], "proj": a["pn"], "t": a["bd"], "org": a["org"], "tx": a.get("tx", "")} for a in w.get("awards", [])],
              open(os.path.join(OUT, "wb_awards.json"), "w"))

# ── Provincial ICT buyers: simple title/date boards ─────────────────────────────
for key, src, buyer, home in [("pitb", "PITB", "Punjab Information Technology Board (PITB)", "https://pitb.gov.pk/tendernotices"),
                              ("kpitb", "KPITB", "KP Information Technology Board (KPITB)", "https://kpitb.gov.pk/tender"),
                              ("psca", "PSCA", "Punjab Safe Cities Authority (PSCA)", "https://psca.gop.pk/home2025/tenders/")]:
    q = load(key)
    if not q:
        continue
    n_open = 0
    for row in q["rows"]:
        title, f, rel, cl = (row + ["", "", "", ""])[:4]
        hid = hashlib.md5((title + rel).encode()).hexdigest()[:8]
        u = home
        if f:
            u = f if f.startswith("http") else ("https://pitb.gov.pk/system/files?file=" + f if key == "pitb" else home)
        t = clean(title)
        rec = {"id": f"{src}-{hid}", "s": src, "ref": "", "t": t, "d": "", "b": buyer, "bn": buyer,
               "cat": "", "mth": "", "nt": "EOI" if re.search(r"expression of interest|\beoi\b", t, re.I) else ("PQ" if re.search(r"pre-?qualification", t, re.I) else ("RFP" if re.search(r"request for proposal|\brfp\b", t, re.I) else "")),
               "pub": rel, "cl": cl, "u": u, "st": "C" if re.search(r"corrigendum|addendum|extension", t, re.I) else ""}
        if cl and TODAY and cl >= TODAY:
            out_open.append(rec); n_open += 1
        else:
            out_hist.append(rec)
    # An addendum, corrigendum or extension replaces the notice it amends: one row, the later closing date.
    AMD = re.compile(r"^(addendum|corrigendum|extension|revised|amendment)( no\.? ?\d+)?\s*[-:–]?\s*", re.I)
    mine = [r for r in out_open if r["s"] == src]
    base = {}
    for r in mine:
        if not AMD.match(r["t"]):
            base.setdefault(AMD.sub("", r["t"]).lower().strip(), r)
    for r in mine:
        if AMD.match(r["t"]):
            k = AMD.sub("", r["t"]).lower().strip()
            b0 = base.get(k)
            if b0 is not None and b0 is not r:
                if (r.get("cl") or "") > (b0.get("cl") or ""):
                    b0["cl"] = r["cl"]
                b0["st"] = (b0.get("st") or "") + ("" if "C" in (b0.get("st") or "") else "C")
                b0["amend"] = r["u"]
                r["dup"] = b0["id"]; n_open -= 1
    out_open[:] = [r for r in out_open if not (r["s"] == src and "dup" in r)]
    meta["sources"][src] = {"name": buyer + " tender notices", "url": home, "pulled": q["now"], "rows": n_open,
                           "note": f"{len(q['rows'])} notices read back to {min(r[2] for r in q['rows'] if r[2])}; closed ones kept as history."}

# ── Federal history: PPRA tenders advertised Feb to Jul 2026 (earlier Tender Desk scans) ──
hp = os.path.join(HERE, "seed", "hist_epms.json")
if os.path.exists(hp):
    open_refs = {r["ref"] for r in out_open if r["s"] == "EPMS"}
    seed = [r for r in json.load(open(hp, encoding="utf-8")) if r.get("ref") not in open_refs]
    out_hist += seed
    meta["sources"]["EPMS-H"] = {"name": "PPRA EPMS history (Tender Desk scans, Feb to Jul 2026)", "url": "https://epms.ppra.gov.pk", "pulled": "2026-07-17", "rows": len(seed),
                                "note": "Federal tenders captured by the earlier Tender Desk scans. Used for demand history and renewal timing only."}

# ── de-duplicate the same tender published on both federal portals ─────────────
# Same closing day, different portal, and the titles share at least 75% of their meaningful words.
STOP = set("tender tenders no notice procurement of the for and supply e invitation bid bids to a an in at on with by from purchase provision hiring services service corrigendum re".split())
def toks(r):
    t = re.sub(r"[^a-z0-9 ]", " ", r["t"].lower())
    return frozenset(w for w in t.split() if w not in STOP and not any(c.isdigit() for c in w) and len(w) > 1)

by_day = {}
for r in out_open:
    r["_k"] = toks(r)
    by_day.setdefault((r["cl"] or "")[:10], []).append(r)
dups = 0
for day, rows in by_day.items():
    if not day:
        continue
    ep = [r for r in rows if r["s"] == "EPADS"]
    for r in rows:
        if r["s"] != "EPMS" or len(r["_k"]) < 3:
            continue
        best, bs = None, 0
        for q in ep:
            if "dup" in q or len(q["_k"]) < 3:
                continue
            u = len(r["_k"] | q["_k"])
            sc = len(r["_k"] & q["_k"]) / u if u else 0
            # a short title fully contained in the longer one is the same notice too
            small, big = (r["_k"], q["_k"]) if len(r["_k"]) <= len(q["_k"]) else (q["_k"], r["_k"])
            if len(small) >= 4 and small <= big:
                sc = max(sc, 0.8)
            if sc > bs:
                best, bs = q, sc
        if best is not None and bs >= 0.75:
            best["also"] = r["u"]; r["dup"] = best["id"]; dups += 1
            if not best.get("d") and r.get("d"): best["d"] = r["d"]
            if not best.get("sec") and r.get("sec"): best["sec"] = r["sec"]
            if not best.get("nt") and r.get("nt"): best["nt"] = r["nt"]
            if r.get("intl"): best["intl"] = 1
            if r.get("kind"): best["kind"] = r["kind"]
# Second pass: the closing date was extended on one portal only. Same buyer, different portal,
# titles share at least 85% of their meaningful words. The EPADS row is kept (system of record).
by_buyer = {}
for r in out_open:
    if "dup" not in r and r.get("bn"):
        by_buyer.setdefault(r["bn"], []).append(r)
for bn, rows in by_buyer.items():
    ep = [r for r in rows if r["s"] == "EPADS"]
    for r in rows:
        if r["s"] != "EPMS" or "dup" in r or len(r["_k"]) < 4:
            continue
        for q in ep:
            if "also" in q and q["also"] or len(q["_k"]) < 4:
                continue
            u = len(r["_k"] | q["_k"])
            if u and len(r["_k"] & q["_k"]) / u >= 0.85:
                q["also"] = r["u"]; r["dup"] = q["id"]; dups += 1
                if (r.get("cl") or "")[:10] != (q.get("cl") or "")[:10]:
                    q["cl_other"] = r.get("cl")
                if not q.get("d") and r.get("d"): q["d"] = r["d"]
                break
# Third pass: the pairs the first two miss. The same notice is often posted on EPADS and on EPMS with a
# reworded title ("NGFW" and "NG Firewalls"), a parent body as buyer on one portal ("Power Division" for
# QESCO), or a closing date extended on one portal only. A pair is merged when the buyers are compatible,
# the closing dates are within 21 days, and either the titles are near-identical, or one title is contained
# in the other and the closing date and time are the same. The EPADS row is kept.
SYN = {"ngfw": "firewall", "firewalls": "firewall", "ng": "", "acess": "access", "procumrement": "", "rocurement": "",
       "laptops": "laptop", "computers": "computer", "switches": "switch", "licenses": "license", "licences": "license",
       "licence": "license", "services": "", "service": "", "nos": "", "qty": "", "lot": "", "items": "", "item": ""}
UMBRELLA = re.compile(r"^(power division|ministry of|federal government|government of|cabinet division|petroleum division|finance division|establishment division|aviation division|defence production)", re.I)
BSTOP = set("of the and for pakistan limited ltd pvt private company co corporation authority department directorate office government".split())


def tset(t):
    t = re.sub(r"[\w.]+(?:/[\w.\-]+)+", " ", (t or "").lower())  # reference codes such as SSGC/LP/EPADS2/PT/2181291
    w = re.sub(r"[^a-z0-9 ]", " ", t).split()
    out = set()
    for x in w:
        x = SYN.get(x, x)
        if not x or x in STOP or any(c.isdigit() for c in x) or len(x) < 2:
            continue
        out.add(x[:-1] if len(x) > 4 and x.endswith("s") and not x.endswith("ss") else x)
    return frozenset(out)


def grams(t):
    z = " ".join(sorted(t))
    return {z[i:i + 3] for i in range(max(0, len(z) - 2))}


def bset(b):
    return frozenset(x for x in re.sub(r"[^a-z0-9 ]", " ", (b or "").lower()).split() if x not in BSTOP and len(x) > 1)


def buyers_compatible(a, b):
    """True, False, or "umbrella" when one side is a parent ministry or division and the other is not."""
    if not a or not b:
        return True
    ua, ub = bool(UMBRELLA.match(a)), bool(UMBRELLA.match(b))
    A, B = bset(a), bset(b)
    if ua and ub:
        return A == B
    if ua or ub:
        return "umbrella"
    if not A or not B:
        return True
    ab = lambda s: set(re.findall(r"\(([A-Za-z]{2,8})\)", s))
    if ab(a) & ab(b):
        return True
    return len(A & B) / len(A | B) >= 0.34 or A <= B or B <= A


def day_gap(x, y):
    try:
        return abs((datetime.fromisoformat(x[:10]) - datetime.fromisoformat(y[:10])).days)
    except Exception:
        return 99


live = [r for r in out_open if "dup" not in r]
ep3 = [r for r in live if r["s"] == "EPADS" and not r.get("also")]
for r in ep3:
    r["_t"] = tset(r["t"]); r["_g"] = grams(r["_t"])
for r in [x for x in live if x["s"] == "EPMS"]:
    rt = tset(r["t"])
    if len(rt) < 2:
        continue
    rg = grams(rt)
    best, bs = None, 0.0
    for q in ep3:
        if q.get("also") or not r.get("cl") or not q.get("cl"):
            continue
        gap = day_gap(r["cl"], q["cl"])
        if gap > 21 or (r.get("cat") and q.get("cat") and r["cat"] != q["cat"]):
            continue
        bc = buyers_compatible(r.get("bn", ""), q.get("bn", ""))
        if not bc:
            continue
        qt = q["_t"]
        same_raw = re.sub(r"[^a-z0-9]", "", r["t"].lower()) == re.sub(r"[^a-z0-9]", "", q["t"].lower())
        if same_raw and gap <= 7:
            best, bs = q, 1.0
            break
        if len(qt) < 2:
            continue
        if bc == "umbrella":
            # a parent ministry on one portal: only an identical title within a week counts
            if rt == qt and len(rt) >= 3 and gap <= 7 and 1.0 > bs:
                best, bs = q, 1.0
            continue
        jac = len(rt & qt) / len(rt | qt)
        tri = len(rg & q["_g"]) / len(rg | q["_g"]) if rg and q["_g"] else 0
        same_close = (r["cl"] or "")[:16] == (q["cl"] or "")[:16] and len(r["cl"]) > 10
        small, big = (rt, qt) if len(rt) <= len(qt) else (qt, rt)
        contained = len(small) >= 2 and small <= big
        sc = 0.0
        if rt == qt or tri >= 0.9:
            sc = 1.0
        elif (jac >= 0.6 or tri >= 0.62) and gap <= 7:
            sc = 0.8
        elif contained and same_close:
            sc = 0.75
        if sc > bs:
            best, bs = q, sc
    if best is not None and bs >= 0.7:
        best["also"] = r["u"]; r["dup"] = best["id"]; dups += 1
        if (r.get("cl") or "")[:10] != (best.get("cl") or "")[:10]:
            best["cl_other"] = r.get("cl")
        if not best.get("d") and r.get("d"): best["d"] = r["d"]
        if not best.get("sec") and r.get("sec"): best["sec"] = r["sec"]
        if r.get("intl"): best["intl"] = 1
for r in out_open:
    r.pop("_k", None); r.pop("_t", None); r.pop("_g", None)
out_open = [r for r in out_open if "dup" not in r]
meta["dups_removed"] = dups
sl = load("scan_log")
if sl:
    meta["scan"] = sl
meta["today"] = TODAY
meta["open_total"] = len(out_open)
meta["hist_total"] = len(out_hist)

json.dump(out_open, open(os.path.join(OUT, "tenders_open.json"), "w"), ensure_ascii=False)
json.dump(out_hist, open(os.path.join(OUT, "tenders_hist.json"), "w"), ensure_ascii=False)
json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(meta, indent=1)[:1800])
import collections
print(collections.Counter(r["s"] for r in out_open), collections.Counter(r["s"] for r in out_hist))
print(collections.Counter(r["mth"] for r in out_open), collections.Counter(r["cat"] for r in out_open))
print(sum(1 for r in out_open if not r["cl"]), "open rows without closing date")
