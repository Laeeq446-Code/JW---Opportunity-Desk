// Shared team store for the self-hosted site: tender calls, trend shortlist, AI reader results run from the page, concept notes, validation runs.
// Needs a KV namespace bound as STORE in Cloudflare Pages > Settings > Bindings. Without it the page hides team features.
const KEYS = { decisions: "decisions", trends: "trends", reader: "reader", notes: "notes", valid: "valid" };
export async function onRequestGet({ env }) {
  if (!env.STORE) return Response.json({ error: "Team store is not switched on" }, { status: 503 });
  const names = Object.keys(KEYS);
  const vals = await Promise.all(names.map((k) => env.STORE.get(KEYS[k], "json")));
  const out = {}; names.forEach((k, i) => (out[k] = vals[i] || {}));
  return Response.json(out, { headers: { "cache-control": "no-store" } });
}
export async function onRequestPost({ request, env }) {
  if (!env.STORE) return Response.json({ error: "Team store is not switched on" }, { status: 503 });
  let b;
  try { b = await request.json(); } catch { return Response.json({ error: "Bad request" }, { status: 400 }); }
  const key = KEYS[b.c];
  if (!key || typeof b.id !== "string" || !/^[\w.:-]{1,120}$/.test(b.id)) return Response.json({ error: "Bad request" }, { status: 400 });
  if (b.data && JSON.stringify(b.data).length > 60000) return Response.json({ error: "Too large" }, { status: 413 });
  const all = (await env.STORE.get(key, "json")) || {};
  if (b.data) all[b.id] = b.data; else delete all[b.id];
  await env.STORE.put(key, JSON.stringify(all));
  return Response.json({ ok: true });
}
