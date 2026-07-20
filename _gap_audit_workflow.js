export const meta = {
  name: 'rt-buyback-gap-audit',
  description: 'Audit RT buyback DB for missing phone models (2014-2026 India) and add new launches',
  phases: [{ title: 'Gap Audit', detail: '24 brand/series agents find missing models + new launches' }],
}

const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
const N = 24

const GAP_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    unit_id: { type: 'string' },
    missing: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          key: { type: 'string' },
          display_name: { type: 'string' },
          tier: { type: 'string', enum: ['S', 'A', 'B', 'C', 'D'] },
          launch_date: { type: 'string' },
          discontinued: { type: 'boolean' },
          anchor_field: { type: 'string', enum: ['resale_target_a1', 'refurb_retail_anchor_excellent', 'cashify_exchange', 'net_new_inr'] },
          anchor_value: { type: 'number' },
          target_margin: { type: ['number', 'null'] },
          market_factor: { type: ['number', 'null'] },
          new_price: { type: ['number', 'null'] },
          calibration_status: { type: 'string', enum: ['verified', 'estimated'] },
          confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
          source: { type: 'string' },
        },
        required: ['key', 'display_name', 'tier', 'launch_date', 'discontinued', 'anchor_field', 'anchor_value', 'calibration_status', 'confidence', 'source'],
      },
    },
  },
  required: ['unit_id', 'missing'],
}

function promptFor(i) {
  return `You audit the Rajdhani Telecom (Moradabad, India) used-phone buyback database for COMPLETENESS. TODAY is 26 June 2026. Find phone models that SHOULD be in the DB but are MISSING, and any brand-new launches.

WORKING DIR: ${DIR}

STEP 1 — Get your audit scope and the models already in the DB:
Run:
  python3 -c "import json; u=json.load(open('${DIR}/_audit_units.json'))[${i}]; inv=json.load(open('${DIR}/_db_inventory.json')); print('UNIT:',u[0]); print('SCOPE:',u[2]); [print('---',b,'---\\nMODELS:',inv.get(b,{}).get('models')) or print('KEYS sample:',inv.get(b,{}).get('keys')[:60]) for b in u[1]]"
This prints your unit's scope description and the EXISTING models + key naming convention for the relevant brand(s). Only audit the series named in SCOPE.

STEP 2 — Research the COMPLETE India lineup for your scope (2014-2026, emphasis on catching 2024-2026 launches) using web search/fetch. Sources: GSMArena brand pages, 91mobiles, Smartprix, Cashify, Wikipedia brand model lists, Flipkart/Amazon. Enumerate every model ACTUALLY LAUNCHED IN INDIA in your scope.

STEP 3 — Diff against the existing MODELS list. A model is MISSING only if it is NOT already present (account for naming variants — "Galaxy S24" vs "S24"; don't re-flag something already there under a slightly different name). Focus on real gaps and new launches.

STEP 4 — For each MISSING model, output one entry PER REAL India storage/RAM variant. RULES (learned from past data bugs — follow strictly):
  - key: MATCH the existing key naming convention for that brand exactly (copy the pattern you saw, e.g. samsung_s24_ultra_256, samsung_a55_5g_8_256, vivo_x200_pro_12_256, oneplus_13_12_256, iphone_16_pro_max_256, realme_c75_5g_4_256). Lowercase, underscores.
  - NO PHANTOM VARIANTS: only storage/RAM configs that genuinely existed in India. Do not invent 1TB/2TB/512 unless that model really shipped it here. Verify max storage.
  - tier: S=Apple/Samsung S·Z·Note flagship/Pixel Pro; A=OnePlus flagship/premium foldables/Samsung A7x; B=Xiaomi/Vivo X/Oppo Reno/OnePlus Nord/Nothing/Moto Edge·Razr; C=Vivo Y·T/Oppo A·F/Realme C·Narzo/Redmi Note/Poco/Samsung A0x-A3x/M·F; D=Itel/Lava/Micromax/Tecno/Infinix entry.
  - anchor_field + anchor_value: For models still in production or <18 months old, use anchor_field='resale_target_a1' = today's realistic A1 mint (with-box) RESALE price (≈ current Cashify refurb retail, or ≈ new price × 0.55-0.75 depending on age). For discontinued/older models use anchor_field='refurb_retail_anchor_excellent' = today's refurbished-excellent retail price. Prefer a LIVE cited number (calibration_status='verified', else 'estimated').
  - ANTI-OVERPAY (critical): resale_target_a1 MUST be <= 0.90 × new_price. The engine derives buyback A1 = resale/(1+margin) or refurb×0.88/(1+margin) — keep it well below new. Set new_price when known.
  - target_margin/market_factor: leave null to use tier defaults unless you have reason.
  - launch_date: real India launch date YYYY-MM-DD (best estimate if exact day unknown, use month-15).
  - source: cite where you confirmed the model + price.
  - HONESTY: only add models you CONFIRM launched in India. If unsure a model exists/launched here, DO NOT add it. Better to miss a doubtful one than invent a fake.

STEP 5 — Write valid JSON to ${DIR}/_gaps/unit_${i}.json AND return it, shape:
  {"unit_id":"<unit name>","missing":[ {"key":...,"display_name":...,"tier":...,"launch_date":...,"discontinued":...,"anchor_field":...,"anchor_value":<num>,"target_margin":null,"market_factor":null,"new_price":<num|null>,"calibration_status":...,"confidence":...,"source":...}, ... ]}
If nothing is missing for your scope, return {"unit_id":"<name>","missing":[]}. Do not duplicate keys already in the DB.`
}

phase('Gap Audit')
log(`Auditing ${N} brand/series units for missing models + new launches (2014-2026)...`)

const results = await parallel(
  Array.from({ length: N }, (_, i) => () =>
    agent(promptFor(i), { label: `audit:${i}`, phase: 'Gap Audit', schema: GAP_SCHEMA, model: 'sonnet', agentType: 'general-purpose' })
  )
)

const ok = results.filter(Boolean)
const totalMissing = ok.reduce((s, r) => s + (r.missing ? r.missing.length : 0), 0)
log(`Done: ${ok.length}/${N} units returned, ${totalMissing} missing variant-entries proposed.`)
return { units_returned: ok.length, total: N, total_missing: totalMissing }
