// RT Khata — read-only bridge from NiryatBooks (Rajdhani Telecom) to the khata page.
//
// The browser never sees the NiryatBooks token. It sends a staff PIN; this
// function checks it, then calls a fixed set of READ tools on the RT MCP
// endpoint and returns only what the khata screen needs. The client never
// names a tool, so nothing it sends can reach a write tool.
//
// Environment (Netlify site settings → Environment variables):
//   NB_RT_TOKEN    required  NiryatBooks MCP token for the Rajdhani Telecom org
//                            (issue it for a viewer-level user)
//   KHATA_PIN      required  staff PIN, 6+ digits
//   NB_RT_MCP_URL  optional  defaults to the RT per-business MCP address
//   RT_UPI_ID      optional  printed in reminder messages
//   RT_SHOP_PHONE  optional  printed in reminder messages

import { timingSafeEqual, createHash } from "node:crypto";

export const config = { path: "/api/khata" };

const DEFAULT_MCP_URL = "https://niryatbooks.com/api/mcp/rajdhani-telecom-c86r";
const READ_TOOLS = new Set(["get_aging", "list_contacts", "list_invoices", "list_payments"]);
const NB_TIMEOUT_MS = 20_000;
const CONTACT_TTL_MS = 10 * 60_000;
const MAX_NAMES_PER_CALL = 10;
const LOOKUP_CONCURRENCY = 4;
const MAX_FAILS = 8;
const LOCK_MS = 15 * 60_000;

// Warm-instance memory only. Best effort: a cold start begins empty.
const contactCache = new Map(); // normalized name -> { at, candidates }
const failures = new Map(); // ip -> { count, until }

class KhataError extends Error {
  constructor(code, status = 502, detail) {
    super(code);
    this.code = code;
    this.status = status;
    this.detail = detail;
  }
}

// ---------- pure helpers (exported for tests) ----------

export function normName(s) {
  return String(s ?? "").toLowerCase().replace(/\s+/g, " ").trim();
}

// Indian mobile → 10 digits, or null. Takes the first valid number when the
// field holds several ("97612 55555 / 98xxxxxxxx").
export function normalizePhone(raw) {
  if (!raw) return null;
  const parts = String(raw).split(/[\/,;|]| or /i);
  for (const p of parts) {
    let d = p.replace(/\D/g, "");
    if (d.length === 12 && d.startsWith("91")) d = d.slice(2);
    else if (d.length === 11 && d.startsWith("0")) d = d.slice(1);
    if (/^[6-9]\d{9}$/.test(d)) return d;
  }
  return null;
}

// NiryatBooks list_contacts puts `q` unquoted into a PostgREST or() filter, so
// parentheses and commas in a name break the query. Search on the longest safe
// run of the name and match the full name exactly afterwards.
export function searchTerm(name) {
  const runs = String(name ?? "")
    .split(/[^A-Za-z0-9 .&'-]+/)
    .map((r) => r.replace(/\s+/g, " ").trim())
    .filter((r) => r.replace(/[^A-Za-z0-9]/g, "").length >= 2);
  runs.sort((a, b) => b.length - a.length);
  return (runs[0] ?? "").slice(0, 60);
}

const round2 = (n) => Math.round(Number(n || 0) * 100) / 100;

// get_aging rows → one entry per customer, biggest balance first.
export function groupAging(rows) {
  const byKey = new Map();
  for (const r of rows ?? []) {
    const name = String(r.contact ?? "").trim() || "Unknown customer";
    const key = r.contact_id ? `id:${r.contact_id}` : `name:${normName(name)}`;
    let c = byKey.get(key);
    if (!c) {
      c = { key, name, contact_id: r.contact_id ?? null, total: 0, oldest_days: 0, bills: [] };
      byKey.set(key, c);
    }
    const amount = round2(r.outstanding_inr);
    c.total = round2(c.total + amount);
    c.oldest_days = Math.max(c.oldest_days, Number(r.days) || 0);
    c.bills.push({ number: r.invoice_number, date: r.date, days: Number(r.days) || 0, bucket: r.bucket, amount });
  }
  const out = [...byKey.values()];
  for (const c of out) c.bills.sort((a, b) => b.days - a.days);
  out.sort((a, b) => b.total - a.total);
  return out;
}

// Exact-name candidates from a list_contacts result, best first:
// customer-tagged, then with a usable phone.
export function rankCandidates(name, contacts) {
  const want = normName(name);
  return (contacts ?? [])
    .filter((c) => normName(c.display_name) === want)
    .map((c) => ({
      id: c.id,
      name: c.display_name,
      phone: normalizePhone(c.phone),
      is_customer: (c.type_tags ?? []).includes("customer"),
      is_vendor: (c.type_tags ?? []).includes("vendor"),
    }))
    .sort((a, b) => (b.is_customer - a.is_customer) || (!!b.phone - !!a.phone));
}

export function pinMatches(given, expected) {
  if (!expected) return false;
  // Hash both sides so the comparison is constant-time regardless of length.
  const a = createHash("sha256").update(String(given ?? "")).digest();
  const b = createHash("sha256").update(String(expected)).digest();
  return timingSafeEqual(a, b);
}

// ---------- NiryatBooks MCP ----------

let rpcId = 0;

async function callTool(env, name, args) {
  if (!READ_TOOLS.has(name)) throw new KhataError("tool_not_allowed", 500);
  let res;
  try {
    res = await fetch(env.url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.token}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ jsonrpc: "2.0", id: ++rpcId, method: "tools/call", params: { name, arguments: args } }),
      signal: AbortSignal.timeout(NB_TIMEOUT_MS),
    });
  } catch (e) {
    throw new KhataError("nb_unreachable", 502, e?.name === "TimeoutError" ? "timeout" : undefined);
  }
  if (res.status === 401) throw new KhataError("nb_unauthorized", 502);
  if (res.status === 429) throw new KhataError("nb_rate_limited", 503);
  if (!res.ok) throw new KhataError("nb_error", 502, `HTTP ${res.status}`);
  let body;
  try {
    body = await res.json();
  } catch {
    throw new KhataError("nb_error", 502, "bad response");
  }
  if (body.error) throw new KhataError("nb_error", 502, String(body.error.message ?? "").slice(0, 200));
  const text = body.result?.content?.[0]?.text;
  try {
    return JSON.parse(text);
  } catch {
    throw new KhataError("nb_error", 502, "unparseable tool result");
  }
}

async function lookupContact(env, name) {
  const key = normName(name);
  const hit = contactCache.get(key);
  if (hit && Date.now() - hit.at < CONTACT_TTL_MS) return hit.candidates;
  const q = searchTerm(name);
  const list = q ? await callTool(env, "list_contacts", { q, limit: 50 }) : [];
  const candidates = rankCandidates(name, list);
  contactCache.set(key, { at: Date.now(), candidates });
  return candidates;
}

async function mapLimit(items, limit, fn) {
  const out = new Array(items.length);
  let next = 0;
  const workers = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (next < items.length) {
      const i = next++;
      out[i] = await fn(items[i], i);
    }
  });
  await Promise.all(workers);
  return out;
}

// ---------- actions ----------

async function summary(env) {
  const aging = await callTool(env, "get_aging", { kind: "receivables" });
  const customers = groupAging(aging.rows);
  return {
    as_of: aging.as_of,
    fetched_at: new Date().toISOString(),
    total: round2(aging.total_outstanding),
    bill_count: (aging.rows ?? []).length,
    customers,
    shop: { upi: env.upi, phone: env.shopPhone },
  };
}

async function contacts(env, body) {
  const names = Array.isArray(body.names) ? body.names.slice(0, MAX_NAMES_PER_CALL).map(String) : [];
  const results = await mapLimit(names, LOOKUP_CONCURRENCY, async (name) => {
    try {
      const c = await lookupContact(env, name);
      const best = c[0];
      // Flags describe the best match only: a same-named vendor elsewhere in
      // the books is a different person, not a reason to warn.
      return [name, best ? { found: true, phone: best.phone, is_vendor: best.is_vendor, matches: c.length } : { found: false }];
    } catch (e) {
      if (e instanceof KhataError && (e.code === "nb_rate_limited" || e.code === "nb_unauthorized")) throw e;
      return [name, { error: true }];
    }
  });
  return { contacts: Object.fromEntries(results) };
}

async function customer(env, body) {
  const name = String(body.name ?? "").slice(0, 200);
  const billNumbers = new Set((Array.isArray(body.bills) ? body.bills : []).map(String));
  const candidates = await lookupContact(env, name);
  if (!candidates.length) return { contact: null, invoices: [], payments: [], ambiguous: false };

  // Same display name can exist twice; pick the one that owns the open bills.
  let chosen = null;
  let invoices = [];
  for (const cand of candidates.slice(0, 3)) {
    const inv = await callTool(env, "list_invoices", { contact_id: cand.id, limit: 15 });
    if (!chosen) {
      chosen = cand;
      invoices = inv;
    }
    if (inv.some((i) => billNumbers.has(i.invoice_number))) {
      chosen = cand;
      invoices = inv;
      break;
    }
  }
  const payments = await callTool(env, "list_payments", { contact_id: chosen.id, direction: "in", limit: 10 });
  return {
    contact: { name: chosen.name, phone: chosen.phone, is_vendor: chosen.is_vendor },
    ambiguous: candidates.length > 1,
    invoices: (invoices ?? []).map((i) => ({
      number: i.invoice_number,
      date: i.date,
      total: round2(i.grand_total),
      payment_status: i.payment_status,
      status: i.status,
    })),
    payments: (payments ?? []).map((p) => ({
      date: p.date,
      amount: round2(p.inr_amount),
      mode: p.mode,
      reference: p.reference ?? null,
    })),
  };
}

// ---------- HTTP ----------

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}

function readEnv() {
  return {
    token: process.env.NB_RT_TOKEN || "",
    pin: process.env.KHATA_PIN || "",
    url: process.env.NB_RT_MCP_URL || DEFAULT_MCP_URL,
    upi: process.env.RT_UPI_ID || null,
    shopPhone: process.env.RT_SHOP_PHONE || null,
  };
}

function clientIp(req, context) {
  return context?.ip || req.headers.get("x-nf-client-connection-ip") || req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
}

export default async function handler(req, context) {
  if (req.method !== "POST") return json({ error: "method_not_allowed" }, 405);

  const env = readEnv();
  const missing = [!env.token && "NB_RT_TOKEN", !env.pin && "KHATA_PIN"].filter(Boolean);
  if (missing.length) return json({ error: "not_configured", missing }, 503);

  const ip = clientIp(req, context);
  const f = failures.get(ip);
  if (f && f.until > Date.now()) {
    return json({ error: "locked", retry_after_s: Math.ceil((f.until - Date.now()) / 1000) }, 429);
  }
  const givenPin = req.headers.get("x-khata-pin") || "";
  // Opening the page without a PIN is not a wrong guess — don't count it.
  if (!givenPin) return json({ error: "need_pin" }, 401);
  if (!pinMatches(givenPin, env.pin)) {
    const count = (f && f.until <= Date.now() && f.count >= MAX_FAILS ? 0 : f?.count ?? 0) + 1;
    failures.set(ip, { count, until: count >= MAX_FAILS ? Date.now() + LOCK_MS : 0 });
    return json({ error: "bad_pin" }, 401);
  }
  failures.delete(ip);

  let body;
  try {
    body = await req.json();
  } catch {
    return json({ error: "bad_request" }, 400);
  }

  try {
    switch (body?.action) {
      case "ping":
        return json({ ok: true });
      case "summary":
        return json(await summary(env));
      case "contacts":
        return json(await contacts(env, body));
      case "customer":
        return json(await customer(env, body));
      default:
        return json({ error: "bad_request" }, 400);
    }
  } catch (e) {
    if (e instanceof KhataError) {
      console.error(`[khata] ${body?.action}: ${e.code}${e.detail ? ` (${e.detail})` : ""}`);
      return json({ error: e.code }, e.status);
    }
    console.error(`[khata] ${body?.action}: unexpected`, e);
    return json({ error: "server_error" }, 500);
  }
}
