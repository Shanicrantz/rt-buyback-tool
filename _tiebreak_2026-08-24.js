export const meta = {
  name: 'rt-gap-tiebreak-2026-08-24',
  description: 'Three independent lenses settle the disputed India launch prices before they enter the DB',
  phases: [{ title: 'Panel', detail: '3 independent price lookups per disputed model family' }],
}
const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'

const FAMILIES = [
  { id: 'iqoo_z11', name: 'iQOO Z11 5G (India, launched ~2026-08-20)',
    disputed: 'Proposed India prices: 6/128 Rs 34,999, 8/128 Rs 39,999, 8/256 Rs 44,999, 12/256 Rs 49,999.',
    predecessors: 'For band context: iQOO Z10 5G 8/128 launched at Rs 21,999 (Apr 2025); iQOO Z11 Lite 5G tops out around Rs 24,500; iQOO Z11x 5G 8/128 about Rs 14,999. The iQOO Z line is a budget/mid series.' },
  { id: 'tecno_pova_8_pro', name: 'Tecno Pova 8 Pro 5G (India, launched ~2026-08-18)',
    disputed: 'Proposed India prices: 8/256 Rs 49,999, 12/512 Rs 54,999.',
    predecessors: 'For band context: Tecno Pova 7 Pro 5G 8/256 launched at Rs 19,999 (Jun 2025); the Pova line is Tecno budget/gaming, historically Rs 12,000-20,000.' },
  { id: 'poco_m8x', name: 'Poco M8x 5G (India, launched ~2026-08-21)',
    disputed: 'Proposed India prices: 4/128 Rs 20,999, 6/128 Rs 22,999.',
    predecessors: 'For band context: Poco M7 5G 4/128 sits around Rs 9,000-11,000; the Poco M line is entry-level, historically Rs 9,000-15,000.' },
]
const LENSES = [
  { id: 'brand', how: 'Go to the BRAND\'S OWN INDIA CHANNEL first — the official India store / product page, and the brand\'s India launch press release. Report the price exactly as the brand states it, and quote the sentence or price element you read.' },
  { id: 'retail', how: 'Go to MAJOR INDIAN RETAILERS — Flipkart, Amazon.in, Croma, Reliance Digital. Report the live selling price AND any struck-through MRP separately, and name the listing title you read so a wrong-variant match can be caught.' },
  { id: 'press', how: 'Go to INDIAN TECH PRESS launch coverage — 91mobiles, Smartprix, Gadgets360, GSMArena, Times of India Gadgets. These report the launch price table. Report the full variant/price table as published and the outlet.' },
]

const SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    family_id: { type: 'string' }, lens: { type: 'string' },
    launched_in_india: { type: 'string', enum: ['on_sale', 'announced_not_on_sale', 'not_found'] },
    india_launch_date: { type: ['string', 'null'] },
    variants: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: { variant: { type: 'string' }, price_inr: { type: ['number', 'null'] },
                    mrp_inr: { type: ['number', 'null'] } },
      required: ['variant', 'price_inr'] } },
    predecessor_price_inr: { type: ['number', 'null'] },
    source_quote: { type: 'string' },
    verdict_on_disputed: { type: 'string', enum: ['disputed_prices_correct', 'disputed_prices_too_high', 'disputed_prices_too_low', 'cannot_determine'] },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
  required: ['family_id', 'lens', 'launched_in_india', 'india_launch_date', 'variants', 'predecessor_price_inr', 'source_quote', 'verdict_on_disputed', 'confidence'],
}

function prompt(fam, lens) {
  return `Settle ONE question for Rajdhani Telecom: what does ${fam.name} ACTUALLY cost new in India, and is it on sale?

${fam.disputed}
${fam.predecessors}

These proposed prices are 2-3x the series' historical band, so they are probably MRPs, wrong-product matches, or fabrications. RT will buy used units at roughly 75% of whatever price lands in its database, so an inflated figure costs real money on every unit. TODAY is 2026-08-24.

YOUR LENS — use it and do not substitute another: ${lens.how}

Report every India variant you find with its selling price and, separately, any MRP. Report the DIRECT PREDECESSOR's India launch price too, so the generational jump is visible. Quote the exact text or price element you actually read in source_quote — if you cannot read a real source, say so and set launched_in_india='not_found' with confidence 'low'. A truthful "cannot determine" is worth more here than a plausible number.
verdict_on_disputed: are the proposed prices above correct, too high, too low, or undeterminable?

Return the JSON object. Do not write any file.`
}

phase('Panel')
const jobs = []
for (const fam of FAMILIES) for (const lens of LENSES) {
  jobs.push({ fam, lens })
}
const out = await parallel(jobs.map((j) => () =>
  agent(prompt(j.fam, j.lens), { label: `${j.fam.id}:${j.lens.id}`, phase: 'Panel', schema: SCHEMA,
                                 model: 'sonnet', agentType: 'general-purpose' })
    .then((r) => r && { ...r, family_id: j.fam.id, lens: j.lens.id })))

const res = out.filter(Boolean)
const byFam = {}
for (const r of res) (byFam[r.family_id] ||= []).push(r)
for (const [fam, rs] of Object.entries(byFam)) {
  const v = rs.map((r) => r.verdict_on_disputed)
  log(`${fam}: ${v.join(' | ')}`)
}
return { panel: res }
