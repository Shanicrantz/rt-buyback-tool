// node khata/test_khata.mjs — checks the khata bridge against a fake NiryatBooks.
// All names and numbers here are synthetic.
import assert from "node:assert/strict";

process.env.NB_RT_TOKEN = "wbops_test_token";
process.env.KHATA_PIN = "246810";
process.env.NB_RT_MCP_URL = "https://nb.test/api/mcp/rt";
process.env.RT_UPI_ID = "shop@upi";

const fn = await import("./netlify/functions/khata.mjs");
const handler = fn.default;

const AGING = {
  kind: "receivables", as_of: "2026-11-07", total_outstanding: 103509.59,
  rows: [
    { invoice_number: "RT/1/26-27", date: "2026-04-12", contact: "Asha Traders ( Shop )", currency: "INR", outstanding_inr: 60000.01, days: 209, bucket: "90+" },
    { invoice_number: "RT/9/26-27", date: "2026-06-13", contact: "Asha Traders ( Shop )", currency: "INR", outstanding_inr: 40000, days: 147, bucket: "90+" },
    { invoice_number: "RT/20/26-27", date: "2026-10-24", contact: "Kiran Kumar", currency: "INR", outstanding_inr: 3500, days: 14, bucket: "0-30" },
    { invoice_number: "RT/21/26-27", date: "2026-08-22", contact: "Round Off Person", currency: "INR", outstanding_inr: 9.58, days: 77, bucket: "61-90" },
  ],
};
const CONTACTS = [
  { id: "c1", display_name: "Asha Traders ( Shop )", type_tags: ["customer", "vendor"], phone: null },
  { id: "c2", display_name: "Kiran Kumar", type_tags: ["vendor"], phone: "+91 90000 00001" },
  { id: "c3", display_name: "Kiran Kumar", type_tags: ["customer"], phone: "09000000002 / 9000000003" },
  { id: "c4", display_name: "Kiran Kumari", type_tags: ["customer"], phone: "9000000004" },
];
const INVOICES = {
  c2: [{ invoice_number: "RT/5/26-27", date: "2026-05-01", grand_total: 100, payment_status: "paid", status: "issued" }],
  c3: [{ invoice_number: "RT/20/26-27", date: "2026-10-24", grand_total: 3500, payment_status: "unpaid", status: "issued" }],
};

const calls = [];
globalThis.fetch = async (url, init) => {
  assert.equal(url, process.env.NB_RT_MCP_URL);
  assert.equal(init.headers.Authorization, "Bearer wbops_test_token");
  const body = JSON.parse(init.body);
  assert.equal(body.method, "tools/call");
  const { name, arguments: args } = body.params;
  calls.push({ name, args });
  let result;
  if (name === "get_aging") result = AGING;
  else if (name === "list_contacts") {
    // NiryatBooks puts q into an unquoted PostgREST or() — parens/commas break it.
    if (/[(),]/.test(args.q)) return new Response(JSON.stringify({ jsonrpc: "2.0", id: body.id, error: { code: -32603, message: "PGRST100 parse error" } }), { status: 200 });
    result = CONTACTS.filter((c) => c.display_name.toLowerCase().includes(args.q.toLowerCase()));
  } else if (name === "list_invoices") result = INVOICES[args.contact_id] ?? [];
  else if (name === "list_payments") result = args.contact_id === "c3" ? [{ date: "2026-10-30", inr_amount: 500, mode: "upi", reference: null }] : [];
  else throw new Error("unexpected tool " + name);
  return new Response(JSON.stringify({ jsonrpc: "2.0", id: body.id, result: { content: [{ type: "text", text: JSON.stringify(result) }] } }), { status: 200 });
};

const post = (body, pin = "246810", ip = "1.1.1.1") =>
  handler(new Request("https://khata.test/api/khata", { method: "POST", headers: { "content-type": "application/json", "x-khata-pin": pin }, body: JSON.stringify(body) }), { ip });

let checks = 0;
async function test(name, f) {
  try { await f(); checks++; } catch (e) { e.message = `${name}: ${e.message}`; throw e; }
}

await test("phone normalisation", () => {
  assert.equal(fn.normalizePhone("+91 90000 00001"), "9000000001");
  assert.equal(fn.normalizePhone("09000000002 / 9000000003"), "9000000002");
  assert.equal(fn.normalizePhone("12345"), null);
  assert.equal(fn.normalizePhone("5000000000"), null);
  assert.equal(fn.normalizePhone(null), null);
});

await test("search term drops characters that break the NiryatBooks filter", () => {
  assert.equal(fn.searchTerm("Asha Traders ( Shop )"), "Asha Traders");
  assert.equal(fn.searchTerm("M/S MERAJ EXPORTS"), "S MERAJ EXPORTS");
  assert.equal(fn.searchTerm("Mohd Danish Mbd...."), "Mohd Danish Mbd....");
  assert.equal(fn.searchTerm("A, B"), "");
});

await test("aging groups per customer, biggest first, oldest bill first", () => {
  const g = fn.groupAging(AGING.rows);
  assert.equal(g.length, 3);
  assert.equal(g[0].name, "Asha Traders ( Shop )");
  assert.equal(g[0].total, 100000.01);
  assert.equal(g[0].oldest_days, 209);
  assert.deepEqual(g[0].bills.map((b) => b.number), ["RT/1/26-27", "RT/9/26-27"]);
  assert.equal(fn.groupAging([{ invoice_number: "X", contact_id: "z", contact: "A", outstanding_inr: 1, days: 1 }])[0].key, "id:z");
});

await test("non-POST and missing config are refused", async () => {
  const g = await handler(new Request("https://khata.test/api/khata"), {});
  assert.equal(g.status, 405);
  const saved = process.env.NB_RT_TOKEN;
  delete process.env.NB_RT_TOKEN;
  const r = await post({ action: "ping" });
  assert.equal(r.status, 503);
  assert.deepEqual((await r.json()).missing, ["NB_RT_TOKEN"]);
  process.env.NB_RT_TOKEN = saved;
});

await test("PIN: empty is not a guess, wrong guesses lock the IP", async () => {
  for (let i = 0; i < 12; i++) assert.equal((await post({ action: "ping" }, "", "2.2.2.2")).status, 401);
  assert.equal((await post({ action: "ping" }, "246810", "2.2.2.2")).status, 200, "empty PINs must not lock");
  for (let i = 0; i < 8; i++) assert.equal((await post({ action: "ping" }, "000000", "3.3.3.3")).status, 401);
  const locked = await post({ action: "ping" }, "246810", "3.3.3.3");
  assert.equal(locked.status, 429);
  assert.equal((await locked.json()).error, "locked");
  assert.equal((await post({ action: "ping" }, "246810", "4.4.4.4")).status, 200, "other IPs unaffected");
});

await test("summary: one NB call, totals and shop details, no-store", async () => {
  calls.length = 0;
  const r = await post({ action: "summary" });
  assert.equal(r.status, 200);
  assert.equal(r.headers.get("cache-control"), "no-store");
  const d = await r.json();
  assert.deepEqual(calls.map((c) => c.name), ["get_aging"]);
  assert.deepEqual(calls[0].args, { kind: "receivables" });
  assert.equal(d.total, 103509.59);
  assert.equal(d.bill_count, 4);
  assert.equal(d.customers.length, 3);
  assert.equal(d.shop.upi, "shop@upi");
});

await test("contacts: exact-name match, customer preferred, vendor flag, safe query", async () => {
  calls.length = 0;
  const d = await (await post({ action: "contacts", names: ["Asha Traders ( Shop )", "Kiran Kumar", "Nobody Here"] })).json();
  assert.deepEqual(d.contacts["Asha Traders ( Shop )"], { found: true, phone: null, is_vendor: true, matches: 1 });
  assert.equal(d.contacts["Kiran Kumar"].phone, "9000000002", "customer-tagged duplicate wins, Kiran Kumari ignored");
  assert.equal(d.contacts["Kiran Kumar"].matches, 2);
  assert.equal(d.contacts["Kiran Kumar"].is_vendor, false, "the same-named vendor is someone else");
  assert.deepEqual(d.contacts["Nobody Here"], { found: false });
  assert.ok(calls.every((c) => c.name === "list_contacts" && !/[(),]/.test(c.args.q)));
});

await test("customer: picks the duplicate that owns the open bill", async () => {
  const d = await (await post({ action: "customer", name: "Kiran Kumar", bills: ["RT/20/26-27"] })).json();
  assert.equal(d.ambiguous, true);
  assert.equal(d.contact.phone, "9000000002");
  assert.deepEqual(d.invoices.map((i) => i.number), ["RT/20/26-27"]);
  assert.deepEqual(d.payments, [{ date: "2026-10-30", amount: 500, mode: "upi", reference: null }]);
});

await test("client cannot reach any other tool", async () => {
  calls.length = 0;
  const r = await post({ action: "record_payment", name: "x" });
  assert.equal(r.status, 400);
  const r2 = await post({ action: "summary", tool: "record_payment" });
  assert.equal(r2.status, 200);
  assert.ok(calls.every((c) => ["get_aging", "list_contacts", "list_invoices", "list_payments"].includes(c.name)));
});

await test("NiryatBooks errors map to plain codes", async () => {
  const real = globalThis.fetch;
  globalThis.fetch = async () => new Response("", { status: 401 });
  assert.equal((await (await post({ action: "summary" })).json()).error, "nb_unauthorized");
  globalThis.fetch = async () => new Response("", { status: 429 });
  assert.equal((await post({ action: "summary" })).status, 503);
  globalThis.fetch = async () => { throw new TypeError("fetch failed"); };
  assert.equal((await (await post({ action: "summary" })).json()).error, "nb_unreachable");
  globalThis.fetch = real;
});

console.log(`khata bridge: ${checks} checks passed`);
