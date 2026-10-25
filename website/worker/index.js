// 3D ZONE TECH: order API (Cloudflare Worker + D1).  Static files come from ./public via the ASSETS binding.
import PRICING from "./pricing.json";

const PIECES = ["tag", "pencil", "ruler", "bottle"];
const STATUSES = ["new", "confirmed", "deposit_paid", "printing", "ready", "delivered", "cancelled"];
const STATUS_AR = { new: "وصلنا طلبك", confirmed: "أكدنا الطلب وبعتنا المعاينة", deposit_paid: "استلمنا العربون", printing: "قيد الطباعة", ready: "جاهز للتسليم", delivered: "تم التسليم", cancelled: "ملغي" };
const AREAS = ["إربد", "عمّان", "غير ذلك"];

const json = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
const bad = (msg, status = 400) => json({ ok: false, error: msg }, status);
const clean = (s, n) => String(s ?? "").replace(/[\u0000-\u001f]/g, " ").trim().slice(0, n);
const orderCode = (id) => `ZT-${1000 + id}`;
const idFromCode = (c) => { const m = /^ZT-(\d+)$/i.exec(String(c).trim()); return m ? Number(m[1]) - 1000 : NaN; };
const digits = (s) => String(s || "").replace(/\D/g, "");

// price = same rules as the website and student_pack/pricing.py
export function priceFor(theme, colours, pieces) {
  const t = PRICING.themes[theme];
  const c = t && t.colours[String(colours)];
  if (!c) return null;
  const sel = PIECES.filter((p) => pieces.includes(p));
  if (!sel.length) return null;
  if (sel.length === PIECES.length) return c.pack;
  const total = PIECES.reduce((a, k) => a + c.costs[k], 0), part = sel.reduce((a, k) => a + c.costs[k], 0);
  const step = PRICING.step;
  return Math.min(c.pack, Math.ceil((c.pack * (part / total) * PRICING.premium) / step - 1e-9) * step);
}

function validateOrder(b) {
  const customer = clean(b.customer, 60), phone = digits(b.phone);
  if (customer.length < 2) return "اكتب اسمك";
  if (phone.length < 9 || phone.length > 15) return "رقم الهاتف غير صحيح";
  const area = AREAS.includes(b.area) ? b.area : "غير ذلك";
  return { customer, phone, area, details: clean(b.details, 500) };
}

async function notify(env, text) {
  if (!env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_CHAT_ID) return;
  try {
    await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text }),
    });
  } catch (_) { /* a failed ping must never lose the order */ }
}

async function tooMany(env, phone) {
  const r = await env.DB.prepare("SELECT COUNT(*) AS n FROM orders WHERE phone = ? AND created_at > datetime('now', '-1 hour')").bind(phone).first();
  return r && r.n >= 5;
}

async function createOrder(env, b) {
  if (b.website) return json({ ok: true, code: "ZT-0000" });          // honeypot field: bots fill it, people never see it
  const v = validateOrder(b);
  if (typeof v === "string") return bad(v);
  if (await tooMany(env, v.phone)) return bad("طلبات كثيرة بوقت قصير. جرّب بعد ساعة أو راسلنا مباشرة.", 429);
  let row;
  if (b.kind === "custom") {
    const details = clean(b.text, 1500);
    if (details.length < 5) return bad("احكيلنا عن الفكرة");
    row = { kind: "custom", name: clean(b.product, 60), theme: null, colours: null, pieces: null, price: null, qty: 1, details: `${details}${b.have ? "\n(عنده القطعة أو صور وقياسات)" : ""}` };
  } else {
    const name = clean(b.name, 11).toUpperCase();
    const colours = Number(b.colours), theme = String(b.theme);
    const pieces = Array.isArray(b.pieces) ? b.pieces.filter((p) => PIECES.includes(p)) : [];
    if (!/^[A-Z ]{1,11}$/.test(name) || !name.trim()) return bad("الاسم بالإنجليزي، حتى 11 حرف");
    const price = priceFor(theme, colours, pieces);
    if (price == null) return bad("اختيار غير صحيح");
    const qty = Math.min(20, Math.max(1, Number(b.qty) || 1));
    row = { kind: "pack", name: name.trim(), theme, colours, pieces: pieces.length === PIECES.length ? "all" : pieces.join("|"), price, qty, details: v.details };
  }
  const res = await env.DB.prepare(
    "INSERT INTO orders (kind, customer, phone, area, name, theme, colours, pieces, price, qty, details) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
  ).bind(row.kind, v.customer, v.phone, v.area, row.name, row.theme, row.colours, row.pieces, row.price, row.qty, row.kind === "custom" ? row.details : v.details).run();
  const id = res.meta.last_row_id, code = orderCode(id);
  const total = row.price != null ? row.price * row.qty : null;
  await notify(env, row.kind === "pack"
    ? `طلب جديد ${code}\n${row.name} · ${row.theme} · ${row.colours} ألوان · ${row.pieces} · x${row.qty}\nالمجموع ${total} دينار\n${v.customer} · ${v.phone} · ${v.area}`
    : `طلب تصميم خاص ${code}\n${row.name}\n${row.details}\n${v.customer} · ${v.phone} · ${v.area}`);
  return json({ ok: true, code, total, status: "new", statusText: STATUS_AR.new });
}

async function track(env, url) {
  const id = idFromCode(url.searchParams.get("id")), phone = digits(url.searchParams.get("phone"));
  if (!(id > 0) || phone.length < 9) return bad("رقم الطلب أو الهاتف غير صحيح");
  const r = await env.DB.prepare("SELECT status, price, qty, name, created_at FROM orders WHERE id = ? AND phone = ?").bind(id, phone).first();
  if (!r) return bad("ما لقينا طلب بهالمعلومات", 404);
  return json({ ok: true, code: orderCode(id), status: r.status, statusText: STATUS_AR[r.status], name: r.name, created: r.created_at });
}

function isAdmin(request, env) {
  const t = (request.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
  if (!env.ADMIN_TOKEN || t.length !== env.ADMIN_TOKEN.length) return false;
  let d = 0;
  for (let i = 0; i < t.length; i++) d |= t.charCodeAt(i) ^ env.ADMIN_TOKEN.charCodeAt(i);
  return d === 0;
}

const csvCell = (v) => { const s = String(v ?? ""); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };

async function admin(request, env, url) {
  if (!isAdmin(request, env)) return bad("غير مصرّح", 401);
  const path = url.pathname;
  if (path === "/api/admin/orders" && request.method === "GET") {
    const { results } = await env.DB.prepare("SELECT * FROM orders ORDER BY id DESC LIMIT 500").all();
    return json({ ok: true, statuses: STATUSES, statusAr: STATUS_AR, orders: results.map((o) => ({ ...o, code: orderCode(o.id) })) });
  }
  if (path === "/api/admin/orders.csv" && request.method === "GET") {
    // same columns as student_pack/order.py reads (order_id,name,theme,colors,pieces,qty) plus customer info
    const { results } = await env.DB.prepare("SELECT * FROM orders WHERE kind = 'pack' AND status NOT IN ('cancelled','delivered') ORDER BY id").all();
    const head = "order_id,name,theme,colors,pieces,qty,status,paid,customer,phone,area,price";
    const lines = results.map((o) => [orderCode(o.id), o.name, o.theme, o.colours, o.pieces, o.qty, o.status, o.paid, o.customer, o.phone, o.area, o.price].map(csvCell).join(","));
    return new Response([head, ...lines].join("\n"), { headers: { "content-type": "text/csv; charset=utf-8", "content-disposition": "attachment; filename=orders.csv" } });
  }
  const m = /^\/api\/admin\/orders\/(\d+)$/.exec(path);
  if (m && request.method === "PATCH") {
    const b = await request.json().catch(() => ({}));
    const sets = [], vals = [];
    if (b.status !== undefined) { if (!STATUSES.includes(b.status)) return bad("حالة غير صحيحة"); sets.push("status = ?"); vals.push(b.status); }
    if (b.paid !== undefined) { sets.push("paid = ?"); vals.push(b.paid ? 1 : 0); }
    if (b.admin_note !== undefined) { sets.push("admin_note = ?"); vals.push(clean(b.admin_note, 500)); }
    if (!sets.length) return bad("لا يوجد تغيير");
    await env.DB.prepare(`UPDATE orders SET ${sets.join(", ")} WHERE id = ?`).bind(...vals, Number(m[1])).run();
    return json({ ok: true });
  }
  return bad("غير موجود", 404);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    try {
      if (url.pathname === "/api/orders" && request.method === "POST") {
        if (Number(request.headers.get("content-length") || 0) > 8000) return bad("الطلب كبير", 413);
        const b = await request.json().catch(() => null);
        return b ? await createOrder(env, b) : bad("طلب غير صالح");
      }
      if (url.pathname === "/api/track" && request.method === "GET") return await track(env, url);
      if (url.pathname.startsWith("/api/admin/")) return await admin(request, env, url);
      if (url.pathname === "/api/health") return json({ ok: true });
    } catch (e) {
      return json({ ok: false, error: "خطأ بالخادم، جرّب مرة ثانية أو راسلنا مباشرة." }, 500);
    }
    return env.ASSETS.fetch(request);
  },
};
