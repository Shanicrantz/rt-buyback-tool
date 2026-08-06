export const meta = {
  name: 'rt-buyback-rate-refresh',
  description: 'Live-refresh today (June 2026) market rates for all 1566 phones in RT buyback DB',
  phases: [
    { title: 'Live Refresh', detail: '167 batch agents fetch today\'s Cashify/Amazon/Flipkart rates and propose updated anchors' },
  ],
}

const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
const N = 50

const UPDATE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    batch_index: { type: 'integer' },
    updates: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          key: { type: 'string' },
          status: { type: 'string', enum: ['live', 'no_live_data'] },
          anchor_field: {
            type: 'string',
            enum: ['rt_buyback_a1_override', 'cashify_exchange', 'resale_target_a1', 'refurb_retail_anchor_excellent', 'net_new_inr', 'none'],
          },
          new_value: { type: ['number', 'null'] },
          old_value: { type: ['number', 'null'] },
          new_a1_estimate: { type: ['number', 'null'] },
          new_price_ceiling: { type: ['number', 'null'] },
          source: { type: 'string' },
          confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
          override_review: {
            type: ['object', 'null'],
            additionalProperties: true,
          },
        },
        required: ['key', 'status', 'anchor_field', 'new_value', 'old_value', 'source', 'confidence'],
      },
    },
  },
  required: ['batch_index', 'updates'],
}

function promptFor(i) {
  return `You are refreshing live market resale/buyback rates for Rajdhani Telecom's (Moradabad, India) used-phone buyback database. TODAY is 2026-08-05. You handle ONE batch of phones.

WORKING DIR: ${DIR}

STEP 1 — Get your assigned phone keys and their current data:
Run:
  python3 -c "import json; ks=json.load(open('${DIR}/_batches.json'))[${i}]; d=json.load(open('${DIR}/phone_db.json')); print(json.dumps({k:d[k] for k in ks}, ensure_ascii=False, indent=1))"
This prints your batch's phone keys with their full current entries. These keys are your ENTIRE job — do not touch any other phone.

STEP 2 — For each DISTINCT base model in your batch (storage variants of the same model share one lookup), research TODAY'S (current, latest 2026) India market using your web search / web fetch tools. Look up, in priority order:
  (a) Cashify "sell old mobile" / exchange value = what Cashify actually PAYS the seller. URL pattern: https://cashify.in/sell-old-mobile-phone/<brand>/<model-slug>  (fallback: web_search "Cashify <model> <storage> sell price latest").
  (b) Cashify refurbished RETAIL price (cashify.in/buy-refurbished...) OR current used price on OLX/Amazon Renewed — used as resale-retail anchor.
  (c) Current NEW price on Amazon.in / Flipkart (for in-production models) — this is the hard CEILING; a used phone's resale can NEVER exceed new net price.
Use 1-3 searches per base model. If after a quick attempt you find NO credible India price for that specific model+era, immediately mark it no_live_data (do NOT grind, do NOT guess — long-tail/old/budget phones often have no data and that is expected).

STEP 3 — For EACH variant key, decide the update. CRITICAL: update the SAME anchor field the entry already uses (check which field is present in the current entry, in this priority):
  1. rt_buyback_a1_override present  -> DO NOT CHANGE IT. This is Shane's hand-set counter rate (source of truth). Set anchor_field='rt_buyback_a1_override', new_value = the SAME current value (unchanged), old_value = current value. If your live research gives an A1 that diverges >10% from the override, populate override_review = {current, live_suggestion, pct_diff, note} so Shane can review. Status='live' if you got data, else 'no_live_data'.
  2. else cashify_exchange present -> new_value = today's Cashify EXCHANGE (what Cashify pays) for that variant. anchor_field='cashify_exchange'.
  3. else resale_target_a1 present -> new_value = today's realistic A1 (mint, w/ box) RESALE price you'd list at (≈ Cashify refurb retail × 0.95, or OLX recent). anchor_field='resale_target_a1'.
  4. else refurb_retail_anchor_excellent present -> new_value = today's refurbished-retail (excellent) price. anchor_field='refurb_retail_anchor_excellent'.
  5. else net_new_inr/formula or none -> if model is in production, new_value = today's NEW net price -> anchor_field='net_new_inr'; else anchor_field='none', status='no_live_data'.

For storage variants, scale from the base lookup by the normal storage premium (≈ +₹2-4k per tier for budget, +₹5-8k for flagships; iPhone 128->256 ≈ +₹4-6k). Keep variant ordering sane (256 > 128).

SANITY (mandatory): proposed resale/anchor must be BELOW the current NEW price ceiling. If a model is discontinued, the ceiling is its refurb retail. If your number violates this, lower it. Also keep newer/higher-tier phones priced above older ones — no inversions.

HONESTY RULES:
- Only status='live' when a real, credible India source returned a number for THAT model. Otherwise 'no_live_data' with new_value=null.
- NEVER fabricate a price from memory. No data = no_live_data.
- old_value = the current value of that anchor field in the entry (or null if field absent).
- new_a1_estimate = your best estimate of the resulting A1 mint buyback (optional, for sanity), new_price_ceiling = the new/refurb ceiling you found (optional).
- source = short note naming where the number came from (e.g. "Cashify exchange iPhone 13 128 ₹14,500, 2026-08-05"). One source line per model is fine.

STEP 4 — Write your result to a file AND return it. Write valid JSON to: ${DIR}/_updates/batch_${i}.json  (use your file-write tool). The JSON must match this shape exactly:
  {"batch_index": ${i}, "updates": [ {"key":..., "status":..., "anchor_field":..., "new_value":..., "old_value":..., "new_a1_estimate":..., "new_price_ceiling":..., "source":..., "confidence":"high|medium|low", "override_review": null}, ... ] }
Include EVERY key from your batch exactly once. Then return the same JSON object as your final answer.`
}

phase('Live Refresh')
log(`Refreshing ${N} batches (449 hot flagship/premium models) with today's live India market rates...`)

const results = await parallel(
  Array.from({ length: N }, (_, i) => () =>
    agent(promptFor(i), {
      label: `batch:${i}`,
      phase: 'Live Refresh',
      schema: UPDATE_SCHEMA,
      model: 'sonnet',
      agentType: 'general-purpose',
    })
  )
)

const ok = results.filter(Boolean)
const totalUpdates = ok.reduce((s, r) => s + (r.updates ? r.updates.length : 0), 0)
const liveCount = ok.reduce((s, r) => s + (r.updates || []).filter(u => u.status === 'live').length, 0)
log(`Done: ${ok.length}/${N} batches returned, ${totalUpdates} phone updates, ${liveCount} live, ${totalUpdates - liveCount} no-live-data.`)

return { batches_returned: ok.length, total: N, total_updates: totalUpdates, live: liveCount, no_live: totalUpdates - liveCount }
