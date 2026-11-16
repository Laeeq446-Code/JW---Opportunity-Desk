"""
ai_reader.py - the second reader. Runs after normalize.py on every scheduled scan.

Reads each open tender that mentions anything digital, and each Pakistani news headline, once.
Uses the same prompts as the page (build/seed/prompts.json) and the same product catalogue.
Results are cached in archive/ai_labels.json and archive/ai_signals.json, so a tender is never
paid for twice. Needs ANTHROPIC_API_KEY; without it the script does nothing and the site runs on
the rules reader alone.

Env: ANTHROPIC_API_KEY (required), READER_MODEL (default claude-haiku-5-5), READER_MAX (default 600 tenders per run)
"""
import json, os, re, sys, time
from datetime import datetime, timezone
import requests

KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
if not KEY:
    print("ai_reader: no ANTHROPIC_API_KEY, skipped"); sys.exit(0)
MODEL = os.getenv("READER_MODEL", "claude-haiku-5-5")
MAX = int(os.getenv("READER_MAX", "600"))
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = lambda *a: os.path.join(ROOT, *a)

cat_js = open(P("app", "data", "catalogue.js"), encoding="utf-8").read()
CAT = json.loads(cat_js[cat_js.index("=") + 1:].strip().rstrip(";"))
PROMPTS = json.load(open(P("build", "seed", "prompts.json"), encoding="utf-8"))
PRODUCTS = "\n".join(f"{p['id']}: {p['name']} [{CAT['sbus'][p['sbu']]['short']}]. {str(p['desc'])[:120]}" for p in CAT["products"])
PIDS = {p["id"] for p in CAT["products"]}
TECH = re.compile(r" (it|ict|digital|software|system|network|internet|data|cloud|cyber|server|computer|laptop|printer|cctv|camera|telecom|mobile|sms|app|application|portal|automation|online|smart|gps|tracking|payment|insurance|connectivity|wifi|wi fi|fiber|fibre|licen[sc]e|hardware|solution|erp|website|biometric|scanner|video|surveillance|lan|wan|router|switch|firewall|ups|toner) ")
PHRASES = sorted({re.sub(r"[^a-z0-9 ]", " ", s.replace("*", "")).strip() for p in CAT["products"] for s in p.get("strong", []) if len(s) > 3}, key=len, reverse=True)


def canon(s):
    return " " + re.sub(r"[^a-z0-9]+", " ", str(s or "").lower().replace("&", " and ")).strip() + " "


def key_of(t):
    return canon(t).replace(" ", "")[:80]


TOOL = {"name": "record", "description": "Record the answer: one result object per item, in the order given.",
        "input_schema": {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object"}}}, "required": ["items"]}}


def salvage(txt):
    """Fallback when the model answers in text: parse the array, else keep every object that parses."""
    a, b = txt.find("["), txt.rfind("]")
    try:
        return json.loads(txt[a:b + 1])
    except Exception:
        out = []
        for m in re.finditer(r"\{[^{}]*\}", txt):
            try:
                out.append(json.loads(m.group(0)))
            except Exception:
                pass
        if not out:
            raise ValueError("no readable JSON in reply")
        return out


def call(prompt, items):
    """One request. The answer comes back through a forced tool call, so it is always valid JSON."""
    body = {"model": MODEL, "max_tokens": 8000, "tools": [TOOL], "tool_choice": {"type": "tool", "name": "record"},
            "messages": [{"role": "user", "content": prompt + "\n\nGive the array to the record tool as items.\n\nPRODUCTS (id: name [SBU]. what it is)\n" + PRODUCTS + "\n\n" + items}]}
    for attempt in range(3):
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=180, json=body,
                          headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        if r.status_code in (429, 529) or r.status_code >= 500:
            time.sleep(10 * (attempt + 1)); continue
        r.raise_for_status()
        content = r.json().get("content", [])
        for b in content:
            if b.get("type") == "tool_use" and isinstance(b.get("input", {}).get("items"), list):
                return b["input"]["items"]
        return salvage("".join(b.get("text", "") for b in content if b.get("type") == "text"))
    raise RuntimeError("API busy")


def read(prompt, head, rows, label):
    """Read a batch. If the reply cannot be read, split the batch in halves so one bad item cannot sink the rest."""
    try:
        return call(prompt, head + "\n".join(rows))
    except (requests.HTTPError, RuntimeError) as e:
        print(f"  {label} batch failed:", e); return []
    except Exception as e:
        if len(rows) < 6:
            print(f"  {label} batch failed:", e); return []
        h = len(rows) // 2
        return read(prompt, head, rows[:h], label) + read(prompt, head, rows[h:], label)


def load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
# ── tenders ──
lab_path = P("archive", "ai_labels.json")
LAB = load(lab_path, {"meta": {}, "labels": {}})
open_ = load(P("build", "out", "tenders_open.json"), [])
pool = []
for t in open_:
    if t["id"] in LAB["labels"] or t.get("kind") == "D":
        continue
    c = canon(t["t"] + " " + str(t.get("d", ""))[:300])
    if TECH.search(c) or any(" " + ph + " " in c for ph in PHRASES[:400]):
        pool.append(t)
pool = pool[:MAX]
done = 0
for i in range(0, len(pool), 25):
    batch = pool[i:i + 25]
    rows = [f"{t['id']} | {t['t'][:200]} | {t.get('bn') or t.get('b', '')} | {t.get('cat', '')} | {t.get('mth', '')} | {str(t.get('d', ''))[:300]}" for t in batch]
    out = read(PROMPTS["reader_tenders_v1"], "TENDERS (id | title | buyer | category | method | scope)\n", rows, "tender")
    for o in out:
        if isinstance(o, dict) and o.get("id") in {t["id"] for t in batch}:
            LAB["labels"][o["id"]] = {"p": [p for p in (o.get("p") or []) if p in PIDS][:3], "f": o.get("f", ""), "c": o.get("c", ""), "ty": o.get("ty", ""), "w": str(o.get("w", ""))[:140], "at": stamp}
            done += 1
LAB["meta"] = {"model": MODEL, "prompt": "reader_tenders_v1", "at": stamp, "read": len(LAB["labels"])}
open_ids = {t["id"] for t in open_}
LAB["labels"] = {k: v for k, v in LAB["labels"].items() if k in open_ids or v.get("at", "") >= stamp[:7]}
json.dump(LAB, open(lab_path, "w", encoding="utf-8"))
print(f"ai_reader: tenders read this run {done} of {len(pool)} candidates")

# ── local news headlines ──
sig_path = P("archive", "ai_signals.json")
SIG = load(sig_path, {"meta": {}, "labels": {}})
news = load(P("raw", "news.json"), {"local": [], "global": []})
heads = [a for a in news.get("local", []) if key_of(a["t"]) not in SIG["labels"]][:150]
accts = "\n".join(f"{a['id']}: {a['name']}" for a in CAT["accounts"] if a.get("digital"))
for i in range(0, len(heads), 30):
    batch = heads[i:i + 30]
    rows = [f"{key_of(a['t'])} | {a.get('date', '')} | {a.get('src', '')} | {a['t']}" for a in batch]
    out = read(PROMPTS["reader_signals_v1"], "BUYERS (id: name)\n" + accts + "\n\nHEADLINES (id | date | outlet | headline)\n", rows, "signal")
    for o in out:
        if isinstance(o, dict) and o.get("id"):
            o["products"] = [p for p in (o.get("products") or []) if p in PIDS][:3]
            o["at"] = stamp
            SIG["labels"][o["id"]] = o
SIG["meta"] = {"model": MODEL, "prompt": "reader_signals_v1", "at": stamp}
json.dump(SIG, open(sig_path, "w", encoding="utf-8"))
print(f"ai_reader: headlines read {sum(1 for a in heads if key_of(a['t']) in SIG['labels'])} of {len(heads)}")
