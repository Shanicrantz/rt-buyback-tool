export const meta = {
  name: 'rt-buyback-gap-audit-2026',
  description: 'Find missing India phone launches (esp 2026) + gaps, with brain-pricing inputs, critic-verified',
  phases: [
    { title: 'Find', detail: 'per-brand: research India lineup, diff vs DB, propose missing with prices' },
    { title: 'Critic', detail: 'verify each proposal is a real India launch with sane prices' },
  ],
}
const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
const N = 5

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
  return `You audit Rajdhani Telecom's used-phone DB for MISSING models. TODAY is 2026-09-26. Find India phones that SHOULD be in the DB but are MISSING. The DB was gap-audited on 2026-09-21 (prev run 2026-09-16), so the PRIMARY target is anything that launched or went on sale in India from 2026-09-19 onward (the last ~7 days) — new launches, new storage/RAM variants of recent phones, and India availability of models announced earlier. SECONDARY: any notable 2025-2026 model still absent. Do not re-propose models already in the DB.

Get your unit scope + what's already in the DB:
  python3 -c "import json; u=json.load(open('${DIR}/_audit_units.json'))[${i}]; inv=json.load(open('${DIR}/_db_inventory.json')); print('SCOPE:',u[2]); [print('---',b,'MODELS:',inv.get(b,{}).get('models')) for b in u[1]]"

Web-research the India lineup for your scope with heavy emphasis on SEPTEMBER 2026 launches (GSMArena/91mobiles/Smartprix/official brand India sites; check 'launched in India September 2026' / 'launch date 2026' style queries). Diff against the MODELS already listed. A model is MISSING only if not already present (account for name variants).

ALREADY HANDLED ELSEWHERE — do NOT propose: Redmi Note 17 Pro Max 5G, OnePlus N6 Lite, Realme 16 Pro 5G Harry Potter Edition, Lava Bold N4 Pro 5G, Lava Virat Curve 5G (a separate unit re-verifies these held models this week). iPhone 18 Pro/Pro Max, Apple Watch S11/S12/SE 3/Ultra 3/Ultra 4, Galaxy S26 FE, Redmi Note 17 Pro, Vivo Y31t are already in the DB. NEVER propose a model whose India FIRST SALE date is after 2026-09-21 — an announced-but-not-on-sale phone has no used market; if you see one, you may list it with its real first-sale date in launch_date so it is held.

For each MISSING model, output one entry per REAL India storage/RAM variant with PRICING for RT's brain:
  - key: match existing key-naming for that brand (lowercase, e.g. samsung_s26_ultra_256, oppo_reno16_8_256, iphone_17_pro_256). NO phantom variants — verify real India storage configs.
  - tier: S=Apple/Samsung S·Z flagship/Pixel Pro; A=OnePlus flagship/premium/Samsung A7x; B=Xiaomi/Vivo X/Oppo Reno/Nord/Nothing/Moto Edge·Razr; C=Vivo Y·T/Oppo A·F/Realme C·Narzo/Redmi Note/Poco/Samsung A0x-A3x·M·F; D=Infinix/Tecno/Lava/itel/Micromax entry.
  - new_price = official current India NEW price (₹). resale_price = realistic used mint resale TODAY (ONLY for a phone first sold in India <30 days ago with genuinely no used market may you use ≈ new × 0.80 — and then write 'PLACEHOLDER 0.80' in source. Anything older trades used: research the real used value, which for a months-old budget phone is typically 25-30% below that 0.80 figure). buyback_market = what Cashify pays if a used market exists, else null.
  - launch_date YYYY-MM-DD (real India date), discontinued (usually false for new).
  - HONESTY: only add models you CONFIRM launched in India. Unsure -> skip. resale_price < new_price always.
  - NO PHANTOM VARIANTS (this DB's #1 historical bug): the tell is a 512GB/1TB tier paired with the WRONG RAM size. Real line-ups pair big storage ONLY with the top RAM. Never extrapolate "the next storage tier up" — list ONLY configs you can see on the brand's India store / a major India retailer.
  - NEW PRICE MUST BE SOURCED, NOT ESTIMATED. Real India prices end in 999/990. If you find yourself writing a round number like 40000 or 25000, you are guessing — go find the actual price or set null. Never derive resale as exactly 80% of a new price you did not verify.
  - DO NOT reject a price for being 2-3x its predecessor. 2026 India budget pricing genuinely stepped up (iQOO Z10 Rs21,999 -> Z11 Rs34,999; Tecno Pova 7 Pro Rs19,999 -> Pova 8 Pro Rs49,999; Poco M7 5G Rs10,499 -> M8x Rs20,999 are all REAL). Check the brand's India store before calling a price an MRP.
  - TIER MUST MATCH THE SERIES' EXISTING TIER IN THE DB. Tier sets the margin floor, so drift gives one phone two different margins. If the DB already lists siblings of this series, use their tier.

Write ${DIR}/_gaps/find_${i}.json AND return: {"unit_id":"<name>","missing":[{...}]}. If none missing, missing:[].`
}
function heldPrompt(i) {
  return `You verify HELD launches for Rajdhani Telecom's used-phone DB. TODAY is 2026-09-26.
On 2026-09-21 these models were HELD out of the DB because they were announced but NOT YET ON SALE in India (an unsold phone has no used market). Read them:
  python3 -c "import json; [print(h['key'],'|',h['name'],'| launch',h.get('launch_date'),'| first_sale',h.get('first_sale_date'),'| new',h.get('new_price_verified')) for h in json.load(open('${DIR}/_held_future_2026-09-21.json'))]"
Existing sibling entries already in the DB (for key naming + tier):
  python3 -c "import json; d=json.load(open('${DIR}/phone_db.json')); [print(k,d[k].get('tier'),d[k].get('display_name')) for k in d if k.startswith(('redmi_note_17','redmi_note_15_pro','oneplus_n6','realme_16_pro','lava_bold','lava_virat'))]"

For EACH held key:
  1) Confirm whether it is NOW actually ON SALE in India (deliveries / open sale started) — give the real first-sale date as launch_date (YYYY-MM-DD). If first sale is still after 2026-09-26, put that future date in launch_date so it stays held.
  2) Confirm the OFFICIAL India new price for EACH real config (brand India store / major India retailer). OnePlus N6 Lite had NO announced price on 09-21 — find its real India configs and prices now. List only configs you can see on sale (no phantom RAM/storage pairings); a held entry with no storage in its key (oneplus_n6_lite) must be replaced by one entry per real config, keyed like the DB's siblings (e.g. oneplus_n6_lite_4_64).
  3) resale_price: these went on sale only days ago, so a real used market barely exists. If you find genuine used/sealed-resale listings (OLX, dealers), report the realistic mint-used figure. If not, you MAY use new x 0.80 and MUST write 'PLACEHOLDER 0.80' in source. buyback_market: a real Cashify sell-flow quote only, else null.
  4) Keep the held key names (except the storage split above); tier = the DB's existing tier for that series (Redmi Note 17 Pro Max = B, OnePlus N-series = C, Realme 16 Pro = B, Lava = D).
Output every held key as an entry in "missing" (display_name from the held file). Skip nothing — if one is still not on sale, keep it with its future launch_date so the pipeline holds it again.

Write ${DIR}/_gaps/find_${i}.json AND return: {"unit_id":"held_carryforward","missing":[{...}]}.`
}
function criticPrompt(i, findJson) {
  return `Adversarial CRITIC for Rajdhani Telecom gap-audit. TODAY is 2026-09-26. A finder proposed missing India models with prices; independently VERIFY each.
Finder output:
${JSON.stringify(findJson)}

For EACH proposed model, web-check:
1. real_india_launch: Did this EXACT model actually launch/sell in India? Reject fakes, rumors, non-India variants, phantom storage configs.
2. new_price_final: correct official India new price (not MRP-inflated, not wrong variant). resale_price_final: realistic used resale (< new; ONLY for a phone first sold in India <30 days ago ≈ new×0.78-0.82; older phones must carry researched used value). buyback_market_final: real Cashify buyback or null.
3. Sanity: resale < new; buyback < resale (if present); storage ordering (256>128).
4. PHANTOM CHECK: reject any variant whose storage tier is paired with the wrong RAM for that line-up (big storage ships only with top RAM). Confirm the exact config on the brand's India store / a major India retailer.
5. ROUND-NUMBER CHECK: a new_price that is a round thousand (40000, 25000) is a fabrication signature — real India prices end in 999/990. Re-source it or null it.
6. FIRST SALE: launch_date must be the India FIRST-SALE date if sale started after the announcement. If a model is not yet on sale in India as of 2026-09-26, keep real_india_launch=true but correct launch_date to the future first-sale date (the pipeline holds it). For phones on sale <30 days, resale ~= new x0.78-0.82 is acceptable ONLY if marked as a placeholder; otherwise require real datapoints.
7. Do NOT reject a price merely for being far above its predecessor — 2026 India budget pricing genuinely stepped up. Verify on the brand's India store instead of assuming an MRP.
Set *_final to correct values (corrected if finder wrong, confirmed if right, rejected+real_india_launch=false if fake/unverifiable).

Write ${DIR}/_gaps/verified_${i}.json AND return: {"unit_id":"<name>","verified":[{...}]}. Every proposed key exactly once.`
}

phase('Find')
const results = await pipeline(
  Array.from({ length: N }, (_, i) => i),
  (i) => agent(i === 4 ? heldPrompt(i) : findPrompt(i), { label: `find:${i}`, phase: 'Find', schema: FIND_SCHEMA, model: 'sonnet', agentType: 'general-purpose' }),
  (findRes, i) => agent(criticPrompt(i, findRes), { label: `critic:${i}`, phase: 'Critic', schema: CRITIC_SCHEMA, model: 'sonnet', agentType: 'general-purpose' }),
)
const ok = results.filter(Boolean)
let proposed = 0, real = 0
for (const r of ok) for (const v of (r.verified || [])) { proposed++; if (v.real_india_launch && v.verdict !== 'rejected') real++ }
log(`Critic done: ${ok.length}/${N} units, ${proposed} proposed, ${real} verified real.`)
return { units: ok.length, total: N, proposed, real }
