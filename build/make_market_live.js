/* make_market_live.js - keep the 2026 market figures growing with every scan.

   The base is the Teknosys export: every tender EPADS (federal) and Punjab e-PADS published from
   1 January to 14 October 2026. It is frozen once, the first time this script runs, as
   archive/market_base.json. From 15 October the scans take over: every distinct tender they see is
   written to archive/ledger.json with its publication date, and the ones published on or after
   15 October are added to the figures. A tender is counted once, however many scans see it.

   Two limits are stated on the page, not hidden:
   - The scans read federal portals (EPADS, PPRA EPMS), PITB and the World Bank. Punjab e-PADS is in
     the base but not in the scans, so the Punjab series stops on 14 October.
   - The scans started on 12 November. Tenders published from 15 October that had already closed by
     then were never seen, so late October and early November are undercounted.

   Each scan also re-reads the base titles with today's rules, so a rule fix (for example dropping
   printer consumables) applies to the whole year, not only to new tenders.

   Writes app/data/market.js (window.JW_MARKET), same shape as before plus:
     rows: a ninth field, the source (0 Teknosys, 1 EPADS, 2 EPMS, 3 PITB, 4 World Bank, 5 seen, details not kept)
     meta: to, base_to, live_from, counts and notes for the page. */
const fs = require('fs'), path = require('path');
const E = require('../app/engine.js'); global.window = {}; require('../app/data/catalogue.js');
const cat = window.JW_CATALOGUE;
const ROOT = path.join(__dirname, '..'), ARC = path.join(ROOT, 'archive');
const rd = (p, d) => { try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) { return d; } };
const S = f => JSON.parse(fs.readFileSync(path.join(__dirname, 'seed', f)));
const O = f => JSON.parse(fs.readFileSync(path.join(__dirname, 'out', f)));

const BASE_TO = '2026-10-14', LIVE_FROM = '2026-10-15', SCANS_FROM = '2026-11-12';

/* ── 1. the frozen base ── */
const basePath = path.join(ARC, 'market_base.json');
let base = rd(basePath, null);
if (!base) {
  const txt = fs.readFileSync(path.join(ROOT, 'app', 'data', 'market.js'), 'utf8');
  const m = JSON.parse(txt.slice(txt.indexOf('=') + 1).trim().replace(/;\s*$/, ''));
  if (m.meta && m.meta.live_from) throw new Error('market.js already holds live rows and archive/market_base.json is missing');
  base = m;
  fs.writeFileSync(basePath, JSON.stringify(base));
  console.log('froze the Teknosys base:', base.rows.split(';').length, 'rows');
}

const meta = O('meta.json'); const today = meta.today; const now = new Date(today + 'T12:00:00+05:00');
const ctx = E.build(cat, { record: [], signals: [], predictions: [], trends: [], types: S('signal_types.json').types, criteria: {}, minCriteria: 3 });
const P = cat.products.map(p => p.id), PI = {}; P.forEach((p, i) => PI[p] = i);
if (base.products.join() !== P.join()) throw new Error('catalogue product list changed; rebuild the base with make_market.js');
const TH = S('themes.json').themes.map(t => ({ id: t.id, re: new RegExp(t.rx) }));
const PLAY = { lead: 1, partner: 2, monitor: 3 };
const themeMask = (t, d) => { let tm = 0; if (!/^ (disposal|auction|sale of|lease)/.test(E.canon(t))) { const c = E.canon(t + ' ' + String(d || '').slice(0, 400)); TH.forEach((x, i) => { if (x.re.test(c)) tm |= (1 << i); }); } return tm; };

/* ── 2. re-read the base with today's rules ──
   Base rows carry no titles; the k-th relevant row is the k-th detail entry (same build order).
   A base tender is dropped only when a title rule now excludes it, so truncated titles cannot
   lose tenders for any other reason. */
const months = base.months.slice(), mi = {}; months.forEach((m, i) => mi[m] = i);
const juris = ['Federal', 'Punjab', 'KP', 'Other (donor-funded)'];
const cats = base.cats.slice(), secs = base.secs.slice(), si = {}; secs.forEach((s, i) => si[s] = i);
const orgs = base.orgs.slice(), oacc = base.oacc.slice(), oi = {}; orgs.forEach((o, i) => { if (oi[o] == null) oi[o] = i; });
const rows = [], detail = []; let k = 0, dropped = 0;
const baseRows = base.rows.split(';');
const relCount = baseRows.filter(r => +r.split(',')[6] > 0).length;
const aligned = relCount === base.detail.length;
baseRows.forEach(s => {
  const a = s.split(',');
  if (+a[6] > 0) {
    const d = base.detail[k++];
    if (aligned) {
      const r = E.assess({ id: d[0], s: 'EPADS', t: d[2], b: orgs[d[3]], bn: orgs[d[3]], mth: d[7], cat: cats[+a[2]] }, ctx, now);
      if (!r.rel && r.excludedBy && r.excludedBy !== 'individual') { a[5] = ''; a[6] = '0'; dropped++; rows.push(a.slice(0, 8).concat(['0']).join(',')); return; }
    }
    detail.push(d);
  }
  rows.push(a.slice(0, 8).concat(['0']).join(','));
});

/* buyer sector for a live tender: the sector the same organisation carries in the base, else by account */
const oSec = {}; { const cnt = {}; baseRows.forEach(s => { const a = s.split(','); const o = +a[4], x = +a[3]; (cnt[o] = cnt[o] || {})[x] = (cnt[o][x] || 0) + 1; });
  Object.keys(cnt).forEach(o => { oSec[o] = +Object.keys(cnt[o]).sort((x, y) => cnt[o][y] - cnt[o][x])[0]; }); }
const ASEC = { 'Energy & Utilities': 'Energy & Utilities', 'Telecom & IT': 'Telecom & IT', 'Governance': 'Governance & Public Admin', 'Banking & Insurance': 'Finance & Revenue',
  'Revenue & Finance': 'Finance & Revenue', 'Education': 'Education & Research', 'Law Enforcement & Cities': 'Defence & Security', 'Transport': 'Transport & Infrastructure',
  'Social Protection': 'Governance & Public Admin', 'Provincial': 'Provincial Government', 'Identity & Registration': 'Governance & Public Admin', 'Defence': 'Defence & Security', 'Agriculture': 'Other Public Sector' };
const secIx = name => { if (si[name] == null) { si[name] = secs.length; secs.push(name); } return si[name]; };
const orgIx = (name, acc) => { const key = name || 'Unknown buyer'; if (oi[key] == null) { oi[key] = orgs.length; orgs.push(key); oacc.push(acc || ''); } else if (!oacc[oi[key]] && acc) oacc[oi[key]] = acc; return oi[key]; };
const monIx = pub => { const m = (pub || '').slice(0, 7); if (!/^2026-\d\d$/.test(m)) return null; while (months[months.length - 1] < m) { const last = months[months.length - 1]; const nx = '2026-' + String(+last.slice(5) + 1).padStart(2, '0'); mi[nx] = months.length; months.push(nx); } return mi[m]; };
const SRCN = { EPADS: 1, EPMS: 2, PITB: 3, KPITB: 3, PSCA: 3, WB: 4 };

/* ── 3. the ledger: every distinct tender the scans have seen ──
   id -> [pub, src, cat, mth, title, buyer, url, firstSeen, alsoUrl, desc] */
const ledPath = path.join(ARC, 'ledger.json');
const led = rd(ledPath, {});
const seen = rd(path.join(ARC, 'seen.json'), {});
const open = O('tenders_open.json');
open.forEach(t => {
  const prev = led[t.id];
  led[t.id] = [t.pub || '', t.s, t.cat || '', t.mth || '', String(t.t || '').slice(0, 200), t.bn || t.b || '', t.u || '', (prev && prev[7]) || seen[t.id] || today, t.also || '', String(t.d || '').slice(0, 300)];
});
/* tenders seen before the ledger existed: only the id and the day first seen are known */
Object.keys(seen).forEach(id => { if (!led[id]) led[id] = ['', id.split('-')[0], '', '', '', '', '', seen[id], '', '']; });
fs.writeFileSync(ledPath, JSON.stringify(led));

/* the same notice on EPADS and EPMS is one tender: drop an EPMS entry an EPADS entry points to */
const alsoSet = new Set(); Object.values(led).forEach(v => { if (v[8]) alsoSet.add(v[8]); });

let live = 0, liveRel = 0, liveBare = 0, gapSeen = 0;
Object.keys(led).forEach(id => {
  const v = led[id]; const [pub, src, c, mth, title, buyer, url, fs0] = v;
  if (src === 'EPMS' && url && alsoSet.has(url)) return;
  let when = pub;
  if (!title) {
    /* no details kept: count it only if first seen after the first scan, when first sight is publication */
    if (!fs0 || fs0.slice(0, 10) <= SCANS_FROM) return;
    when = fs0.slice(0, 10);
  }
  if (!when || when < LIVE_FROM || when > today) return;
  const m = monIx(when); if (m == null) return;
  const sc = SRCN[src] != null ? SRCN[src] : 5;
  if (!title) {
    rows.push([m, src === 'PITB' ? 1 : 0, cats.indexOf(''), secIx('Not classified (seen before details were kept)'), orgIx('Not recorded'), '', 0, 0, 5].join(','));
    live++; liveBare++; return;
  }
  const t = { id, s: src, t: title, b: buyer, bn: buyer, cat: c, mth, pub, u: url, d: v[9] || '' };
  const r = E.assess(t, ctx, now);
  const acc = r.account || {};
  const o = orgIx(buyer, acc.id || '');
  const j = src === 'PITB' || src === 'PSCA' ? 1 : src === 'KPITB' ? 2 : src === 'WB' ? ({ Punjab: 1, KP: 2 }[acc.province] != null ? { Punjab: 1, KP: 2 }[acc.province] : 3) : 0;
  const sec = src === 'WB' ? secIx('Multilateral & Donor') : oSec[o] != null ? oSec[o] : secIx(ASEC[acc.sector] || 'Other Public Sector');
  const pr = r.rel ? r.asked.map(p => PI[p.id]).filter(x => x != null) : [];
  rows.push([m, j, Math.max(0, cats.indexOf(c)), sec, o, pr.join('.'), r.rel ? PLAY[r.play] || 0 : 0, themeMask(title, t.d), sc].join(','));
  live++;
  if (fs0 && fs0.slice(0, 10) <= SCANS_FROM) gapSeen++;
  if (r.rel) { liveRel++; detail.push([id, pub, title.slice(0, 170), o, pr.join('.'), PLAY[r.play] || 0, url, mth || '', sec, j]); }
});

const baseN = baseRows.length;
const out = {
  themes: base.themes, built: new Date().toISOString(),
  source: 'Teknosys export (EPADS federal and Punjab e-PADS) for 1 January to 14 October 2026; the daily scans (EPADS, PPRA EPMS, PITB, World Bank) from 15 October',
  months, juris, cats, secs, orgs, oacc, products: P, rows: rows.join(';'), detail,
  meta: {
    to: today, base_to: BASE_TO, live_from: LIVE_FROM, scans_from: SCANS_FROM,
    base: baseN, base_dropped: dropped, live, live_relevant: liveRel, live_bare: liveBare,
    notes: [
      'Punjab e-PADS is in the Teknosys export but not in the daily scans, so Punjab tenders after 14 October are not counted.',
      'The scans began on 12 November. Tenders published from 15 October that closed before then were never seen, so late October and early November are undercounted.',
      'The scans add PPRA EPMS, PITB and World Bank notices that the export did not hold, so daily volumes after 14 October are not like-for-like with earlier months.'
    ]
  }
};
fs.writeFileSync(path.join(ROOT, 'app', 'data', 'market.js'), 'window.JW_MARKET=' + JSON.stringify(out) + ';\n');
console.log('market: base', baseN, '(rule drops', dropped + ')', '+ live', live, '(relevant', liveRel + ', details not kept', liveBare + ')', '= total', rows.length,
  '| months', months[0], 'to', months[months.length - 1], '| relevant detail', detail.length,
  '| size', (fs.statSync(path.join(ROOT, 'app', 'data', 'market.js')).size / 1e6).toFixed(2) + 'MB');
