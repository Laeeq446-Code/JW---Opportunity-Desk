// Passphrase gate for the whole site. Set SITE_PASSPHRASE in Cloudflare Pages > Settings > Variables.
// With no passphrase set, the site is open. The cookie holds an HMAC of the passphrase, never the passphrase.
const COOKIE = "jwod_session";
async function token(secret) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode("jw-opportunity-desk-v1"));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
function page(msg) {
  return new Response(`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>JW Opportunity Desk</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#F5F6F8;font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;color:#151821}
form{background:#fff;border:1px solid #E2E5EA;border-radius:12px;padding:28px;width:min(360px,92vw);display:flex;flex-direction:column;gap:12px}
b{font-size:18px}b i{font-style:normal;color:#C8102E}input,button{font:inherit;padding:10px 12px;border-radius:8px;border:1px solid #D2D6DD}button{background:#151821;color:#fff;border:0;cursor:pointer}p{margin:0;color:#B4232A;font-size:13px}</style></head>
<body><form method="post" action="/__login"><b>JW <i>Opportunity</i> Desk</b><label for="p">Passphrase</label><input id="p" name="p" type="password" autofocus required><button>Open</button>${msg ? `<p>${msg}</p>` : ""}</form></body></html>`,
    { status: 401, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" } });
}
export async function onRequest({ request, env, next }) {
  const pass = env.SITE_PASSPHRASE;
  if (!pass) return next();
  const url = new URL(request.url);
  const want = await token(pass);
  if (url.pathname === "/__login" && request.method === "POST") {
    const form = await request.formData();
    if (String(form.get("p") || "") !== pass) return page("That passphrase is not right.");
    return new Response(null, { status: 303, headers: { location: "/", "set-cookie": `${COOKIE}=${want}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=2592000` } });
  }
  const have = (request.headers.get("cookie") || "").split(/;\s*/).find((c) => c.startsWith(COOKIE + "="));
  if (have && have.slice(COOKIE.length + 1) === want) return next();
  if (url.pathname.startsWith("/api/")) return new Response(JSON.stringify({ error: "Sign in first" }), { status: 401, headers: { "content-type": "application/json" } });
  return page("");
}
