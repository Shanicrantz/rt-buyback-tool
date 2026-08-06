export const meta = {
  name: 'rt-buyback-gap-audit-2026',
  description: 'Find missing India phone launches (esp 2026) + gaps, with brain-pricing inputs, critic-verified',
  phases: [
    { title: 'Find', detail: 'per-brand: research India lineup, diff vs DB, propose missing with prices' },
    { title: 'Critic', detail: 'verify each proposal is a real India launch with sane prices' },
  ],
}
const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
const N = 8

const FIND_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    unit_id: { type: 'string' },
    missing: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        display_name: { type: 'string' },
        tier: { type: 'string', enum: ['S','A','B','C','D'] },
        launch_date: { type: 'string' },
        discontinued: { type: 'boolean' },
        new_price: { type: ['number','null'] },
        resale_price: { type: ['number','null'] },
        buyback_market: { type: ['number','null'] },
        confidence: { type: 'string', enum: ['high','medium','low'] },
        source: { type: 'string' },
      },
      required: ['key','display_name','tier','launch_date','discontinued','new_price','resale_price','buyback_market','confidence'],
    } },
  },
  required: ['unit_id','missing'],
}
const CRITIC_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    unit_id: { type: 'string' },
    verified: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        real_india_launch: { type: 'boolean' },
        new_price_final: { type: ['number','null'] },
        resale_price_final: { type: ['number','null'] },
        buyback_market_final: { type: ['number','null'] },
        verdict: { type: 'string', enum: ['confirmed','corrected','rejected'] },
        note: { type: 'string' },
      },
      required: ['key','real_india_launch','new_price_final','resale_price_final','verdict'],
    } },
  },
  required: ['unit_id','verified'],
}

function findPrompt(i) {
  return `You audit Rajdhani Telecom's used-phone DB for MISSING models. TODAY is 2026-08-07. Find India phones that SHOULD be in the DB but are MISSING — focus on 2025-2026 launches, ESPECIALLY the last few months (May-Aug 2026), plus any notable gap.

Get your unit scope + what's already in the DB:
  python3 -c "import json; u=json.load(open('${DIR}/_audit_units.json'))[${i}]; inv=json.load(open('${DIR}/_db_inventory.json')); print('SCOPE:',u[2]); [print('---',b,'MODELS:',inv.get(b,{}).get('models')) for b in u[1]]"

Web-research the COMPLETE India lineup for your scope for 2025-2026 (GSMArena/91mobiles/Smartprix/official brand sites), emphasis on recent 2026 launches. Diff against the MODELS already listed. A model is MISSING only if not already present (account for name variants).

For each MISSING model, output one entry per REAL India storage/RAM variant with PRICING for RT's brain:
  - key: match existing key-naming for that brand (lowercase, e.g. samsung_s26_ultra_256, oppo_reno16_8_256, iphone_17_pro_256). NO phantom variants — verify real India storage configs.
  - tier: S=Apple/Samsung S·Z flagship/Pixel Pro; A=OnePlus flagship/premium/Samsung A7x; B=Xiaomi/Vivo X/Oppo Reno/Nord/Nothing/Moto Edge·Razr; C=Vivo Y·T/Oppo A·F/Realme C·Narzo/Redmi Note/Poco/Samsung A0x-A3x·M·F; D=Infinix/Tecno/Lava/itel/Micromax entry.
  - new_price = official current India NEW price (₹). resale_price = realistic used mint resale TODAY (for a brand-new <3-month phone with thin used market, use ≈ new × 0.80; older = real used value below new). buyback_market = what Cashify pays if a used market exists, else null.
  - launch_date YYYY-MM-DD (real India date), discontinued (usually false for new).
  - HONESTY: only add models you CONFIRM launched in India. Unsure -> skip. resale_price < new_price always.

Write ${DIR}/_gaps/find_${i}.json AND return: {"unit_id":"<name>","missing":[{...}]}. If none missing, missing:[].`
}
function criticPrompt(i, findJson) {
  return `Adversarial CRITIC for Rajdhani Telecom gap-audit. TODAY is 2026-08-07. A finder proposed missing India models with prices; independently VERIFY each.
Finder output:
${JSON.stringify(findJson)}

For EACH proposed model, web-check:
1. real_india_launch: Did this EXACT model actually launch/sell in India? Reject fakes, rumors, non-India variants, phantom storage configs.
2. new_price_final: correct official India new price (not MRP-inflated, not wrong variant). resale_price_final: realistic used resale (< new; for brand-new ≈ new×0.78-0.82). buyback_market_final: real Cashify buyback or null.
3. Sanity: resale < new; buyback < resale (if present); storage ordering (256>128).
Set *_final to correct values (corrected if finder wrong, confirmed if right, rejected+real_india_launch=false if fake/unverifiable).

Write ${DIR}/_gaps/verified_${i}.json AND return: {"unit_id":"<name>","verified":[{...}]}. Every proposed key exactly once.`
}

phase('Find')
const results = await pipeline(
  Array.from({ length: N }, (_, i) => i),
  (i) => agent(findPrompt(i), { label: `find:${i}`, phase: 'Find', schema: FIND_SCHEMA, model: 'sonnet', agentType: 'general-purpose' }),
  (findRes, i) => agent(criticPrompt(i, findRes), { label: `critic:${i}`, phase: 'Critic', schema: CRITIC_SCHEMA, model: 'sonnet', agentType: 'general-purpose' }),
)
const ok = results.filter(Boolean)
let proposed = 0, real = 0
for (const r of ok) for (const v of (r.verified || [])) { proposed++; if (v.real_india_launch && v.verdict !== 'rejected') real++ }
log(`Critic done: ${ok.length}/${N} units, ${proposed} proposed, ${real} verified real.`)
return { units: ok.length, total: N, proposed, real }
