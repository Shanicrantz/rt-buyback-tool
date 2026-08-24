export const meta = {
  name: 'rt-gap-pricecheck-2026-08-24',
  description: 'Verify the official India price + realistic used resale of this week gap-audit additions before they enter the DB',
  phases: [
    { title: 'Price', detail: 'independent official India price + used resale per new model' },
    { title: 'Refute', detail: 'adversarial check vs the series price band and MRP confusion' },
  ],
}
const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
const N = 4

const TRAP = `KNOWN TRAPS on this dataset — the gap-audit finder has repeatedly been caught on all three:
1. MRP vs SELLING PRICE. Indian listings print an inflated "MRP" beside the real price (e.g. "Rs 20,999, MRP Rs 44,999, 53% off"). The MRP is fiction. Report the real selling price. Also make sure you did not pick up the MRP itself as the price.
2. SERIES BAND. A new model almost never costs 2-3x its own predecessor. If your price is far outside the series' historical India band (given to you as db_series_context), you are probably reading the wrong product, the wrong variant, or an MRP.
3. VARIANT SUBSTITUTION. Price the EXACT RAM/storage in the key. Do not carry the top trim's price onto a base trim.
Also: "Coming Soon" / pre-order listings are not proof a phone is ON SALE. Say so if that is all you found.`

const PRICE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    batch_index: { type: 'integer' },
    items: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        on_sale_in_india: { type: 'string', enum: ['yes', 'preorder_or_announced', 'no', 'unverified'] },
        india_launch_date: { type: ['string', 'null'] },
        official_new_inr: { type: ['number', 'null'] },
        price_source: { type: 'string' },
        mrp_seen_inr: { type: ['number', 'null'] },
        used_resale_inr: { type: ['number', 'null'] },
        resale_method: { type: 'string' },
        suggested_tier: { type: 'string', enum: ['S', 'A', 'B', 'C', 'D'] },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      },
      required: ['key', 'on_sale_in_india', 'india_launch_date', 'official_new_inr', 'price_source', 'used_resale_inr', 'resale_method', 'suggested_tier', 'confidence'],
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
        add_to_db: { type: 'boolean' },
        new_final_inr: { type: ['number', 'null'] },
        resale_final_inr: { type: ['number', 'null'] },
        tier_final: { type: 'string', enum: ['S', 'A', 'B', 'C', 'D'] },
        launch_final: { type: ['string', 'null'] },
        price_provenance: { type: 'string', enum: ['official_brand_india', 'major_retailer', 'press_coverage', 'inferred', 'none'] },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
        note: { type: 'string' },
      },
      required: ['key', 'add_to_db', 'new_final_inr', 'resale_final_inr', 'tier_final', 'launch_final', 'price_provenance', 'confidence', 'note'],
    } },
  },
  required: ['batch_index', 'items'],
}

function pricePrompt(i) {
  return `You price-check candidate NEW additions to Rajdhani Telecom's used-phone DB. TODAY is 2026-08-24. These models were proposed by a gap audit whose prices look inflated; establish the truth independently.

${TRAP}

Your batch (includes the proposal AND db_series_context = what the same series already costs in the DB):
  python3 -c "import json;print(json.dumps(json.load(open('${DIR}/_gaps/check_batches.json'))[${i}],indent=1,ensure_ascii=False))"

For EACH item, research from scratch:
  - on_sale_in_india + india_launch_date: is it actually selling in India now? Prefer the brand's own India store, then Flipkart/Amazon.in live listings, then India press coverage.
  - official_new_inr for the EXACT variant, plus mrp_seen_inr if a struck-through MRP was shown next to it (report both so the two can never be confused).
  - used_resale_inr: what a mint used unit re-sells for locally TODAY. A phone launched days ago has essentially no used market — use roughly 80-85% of the REAL selling price and say so in resale_method. Never exceed the new price.
  - suggested_tier: S=Apple/Samsung S·Z flagship/Pixel Pro; A=OnePlus flagship/premium/Samsung A7x; B=Xiaomi/Vivo X/Oppo Reno/Nord/Nothing/Moto Edge·Razr; C=Vivo Y·T/Oppo A·F/Realme C·Narzo/Redmi Note/Poco/iQOO Z/Samsung A0x-A3x·M·F/Tecno-Infinix upper; D=entry Infinix/Tecno/Lava/itel/Micromax. Budget series do NOT get tier B just because the model is new.
Say 'unverified' rather than guessing. Getting a price wrong here makes RT overpay every customer who walks in with this phone.

Write ${DIR}/_gaps/price_${i}.json AND return {"batch_index":${i},"items":[...]}. Every key exactly once.`
}

function refutePrompt(i, p) {
  return `Adversarial REFUTER for Rajdhani Telecom's gap additions. TODAY is 2026-08-24. Assume the price researcher was fooled; prove it or clear it.

${TRAP}

Batch + series context:
  python3 -c "import json;print(json.dumps(json.load(open('${DIR}/_gaps/check_batches.json'))[${i}],indent=1,ensure_ascii=False))"

Researcher output:
${JSON.stringify(p)}

For EACH item:
1. BAND TEST: compare new_final against db_series_context and the model's own predecessor. A >40% jump over the predecessor's launch price needs a named source saying so, not an inference. If it fails the band test and you cannot source it, treat the price as unproven.
2. MRP TEST: could this number be the struck-through MRP? Check for a matching "N% off" pair.
3. VARIANT TEST: is it the exact RAM/storage in the key?
4. SALE TEST: on sale, or only announced/pre-order/'coming soon'?
5. RESALE TEST: resale must be below the real selling price, and for a phone with no used market yet it should be ~80-85% of it — not of the MRP.
Then decide add_to_db. Add ONLY when the model is real AND you have a defensible price for that exact variant (price_provenance official_brand_india / major_retailer, or press_coverage at medium+ confidence). If the model is real but the price is unproven, set add_to_db=false and explain — a missing entry costs one quote, a wrong entry costs money on every unit.

Write ${DIR}/_gaps/checked_${i}.json AND return {"batch_index":${i},"items":[...]}. Every key exactly once.`
}

phase('Price')
const results = await pipeline(
  Array.from({ length: N }, (_, i) => i),
  (i) => agent(pricePrompt(i), { label: `price:${i}`, phase: 'Price', schema: PRICE_SCHEMA, model: 'sonnet', agentType: 'general-purpose' }),
  (p, i) => agent(refutePrompt(i, p), { label: `refute:${i}`, phase: 'Refute', schema: REFUTE_SCHEMA, model: 'sonnet', agentType: 'general-purpose' }),
)
const ok = results.filter(Boolean)
let n = 0, add = 0
for (const r of ok) for (const it of (r.items || [])) { n++; if (it.add_to_db) add++ }
log(`Gap price-check done: ${ok.length}/${N} batches, ${n} items, ${add} cleared to add.`)
return { batches: ok.length, total: N, items: n, cleared: add }
