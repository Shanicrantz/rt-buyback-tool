// Historical research template. Every recurring refresh must first follow
// REFRESH-POLICY.md and generate the full all-catalogue-v1 manifest. Its fixed
// batches are NOT a full refresh; adapt a dated copy to every manifest key.
export const meta = {
  name: 'rt-buyback-market-reprice',
  description: 'Research REAL resale price + buyback-market rate per model (audit + critic), for Shane-style buyback calc',
  phases: [
    { title: 'Market Research', detail: 'fetch real resale price + what buyers pay, per model' },
    { title: 'Critic', detail: 'adversarially verify both prices are real local-market numbers' },
  ],
}

const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
const N = 12
const TODAY = new Intl.DateTimeFormat('en-CA', {timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date())

const BRAIN = `RT (Rajdhani Telecom, Moradabad) BUYBACK BRAIN — how Shane actually prices:
- REQUIRED REFRESH COVERAGE (2026-10-08): read REFRESH-POLICY.md. Every catalogue model and exact variant needs a fresh current-new-price check, including old/discontinued/budget models and nonphones. No 96-entry, recent/demand or fixed-batch sample is a complete refresh. Missing evidence remains pending with dated attempted sources. Generate all-catalogue-v1 and validate complete coverage before applying. International-derived rows remain separately accounted for. The source writer rejects incomplete refreshes.
- CURRENT RETAIL ESTIMATE POLICY v6.22: current retailer asks already reflect model generation. Use the disclosed 10% retailer/service allowance for normal phones or 15% for C/D tiers and foldables; do not add a model-launch-age haircut. Actual customer-device age and the scaled 13% warranty rule stay separate. Asking prices and allowance-adjusted values remain estimates, never measured local sales.
- CURRENT POLICY v6.15 (2026-10-04): runtime base = current exact new cash market price × actual device age retention × condition. Old resale targets, manual rates, launch age and warranty overrides are historical data, not base inputs. Never calculate the customer's device age from model launch date. Research exact available NEW cash selling prices as separate observations {kind:"retail_cash_price",variant_name:<exact display_name>,amount_inr,observed_at:<ISO timestamp>,source_url,available:true} in current_new_price. Bank/exchange prices, MRP without a selling offer, launch prices and out-of-stock listings are not usable current observations. Do not overwrite a current observation with historical net_new_inr. Missing current price requires counter confirmation; never invent it. Keep all price evidence and paired databases in sync. _engine_quote.cjs deliberately refuses a context-free A1 under v6.15. The fixed-v6.12 _refresh_cashify.py is archival and must not rebuild a v6.15 release.
- RESALE price = what RT can ACTUALLY re-sell a mint (A1) used unit for in the LOCAL Indian second-hand market. This is NOT Cashify's "buy refurbished" retail price for older phones — Cashify's refurb price includes their warranty + brand premium and is INFLATED vs what a local shop gets. Real resale for older/less-popular phones is BELOW Cashify refurb retail. For current hot phones (in demand) real resale is close to Cashify refurb retail. Triangulate from OLX recent SOLD (not asking) + local used-market + Cashify refurb (as an upper bound).
- SHANE'S CASHIFY POLICY (2026-10-02): target the FINAL offer at least 2% above the actual assessed Cashify quote, with a minimum Rs100 premium, rounded UP to Rs100. Match exact variant, actual unit age, condition, kit, battery, warranty and market. Preserve an already higher RT offer. Public 'Get Upto' headlines remain ceilings, not condition-specific offers; record them separately and never fabricate a payout from a fraction of resale. Legacy undated cashify_exchange/buyback_market fields are not fresh evidence.
- Research resale independently; NEVER inflate it to make a competitor target fit. Apply configured resale markup (resale/(1+target_margin), legacy default), or explicit margin_basis:gross (resale*(1-target_margin)), with at least 8% gross margin, plus trusted-current-new*0.85 ceiling. These limits apply to BOTH base offers and competitor uplifts; subtract entered per-deal costs once after condition/repair adjustments. Missing/stale resale remains an explicit estimate, not proof of profit. Preserve the International discount/review rule. A verified Cashify quote can genuinely exceed the safe RT ceiling: keep the evidence and flag the conflict instead of declaring it fake solely because its ratio is high. Store the full condition questionnaire and source/date for assessed quotes; use the current shipped engine and test_age_formula.cjs for the condition-matched final-offer policy. Preserve legacy net_new_inr only as historical reference.
- POISONED SOURCE — DO NOT USE: the "Approx. Buyback Value" box on cashify.in/<model>-price-in-india pages is a TEMPLATE that always prints exactly 40% of the price listed on that page. It is not a quote. Verified identical across Z Fold8, Z Fold8 Ultra and iPhone 17 Pro Max. A real competitor buyback comes ONLY from a cashify.in/sell-old-mobile-phone/... quote flow or another buyer's actual sell page. Those same price pages also carry WRONG new prices (iPhone 17 Pro Max shown as Rs1,37,900 vs Apple India's real Rs1,49,900) — never take a new price or refurb ceiling from them either.`

const FETCH_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    batch_index: { type: 'integer' },
    models: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        display_name: { type: 'string' },
        current_new_price: { type: ['object','null'] },
        current_resale_price: { type: ['object','null'] },
        new_price_status: { type: 'string', enum: ['verified','unverified','unavailable'] },
        new_price_note: { type: 'string' },
        resale_price: { type: ['number', 'null'] },
        resale_low: { type: ['number', 'null'] },
        resale_high: { type: ['number', 'null'] },
        resale_sources: { type: 'string' },
        buyback_market: { type: ['number', 'null'] },
        buyback_source: { type: 'string' },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      },
      required: ['key', 'current_new_price', 'current_resale_price', 'new_price_status', 'new_price_note', 'resale_price', 'buyback_market', 'resale_sources', 'buyback_source', 'confidence'],
    } },
  },
  required: ['batch_index', 'models'],
}

const CRITIC_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    batch_index: { type: 'integer' },
    models: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        key: { type: 'string' },
        current_new_price: { type: ['object','null'] },
        current_resale_price: { type: ['object','null'] },
        new_price_status: { type: 'string', enum: ['verified','unverified','unavailable'] },
        new_price_verdict: { type: 'string', enum: ['confirmed','corrected','rejected'] },
        resale_final: { type: ['number', 'null'] },
        buyback_final: { type: ['number', 'null'] },
        resale_verdict: { type: 'string', enum: ['confirmed', 'corrected', 'rejected'] },
        buyback_verdict: { type: 'string', enum: ['confirmed', 'corrected', 'rejected'] },
        note: { type: 'string' },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      },
      required: ['key', 'current_new_price', 'current_resale_price', 'new_price_status', 'new_price_verdict', 'resale_final', 'buyback_final', 'resale_verdict', 'buyback_verdict', 'confidence'],
    } },
  },
  required: ['batch_index', 'models'],
}

function fetchPrompt(i) {
  return `You research the REAL Indian second-hand market for Rajdhani Telecom. TODAY is ${TODAY}.

${BRAIN}

Get your batch's phone keys + names:
  python3 -c "import json; d=json.load(open('${DIR}/phone_db.json')); ks=json.load(open('${DIR}/_ov_batches.json'))[${i}]; print({k:d[k]['display_name'] for k in ks})"

For EACH exact model/RAM/storage variant, find THREE INDEPENDENT prices via fresh primary-page reads (not cached search snippets):
  0) CURRENT_NEW_PRICE: exact India RAM/storage model, currently available unconditional NEW cash selling price including mandatory fees. Record {kind:"retail_cash_price",variant_name,amount_inr,observed_at,source_url,available:true,market:"India",condition:"new",requires_exchange:false,requires_bank_offer:false}. Exclude MRP-only, out-of-stock, exchange, EMI, bank/member-only prices; null with reason when unverifiable. Read date must be real, never reuse an old observation with a new timestamp. Also return current_resale_price as {kind:"local_resale_observed"|"local_resale_estimate",variant_name,amount_inr,observed_at,source_url,market:"India",grade:"A1",method}. Warranty refurb retail is an upper bound only; a discounted inference MUST be local_resale_estimate. Preserve both original source amount and assumptions. A higher new price does not justify raising old used resale.
  1) RESALE_PRICE = realistic price a LOCAL shop can re-sell a mint (excellent, with-box) used unit for TODAY in India.
     Triangulate current exact-grade primary sources. A retailer-derived estimate uses the disclosed current allowance above, with raw asks and assumptions retained. A discount on an asking price is not a real sold observation. Give resale_low, resale_high, and resale_price with honest evidence classification.
  2) BUYBACK_MARKET = what sellers are actually PAID today, from a REAL sell/exchange quote flow only (never the 40%-template "Approx. Buyback Value" box on a price-in-india page): Cashify "sell old phone" / exchange value is the primary benchmark (web_search "Cashify <model> <storage> sell price" or fetch cashify.in/sell-old-mobile-phone/...). Note if other buyers differ.
Do not scale a competitor quote from another RAM/storage variant. Only report numbers you actually find for the exact variant; null if none. A public maximum never populates BUYBACK_MARKET as an assessed payout. Save structured assessed quote evidence in the current dated review artifacts, preserving the condition answers and source.

CRITICAL — BRAND-NEW / THIN-MARKET MODELS: some entries are 2026 launches whose used market barely exists. For any model launched in the last ~6 months you MUST:
  (a) CONFIRM the model actually is ON SALE IN INDIA under that exact name and storage config. Only claim it does not exist if you have HARD evidence (brand India site lineup / major India outlet listing the real variants). A missing Cashify page or a thin OLX result is NOT evidence of non-existence — say 'unverified', not 'does not exist'. False 'does not exist' verdicts have repeatedly been wrong on this DB.
  (b) Verify launch/release and successor dates against current primary India sources. Do not calculate the customer's unit age from model launch. Do not infer non-existence from thin coverage.
  (c) A fraction of new price is a valuation assumption, never observed resale. No variant may borrow another variant's price. Keep MRP/launch price separate from today's available selling price.

Write ${DIR}/_ov_updates/fetch_${i}.json AND return:
{"batch_index":${i},"models":[{"key":...,"display_name":...,"current_new_price":<object|null>,"current_resale_price":<object|null>,"new_price_status":"verified|unverified|unavailable","new_price_note":"...","resale_price":<num|null>,"resale_low":<num|null>,"resale_high":<num|null>,"resale_sources":"<olx/cashify/... + numbers>","buyback_market":<num|null>,"buyback_source":"<cashify sell + number>","confidence":"high|medium|low"}, ...]}
Every key exactly once.`
}

function criticPrompt(i, fetchJson) {
  return `You are an adversarial MARKET-PRICE CRITIC for Rajdhani Telecom. TODAY is ${TODAY}. Assume the fetcher may have erred — catch it.

${BRAIN}

Fetcher output:
${JSON.stringify(fetchJson)}

For EACH model, independently sanity-check and CORRECT:
0. CURRENT_NEW_PRICE and CURRENT_RESALE_PRICE: independently open exact variant source; validate timestamp, India region, stock, grade and unconditional cash basis. Return structured evidence in the matching schema fields, null if rejected. Never stamp the whole catalogue fresh. Never overwrite current-new with historic net_new_inr. A refresh is PARTIAL if any scoped model lacks either new-price evidence or a clearly classified resale reference. Inferred local resale remains an estimate and cannot authorize competitor uplift.
1. RESALE_FINAL: Is resale_price a REALISTIC local re-sale price (what a Moradabad shop actually gets), NOT (a) an OLX ASKING price (inflated ~10%), NOR (b) Cashify's warranty-inflated refurb-retail for an OLDER phone. For older/unpopular models pull it DOWN toward real used value. For current hot models it can sit near refurb retail.
2. BUYBACK_FINAL: Is it a real current Cashify/market buyback (what sellers get paid)?
3. EXISTENCE: verify exact model and storage from current official India sources. Report unverified when evidence is missing. Prior dated notes are historical, not proof of today's lineup or stock.
4. Hard sanity: RESALE_FINAL > BUYBACK_FINAL (a reseller must buy below resale). If violated, fix. Typical gap: buyback ≈ 55-80% of resale. If you have no real buyback datapoint, set buyback_final null — NEVER back into it as a round fraction of resale, and never echo the fetcher's number without a source.
5. OUTGOING GENERATION: verify successor availability now and use post-event used evidence; no fixed historical event list. Never inflate resale to beat a competitor.
6. UPWARD BIAS CHECK: OLX asking prices and Cashify refurb retail both run ABOVE what a Moradabad shop really gets. If resale_price looks like an asking price or a warranty-backed refurb price, pull it DOWN. Overpaying costs RT money on every unit; underpaying only loses one deal.
Set *_final to the correct value (yours if fetcher wrong -> 'corrected', theirs if right -> 'confirmed', null -> 'rejected').

Write ${DIR}/_ov_updates/verified_${i}.json AND return:
{"batch_index":${i},"models":[{"key":...,"current_new_price":<object|null>,"current_resale_price":<object|null>,"new_price_status":"verified|unverified|unavailable","new_price_verdict":"confirmed|corrected|rejected","resale_final":<num|null>,"buyback_final":<num|null>,"resale_verdict":"confirmed|corrected|rejected","buyback_verdict":"...","note":"<what & why + source>","confidence":"high|medium|low"}, ...]}
Every key exactly once.`
}

phase('Market Research')
const results = await pipeline(
  Array.from({ length: N }, (_, i) => i),
  (i) => agent(fetchPrompt(i), { label: `fetch:${i}`, phase: 'Market Research', schema: FETCH_SCHEMA, model: 'sonnet', agentType: 'general-purpose' }),
  (fetchRes, i) => agent(criticPrompt(i, fetchRes), { label: `critic:${i}`, phase: 'Critic', schema: CRITIC_SCHEMA, model: 'sonnet', agentType: 'general-purpose' }),
)

const ok = results.filter(Boolean)
let models = 0, corrected = 0
for (const r of ok) for (const m of (r.models || [])) { models++; if (m.resale_verdict === 'corrected' || m.buyback_verdict === 'corrected') corrected++ }
log(`Critic done: ${ok.length}/${N} batches, ${models} models, ${corrected} prices corrected.`)
return { batches: ok.length, total: N, models, corrected }
