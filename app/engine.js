/*
 * JW Opportunity Desk - engine.js
 *
 * One engine, used twice: by the build (Node, for validation and history) and by the
 * page (browser, on every load). It contains no data. Every rule it applies is read
 * from the catalogue file, and every decision it makes is returned with its evidence.
 *
 * Three steps, in order:
 *   1. RELEVANT?   Does the buyer ask for something in the JazzWorld catalogue?
 *   2. WHO?        Which products, hence which SBUs, and can JazzWorld lead the bid?
 *   3. HOW GOOD?   A 0-100 priority score built only from things that can be observed.
 */
(function (root) {
  'use strict';

  var DAY = 86400000;

  function canon(s) {
    return ' ' + String(s == null ? '' : s).toLowerCase().replace(/\bi\.\s?t\.?(?=[^a-z0-9]|$)/g, 'it').replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').trim() + ' ';
  }

  /* "sim card*" -> / sim card[a-z0-9]*(?= )/   "bulk sms" -> / bulk sms(?:s|es)?(?= )/ */
  function termRx(term) {
    var wild = /\*$/.test(term);
    var t = wild ? term.slice(0, -1) : term;
    var body = t.toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9*]+/g, ' ').trim()
      .split(' ').map(function (tok) { return tok.replace(/\*/g, '[a-z0-9]*'); }).join(' ');
    return new RegExp(' ' + body + (wild ? '[a-z0-9]*' : '(?:s|es)?') + '(?= )');
  }

  function build(cat, insights) {
    var ctx = { cat: cat, byId: {}, products: [], contexts: [], exclude: [], gaps: [], accounts: [], partnersByCat: {} };
    cat.products.forEach(function (p) {
      var q = {
        p: p, id: p.id, sbu: p.sbu, mode: p.mode, block: p.block || [],
        strong: p.strong.map(function (t) { return { t: t, rx: termRx(t), titleOnly: (p.title_only || []).indexOf(t) >= 0, not: p.not && p.not[t] ? new RegExp(p.not[t]) : null }; }),
        support: p.support.map(function (t) { return { t: t, rx: termRx(t), not: p.not && p.not[t] ? new RegExp(p.not[t]) : null }; })
      };
      ctx.products.push(q); ctx.byId[p.id] = p;
    });
    Object.keys(cat.contexts).forEach(function (k) { ctx.contexts.push({ k: k, rx: new RegExp(cat.contexts[k]) }); });
    Object.keys(cat.exclude_title).forEach(function (k) { ctx.exclude.push({ k: k, rx: new RegExp(cat.exclude_title[k]) }); });
    cat.gaps.forEach(function (g) { ctx.gaps.push({ cat: g.cat, label: g.label, rx: new RegExp(g.rx) }); });
    cat.partners.forEach(function (pt) { pt.cats.forEach(function (c) { (ctx.partnersByCat[c] = ctx.partnersByCat[c] || []).push(pt.name); }); });
    cat.accounts.forEach(function (a) { ctx.accounts.push({ a: a, rx: new RegExp(a.rx) }); });

    /* relationship and signal sets, keyed by account id and by account group */
    ctx.rel = {}; ctx.sig = {}; ctx.pred = {};
    ctx.insights = insights || { record: [], signals: [], predictions: [], trends: [] };
    function mark(set, rows) { (rows || []).forEach(function (r) { (r.acc || []).forEach(function (k) { (set[k] = set[k] || []).push(r); }); }); }
    mark(ctx.rel, ctx.insights.record); mark(ctx.sig, ctx.insights.signals); mark(ctx.pred, ctx.insights.predictions);
    return ctx;
  }

  function accountOf(t, ctx) {
    var s = canon((t.b || '') + ' ' + (t.bn || ''));
    for (var i = 0; i < ctx.accounts.length; i++) {
      if (ctx.accounts[i].rx.test(s)) {
        var a = ctx.accounts[i].a;
        var keys = [a.id]; if (a.group) keys.push(a.group);
        var rel = [], sig = [], pred = [];
        keys.forEach(function (k) { rel = rel.concat(ctx.rel[k] || []); sig = sig.concat(ctx.sig[k] || []); pred = pred.concat(ctx.pred[k] || []); });
        var tier = (rel.length || sig.length || pred.length) ? 'A' : (a.digital ? 'B' : 'C');
        return { id: a.id, name: a.name, sector: a.sector, province: a.province, group: a.group, digital: a.digital, bucket: !!a.bucket, tier: tier, rel: rel, sig: sig, pred: pred };
      }
    }
    return { id: '', name: t.bn || t.b || 'Unknown buyer', sector: '', province: '', group: '', digital: false, tier: 'C', rel: [], sig: [], pred: [] };
  }

  var ICT_TITLE = / (it|ict|i t|information technology|software|hardware|network|networking|digital|computer|computers|data cent[a-z]*|datacent[a-z]*|internet|telecom[a-z]*|cyber[a-z]*|online|automation|system integration|server|servers|cloud|telephone|telephony|e (?:office|governance|government|procurement|filing|ticketing|payment|payments|portal|learning|services|commerce|challan|health|billing|stamp|stamping|tendering|khidmat)|electronic|web|website|portal|application|sms|licen[a-z]*|insurance|payment[a-z]*|bank[a-z]*) /;

  /* Step 1 and 2: which catalogue products does this tender ask for, and on what evidence? */
  function match(t, ctx) {
    var T = canon(t.t), D = t.d ? canon(t.d) : '', X = t.x ? canon(t.x) : '', ALL = T + D + X;
    var onCtx = {};
    ctx.contexts.forEach(function (c) { if (c.rx.test(T)) onCtx[c.k] = true; });
    var ictSector = t.sec === 'Info and Comm Tech' || t.s === 'PITB' || t.s === 'KPITB';
    var ictTitle = ICT_TITLE.test(T);
    var found = [];
    ctx.products.forEach(function (q) {
      var blocked = q.block.some(function (b) { return onCtx[b]; });
      var sT = [], sD = [], wT = [];
      q.strong.forEach(function (term) {
        if (term.not && term.not.test(ALL)) return;
        if (term.rx.test(T)) sT.push(term.t);
        else if (!term.titleOnly && ((D && term.rx.test(D)) || (X && term.rx.test(X)))) sD.push(term.t);
      });
      if (!blocked) q.support.forEach(function (term) {
        if (term.not && term.not.test(ALL)) return;
        if (term.rx.test(T)) wT.push(term.t);
      });
      if (!sT.length && !sD.length && wT.length < 2) return;
      found.push({ q: q, sT: sT, sD: sD, wT: wT, blocked: blocked });
    });
    var anyTitleStrong = found.some(function (f) { return f.sT.length && !(f.blocked && f.sT.length + f.sD.length < 2 && !ictSector); });
    var out = [];
    found.forEach(function (f) {
      var str;
      if (f.sT.length) str = (f.blocked && (f.sT.length + f.sD.length) < 2 && !ictSector) ? 1 : 3;
      else if (f.sD.length) str = (anyTitleStrong || ictSector || ictTitle) ? 2 : 1;
      else str = 1;
      var extra = Math.max(0, f.sT.length + f.sD.length - 1) + f.wT.length / 2;
      var fit = str === 3 ? Math.min(1, 0.75 + 0.125 * Math.min(2, extra)) : str === 2 ? Math.min(0.7, 0.5 + 0.1 * Math.min(2, extra)) : 0.2;
      out.push({ id: f.q.id, sbu: f.q.sbu, mode: f.q.mode, str: str, fit: fit, title: longest(f.sT), desc: longest(f.sD), weak: f.wT.slice(0, 4), risk: f.blocked });
    });
    out.sort(function (a, b) { return b.fit - a.fit || (a.mode === 'own' ? -1 : 1); });
    return { products: out, ctx: Object.keys(onCtx), ictSector: ictSector, all: ALL, T: T };
  }

  /* keep the most specific phrases: drop a term when a longer matched term contains it */
  function longest(terms) {
    var c = terms.map(function (t) { return t.replace(/\*/g, ''); });
    var keep = terms.filter(function (t, i) { return !c.some(function (o, j) { return j !== i && o.length > c[i].length && o.indexOf(c[i]) >= 0; }); });
    return keep.slice(0, 5);
  }

  var DEFAULTS = {
    weights: { fit: 35, breadth: 15, account: 15, size: 15, time: 10, signal: 10 },
    partnerMax: 10, rushDays: 3, rushPoints: 5,
    capPartner: 64, capMonitor: 39, capAI: 64, aiFit: { high: 0.6, medium: 0.45 },
    bands: [{ key: 'pursue', label: 'Pursue', min: 65 }, { key: 'qualify', label: 'Qualify', min: 50 }, { key: 'watch', label: 'Watch', min: 35 }, { key: 'low', label: 'Low', min: 0 }],
    tier: { A: 1, B: 0.65, C: 0.3 }
  };

  function sizeSignal(t) {
    var bs = t.doc && t.doc.bs ? t.doc.bs : 0;
    if (bs > 0) {
      var implied = bs / 0.05;
      var v = implied >= 1e8 ? 1 : implied >= 2e7 ? 0.8 : implied >= 5e6 ? 0.6 : implied >= 1e6 ? 0.4 : 0.25;
      return { v: v, why: 'Bid security Rs ' + fmtMoney(bs) + ' implies a contract of at least Rs ' + fmtMoney(implied) + ' if security is capped at 5%', basis: 'bid security' };
    }
    var m = t.mth, nt = t.nt;
    if (m === 'PP') return { v: 0.1, why: 'Petty purchase', basis: 'method' };
    if (m === 'ICS') return { v: 0.1, why: 'Individual consultant selection', basis: 'method' };
    if (m === 'RFQ') return { v: 0.25, why: 'Request for quotation, below the open-tender threshold', basis: 'method' };
    if (t.kind === 'F') return { v: 0.85, why: 'Framework agreement', basis: 'method' };
    if (t.intl && t.s !== 'WB') return { v: 0.85, why: 'International competitive tender', basis: 'method' };
    if (m === 'TS' || m === 'OCB2' || m === 'RFP' || nt === 'RFP' || nt === 'PQ' || nt === 'EOI') return { v: 0.8, why: ({ TS: 'Two-stage', OCB2: 'Two-envelope open tender', RFP: 'Request for proposal' }[m]) || ({ RFP: 'Request for proposal', PQ: 'Pre-qualification', EOI: 'Expression of interest' }[nt]), basis: 'method' };
    if (m === 'OCB1') return { v: 0.6, why: 'Single-envelope open tender', basis: 'method' };
    return { v: 0.6, why: 'Open tender notice, size not stated', basis: 'default' };
  }

  function fmtMoney(n) {
    if (n >= 1e9) return (n / 1e9).toFixed(n >= 1e10 ? 0 : 1) + ' bn';
    if (n >= 1e6) return (n / 1e6).toFixed(n >= 1e8 ? 0 : 1) + ' m';
    if (n >= 1e3) return Math.round(n / 1e3) + 'k';
    return String(Math.round(n));
  }

  function timeFactor(d) { return d < 0 ? 0 : d >= 14 ? 1 : d >= 7 ? 0.7 : d >= 3 ? 0.4 : 0.15; }
  function roundHalfUp(x) { return Math.floor(x + 0.5); }

  /* Full assessment of one tender. `now` is a Date. `S` is the settings object (weights etc.). */
  function assess(t, ctx, now, S, ai) {
    S = S || DEFAULTS;
    var r = { id: t.id, rel: false, play: 'none', reason: '', products: [], asked: [], possible: [], sbus: [], lead: '', addons: [], gaps: [], score: 0, band: null };
    var Tt = canon(t.t).trim();
    r.account = accountOf(t, ctx);
    if (t.cl) { var c = new Date(t.cl.length <= 10 ? t.cl + 'T17:00' : t.cl); r.days = Math.floor((c - now) / DAY); r.closed = c < now; } else { r.days = null; r.closed = false; }

    if (t.st && t.st.indexOf('X') >= 0) { r.reason = 'Cancelled by the buyer'; return r; }
    if (t.kind === 'D') { r.reason = 'Disposal or auction, not a purchase'; return r; }
    for (var i = 0; i < ctx.exclude.length; i++) if (ctx.exclude[i].rx.test(Tt)) {
      r.reason = { disposal: 'Disposal or auction, not a purchase', individual: 'Hiring of an individual, not a company bid', property: 'Property hire, purchase or valuation', consumables: 'Consumables or printing, not a JazzWorld product', oversight: 'A firm hired to manage or monitor a programme' }[ctx.exclude[i].k] || 'Excluded by rule';
      r.excludedBy = ctx.exclude[i].k;
      if (ctx.exclude[i].k !== 'individual') return r;
      r.individual = true;
    }

    var m = match(t, ctx);
    r.ctx = m.ctx;
    r.products = m.products;
    r.asked = m.products.filter(function (p) { return p.str >= 2; });
    r.possible = m.products.filter(function (p) { return p.str < 2; });
    /* Second reader. `ai` is the AI reader's label for this tender: {p:[product ids], c:'high'|'medium'|'low', f:'core'|'partner'|'none', ty:type, w:why}.
       Both readers agree: confirmed. Rules only: kept, flagged for review. AI only (medium or high confidence): kept as AI-found with lower evidence weight. */
    var aiP = [];
    if (ai) { r.ai = ai; r.ttype = ai.ty || ''; aiP = (ai.p || []).filter(function (id) { return ctx.byId[id]; }); if (ai.c === 'low' || ai.f === 'none') aiP = []; }
    if (!r.asked.length && aiP.length) {
      r.asked = aiP.slice(0, 3).map(function (id) { var q = ctx.byId[id]; return { id: id, sbu: q.sbu, mode: q.mode, title: [], desc: [], str: 2, fit: ai.c === 'high' ? S.aiFit.high : S.aiFit.medium, ai: true }; });
      r.source = 'ai';
    } else if (r.asked.length) r.source = !ai ? 'rules' : (aiP.length ? 'both' : 'rules-only');
    if (!r.asked.length) { if (!r.reason) r.reason = ai ? 'Neither reader found a catalogue product' + (ai.w ? ' (AI: ' + ai.w + ')' : '') : (r.possible.length ? 'Only generic words matched, no product-level evidence' : 'No catalogue product matched'); return r; }

    r.rel = true;
    var sb = {}; r.asked.forEach(function (p) { sb[p.sbu] = (sb[p.sbu] || 0) + p.fit; });
    r.sbus = Object.keys(sb).sort(function (a, b) { return sb[b] - sb[a]; });
    r.lead = r.sbus[0];
    var own = r.asked.filter(function (p) { return p.mode === 'own'; });
    var ownStrong = own.filter(function (p) { return p.str === 3; });
    var partnerStrong = r.asked.filter(function (p) { return p.mode !== 'own' && p.str === 3; });
    r.conf = (r.asked.some(function (p) { return p.str === 3 && !p.risk; })) ? 'high' : 'medium';

    /* add-ons: products usually sold alongside what was asked for, not evidenced in the tender */
    var askedIds = {}; r.asked.forEach(function (p) { askedIds[p.id] = 1; });
    r.asked.forEach(function (p) { (ctx.byId[p.id].addons || []).forEach(function (a) { if (!askedIds[a] && r.addons.indexOf(a) < 0) r.addons.push(a); }); });
    r.addons = r.addons.slice(0, 5);

    /* partner gaps */
    var seen = {};
    ctx.gaps.forEach(function (g) { if (!seen[g.cat] && g.rx.test(m.all)) { seen[g.cat] = 1; r.gaps.push({ cat: g.cat, label: g.label, partners: ctx.partnersByCat[g.cat] || [] }); } });

    /* play */
    var small = t.mth === 'PP' || t.mth === 'RFQ';
    if (r.individual || t.mth === 'ICS') { r.play = 'monitor'; r.playWhy = 'Individual hire. Useful as a signal that the buyer is staffing a digital project.'; }
    else if (small) { r.play = 'monitor'; r.playWhy = (t.mth === 'PP' ? 'Petty purchase' : 'Request for quotation') + '. Too small for a managed bid, but it shows live demand at this buyer.'; }
    else if (t.cat === 'W') { r.play = 'partner'; r.playWhy = 'Works contract. A contractor will prime; JazzWorld can supply the digital component.'; }
    else if (ownStrong.length || (own.length && !partnerStrong.length)) { r.play = 'lead'; r.playWhy = 'The buyer asks for a service JazzWorld sells itself.'; }
    else { r.play = 'partner'; r.playWhy = own.length ? 'The main ask needs an OEM or delivery partner; JazzWorld products are a secondary part.' : 'Needs an OEM or delivery partner to bid (resale or build work).'; }

    /* signal backing */
    var ids = Object.keys(askedIds);
    function overlap(row) { return (row.products || []).some(function (p) { return askedIds[p]; }); }
    r.preds = r.account.pred.filter(overlap); r.sigs = r.account.sig.filter(overlap);
    r.rels = r.account.rel;

    /* score */
    var f = r.asked.map(function (p) { return p.fit; });
    var fit = Math.min(1, f[0] + 0.25 * (f[1] || 0) + 0.15 * (f[2] || 0));
    var breadth = 0.5 * Math.min(1, r.sbus.length / 3) + 0.5 * Math.min(1, r.asked.length / 4);
    var size = sizeSignal(t);
    var parts = {
      fit: { v: fit, why: bestWhy(r, ctx) },
      breadth: { v: breadth, why: r.sbus.length + ' SBU' + (r.sbus.length > 1 ? 's' : '') + ', ' + r.asked.length + ' product' + (r.asked.length > 1 ? 's' : '') + ' asked for' },
      account: { v: S.tier[r.account.tier], why: tierWhy(r.account) },
      size: { v: size.v, why: size.why },
      time: { v: r.days == null ? 0.6 : timeFactor(r.days), why: r.days == null ? 'No closing date published' : (r.days < 0 ? 'Closed' : r.days + ' day' + (r.days === 1 ? '' : 's') + ' left') },
      signal: { v: r.preds.length ? 1 : r.sigs.length ? 0.6 : 0, why: r.preds.length ? 'Predicted: ' + r.preds[0].title : r.sigs.length ? 'Backed by signal: ' + r.sigs[0].title : 'No tracked signal for this buyer and product' }
    };
    var W = S.weights, tw = 0, base = 0;
    Object.keys(parts).forEach(function (k) { tw += W[k] || 0; });
    Object.keys(parts).forEach(function (k) { parts[k].w = W[k] || 0; parts[k].pts = tw ? parts[k].v * (W[k] || 0) / tw * 100 : 0; base += parts[k].pts; });
    r.parts = parts; r.base = roundHalfUp(base);
    r.ded = [];
    var gapN = r.gaps.length, share = gapN ? gapN / (gapN + own.length) : 0;
    if (share > 0) r.ded.push({ k: 'partner', pts: -roundHalfUp(share * S.partnerMax), why: gapN + ' scope area' + (gapN > 1 ? 's need' : ' needs') + ' a partner against ' + own.length + ' JazzWorld-own product' + (own.length === 1 ? '' : 's') });
    if (r.days != null && r.days >= 0 && r.days < S.rushDays) r.ded.push({ k: 'rush', pts: -S.rushPoints, why: 'Closes in under ' + S.rushDays + ' days' });
    var sc = Math.max(0, roundHalfUp(base + r.ded.reduce(function (a, d) { return a + d.pts; }, 0)));
    if (r.play === 'partner' && sc > S.capPartner) { r.cap = 'Partner-led bids are capped at ' + S.capPartner; sc = S.capPartner; }
    if (r.play === 'monitor' && sc > S.capMonitor) { r.cap = 'Small buys and individual hires are capped at ' + S.capMonitor; sc = S.capMonitor; }
    if (r.source === 'ai' && sc > S.capAI) { r.cap = 'Tenders found only by the AI reader are capped at ' + S.capAI + ' until a person confirms them'; sc = S.capAI; }
    r.score = sc;
    for (var b = 0; b < S.bands.length; b++) if (sc >= S.bands[b].min) { r.band = S.bands[b]; break; }
    r.size = size;
    return r;
  }

  function bestWhy(r, ctx) {
    var p = r.asked[0], name = ctx.byId[p.id].name;
    if (p.ai) return name + ': AI reader, ' + (r.ai.c || '') + ' confidence. ' + (r.ai.w || '');
    var ev = (p.title.length ? p.title : p.desc).slice(0, 2).map(function (x) { return '"' + x.replace(/\*/g, '') + '"'; }).join(', ');
    return name + ': ' + ev + (p.title.length ? ' in the title' : ' in the scope');
  }
  function tierWhy(a) {
    if (a.tier === 'A') return 'Tier A: ' + (a.rel.length ? 'existing JazzWorld relationship' : 'named in a tracked signal');
    if (a.tier === 'B') return 'Tier B: digital budget holder, no relationship or signal on file';
    return 'Tier C: no relationship, signal or digital mandate on file';
  }

  var api = { canon: canon, termRx: termRx, build: build, match: match, assess: assess, accountOf: accountOf, DEFAULTS: DEFAULTS, fmtMoney: fmtMoney, version: '1.0' };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.JWEngine = api;
})(typeof window !== 'undefined' ? window : this);
