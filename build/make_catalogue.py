"""
make_catalogue.py - write app/data/catalogue.js.

Product facts (name, brand, description, key facts, government use, source deck) come
from the Opportunity Radar catalogue. Matching rules come from rules.py. The buyer
registry comes from accounts.py. Everything the engine needs is in this one data file.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rules import RULES, CONTEXTS, EXCLUDE_TITLE, PARTNER_GAPS
from accounts import to_json as accounts_json

RADAR = "/home/claude/radar_src/jw-opportunity-radar/backend/app/data"
SEED = os.path.join(HERE, "seed")  # copied from the Radar folder so the build does not depend on the scratchpad
os.makedirs(SEED, exist_ok=True)
for f in ["seed/products.json", "seed/partners.json", "seed/public_record.json", "seed/signals.json", "seed/predictions.json",
          "seed/trends.json", "config/adjacency.json", "config/signal_types.json", "config/catalog.json", "config/trend_scouting.json"]:
    dst = os.path.join(SEED, os.path.basename(f))
    if not os.path.exists(dst) and os.path.exists(os.path.join(RADAR, f)):
        open(dst, "w").write(open(os.path.join(RADAR, f)).read())

products = json.load(open(os.path.join(SEED, "products.json")))
adj = json.load(open(os.path.join(SEED, "adjacency.json")))["adjacency"]
cat = json.load(open(os.path.join(SEED, "catalog.json")))
partners = json.load(open(os.path.join(SEED, "partners.json")))

SBU = {
    "conn": {"name": "Connectivity", "short": "Connectivity", "brands": "Jazz Business (GSM, Fixed), USF programmes"},
    "ent": {"name": "Enterprise Solutions", "short": "Enterprise", "brands": "Garaj, Quantica, Jazz Business IoT and SME"},
    "fin": {"name": "Financial Services", "short": "Financial", "brands": "JazzCash, Mobilink Bank, JazzSure, FikrFree"},
    "plat": {"name": "Digital Platforms", "short": "Platforms", "brands": "Tamasha, SIMOSA, GameNow"},
}

out = []
missing = []
for p in products:
    r = RULES.get(p["id"])
    if not r:
        missing.append(p["id"]); continue
    strong = [t for t in r["terms"] if not t.startswith("?")]
    support = [t[1:] for t in r["terms"] if t.startswith("?")]
    out.append({
        "id": p["id"], "sbu": p["sbu"], "brand": p["brand"], "name": p["name"], "src": p["source_file"],
        "desc": p["description"], "facts": p.get("key_facts", []), "gov": p.get("government_use", ""),
        "refs": p.get("references", ""), "mode": r["mode"], "strong": strong, "support": support,
        "not": {k: v for k, v in r.get("not", {}).items() if v}, "block": r.get("block", []),
        "title_only": r.get("title_only", []), "addons": adj.get(p["id"], []),
    })
assert not missing, missing
extra = set(RULES) - {p["id"] for p in products}
assert not extra, extra

data = {
    "version": "1.0",
    "sbus": SBU,
    "sources_of_catalogue": cat["catalog_files"],
    "products": out,
    "contexts": CONTEXTS,
    "exclude_title": EXCLUDE_TITLE,
    "gaps": [{"cat": c, "label": l, "rx": rx} for c, l, rx in PARTNER_GAPS],
    "partners": [{"name": p["name"], "cats": p["categories"], "cap": p["capabilities"], "u": p.get("source_url") or ""} for p in partners],
    "accounts": accounts_json(),
}
os.makedirs(os.path.join(HERE, "..", "app", "data"), exist_ok=True)
js = "window.JW_CATALOGUE = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
open(os.path.join(HERE, "..", "app", "data", "catalogue.js"), "w").write(js)
n_strong = sum(len(p["strong"]) for p in out); n_sup = sum(len(p["support"]) for p in out)
print(f"catalogue.js: {len(out)} products, {n_strong} strong terms, {n_sup} support terms, {len(data['accounts'])} accounts, {len(js)//1024} KB")
