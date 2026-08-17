export const meta = {
  name: 'rt-buyback-verify-pending',
  description: 'Hand-verify the 3 items left over from the 2026-08-17 refresh: phantom variants, Z Fold8 pricing, capped rises',
  phases: [
    { title: 'Verify', detail: 'existence checks, Z Fold8 real pricing, capped-rise re-check' },
    { title: 'Critic', detail: 'adversarial second opinion on each' },
  ],
}

const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'

const BRAIN = `RT (Rajdhani Telecom, Moradabad) BUYBACK BRAIN:
- RESALE price = what RT can ACTUALLY re-sell a mint (A1) used unit for in the LOCAL India second-hand market. NOT Cashify's "buy refurbished" retail (warranty-inflated for older phones). Triangulate OLX recent SOLD (discount asking ~10%) + local used value + Cashify refurb as an UPPER bound.
- BUYBACK_MARKET = what buyers (Cashify sell/exchange, other buyback services) currently PAY a seller.
- RT buys at resale/(1+margin). Overpaying loses money; underpaying only loses a deal. When genuinely uncertain, report the LOWER figure.`

const EXIST_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    task: { type: 'string' },
    models: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        exists_in_india: { type: 'boolean' },
        evidence: { type: 'string' },
        real_variants_that_do_ship: { type: 'string' },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      },
      required: ['key', 'exists_in_india', 'evidence', 'confidence'],
    } },
  },
  required: ['task', 'models'],
}

const PRICE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    task: { type: 'string' },
    models: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        resale_price: { type: ['number', 'null'] },
        buyback_market: { type: ['number', 'null'] },
        official_new_price: { type: ['number', 'null'] },
        sources: { type: 'string' },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      },
      required: ['key', 'resale_price', 'buyback_market', 'sources', 'confidence'],
    } },
  },
  required: ['task', 'models'],
}

const PHANTOMS = [
  ['oneplus_15r_8_128', 'OnePlus 15R 8GB/128GB'],
  ['oneplus_15r_8_256', 'OnePlus 15R 8GB/256GB'],
  ['oneplus_13t_16_512', 'OnePlus 13T 16GB/512GB'],
  ['oppo_reno_15_8_512', 'Oppo Reno 15 5G 8GB/512GB'],
  ['nothing_phone_3_12_512', 'Nothing Phone (3) 12GB/512GB'],
  ['vivo_x200_fe_12_512', 'Vivo X200 FE 12GB/512GB'],
  ['moto_edge_70_pro_5g_12_512', 'Motorola Edge 70 Pro 5G 12GB/512GB'],
  ['asus_rog_phone_9_12_256', 'Asus ROG Phone 9 12GB/256GB'],
  ['samsung_z_flip_8_256', 'Samsung Galaxy Z Flip8 12GB/256GB'],
]

const FOLD8 = [
  ['samsung_z_fold_8_256', 'Samsung Galaxy Z Fold8 12GB/256GB'],
  ['samsung_z_fold_8_512', 'Samsung Galaxy Z Fold8 12GB/512GB'],
  ['samsung_z_fold_8_1tb', 'Samsung Galaxy Z Fold8 16GB/1TB'],
  ['samsung_z_fold_8_ultra_256', 'Samsung Galaxy Z Fold8 Ultra 12GB/256GB'],
  ['samsung_z_fold_8_ultra_512', 'Samsung Galaxy Z Fold8 Ultra 12GB/512GB'],
  ['samsung_z_fold_8_ultra_1tb', 'Samsung Galaxy Z Fold8 Ultra 16GB/1TB'],
]

const RISES = [
  ['iphone_17_pro_256', 'iPhone 17 Pro 256GB'],
  ['iphone_17_pro_1tb', 'iPhone 17 Pro 1TB'],
  ['iphone_17_pro_max_256', 'iPhone 17 Pro Max 256GB'],
  ['iphone_17_pro_max_512', 'iPhone 17 Pro Max 512GB'],
  ['iphone_17_pro_max_1tb', 'iPhone 17 Pro Max 1TB'],
  ['iphone_17_pro_max_2tb', 'iPhone 17 Pro Max 2TB'],
  ['vivo_v70_elite_12_256', 'Vivo V70 Elite 12GB/256GB'],
  ['vivo_v70_elite_12_512', 'Vivo V70 Elite 12GB/512GB'],
  ['ipad_pro_m5_13_256_wifi', 'iPad Pro M5 13" 256GB WiFi'],
]

const TASKS = [
  {
    id: 'existence',
    schema: EXIST_SCHEMA,
    prompt: `TODAY is 2026-08-17. You settle a factual question for Rajdhani Telecom's used-phone DB: do these exact RAM/STORAGE variants actually SHIP IN INDIA? An automated critic claimed each DOES NOT EXIST. That critic has a poor track record (last week it was wrong 5 times out of 6), so verify each one INDEPENDENTLY and do not simply agree.

Variants to check:
${PHANTOMS.map(([k, n]) => `  ${k} = ${n}`).join('\n')}

For EACH: check the brand's own India site, Flipkart/Amazon.in listings, Cashify/91mobiles/Smartprix India spec pages. Decide whether that EXACT RAM+storage combination was ever sold in India.
- exists_in_india = true if you find a real India listing/spec page for that exact combo.
- exists_in_india = false ONLY if you positively confirm India got a different set of variants (list them in real_variants_that_do_ship).
- If you genuinely cannot tell, set exists_in_india = true and confidence 'low' — we keep doubtful entries rather than delete real ones.
Quote the concrete evidence (site + what it lists) in 'evidence'.

Return {"task":"existence","models":[{"key":...,"exists_in_india":bool,"evidence":"...","real_variants_that_do_ship":"...","confidence":"high|medium|low"}]}. Every key exactly once.`,
  },
  {
    id: 'fold8',
    schema: PRICE_SCHEMA,
    prompt: `TODAY is 2026-08-17. Price the Samsung Galaxy Z Fold8 family for Rajdhani Telecom.

${BRAIN}

These entries were originally added from PRE-LAUNCH LEAKS and two weekly research runs in a row returned obviously fake numbers (resale echoed back exactly, buyback at exactly 50% of it). We need REAL numbers this time.

Models:
${FOLD8.map(([k, n]) => `  ${k} = ${n}`).join('\n')}

The Galaxy Z Fold8 family launched in India on 2026-07-22 (about 4 weeks ago), so:
1. FIRST confirm which variants Samsung India actually sells (samsung.com/in) and the OFFICIAL India launch price of each -> official_new_price. If a variant (e.g. an "Ultra" trim or a given storage) does NOT exist in India, set resale_price and buyback_market to null and say so in sources.
2. resale_price = realistic price a local shop re-sells a mint used unit for TODAY. A 4-week-old flagship has a THIN used market: real resale is typically 78-88% of official new. Check OLX/Cashify refurb for anything real.
3. buyback_market = what Cashify/others PAY today for a used one (often not yet quoted this early -> null is fine and better than a guess).

Do NOT invent numbers, do NOT set buyback to a round fraction of resale, and do NOT echo a figure back without a source. null beats a fabricated number.

Return {"task":"fold8","models":[{"key":...,"resale_price":<num|null>,"buyback_market":<num|null>,"official_new_price":<num|null>,"sources":"<sites + actual numbers seen>","confidence":"high|medium|low"}]}. Every key exactly once.`,
  },
  {
    id: 'rises',
    schema: PRICE_SCHEMA,
    prompt: `TODAY is 2026-08-17. Independent price re-check for Rajdhani Telecom.

${BRAIN}

This week's research wanted to RAISE what RT pays for these models by 14-52%. Big rises are exactly where web research goes wrong (it anchors to OLX ASKING prices, which are ~10% above real sold prices, and to Cashify's warranty-inflated refurb retail). Your job is to independently establish the TRUE numbers so we can decide whether the rise is real. Be skeptical and lean LOW.

Models:
${RISES.map(([k, n]) => `  ${k} = ${n}`).join('\n')}

For each: find (a) resale_price = what a local shop really re-sells a mint used unit for today — prefer OLX recent SOLD / actual completed listings over asking prices, and treat Cashify "buy refurbished" as an UPPER BOUND only; (b) buyback_market = what Cashify/others actually PAY a seller today (fetch cashify.in sell-old-mobile-phone pages); (c) official_new_price = current official India new price, since RT never pays above 85% of new.

Sanity rules you must enforce on your own output: resale < new. buyback < resale, typically 55-80% of it — if your two numbers sit closer than that, at least one is wrong, so re-check rather than reporting them.

Return {"task":"rises","models":[{"key":...,"resale_price":<num|null>,"buyback_market":<num|null>,"official_new_price":<num|null>,"sources":"<sites + actual numbers seen>","confidence":"high|medium|low"}]}. Every key exactly once.`,
  },
]

function criticPrompt(t, res) {
  return `You are an adversarial CRITIC for Rajdhani Telecom. TODAY is 2026-08-17. Assume the researcher below may have erred — check it independently and correct it.

${BRAIN}

Researcher output for task "${t.id}":
${JSON.stringify(res)}

${t.id === 'existence'
  ? `Re-check each variant's existence in India yourself. Overturn any claim you can disprove. Remember the asymmetry: wrongly deleting a REAL variant costs RT a quote at the counter, so anything you cannot positively disprove stays exists_in_india=true. Return the SAME schema the researcher used, with your corrected values.`
  : `Re-check each price yourself. Specifically hunt for: OLX ASKING prices passed off as sold, Cashify refurb RETAIL passed off as local resale, buyback figures sitting implausibly close to resale (>85% is never a real competitor quote), and fabricated round numbers. Correct anything wrong; set a field to null rather than keep a number you cannot source. Return the SAME schema the researcher used, with your corrected values.`}

Write ${DIR}/_pending/verified_${t.id}.json AND return the corrected object. Every key exactly once.`
}

phase('Verify')
const out = await pipeline(
  TASKS,
  (t) => agent(t.prompt, { label: `verify:${t.id}`, phase: 'Verify', schema: t.schema, model: 'sonnet', agentType: 'general-purpose' }),
  (res, t) => agent(criticPrompt(t, res), { label: `critic:${t.id}`, phase: 'Critic', schema: t.schema, model: 'sonnet', agentType: 'general-purpose' }),
)

const ok = out.filter(Boolean)
log(`Verified ${ok.length}/${TASKS.length} tasks.`)
return { tasks: ok.length, total: TASKS.length, results: ok }
