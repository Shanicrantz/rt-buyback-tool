export const meta = {
  name: 'rt-buyback-market-reprice',
  description: 'Research REAL resale price + buyback-market rate per model (audit + critic), for Shane-style buyback calc',
  phases: [
    { title: 'Market Research', detail: 'fetch real resale price + what buyers pay, per model' },
    { title: 'Critic', detail: 'adversarially verify both prices are real local-market numbers' },
  ],
}

const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
const N = 15

const BRAIN = `RT (Rajdhani Telecom, Moradabad) BUYBACK BRAIN — how Shane actually prices:
- RESALE price = what RT can ACTUALLY re-sell a mint (A1) used unit for in the LOCAL Indian second-hand market. This is NOT Cashify's "buy refurbished" retail price for older phones — Cashify's refurb price includes their warranty + brand premium and is INFLATED vs what a local shop gets. Real resale for older/less-popular phones is BELOW Cashify refurb retail. For current hot phones (in demand) real resale is close to Cashify refurb retail. Triangulate from OLX recent SOLD (not asking) + local used-market + Cashify refurb (as an upper bound).
- BUYBACK-MARKET rate = what buyers (Cashify exchange/sell-old value, other buyback services, local competitors) currently PAY the seller for that phone. RT must pay slightly ABOVE this to win the walk-in.
- RT then buys at resale/(1+margin) (~15-18% margin), and always at/above the buyback-market rate to stay competitive.`

const FETCH_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    batch_index: { type: 'integer' },
    models: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        display_name: { type: 'string' },
        resale_price: { type: ['number', 'null'] },
        resale_low: { type: ['number', 'null'] },
        resale_high: { type: ['number', 'null'] },
        resale_sources: { type: 'string' },
        buyback_market: { type: ['number', 'null'] },
        buyback_source: { type: 'string' },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      },
      required: ['key', 'resale_price', 'buyback_market', 'resale_sources', 'buyback_source', 'confidence'],
    } },
  },
  required: ['batch_index', 'models'],
}

const CRITIC_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    batch_index: { type: 'integer' },
    models: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        resale_final: { type: ['number', 'null'] },
        buyback_final: { type: ['number', 'null'] },
        resale_verdict: { type: 'string', enum: ['confirmed', 'corrected', 'rejected'] },
        buyback_verdict: { type: 'string', enum: ['confirmed', 'corrected', 'rejected'] },
        note: { type: 'string' },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      },
      required: ['key', 'resale_final', 'buyback_final', 'resale_verdict', 'buyback_verdict', 'confidence'],
    } },
  },
  required: ['batch_index', 'models'],
}

function fetchPrompt(i) {
  return `You research the REAL Indian second-hand market for Rajdhani Telecom. TODAY is 2026-08-05.

${BRAIN}

Get your batch's phone keys + names:
  python3 -c "import json; d=json.load(open('${DIR}/phone_db.json')); ks=json.load(open('${DIR}/_ov_batches.json'))[${i}]; print({k:d[k]['display_name'] for k in ks})"

For EACH distinct model (storage variants share one lookup, then scale), find TWO numbers via web search/fetch:
  1) RESALE_PRICE = realistic price a LOCAL shop can re-sell a mint (excellent, with-box) used unit for TODAY in India.
     Triangulate: OLX recent listings (discount asking by ~8-12% for real sold), Cashify "buy refurbished" retail (UPPER bound — real local resale is 5-20% below this for older phones), 2gud/Amazon Renewed. Give resale_low, resale_high, and resale_price = your best single realistic figure.
  2) BUYBACK_MARKET = what sellers are actually PAID today: Cashify "sell old phone" / exchange value is the primary benchmark (web_search "Cashify <model> <storage> sell price" or fetch cashify.in/sell-old-mobile-phone/...). Note if other buyers differ.
Scale storage variants (256 > 128). Only report numbers you actually find; null if none.

Write ${DIR}/_ov_updates/fetch_${i}.json AND return:
{"batch_index":${i},"models":[{"key":...,"display_name":...,"resale_price":<num|null>,"resale_low":<num|null>,"resale_high":<num|null>,"resale_sources":"<olx/cashify/... + numbers>","buyback_market":<num|null>,"buyback_source":"<cashify sell + number>","confidence":"high|medium|low"}, ...]}
Every key exactly once.`
}

function criticPrompt(i, fetchJson) {
  return `You are an adversarial MARKET-PRICE CRITIC for Rajdhani Telecom. TODAY is 2026-08-05. Assume the fetcher may have erred — catch it.

${BRAIN}

Fetcher output:
${JSON.stringify(fetchJson)}

For EACH model, independently sanity-check and CORRECT:
1. RESALE_FINAL: Is resale_price a REALISTIC local re-sale price (what a Moradabad shop actually gets), NOT (a) an OLX ASKING price (inflated ~10%), NOR (b) Cashify's warranty-inflated refurb-retail for an OLDER phone. For older/unpopular models pull it DOWN toward real used value. For current hot models it can sit near refurb retail.
2. BUYBACK_FINAL: Is it a real current Cashify/market buyback (what sellers get paid)?
3. Hard sanity: RESALE_FINAL > BUYBACK_FINAL (a reseller must buy below resale). If violated, fix. Typical gap: buyback ≈ 55-80% of resale.
Set *_final to the correct value (yours if fetcher wrong -> 'corrected', theirs if right -> 'confirmed', null -> 'rejected').

Write ${DIR}/_ov_updates/verified_${i}.json AND return:
{"batch_index":${i},"models":[{"key":...,"resale_final":<num|null>,"buyback_final":<num|null>,"resale_verdict":"confirmed|corrected|rejected","buyback_verdict":"...","note":"<what & why + source>","confidence":"high|medium|low"}, ...]}
Every key exactly once.`
}

phase('Market Research')
const results = await pipeline(
  Array.from({ length: N }, (_, i) => i),
  (i) => agent(fetchPrompt(i), { label: `fetch:${i}`, phase: 'Market Research', schema: FETCH_SCHEMA, model: 'sonnet', agentType: 'general-purpose' }),
  (fetchRes, i) => agent(criticPrompt(i, fetchRes), { label: `critic:${i}`, phase: 'Critic', schema: CRITIC_SCHEMA, model: 'sonnet', agentType: 'general-purpose' }),
)

const ok = results.filter(Boolean)
let models = 0, corrected = 0
for (const r of ok) for (const m of (r.models || [])) { models++; if (m.resale_verdict === 'corrected' || m.buyback_verdict === 'corrected') corrected++ }
log(`Critic done: ${ok.length}/${N} batches, ${models} models, ${corrected} prices corrected.`)
return { batches: ok.length, total: N, models, corrected }
