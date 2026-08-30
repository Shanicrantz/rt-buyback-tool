export const meta = {
  name: 'rt-buyback-verify-outliers-2026-08-30',
  description: 'Independently re-verify the weekly refresh outliers: capped rises, big drops, existence claims, missing resale',
  phases: [
    { title: 'Verify', detail: 'fresh independent research per item, blind to the weekly figure' },
    { title: 'Refute', detail: 'adversarial second lens — try to break the verifier' },
  ],
}
const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
const N = 6

const BRAIN = `RT (Rajdhani Telecom, Moradabad) buys used phones to re-sell locally. Two numbers matter:
- RESALE = what a LOCAL Indian shop actually re-sells a mint (A1, with box) used unit for TODAY. NOT an OLX asking price (asking runs ~10% above sold). NOT Cashify's "buy refurbished" retail for an older phone (that carries warranty + brand premium and sits ABOVE local resale).
- BUYBACK_MARKET = what a seller is actually PAID today by Cashify/other buyers. It must sit WELL BELOW resale (typically 55-80% of it) or one of the two numbers is wrong.
KNOWN TRAP: Cashify price pages show an "Approx. Buyback Value" widget that is a hard-coded 40% of the listed price — it is a template, NOT a quote. Never report it as buyback_market; say null instead.
CONSERVATIVE IS THE SAFE ERROR: overpaying loses money on every unit RT buys; underpaying only loses one deal.`

const VERIFY_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    batch_index: { type: 'integer' },
    items: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        exists_in_india: { type: 'string', enum: ['yes', 'no', 'unverified'] },
        existence_evidence: { type: 'string' },
        official_new_inr: { type: ['number', 'null'] },
        resale_inr: { type: ['number', 'null'] },
        resale_method: { type: 'string' },
        buyback_inr: { type: ['number', 'null'] },
        buyback_source: { type: 'string' },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      },
      required: ['key', 'exists_in_india', 'existence_evidence', 'official_new_inr', 'resale_inr', 'resale_method', 'buyback_inr', 'confidence'],
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
        exists_final: { type: 'string', enum: ['yes', 'no', 'unverified'] },
        resale_final: { type: ['number', 'null'] },
        new_final: { type: ['number', 'null'] },
        buyback_final: { type: ['number', 'null'] },
        verdict: { type: 'string', enum: ['grant', 'refuse', 'lower', 'remove', 'hold'] },
        triangulated: { type: 'boolean' },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
        note: { type: 'string' },
      },
      required: ['key', 'exists_final', 'resale_final', 'new_final', 'buyback_final', 'verdict', 'triangulated', 'confidence', 'note'],
    } },
  },
  required: ['batch_index', 'items'],
}

function verifyPrompt(i) {
  return `You are re-verifying outliers from Rajdhani Telecom's weekly buyback refresh. TODAY is 2026-08-30.

${BRAIN}

Your batch:
  python3 -c "import json;print(json.dumps(json.load(open('${DIR}/_pending/batches.json'))[${i}],indent=1,ensure_ascii=False))"

Each item has a "kind":
- kind=rise  : this week's research wants to RAISE what RT pays by a lot (pct_wanted). Research is systematically biased UPWARD on this DB (it anchors on OLX asking prices and Cashify refurb retail). Your job is to find the DEFENSIBLE resale number from scratch — do NOT start from research_resale or cur_a1, find it yourself and only then compare.
- kind=drop  : this week's research says the value COLLAPSED. Confirm the collapse is real and not a bad datapoint. A stale, too-high old anchor is a common and legitimate cause.
- kind=existence : a critic claimed this exact model+storage does not sell in India. Settle it with HARD evidence — the brand's own India store/spec page or the India launch coverage listing the real variant line-up. "Cashify has no page" or "few OLX listings" is NOT evidence of non-existence.
- kind=missing : no resale figure came back at all. Find one.
- kind=roundprice : this entry was just gap-added with a suspiciously ROUND official new price (real India prices end in 999/990) — the known fabricated-estimate signature on this DB. Re-source the brand's real India price and a realistic resale from scratch; treat the stored numbers as unresearched.

For EVERY item report: exists_in_india (+ evidence with the URL/source you actually read), official_new_inr (brand's own India price; null if unknown), resale_inr (your independent mint-used resale, with resale_method naming the datapoints you triangulated), buyback_inr (a REAL quoted buyback, else null — never the 40% widget), confidence.
Storage/RAM matters: price the EXACT variant in the key, and say so if you could only find a different variant's price.

Write ${DIR}/_pending/verify_${i}.json AND return that JSON: {"batch_index":${i},"items":[...]}. Every key exactly once.`
}

function refutePrompt(i, v) {
  return `You are an adversarial REFUTER for Rajdhani Telecom. TODAY is 2026-08-30. A verifier just researched these items; assume they are wrong until their numbers survive your checks.

${BRAIN}

Batch context (the DB's current value + what this week's research wanted):
  python3 -c "import json;print(json.dumps(json.load(open('${DIR}/_pending/batches.json'))[${i}],indent=1,ensure_ascii=False))"

Verifier output:
${JSON.stringify(v)}

For EACH item, attack the weakest link and then settle it:
1. EXISTENCE: if the verifier says a variant does not exist, demand the line-up evidence. Deleting a REAL variant costs RT a counter-quote every time a customer walks in with it, so 'no' requires the brand's own India line-up naming the real configs. Absence of a Cashify/OLX page is never enough -> 'unverified'.
2. RESALE PROVENANCE: was resale_inr triangulated from real datapoints, or back-solved from a buyback figure / copied off Cashify refurb retail / taken from an OLX asking price? Set triangulated=false and pull the number DOWN when the provenance is weak. A resale that would let RT pay more than the phone re-sells for is the one unrecoverable error.
3. VARIANT MATCH: is the price for the exact RAM/storage in the key, or a cheaper/costlier trim silently substituted?
4. NEW PRICE: is official_new_inr really the brand's India price? Retailer/Cashify-quoted "new" prices on this DB have been caught running BELOW Apple's real price. RT never pays above new x 0.85.
5. BUYBACK: real quote, or the 40%-of-listed-price widget / a round fraction of resale? If it is not a real quote, set buyback_final null.

Then set verdict:
- 'grant'  : the rise is justified — resale is triangulated at medium/high confidence and clears the +8% weekly cap honestly.
- 'refuse' : the rise is not supported; RT keeps its current price.
- 'lower'  : the correct number is BELOW what is live today (applies to rises and drops alike) — resale_final drives it down.
- 'remove' : hard evidence the variant does not exist in India.
- 'hold'   : genuinely unresolved; leave the DB untouched.
resale_final / new_final / buyback_final = the numbers you would stake money on (null if unknown).

Write ${DIR}/_pending/verified_${i}.json AND return: {"batch_index":${i},"items":[...]}. Every key exactly once.`
}

phase('Verify')
const results = await pipeline(
  Array.from({ length: N }, (_, i) => i),
  (i) => agent(verifyPrompt(i), { label: `verify:${i}`, phase: 'Verify', schema: VERIFY_SCHEMA, model: 'opus', agentType: 'general-purpose' }),
  (v, i) => agent(refutePrompt(i, v), { label: `refute:${i}`, phase: 'Refute', schema: REFUTE_SCHEMA, model: 'opus', agentType: 'general-purpose' }),
)
const ok = results.filter(Boolean)
const counts = {}
let n = 0
for (const r of ok) for (const it of (r.items || [])) { n++; counts[it.verdict] = (counts[it.verdict] || 0) + 1 }
log(`Refute done: ${ok.length}/${N} batches, ${n} items, verdicts ${JSON.stringify(counts)}`)
return { batches: ok.length, total: N, items: n, verdicts: counts }
