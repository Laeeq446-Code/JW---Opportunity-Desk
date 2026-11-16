// AI for the self-hosted site. The key stays on the server (ANTHROPIC_API_KEY); the page never sees it.
// GET tells the page whether AI is switched on. POST forwards a Messages API request with the model and limits set here.
const MAX_TOKENS = 2000;
export async function onRequestGet({ env }) {
  return Response.json({ ok: !!env.ANTHROPIC_API_KEY });
}
export async function onRequestPost({ request, env }) {
  if (!env.ANTHROPIC_API_KEY) return Response.json({ error: "AI is not switched on" }, { status: 503 });
  let body;
  try { body = await request.json(); } catch { return Response.json({ error: "Bad request" }, { status: 400 }); }
  if (!Array.isArray(body.messages) || !body.messages.length) return Response.json({ error: "No messages" }, { status: 400 });
  const size = JSON.stringify(body).length;
  if (size > 400000) return Response.json({ error: "Request too large" }, { status: 413 });
  const req = { model: env.AI_MODEL || "claude-sonnet-5-5", max_tokens: Math.min(Number(body.max_tokens) || 1200, MAX_TOKENS), messages: body.messages };
  if (Array.isArray(body.tools) && body.tools.length) req.tools = body.tools.slice(0, 12);
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "content-type": "application/json", "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01" },
    body: JSON.stringify(req),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) return Response.json({ error: (j.error && j.error.message) || "AI request failed" }, { status: r.status });
  return Response.json({ content: j.content, stop_reason: j.stop_reason, usage: j.usage });
}
