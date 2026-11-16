"""digest.py - post the new relevant tenders from this scan to a Microsoft Teams channel.

Set TEAMS_WEBHOOK_URL (a Teams Workflows "When a Teams webhook request is received" URL) as a
GitHub Actions secret. With no URL set this does nothing. Only tenders first seen in this scan
are sent, so each one appears once.
"""
import json, os, sys, requests

url = os.getenv("TEAMS_WEBHOOK_URL", "").strip()
site = os.getenv("SITE_URL", "").strip()
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build", "out", "new_today.json")
if not url or not os.path.exists(p):
    print("digest: nothing to do"); sys.exit(0)
rows = json.load(open(p, encoding="utf-8"))
top = [r for r in rows if r["score"] >= 35][:12]
if not top:
    print("digest: no new relevant tenders"); sys.exit(0)
body = [{"type": "TextBlock", "size": "Medium", "weight": "Bolder", "text": f"{len(rows)} new relevant tender{'s' if len(rows) != 1 else ''} since the last scan"}]
for r in top:
    body.append({"type": "TextBlock", "wrap": True, "spacing": "Medium", "text": f"**{r['score']} {r['band']}** · [{r['title'][:140]}]({r['u']})"})
    body.append({"type": "TextBlock", "wrap": True, "isSubtle": True, "spacing": "None",
                 "text": f"{r['buyer']} · {' + '.join(r['sbus'])} · {', '.join(r['products'][:2])} · closes {r['closes'] or 'n/a'}"})
if site:
    body.append({"type": "ActionSet", "actions": [{"type": "Action.OpenUrl", "title": "Open JW Opportunity Desk", "url": site}]})
card = {"type": "message", "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive", "content": {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json", "type": "AdaptiveCard", "version": "1.4", "body": body}}]}
r = requests.post(url, json=card, timeout=30)
print("digest:", r.status_code, len(top), "tenders")
