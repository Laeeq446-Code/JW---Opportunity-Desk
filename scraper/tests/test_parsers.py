import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scan import parse_epads, parse_epms, parse_pitb
from fixtures import EPADS, EPMS, PITB
e = parse_epads(EPADS)
assert len(e) == 2, e
assert e[0][0] == 178218 and e[0][1].endswith("GSO Network") and "Corrigendum" in e[0][7] and e[0][4].startswith("2d 0h 10m Left"), e[0]
assert e[1][2] == "Pakistan Railways (Pakistan Railways)" and e[1][4] == "Saturday, November 14, 2026 12:00 PM" and e[1][5] == "Goods" and e[1][6] == "Single Stage-One Envelope", e[1]
orgs, secs = [], []
m = parse_epms(EPMS, orgs, secs)
assert len(m) == 2, m
assert m[0][0] == "FW0000018026" and m[0][1] == "Framework Agreement" and m[0][9] == "Pre-qualification Notice (PQ)" and m[0][11] == "International", m[0]
assert m[1][0] == "17610" and m[1][5] == "Published Corrigendum" and m[1][7] == "Nov 20, 2026 11:00 AM" and m[1][10] == "Goods" and m[1][3].startswith("REQUEST FOR BIDS"), m[1]
assert orgs[1].startswith("COMSATS University Islamabad") and secs[m[1][4]] == "Civil Goods", (orgs, secs)
p = parse_pitb(PITB)
assert p == [["PROCUREMENT OF IT TRAINING SERVICES FOR SKILLS ENHANCEMENT", "BD_ITSOL_02_Published.pdf", "2026-11-04", "2026-11-23"]], p
print("parsers OK", e[0][:5], m[0][:3])
