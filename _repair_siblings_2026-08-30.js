export const meta = {
  name: 'rt-buyback-repair-siblings-2026-08-30',
  description: 'Research the REAL storage variants that the removed phantoms were standing in for',
  phases: [
    { title: 'Research', detail: 'official India price + real mint resale per real variant' },
    { title: 'Refute', detail: 'adversarial check on existence, variant match and resale provenance' },
  ],
}
const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
const N = 2

const BRAIN = `RT (Rajdhani Telecom, Moradabad) buys used phones to re-sell locally. Two numbers matter:
- RESALE = what a LOCAL Indian shop actually re-sells a mint (A1, with box) used unit for TODAY. NOT an OLX asking price (asking runs ~10% above sold). NOT Cashify's "buy refurbished" retail for an older phone (that carries warranty + brand premium and sits ABOVE local resale).
- BUYBACK_MARKET = what a seller is actually PAID today by Cashify/other buyers. It must sit WELL BELOW resale (typically 55-80% of it) or one of the two numbers is wrong.
KNOWN TRAP: Cashify price pages show an "Approx. Buyback Value" widget that is a hard-coded 40% of the listed price — a template, NOT a quote. Never report it as buyback; say null.
KNOWN TRAP: a ROUND new price (ending 000) is a fabrication signature on this DB — real India prices end in 999/990. Report the brand's actual price.
CONSERVATIVE IS THE SAFE ERROR: overpaying loses money on every unit RT buys; underpaying only loses one deal.`

const BATCHES = [
  [
    { key: 'oppo_find_x9_16_512', name: 'Oppo Find X9 16GB/512GB', known_new: 84999, note: 'Oppo India PR lists Find X9 as 12/256 Rs74,999 and 16/512 Rs84,999. Launched India 2025-11-21. DB held a phantom 12/512 which has been removed.' },
    { key: 'vivo_v50_12_512', name: 'Vivo V50 5G 12GB/512GB', known_new: 40999, note: 'vivo India line-up: 8/128 Rs34,999, 8/256 Rs36,999, 12/512 Rs40,999. India launch 2025-02-17. DB held a phantom 8/512 which has been removed.' },
    { key: 'oppo_reno_13_8_128', name: 'Oppo Reno 13 5G 8GB/128GB', known_new: 37999, note: 'Oppo India PR: Reno13 5G is 8/128 Rs37,999 and 8/256 Rs39,999 only. India launch 2025-01-11.' },
  ],
  [
    { key: 'realme_14_pro_plus_5g_12_512', name: 'Realme 14 Pro+ 5G 12GB/512GB', known_new: 37999, note: 'Realme added a 12GB+512GB India variant at Rs37,999 in Mar 2025. DB held a phantom 8/512 which has been removed.' },
    { key: 'realme_14_pro_plus_5g_8_128', name: 'Realme 14 Pro+ 5G 8GB/128GB', known_new: 29999, note: 'India launch Jan 2025: 8/128 Rs29,999, 8/256 Rs31,999, 12/256 Rs34,999.' },
    { key: 'realme_14_pro_plus_5g_12_256', name: 'Realme 14 Pro+ 5G 12GB/256GB', known_new: 34999, note: 'India launch Jan 2025 variant at Rs34,999.' },
  ],
]

const SCHEMA = (extra) => ({
  type: 'object', additionalProperties: false,
  properties: {
    batch_index: { type: 'integer' },
    items: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        exists_in_india: { type: 'string', enum: ['yes', 'no', 'unverified'] },
        evidence: { type: 'string' },
        official_new_inr: { type: ['number', 'null'] },
        launch_date: { type: ['string', 'null'] },
        resale_inr: { type: ['number', 'null'] },
        resale_method: { type: 'string' },
        buyback_inr: { type: ['number', 'null'] },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
        ...extra,
      },
      required: ['key', 'exists_in_india', 'evidence', 'official_new_inr', 'resale_inr', 'resale_method', 'buyback_inr', 'confidence'],
    } },
  },
  required: ['batch_index', 'items'],
})

const RESEARCH_SCHEMA = SCHEMA({})
const REFUTE_SCHEMA = SCHEMA({
  verdict: { type: 'string', enum: ['add', 'skip'] },
  triangulated: { type: 'boolean' },
  note: { type: 'string' },
})

function researchPrompt(i) {
  return `You research the REAL Indian second-hand market for Rajdhani Telecom. TODAY is 2026-08-30.

${BRAIN}

RT's DB just had several PHANTOM storage variants removed (configs that were never sold in India, e.g. a 512GB paired with the wrong RAM tier). Each phantom was standing in for a REAL variant that is missing from the DB. Research these real variants so they can be added:

${JSON.stringify(BATCHES[i], null, 1)}

The known_new figure is what I already verified from the brand's own India source — CONFIRM it independently and correct it if I am wrong, but do not silently replace it with a retailer discount or a street price. official_new_inr must be the brand's official India launch/current price.

For EACH item find:
  1. exists_in_india + evidence: confirm this EXACT RAM/storage config really shipped in India (brand India store/press release/major India outlet naming the config). This matters — I removed the sibling for being fake, so do not let me add another fake.
  2. official_new_inr and launch_date (YYYY-MM-DD, real India date).
  3. resale_inr: realistic price a local shop re-sells a MINT used unit for TODAY, triangulated from real datapoints (OLX recent listings discounted ~8-12% for asking-vs-sold, Cashify refurb retail as an UPPER bound, 2gud/Amazon Renewed). Name your datapoints in resale_method. These are 2025 phones, so the used market is real — a figure should exist.
  4. buyback_inr: a REAL quoted buyback, else null.

Write ${DIR}/_gaps/repair_${i}.json AND return: {"batch_index":${i},"items":[...]}. Every key exactly once.`
}

function refutePrompt(i, r) {
  return `You are an adversarial REFUTER for Rajdhani Telecom. TODAY is 2026-08-30. A researcher proposes ADDING these storage variants to the buyback DB. Assume they are wrong until the numbers survive.

${BRAIN}

Context — each of these is a real variant that should replace a PHANTOM just removed from the DB:
${JSON.stringify(BATCHES[i], null, 1)}

Researcher output:
${JSON.stringify(r)}

For EACH item:
1. EXISTENCE: does this EXACT RAM+storage config ship in India? Demand the brand's own line-up. If you cannot confirm it, verdict 'skip' — adding a second phantom to replace the first is the worst outcome here.
2. VARIANT MATCH: is official_new_inr and resale_inr for THIS config, or silently borrowed from a cheaper/costlier trim?
3. RESALE PROVENANCE: triangulated from real datapoints, or back-solved from the new price / copied off Cashify refurb retail / an OLX asking price? Set triangulated=false and pull the number DOWN when provenance is weak. A resale that lets RT pay more than the phone re-sells for is the one unrecoverable error.
4. NEW PRICE: brand's real India price (ends 999/990), not a round fabrication and not a discounted retailer price.
5. BUYBACK: real quote, or the 40% widget / a round fraction of resale? If not real, null.

verdict 'add' only when existence is confirmed AND resale is defensible. Otherwise 'skip'.

Write ${DIR}/_gaps/repair_verified_${i}.json AND return: {"batch_index":${i},"items":[...]}. Every key exactly once.`
}

phase('Research')
const results = await pipeline(
  Array.from({ length: N }, (_, i) => i),
  (i) => agent(researchPrompt(i), { label: `research:${i}`, phase: 'Research', schema: RESEARCH_SCHEMA, model: 'opus', agentType: 'general-purpose' }),
  (r, i) => agent(refutePrompt(i, r), { label: `refute:${i}`, phase: 'Refute', schema: REFUTE_SCHEMA, model: 'opus', agentType: 'general-purpose' }),
)
const ok = results.filter(Boolean)
let n = 0, add = 0
for (const r of ok) for (const it of (r.items || [])) { n++; if (it.verdict === 'add') add++ }
log(`Refute done: ${ok.length}/${N} batches, ${n} items, ${add} approved to add.`)
return { batches: ok.length, total: N, items: n, add }
