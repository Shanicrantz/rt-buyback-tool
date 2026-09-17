export const meta = {
  name: 'rt-buyback-sibling-repair-2026-09-16',
  description: 'Repair real configs behind removed phantoms + recheck flagged overpays — verify + adversarial refute',
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
  { id: 'oneplus_nord_5',
    brief: `ONEPLUS NORD 5 (India). A phantom 8/128 entry was just REMOVED (hand-verified: India ships 8/256 Rs29,999, 12/256 Rs32,999, 12/512 Rs35,999 per Croma launch coverage; oneplus.in lists the same three). DB now holds only oneplus_nord_5_8_256 (tier B, launch 2025-07-08, new Rs31,999, resale anchor Rs20,200 — a refuter flagged this as stale-LOW: Cashify refurb 8/256 Fair Rs25,299, OLX asks 30-35k; likely real resale ~23-25k, but verify before raising).
TASKS: (1) Confirm the India line-up. (2) Add the missing real configs: keys oneplus_nord_5_12_256 and oneplus_nord_5_12_512, display 'OnePlus Nord 5 12/256GB' / 'OnePlus Nord 5 12/512GB' — launch price, realistic local mint resale TODAY per variant (hand-read OLX, ask -10% to sold, excluding damaged/near-new/sealed), real buyback if a sell-flow quote exists. (3) Re-price oneplus_nord_5_8_256 resale with the same method.` },
  { id: 'poco_x7_pro',
    brief: `POCO X7 PRO 5G (India). A phantom 8/512 entry was just REMOVED (hand-verified: India launched 8/256 Rs27,999 and 12/256 Rs29,999 only, Flipkart-exclusive, Jan 2025). DB now holds only poco_x7_pro_5g_8_256 (tier B, launch 2025-01-09, stored new Rs27,000 — round, unresearched; resale anchor Rs19,500, calibrated 2026-06-25).
TASKS: (1) Add the missing real config poco_x7_pro_5g_12_256, display 'Poco X7 Pro 5G 12/256GB': launch price, realistic local mint resale TODAY. (2) Re-price poco_x7_pro_5g_8_256 (resale today; correct the round new price).` },
  { id: 'moto_edge_60_pro_fusion',
    brief: `MOTOROLA EDGE 60 PRO and EDGE 60 FUSION (India). Two DB entries look like phantoms, each paired with the wrong RAM for its 512GB tier:
- moto_edge_60_pro_12_512 (round new Rs43,000). India Edge 60 Pro line-up per Smartprix/launch coverage: 8/256 Rs29,999, 12/256 Rs32,999, 16/512 Rs37,999 — i.e. 512GB ships only with 16GB. DB also holds moto_edge_60_pro_12_256 (resale Rs18,500).
- moto_edge_60_fusion_8_512 (round new Rs29,000; its own source admits '512GB variant is 12/512'). Motorola India catalogue reportedly lists Edge 60 Fusion as 8+128, 8+256, 12+256 — no 512GB at all. DB also holds moto_edge_60_fusion_8_256 (stored new Rs24,000 round; resale anchor Rs18,000 from 2026-06-25).
TASKS: (1) Settle BOTH India line-ups with positive evidence (motorola.in store/catalogue, India launch coverage with prices). (2) Verdicts on moto_edge_60_pro_12_512 and moto_edge_60_fusion_8_512. (3) Add each MISSING real config with resale: keys moto_edge_60_pro_<ram>_<storage> (e.g. _8_256, _16_512) and moto_edge_60_fusion_<ram>_<storage> (e.g. _12_256, _8_128 only if it really sold in India), display 'Motorola Edge 60 Pro <ram>/<storage>GB' / 'Motorola Edge 60 Fusion <ram>/<storage>GB'. (4) Re-price the existing real keys.` },
  { id: 'civi_gt6_overpay',
    brief: `OVERPAY RECHECK — two 2024 Snapdragon 8s Gen 3 phones whose 512GB anchors a refuter flagged as too HIGH.
- xiaomi_14_civi_12_512 (India line-up 8/256 Rs42,999 + 12/512 Rs47,999, launched 2024-06-12): resale anchor Rs32,000 vs Cashify refurb Fair about Rs26k — likely overpay. Sibling xiaomi_14_civi_8_256 refurb anchor Rs22,000.
- realme_gt_6_5g_16_512 (India line-up 8/256, 12/256, 16/512; launched 2024-06-20): refurb anchor Rs30,000 vs Cashify refurb 12/256 Fair about Rs23k — likely overpay. Siblings realme_gt_6_5g_12_256 (refurb anchor 28,000), realme_gt_6_5g_8_256.
TASKS: existing_keys items for ALL FIVE keys (xiaomi_14_civi_8_256, xiaomi_14_civi_12_512, realme_gt_6_5g_8_256, realme_gt_6_5g_12_256, realme_gt_6_5g_16_512) with realistic local mint resale TODAY, official launch price, action keep. missing_configs: [].` },
  { id: 'pixel_10_pro_overpay',
    brief: `OVERPAY RECHECK — Google Pixel 10 Pro / 10 Pro XL (India). India line-up: Pixel 10 Pro single 16/256 Rs1,09,999; Pixel 10 Pro XL 256 Rs1,24,999 and 512 Rs1,39,999. A refuter found the DB resale anchors sit ABOVE Cashify's own refurbished RETAIL (which is itself an upper bound on local resale): google_pixel_10_pro_16_256 resale Rs77,000 vs Cashify refurb 16/256 Best Value Rs75,499; google_pixel_10_pro_xl_256 resale Rs79,000 vs XL refurb Rs78,599. DB also has google_pixel_10_pro_xl_512 resale Rs89,000.
TASKS: existing_keys items for google_pixel_10_pro_16_256, google_pixel_10_pro_xl_256, google_pixel_10_pro_xl_512 with realistic local mint resale TODAY (hand-read OLX, ask -10% to sold; Cashify refurb is an upper bound), official India price, action keep. missing_configs: [].` },
  { id: 'z_fold_7_ladder',
    brief: `STORAGE-LADDER RECHECK — Samsung Galaxy Z Fold 7 (India, launched 2025-07-09; India prices 12/256 Rs1,74,999, 12/512 Rs1,86,999, 16/1TB Rs2,10,999). This week the 256GB was verified DOWN to resale Rs95,000 (OLX dealer asks with bill+box Rs89,900-1,00,000 in Sept; Cashify refurb Good Rs1,24,299 is warranty-inflated). The 512GB sits at resale Rs1,10,000-1,11,200 and the 1TB at Rs1,05,000 — the 512 now prices ABOVE the 1TB, and a refuter noted 512GB OLX asks are only Rs1.05-1.10L (~Rs95-99k sold).
TASKS: existing_keys items for samsung_z_fold_7_512 and samsung_z_fold_7_1tb (and samsung_z_fold_7_256 as the base check) with realistic local mint resale TODAY per exact storage, action keep. missing_configs: [].` },
]

function verifyPrompt(s) {
  return `You are researching one phone family for Rajdhani Telecom's used-phone buyback DB. TODAY is 2026-09-16.

${BRAIN}

SUBJECT:
${s.brief}

Use web search and fetch. For every claim name the URL/source you actually read. Price the EXACT RAM/storage in each key; if you could only find a different variant's number, say so and lower your confidence. For missing configs set add=true only if existence is proven by positive evidence AND you have a researched (not back-solved) resale.

Write ${DIR}/_pending/sr_verify_${s.id}.json AND return that JSON with subject "${s.id}".`
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

Write ${DIR}/_pending/sr_final_${s.id}.json AND return that JSON with subject "${s.id}".`
}

phase('Verify')
const results = await pipeline(
  SUBJECTS,
  (s) => agent(verifyPrompt(s), { label: `verify:${s.id}`, phase: 'Verify', schema: SCHEMA, agentType: 'general-purpose' }),
  (v, s) => agent(refutePrompt(s, v), { label: `refute:${s.id}`, phase: 'Refute', schema: SCHEMA, agentType: 'general-purpose' }),
)
const ok = results.filter(Boolean)
log(`Sibling repair done: ${ok.length}/${SUBJECTS.length} subjects settled.`)
return { settled: ok.length, total: SUBJECTS.length, subjects: ok.map(r => r.subject) }
