export const meta = {
  name: 'rt-buyback-carryforward-2026-09-16',
  description: 'Settle real India line-ups (Vivo T3x gap, suspected phantoms) and price the real configs — verify + adversarial refute',
  phases: [
    { title: 'Verify', detail: 'independent India line-up + resale research per family' },
    { title: 'Refute', detail: 'adversarial second lens — try to break the verifier' },
  ],
}
const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'

const BRAIN = `RT (Rajdhani Telecom, Moradabad) buys used phones to re-sell locally. Two numbers matter:
- RESALE = what a LOCAL Indian shop actually re-sells a mint (A1, with box) used unit for TODAY. NOT an OLX asking price (asking runs ~10% above sold). NOT Cashify's "buy refurbished" retail for an older phone (that carries warranty + brand premium and sits ABOVE local resale).
- BUYBACK_MARKET = what a seller is actually PAID today by Cashify/other buyers, from a real sell-old-phone quote flow. It must sit WELL BELOW resale (typically 55-80% of it) or one of the two numbers is wrong.
KNOWN TRAPS: (1) Cashify price pages show an "Approx. Buyback Value" widget that is a hard-coded 40% of the listed price — a template, NOT a quote. (2) Cashify "Get Upto Rs X" headlines are ceilings, not quotes. (3) Cashify price pages carry WRONG new prices. (4) Real India launch prices end in 999/990 — a round-thousand new price is an unresearched estimate.
PHANTOM VARIANTS are this DB's #1 historical bug: a past audit invents a storage tier that was never sold in India, usually a big storage tier paired with the WRONG RAM. But deleting a REAL variant costs RT a counter-quote on every walk-in, so existence is settled only by POSITIVE evidence: the brand's own India store/spec page, or India launch coverage listing every variant with its price. "Cashify has no page" / "few OLX listings" / "the brand store no longer lists it" (discontinued phones drop off stores) are NOT evidence of non-existence.
CONSERVATIVE IS THE SAFE ERROR: overpaying loses money on every unit RT buys; underpaying only loses one deal.`

const SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    subject: { type: 'string' },
    india_lineup: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        ram_gb: { type: 'integer' }, storage_gb: { type: 'integer' },
        launch_price_inr: { type: ['number', 'null'] },
        source: { type: 'string' },
      },
      required: ['ram_gb', 'storage_gb', 'launch_price_inr', 'source'],
    } },
    existing_keys: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        exists_in_india: { type: 'string', enum: ['yes', 'no', 'unverified'] },
        evidence: { type: 'string' },
        action: { type: 'string', enum: ['keep', 'remove', 'hold'] },
        official_new_inr: { type: ['number', 'null'] },
        resale_inr: { type: ['number', 'null'] },
        resale_method: { type: 'string' },
        buyback_inr: { type: ['number', 'null'] },
        triangulated: { type: 'boolean' },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      },
      required: ['key', 'exists_in_india', 'evidence', 'action', 'official_new_inr', 'resale_inr', 'resale_method', 'buyback_inr', 'triangulated', 'confidence'],
    } },
    missing_configs: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        display_name: { type: 'string' },
        india_launch_date: { type: 'string' },
        official_new_inr: { type: ['number', 'null'] },
        resale_inr: { type: ['number', 'null'] },
        resale_method: { type: 'string' },
        buyback_inr: { type: ['number', 'null'] },
        add: { type: 'boolean' },
        triangulated: { type: 'boolean' },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
        note: { type: 'string' },
      },
      required: ['key', 'display_name', 'india_launch_date', 'official_new_inr', 'resale_inr', 'resale_method', 'buyback_inr', 'add', 'triangulated', 'confidence', 'note'],
    } },
    note: { type: 'string' },
  },
  required: ['subject', 'india_lineup', 'existing_keys', 'missing_configs', 'note'],
}

const SUBJECTS = [
  { id: 'vivo_t3x',
    brief: `VIVO T3x 5G (India). The shop owner (Shane) reports the DB is MISSING the 6GB/128GB and 8GB/128GB variants — customers walk in with them. DB currently holds: vivo_t3x_5g_4_128 (stored new Rs14,000 — round, unresearched; resale anchor Rs10,500) and vivo_t3x_5g_4_256 (stored new Rs16,000 — round; resale anchor Rs12,000), both tier C, launch 2024-04-22.
TASKS: (1) Establish the complete India RAM/storage line-up with launch prices. (2) Confirm 6/128 and 8/128 and price them: official India launch price, realistic local mint resale TODAY, real Cashify sell quote if one exists. Keys: vivo_t3x_5g_6_128 / vivo_t3x_5g_8_128, display names 'Vivo T3x 5G 6/128GB' / 'Vivo T3x 5G 8/128GB'. (3) Is 4GB/256GB a real India config? The smallest RAM paired with the biggest storage is the classic phantom tell — but settle it with positive evidence either way. (4) Re-price the existing real keys (resale today).` },
  { id: 'razr_60_ultra',
    brief: `MOTOROLA RAZR 60 ULTRA (India). DB holds ONE entry: moto_razr_60_ultra_12_512 (resale anchor Rs54,000, buyback Rs45,700, tier S, launch 2025-04-29). Last week's hand check claimed India launched a SINGLE 16GB/512GB trim at Rs99,999 (Business Standard 2025-05-13; Flipkart listing '512 GB Storage, 16 GB RAM') — which would make 12/512 a phantom and 16/512 the real MISSING config.
TASKS: (1) Settle the India line-up with positive evidence. (2) If 16/512 is real, price it: key moto_razr_60_ultra_16_512, display 'Motorola Razr 60 Ultra 16/512GB', India launch date, official price, realistic local mint resale TODAY, real buyback quote. (3) Verdict on the 12/512 key.` },
  { id: 'note_14_pro_plus',
    brief: `REDMI NOTE 14 PRO+ 5G (India). DB holds ONE entry: redmi_note_14_pro_plus_5g_8_256 (stored new Rs29,000 — round, unresearched; resale anchor Rs21,500; tier B; launch 2024-12-09). An 8/512 entry was removed last week as a phantom (512GB pairs only with 12GB). Last week's note ALSO claimed the India line-up is only 8/128 (Rs30,999) and 12/512 (Rs35,999), making 8/256 a phantom too — BUT the entry's own older source cites an official 256GB new price of Rs31,999, so that note may have MISSED a middle variant. Treat BOTH claims as unproven.
TASKS: (1) Settle the COMPLETE India line-up with every variant and its launch price, from positive evidence (Xiaomi India store / India launch coverage listing all variants). (2) Verdict on the 8/256 key. (3) Price every real config that is missing: keys redmi_note_14_pro_plus_5g_<ram>_<storage> (e.g. _8_128, _12_512), display 'Redmi Note 14 Pro+ 5G <ram>/<storage>GB'. (4) Resale today for each real config.` },
  { id: 'pixel_9_pro_family',
    brief: `GOOGLE PIXEL 9 PRO / 9 PRO XL (India). DB holds: google_pixel_9_pro_128 (resale Rs51,000, buyback Rs43,000), google_pixel_9_pro_256 (resale Rs58,000, stored new Rs1,05,000 — round), google_pixel_9_pro_xl_16_256 (resale anchor Rs64,900), google_pixel_9_pro_xl_16_512 and google_pixel_9_pro_xl_16_1tb (both with NO price data at all). A 9 Pro 512GB entry was removed last week after a hand check found India received the 9 Pro in a SINGLE 256GB trim at Rs1,09,999 (128/512/1TB international-only).
TASKS: (1) Settle which Pixel 9 Pro and 9 Pro XL configs Google actually sold IN INDIA (Google Store India at launch / India launch coverage with prices). (2) Verdict on google_pixel_9_pro_128, google_pixel_9_pro_xl_16_512, google_pixel_9_pro_xl_16_1tb. (3) Realistic local mint resale TODAY + real buyback for each real config (9 Pro 256, 9 Pro XL 256, any other real one), plus the official India launch price.` },
  { id: 'ipad_pro_m4_13_256',
    brief: `iPAD PRO M4 13-inch 256GB Wi-Fi (India) — OBSERVATION ONLY, no line-up question. Shane hand-set RT's buyback at Rs67,100 on 2026-09-10 = resale Rs73,000 x 0.92 (the hard cap). It must be reviewed if real resale has fallen below Rs72,935. The M4 is discontinued (replaced by M5); India launch price was Rs1,29,900.
TASKS: report ONE existing_keys item for key ipad_pro_m4_13_256_wifi with action 'keep', exists 'yes', and your independent realistic local mint resale TODAY for exactly the 13-inch 256GB Wi-Fi M4 (not the 11-inch, not cellular, not M5), with a real buyback quote if one exists. missing_configs: [].` },
]

function verifyPrompt(s) {
  return `You are researching one phone family for Rajdhani Telecom's used-phone buyback DB. TODAY is 2026-09-16.

${BRAIN}

SUBJECT:
${s.brief}

Use web search and fetch. For every claim name the URL/source you actually read. Price the EXACT RAM/storage in each key; if you could only find a different variant's number, say so and lower your confidence. For missing configs set add=true only if existence is proven by positive evidence AND you have a researched (not back-solved) resale.

Write ${DIR}/_pending/cf_verify_${s.id}.json AND return that JSON with subject "${s.id}".`
}

function refutePrompt(s, v) {
  return `You are an adversarial REFUTER for Rajdhani Telecom. TODAY is 2026-09-16. A verifier just researched this phone family; assume they are wrong until their claims survive your own independent checks.

${BRAIN}

SUBJECT:
${s.brief}

Verifier output:
${JSON.stringify(v)}

Attack the weakest links, re-checking with your own searches:
1. LINE-UP: is every config backed by POSITIVE India evidence (brand India store / launch coverage listing variants + prices)? A 'no' for an existing key needs that evidence naming the real configs — otherwise 'unverified' with action 'hold'. A config missed by the verifier is as bad as a phantom it invented.
2. RESALE PROVENANCE: triangulated from real datapoints, or back-solved from new price / copied off Cashify refurb retail / an OLX asking price? Set triangulated=false and pull DOWN when weak. Resale must never let RT pay more than the phone re-sells for.
3. VARIANT MATCH: is each price for the exact RAM/storage, or a neighbouring trim?
4. NEW PRICE: the brand's real India launch price (ends 999/990), not a discounted or Cashify-page figure?
5. BUYBACK: a real sell-flow quote, or the 40% widget / a "Get Upto" headline / a round fraction of resale? If not real, null.
Return the FINAL corrected record — the numbers and verdicts you would stake money on.

Write ${DIR}/_pending/cf_final_${s.id}.json AND return that JSON with subject "${s.id}".`
}

phase('Verify')
const results = await pipeline(
  SUBJECTS,
  (s) => agent(verifyPrompt(s), { label: `verify:${s.id}`, phase: 'Verify', schema: SCHEMA, agentType: 'general-purpose' }),
  (v, s) => agent(refutePrompt(s, v), { label: `refute:${s.id}`, phase: 'Refute', schema: SCHEMA, agentType: 'general-purpose' }),
)
const ok = results.filter(Boolean)
log(`Carry-forward done: ${ok.length}/${SUBJECTS.length} subjects settled.`)
return { settled: ok.length, total: SUBJECTS.length, subjects: ok.map(r => r.subject) }
