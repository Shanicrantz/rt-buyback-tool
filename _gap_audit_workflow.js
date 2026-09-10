export const meta = {
  name: 'rt-buyback-gap-audit-2026',
  description: 'Find missing India phone launches (esp 2026) + gaps, with brain-pricing inputs, critic-verified',
  phases: [
    { title: 'Find', detail: 'per-brand: research India lineup, diff vs DB, propose missing with prices' },
    { title: 'Critic', detail: 'verify each proposal is a real India launch with sane prices' },
  ],
}
const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
const N = 4

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
  return `You audit Rajdhani Telecom's used-phone DB for MISSING models. TODAY is 2026-09-10. Find India phones that SHOULD be in the DB but are MISSING. The DB was gap-audited on 2026-08-30 (prev run 2026-08-24), so the PRIMARY target is anything that launched or went on sale in India from 2026-08-28 onward (the last ~2 weeks) — new launches, new storage/RAM variants of recent phones, and India availability of models announced earlier. SECONDARY: any notable 2025-2026 model still absent. Do not re-propose models already in the DB.

Get your unit scope + what's already in the DB:
  python3 -c "import json; u=json.load(open('${DIR}/_audit_units.json'))[${i}]; inv=json.load(open('${DIR}/_db_inventory.json')); print('SCOPE:',u[2]); [print('---',b,'MODELS:',inv.get(b,{}).get('models')) for b in u[1]]"

Web-research the India lineup for your scope with heavy emphasis on LATE-AUGUST 2026 launches (GSMArena/91mobiles/Smartprix/official brand India sites; check 'launched in India August 2026' / 'launch date 2026' style queries). Diff against the MODELS already listed. A model is MISSING only if not already present (account for name variants).

For each MISSING model, output one entry per REAL India storage/RAM variant with PRICING for RT's brain:
  - key: match existing key-naming for that brand (lowercase, e.g. samsung_s26_ultra_256, oppo_reno16_8_256, iphone_17_pro_256). NO phantom variants — verify real India storage configs.
  - tier: S=Apple/Samsung S·Z flagship/Pixel Pro; A=OnePlus flagship/premium/Samsung A7x; B=Xiaomi/Vivo X/Oppo Reno/Nord/Nothing/Moto Edge·Razr; C=Vivo Y·T/Oppo A·F/Realme C·Narzo/Redmi Note/Poco/Samsung A0x-A3x·M·F; D=Infinix/Tecno/Lava/itel/Micromax entry.
  - new_price = official current India NEW price (₹). resale_price = realistic used mint resale TODAY (for a brand-new <3-month phone with thin used market, use ≈ new × 0.80; older = real used value below new). buyback_market = what Cashify pays if a used market exists, else null.
  - launch_date YYYY-MM-DD (real India date), discontinued (usually false for new).
  - HONESTY: only add models you CONFIRM launched in India. Unsure -> skip. resale_price < new_price always.
  - NO PHANTOM VARIANTS (this DB's #1 historical bug): the tell is a 512GB/1TB tier paired with the WRONG RAM size. Real line-ups pair big storage ONLY with the top RAM. Never extrapolate "the next storage tier up" — list ONLY configs you can see on the brand's India store / a major India retailer.
  - NEW PRICE MUST BE SOURCED, NOT ESTIMATED. Real India prices end in 999/990. If you find yourself writing a round number like 40000 or 25000, you are guessing — go find the actual price or set null. Never derive resale as exactly 80% of a new price you did not verify.
  - DO NOT reject a price for being 2-3x its predecessor. 2026 India budget pricing genuinely stepped up (iQOO Z10 Rs21,999 -> Z11 Rs34,999; Tecno Pova 7 Pro Rs19,999 -> Pova 8 Pro Rs49,999; Poco M7 5G Rs10,499 -> M8x Rs20,999 are all REAL). Check the brand's India store before calling a price an MRP.
  - TIER MUST MATCH THE SERIES' EXISTING TIER IN THE DB. Tier sets the margin floor, so drift gives one phone two different margins. If the DB already lists siblings of this series, use their tier.

Write ${DIR}/_gaps/find_${i}.json AND return: {"unit_id":"<name>","missing":[{...}]}. If none missing, missing:[].`
}
function criticPrompt(i, findJson) {
  return `Adversarial CRITIC for Rajdhani Telecom gap-audit. TODAY is 2026-09-10. A finder proposed missing India models with prices; independently VERIFY each.
Finder output:
${JSON.stringify(findJson)}

For EACH proposed model, web-check:
1. real_india_launch: Did this EXACT model actually launch/sell in India? Reject fakes, rumors, non-India variants, phantom storage configs.
2. new_price_final: correct official India new price (not MRP-inflated, not wrong variant). resale_price_final: realistic used resale (< new; for brand-new ≈ new×0.78-0.82). buyback_market_final: real Cashify buyback or null.
3. Sanity: resale < new; buyback < resale (if present); storage ordering (256>128).
4. PHANTOM CHECK: reject any variant whose storage tier is paired with the wrong RAM for that line-up (big storage ships only with top RAM). Confirm the exact config on the brand's India store / a major India retailer.
5. ROUND-NUMBER CHECK: a new_price that is a round thousand (40000, 25000) is a fabrication signature — real India prices end in 999/990. Re-source it or null it.
6. Do NOT reject a price merely for being far above its predecessor — 2026 India budget pricing genuinely stepped up. Verify on the brand's India store instead of assuming an MRP.
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
