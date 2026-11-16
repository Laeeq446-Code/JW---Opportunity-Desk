"""make_standalone.py - one self-contained HTML file. Opens from a laptop, a shared drive or an email attachment. No server."""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__)); APP = os.path.join(HERE, "..", "app")
page = open(os.path.join(APP, "opportunity-desk.html"), encoding="utf-8").read()
def inline(m):
    js = open(os.path.join(APP, m.group(1)), encoding="utf-8").read().replace("</", "<\\/")
    return "<script>\n" + js + "\n</script>"
page, n = re.subn(r'<script src="([^"]+)" charset="utf-8"></script>', inline, page)
assert n == 4, n
out = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
       '<style>body{margin:0}[hidden]{display:none!important}</style></head><body>\n' + page + "\n</body></html>")
dst = os.path.join(HERE, "..", "dist"); os.makedirs(dst, exist_ok=True)
open(os.path.join(dst, "JW_Opportunity_Desk.html"), "w", encoding="utf-8").write(out)
print("standalone", round(len(out.encode()) / 1e6, 2), "MB")
