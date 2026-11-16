"""
scan.py - read today's tenders and news from official and public sources.

Runs on a schedule in GitHub Actions (see .github/workflows/scan.yml) or by hand:
    python scraper/scan.py            # everything
    python scraper/scan.py --only epads,wb

Writes raw/<source>.json in the shapes build/normalize.py reads. If a source fails,
its previous file is kept, so one broken portal never empties the site. A summary of
what ran goes to raw/scan_log.json and is shown on the page.

Rules this scraper keeps: public pages only, no logins, no CAPTCHA or bot-check
workarounds, one request at a time with a pause between pages.
"""
import json, os, re, sys, time, argparse, html
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "raw")
os.makedirs(RAW, exist_ok=True)
UA = "Mozilla/5.0 (compatible; JW-Opportunity-Desk/1.0; public tender monitor)"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
PAUSE = float(os.getenv("SCAN_PAUSE", "1.0"))


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(str(s or ""))).strip()


def get(url, **kw):
    r = S.get(url, timeout=60, **kw)
    r.raise_for_status()
    return r


def save(name, obj):
    tmp = os.path.join(RAW, name + ".json.tmp")
    json.dump(obj, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, os.path.join(RAW, name + ".json"))


# ── EPADS 2.0 public board: https://epads.gov.pk/?page=N ─────────────────────
def parse_epads(page_html):
    sp = BeautifulSoup(page_html, "lxml")
    rows = []
    for tr in sp.find_all("tr"):
        a = tr.find("a", href=re.compile(r"/procurements/\d+"))
        if not a:
            continue
        pid = int(re.search(r"/procurements/(\d+)", a["href"]).group(1))
        tds = tr.find_all("td")
        if len(tds) < 4:
            continue
        span = a.find("span")
        title = clean((span.get("title") or span.get("data-bs-original-title")) if span and (span.get("title") or span.get("data-bs-original-title")) else a.get_text(" "))
        spans = [s for s in tds[1].find_all("span", recursive=False)]
        dept = spans[0] if spans else None
        buyer = clean((dept.get("title") or dept.get_text(" ")) if dept else "")
        flags = " ".join(clean(b.get_text(" ")) for b in tds[1].find_all("span", class_="badge") if not re.match(r"^\s*P\d+\s*$", b.get_text()))
        badges = tds[2].find_all("span", class_="badge")
        pub = clean(badges[0].get_text(" ")) if badges else ""
        cl = clean(badges[1].get_text(" ")) if len(badges) > 1 else ""
        typ = tds[3].find("span", class_="badge")
        proc = tds[3].find("span", class_=re.compile("text-secondary"))
        extra = clean(tds[3].get_text(" "))
        extra = "Pre-qualification" if re.search(r"pre\s*-?\s*qualif", extra, re.I) else ""
        rows.append([pid, title, buyer, pub, cl, clean(typ.get_text(" ")) if typ else "", clean(proc.get_text(" ")) if proc else "", flags, extra])
    return rows


def scan_epads(max_pages=40):
    rows, seen = [], set()
    for p in range(1, max_pages + 1):
        got = parse_epads(get("https://epads.gov.pk/", params={"page": p}).text)
        new = [r for r in got if r[0] not in seen]
        if not new:
            break
        for r in new:
            seen.add(r[0])
        rows += new
        time.sleep(PAUSE)
    if len(rows) < 50:
        raise RuntimeError(f"only {len(rows)} rows; the page layout may have changed")
    save("epads2", {"now": now_iso(), "det": {}, "rows": rows})
    return len(rows)


# ── PPRA EPMS active tenders: https://epms.ppra.gov.pk/public/tenders/active-tenders ──
def parse_epms(page_html, orgs, secs):
    sp = BeautifulSoup(page_html, "lxml")
    rows = []
    for tr in sp.find_all("tr", class_="cb-rt-main"):
        ref = tr.find("strong", class_="cb-rt-name")
        if not ref:
            continue
        ref = clean(ref.get_text())
        m = re.match(r"^([A-Z]{2})0*(\d+)E$", ref)
        no = (str(int(m.group(2))) if m.group(1) == "TS" else m.group(1) + m.group(2).zfill(10)) if m else ref.rstrip("E")
        kind = tr.find("td", attrs={"data-label": "Tender No"}).find("span", class_="badge")
        kind = clean(kind.get_text()) if kind else ""
        det = tr.find("td", attrs={"data-label": "Tender Details"})
        title = clean(det.find("strong").get_text(" ")) if det and det.find("strong") else ""
        smalls = [clean(s.get_text(" ")) for s in det.find_all("small", class_="d-block")] if det else []
        desc = max(smalls, key=len) if smalls else ""
        sec = ""
        for b in (det.find_all("small", class_="badge") if det else []):
            if "text-muted" not in (b.get("class") or []):
                sec = clean(b.get_text()); break
        status = " ".join(clean(s.get_text()) for s in tr.find("td", attrs={"data-label": "Status"}).find_all("span"))
        adv = clean(tr.find("td", attrs={"data-label": "Advertised"}).get_text(" "))
        cl = clean(tr.find("td", attrs={"data-label": "Closing"}).get_text(" "))
        org = ttype = cat = nature = ""
        nxt = tr.find_next_sibling("tr")
        if nxt is not None and "cb-rt-detail" in (nxt.get("class") or []):
            for blk in nxt.select(".cb-rt-grid > div"):
                lab = clean(blk.find("span", class_="cb-rt-dl").get_text()) if blk.find("span", class_="cb-rt-dl") else ""
                val = clean(blk.find("span", class_="cb-rt-dv").get_text(" ")) if blk.find("span", class_="cb-rt-dv") else ""
                if lab == "Organization": org = val
                elif lab == "Tender Type": ttype = val
                elif lab == "Procurement Category": cat = val
                elif lab == "Tender Nature": nature = val
        if org not in orgs: orgs.append(org)
        if sec not in secs: secs.append(sec)
        rows.append([no, 0 if kind in ("", "Procurement") else kind, title, desc if desc != title else "", secs.index(sec),
                     0 if status in ("", "Published") else status, adv, cl, orgs.index(org),
                     0 if ttype in ("", "Tender Notice") else ttype, cat, 0 if nature in ("", "Local") else nature])
    return rows


def scan_epms(max_pages=80):
    rows, orgs, secs, seen = [], [], [], set()
    for p in range(1, max_pages + 1):
        got = parse_epms(get("https://epms.ppra.gov.pk/public/tenders/active-tenders", params={"page": p}).text, orgs, secs)
        new = [r for r in got if r[0] not in seen]
        if not new:
            break
        for r in new:
            seen.add(r[0])
        rows += new
        time.sleep(PAUSE)
    if len(rows) < 50:
        raise RuntimeError(f"only {len(rows)} rows; the page layout may have changed")
    save("epms", {"now": now_iso(), "total": len(rows), "orgs": orgs, "sec": secs, "rows": rows})
    return len(rows)


# ── World Bank procurement notices API, Pakistan projects ─────────────────────
def scan_wb(pages=6):
    API = "https://search.worldbank.org/api/v2/procnotices"
    items = []
    for p in range(pages):
        j = get(API, params={"format": "json", "rows": 100, "os": p * 100, "project_ctry_name_exact": "Pakistan",
                             "srt": "noticedate", "order": "desc"}).json()
        batch = j.get("procnotices") or []
        if isinstance(batch, dict):
            batch = list(batch.values())
        if not batch:
            break
        items += [b for b in batch if isinstance(b, dict) and "pakistan" in str(b.get("project_ctry_name", "")).lower()]
        time.sleep(PAUSE)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def short(o):
        tx = re.sub(r"<[^>]+>", " ", o.get("notice_text") or "")
        return {"id": o.get("id"), "nt": o.get("notice_type", ""), "nd": o.get("noticedate", ""),
                "dl": o.get("submission_deadline_date") or o.get("deadline_date") or "", "pid": o.get("project_id", ""),
                "pn": o.get("project_name", ""), "ref": o.get("bid_reference_no", ""), "bd": clean(o.get("bid_description", "")),
                "pg": o.get("procurement_group", ""), "pm": o.get("procurement_method_name", ""),
                "org": clean(o.get("contact_organization") or o.get("borrower") or ""), "st": o.get("notice_status", ""), "tx": clean(tx)[:3000]}
    rows = [short(o) for o in items]
    awards = [r for r in rows if "award" in r["nt"].lower()]
    live = [r for r in rows if "award" not in r["nt"].lower()]
    open_ = [r for r in live if (r["dl"] or "")[:10] >= today]
    closed = [r for r in live if r["dl"] and r["dl"][:10] < today][:300]
    save("wb", {"now": now_iso(), "counts": {"all": len(rows), "awardsAll": len(awards)}, "open": open_, "recentClosed": closed, "awards": awards})
    return len(open_)


# ── PITB tender notices (Drupal table, newest first) ───────────────────────────
def parse_pitb(page_html):
    sp = BeautifulSoup(page_html, "lxml")
    out = []
    for tr in sp.find_all("tr"):
        t = tr.find("td", class_="views-field-title")
        if not t:
            continue
        a = tr.find("a", href=True)
        f = a["href"].split("file=")[-1] if a else ""
        times = [x.get("datetime", "")[:10] for x in tr.find_all("time")]
        out.append([clean(t.get_text(" ")), f, times[0] if times else "", times[1] if len(times) > 1 else ""])
    return out


def scan_pitb(pages=4):
    rows = []
    for p in range(pages):
        rows += parse_pitb(get("https://pitb.gov.pk/tendernotices", params={"page": p} if p else None).text)
        time.sleep(PAUSE)
    old = os.path.join(RAW, "pitb.json")
    if os.path.exists(old):   # keep older notices so the history and renewal rules still see them
        have = {r[0] + r[2] for r in rows}
        rows += [r for r in json.load(open(old, encoding="utf-8"))["rows"] if r[0] + r[2] not in have]
    if not rows:
        raise RuntimeError("no rows; the page layout may have changed")
    save("pitb", {"now": now_iso(), "rows": rows})
    return len(rows)


# ── News: global government-digital trends and Pakistani funding/policy signals ──
# Google News RSS gives headline, outlet, date and link. Nothing behind a paywall is read.
GLOBAL_Q = [
    'government "AI agents" OR "AI assistant" citizens',
    '"digital public infrastructure" OR "digital ID" government launch',
    '"smart city" "command and control" OR "digital twin" government',
    'government "sovereign cloud" OR "government cloud" launch',
    '"digital payments" government OR "G2P" OR "e-government payments"',
    'government "IoT" OR "smart meters" OR "smart agriculture" rollout',
    '"cybersecurity operations centre" government national',
    'government "super app" OR "citizen app" launch',
]
LOCAL_Q = [
    'Pakistan (USF OR "Universal Service Fund" OR MoITT OR PTA OR NITB OR "Digital Authority") (approves OR project OR budget OR launch)',
    'Pakistan (NADRA OR FBR OR PRAL OR "Pakistan Single Window" OR SBP) (digital OR system OR automation OR project)',
    'Pakistan ("Safe City" OR PSCA OR "Islamabad police" OR NHMP) (cameras OR "command" OR digital OR e-challan)',
    'Pakistan (ADB OR "World Bank") loan approves (digital OR e-governance OR connectivity OR payments)',
    '(Punjab OR Sindh OR "Khyber Pakhtunkhwa" OR KP OR Balochistan) (PITB OR KPITB OR "IT board") (launch OR project OR approves)',
    'Pakistan ECNEC OR CDWP approves (digital OR IT OR broadband OR fibre OR data centre)',
]


def rss(q, pk):
    loc = "hl=en-PK&gl=PK&ceid=PK:en" if pk else "hl=en-US&gl=US&ceid=US:en"
    url = f"https://news.google.com/rss/search?q={quote_plus(q + ' when:30d')}&{loc}"
    sp = BeautifulSoup(get(url).content, "xml")
    out = []
    for it in sp.find_all("item")[:40]:
        t = clean(it.title.get_text() if it.title else "")
        src = it.find("source")
        outlet = clean(src.get_text()) if src else ""
        if outlet and t.endswith(" - " + outlet):
            t = t[: -len(outlet) - 3]
        try:
            d = parsedate_to_datetime(it.pubDate.get_text()).strftime("%Y-%m-%d")
        except Exception:
            d = ""
        out.append({"t": t, "src": outlet, "home": src.get("url", "") if src else "", "date": d, "u": clean(it.link.get_text() if it.link else "")})
    return out


def scan_news():
    res = {"now": now_iso(), "global": [], "local": []}
    for key, qs, pk in (("global", GLOBAL_Q, False), ("local", LOCAL_Q, True)):
        seen = set()
        for q in qs:
            try:
                for a in rss(q, pk):
                    k = re.sub(r"[^a-z0-9]", "", a["t"].lower())[:70]
                    if k and k not in seen:
                        seen.add(k); a["q"] = qs.index(q); res[key].append(a)
            except Exception as e:
                print("   news query failed:", q[:50], e)
            time.sleep(PAUSE)
    if not (res["global"] or res["local"]):
        raise RuntimeError("no news items")
    save("news", res)
    return len(res["global"]) + len(res["local"])


SOURCES = {"epads": scan_epads, "epms": scan_epms, "wb": scan_wb, "pitb": scan_pitb, "news": scan_news}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    names = [n for n in args.only.split(",") if n] or list(SOURCES)
    log = {"at": now_iso(), "sources": {}}
    for n in names:
        t0 = time.time()
        try:
            k = SOURCES[n]()
            log["sources"][n] = {"ok": True, "rows": k, "secs": round(time.time() - t0)}
            print(f"OK     {n:6} {k} rows in {time.time() - t0:.0f}s")
        except Exception as e:
            log["sources"][n] = {"ok": False, "error": str(e)[:300], "secs": round(time.time() - t0)}
            print(f"FAILED {n:6} {e}")
    save("scan_log", log)
    if not any(v["ok"] for v in log["sources"].values()):
        sys.exit(1)
