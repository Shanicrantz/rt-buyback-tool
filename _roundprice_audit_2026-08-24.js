export const meta = {
  name: 'rt-roundprice-audit-2026-08-24',
  description: 'Audit DB entries whose new price is a round-number estimate rather than a researched India price',
  phases: [
    { title: 'Audit', detail: 'find the real official India price + real used resale' },
    { title: 'Refute', detail: 'adversarial check before any anchor is moved' },
  ],
}
const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
const N = 12

const CONTEXT = `Rajdhani Telecom (Moradabad) buys used phones to re-sell locally. Its buyback = resale / (1 + margin), so a wrong resale anchor makes RT overpay on EVERY unit of that model.
These DB entries were created by an automated gap audit that recorded suspiciously ROUND new prices (e.g. new=Rs 40,000, resale=Rs 32,000 = exactly 80%). Real India prices almost always end in 999 or 990. So these anchors are probably estimates that were never verified — some are wildly out (a Tecno/Infinix mid-ranger recorded at Rs 40,000 when the series sells at Rs 15-20k).
Your job: replace the estimate with a real, sourced number, or confirm the estimate was right.
- RESALE = what a local Indian shop actually re-sells a mint used unit for TODAY. NOT an OLX asking price (asking runs ~10% high). NOT Cashify's "buy refurbished" retail (warranty-inflated, above local resale).
- Cashify pages show an "Approx. Buyback Value" widget that is hard-coded to 40% of the listed price — a template, never a real quote. Do not use it.
- CONSERVATIVE IS THE SAFE ERROR: overpaying loses money on every unit; underpaying loses one deal.`

const AUDIT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    batch_index: { type: 'integer' },
    items: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        exists_in_india: { type: 'string', enum: ['yes', 'no', 'unverified'] },
        official_new_inr: { type: ['number', 'null'] },
        price_source: { type: 'string' },
        used_resale_inr: { type: ['number', 'null'] },
        resale_method: { type: 'string' },
        buyback_inr: { type: ['number', 'null'] },
        db_price_verdict: { type: 'string', enum: ['db_ok', 'db_too_high', 'db_too_low', 'unknown'] },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      },
      required: ['key', 'exists_in_india', 'official_new_inr', 'price_source', 'used_resale_inr', 'resale_method', 'buyback_inr', 'db_price_verdict', 'confidence'],
    } },
  },
  required: ['batch_index', 'items'],
}

const REFUTE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    batch_index: { type: 'integer' },
    items: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        new_final_inr: { type: ['number', 'null'] },
        resale_final_inr: { type: ['number', 'null'] },
        buyback_final_inr: { type: ['number', 'null'] },
        action: { type: 'string', enum: ['lower', 'raise', 'keep', 'hold'] },
        provenance: { type: 'string', enum: ['official_brand_india', 'major_retailer', 'marketplace_used', 'press_coverage', 'inferred', 'none'] },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
        note: { type: 'string' },
      },
      required: ['key', 'new_final_inr', 'resale_final_inr', 'buyback_final_inr', 'action', 'provenance', 'confidence', 'note'],
    } },
  },
  required: ['batch_index', 'items'],
}

function auditPrompt(i) {
  return `You audit unverified price anchors in Rajdhani Telecom's used-phone DB. TODAY is 2026-08-24.

${CONTEXT}

Your batch (db_new_inr / db_resale_anchor / db_a1 are the CURRENT, SUSPECT values):
  python3 -c "import json;print(json.dumps(json.load(open('${DIR}/_pending/roundprice_batches.json'))[${i}],indent=1,ensure_ascii=False))"

For EACH key:
1. Confirm the model + that exact RAM/storage variant is real and sold in India.
2. official_new_inr: the brand's own India price for that exact variant (Google Store India / Samsung India / brand India store first, then Flipkart/Amazon.in). Note in price_source WHERE you read it and whether the listing showed a struck-through MRP (never report the MRP as the price).
3. used_resale_inr: real local resale for a mint used unit TODAY. For a phone launched under ~3 months ago the used market is thin — about 80-85% of the REAL selling price. For older models, find actual used datapoints and say which.
4. buyback_inr: a real quoted buyback if one exists, else null.
5. db_price_verdict: is the DB's current anchor about right, too high, or too low?
Report null + 'unverified' rather than guessing. A guess here is exactly what created this problem.

Write ${DIR}/_pending/rp_audit_${i}.json AND return {"batch_index":${i},"items":[...]}. Every key exactly once.`
}

function refutePrompt(i, a) {
  return `Adversarial REFUTER for Rajdhani Telecom's price-anchor audit. TODAY is 2026-08-24. An auditor re-priced these; assume they are wrong until it holds up.

${CONTEXT}

Batch (current DB values):
  python3 -c "import json;print(json.dumps(json.load(open('${DIR}/_pending/roundprice_batches.json'))[${i}],indent=1,ensure_ascii=False))"

Auditor output:
${JSON.stringify(a)}

For EACH key, check and settle:
1. Is official_new_inr the real India selling price for THAT variant — not an MRP, not a US price converted, not another trim, not a rumour? A price ending in a round thousand is itself a warning sign; re-source it.
2. Is used_resale_inr grounded in real datapoints, or just new x 0.8 again? If it is just a fraction of new, say so in the note and keep it conservative.
3. Does resale sit BELOW new, and does any buyback sit well below resale (55-80%)? Fix violations.
4. Direction check: if the DB anchor is too high, LOWERING it is safe and should be applied. RAISING an anchor needs medium/high confidence and real provenance — an unsupported raise makes RT overpay.
Set action: 'lower' (DB anchor is too high), 'raise' (defensibly too low), 'keep' (DB is fine), 'hold' (cannot establish anything — leave untouched).
new_final_inr / resale_final_inr = the numbers you would stake money on, null if unknown.

Write ${DIR}/_pending/rp_verified_${i}.json AND return {"batch_index":${i},"items":[...]}. Every key exactly once.`
}

phase('Audit')
const results = await pipeline(
  Array.from({ length: N }, (_, i) => i),
  (i) => agent(auditPrompt(i), { label: `audit:${i}`, phase: 'Audit', schema: AUDIT_SCHEMA, model: 'sonnet', agentType: 'general-purpose' }),
  (a, i) => agent(refutePrompt(i, a), { label: `refute:${i}`, phase: 'Refute', schema: REFUTE_SCHEMA, model: 'sonnet', agentType: 'general-purpose' }),
)
const ok = results.filter(Boolean)
const counts = {}
let n = 0
for (const r of ok) for (const it of (r.items || [])) { n++; counts[it.action] = (counts[it.action] || 0) + 1 }
log(`Round-price audit done: ${ok.length}/${N} batches, ${n} items, actions ${JSON.stringify(counts)}`)
return { batches: ok.length, total: N, items: n, actions: counts }
