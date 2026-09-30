export const meta = {
  name: 'rt-buyback-rerun-missing-2026-09-30',
  description: 'Re-run only the two agents lost to the session limit: reprice critic batch 3 and gap-audit unit 0 (find + critic)',
  phases: [
    { title: 'Rerun', detail: 'reprice critic:3 + gap find:0 -> critic:0' },
  ],
}
const FETCH3 = {"batch_index": 3, "models": [{"key": "iphone_air_512", "display_name": "iPhone Air 512GB", "resale_price": 82000, "resale_low": 75000, "resale_high": 92000, "resale_sources": "NEW=174900 (apple.com/in raw HTML 2026-09-30: SKU 'iPhone Air 512GB' fullPrice 174,900; 256GB 149,900; 1TB 224,900; Amazon.in street 256GB 119,900). OLX 2026-09-30 individual Indian-unit 512GB asks (dealer 'global new phone' 111,990 ads, MacBook ads, brand-new/open-box ads excluded): about 16 asks, core cluster 89,500-91,999 (median ~90,000). Post-09-18 asks (0-3 days old, plus 09-19/09-20): 90,000 Surat, 89,990 + 89,999 + 91,990 + 89,999 Delhi/Noida (warranty to Mar/May 2027), 89,500 Hyderabad, 89,999 Mumbai (battery 92%), outliers 100,000 / 109,000 / 115,000 (Apple Care). Pre-09-18 asks 85,000-97,999 = same level, so no visible softening after 09-18 (the Air has no successor yet). Sold-adj (-8..-12%) ~79-83k. ORU 512GB has only 3 stale listings (57,150 and 59,240 no warranty Jun-Jul; 70,000 sold Mar) - unusable. Cashify refurb 512GB (upper bound, all out of stock/stale): Fair 95,599, Good 99,399, Superb 103,399 - real local resale far below. Best single estimate 82k for a mint unit with box and warranty left; 256GB sibling evidence (batch 4) ~72k so the 512GB step is ~+10k. FYI DB net_new_inr for iphone_air_256 (119,900) and iphone_air_1tb (132,000) are stale/wrong: apple.com/in shows 149,900 and 224,900.", "buyback_market": 75200, "buyback_source": "Cashify sell page cashify.in/sell-old-mobile-phone/used-apple-iphone-air-12-gb-512-gb 'Get Upto' 75,200 (top-condition ceiling, 2026-09-30; 256GB 69,000, 1TB 87,000). Cashkr iPhone Air pages never render a price (stay on 'Loading').", "confidence": "medium"}, {"key": "samsung_z_fold_6_1tb", "display_name": "Samsung Galaxy Z Fold 6 1TB", "resale_price": 73000, "resale_low": 63000, "resale_high": 82000, "resale_sources": "NEW=200999 (Fold6 1TB launch MRP; Cashify MRP field 200,999 while 256GB 164,999 / 512GB 176,999 match the Samsung India launch; samsung.com/in Fold6 buy page still lists the 1TB|12GB SKU SM-F956BZSH, so the variant is real; Amazon.in still sells the 256GB at 139,999). The DB's 185,000 is a round placeholder. OLX 2026-09-30 Fold6 1TB (thin, 5 asks): 70,000 (3d, Gwalior), 78,000 (1d, full kit), 82,999 (2d, Indian unit), 85,000 (16d, excellent), 90,000 (0d, 'global limited edition' - excluded); Indian-unit median ~80,500 => sold-adj ~70-75k. Same-day 512GB asks (n=29, median ~78k incl. some sealed) => ~68k sold-adj, consistent with the batch-4 512GB estimate 68k; 1TB step ~+4-5k. ORU (algorithmic, far below OLX): 1TB sold-out 60,150 x2 (Apr 6-7, no warranty), 512GB active 56,960-59,430, 256GB sold 56.6-61k (Feb-May), now ~48.9k. Cashify refurb 1TB (upper bound): Best Value 92,799 and Fair 97,599 in stock, Good 101,499 / Superb 105,699 out of stock. Fold6 is two generations back (Fold7 and Fold8 shipped). Estimate 73k; low confidence, few datapoints.", "buyback_market": 68830, "buyback_source": "Cashify sell page ...used-samsung-galaxy-z-fold6-5g-12-gb-1-tb 'Get Upto' 68,830 (ceiling; the 512GB 66,240 and 256GB 65,560 ceilings look stale/high vs ORU/OLX). Cashkr Z Fold6 12GB/1TB 'up to' 73,000.", "confidence": "low"}, {"key": "macbook_air_m3_13_2024_16_512", "display_name": "MacBook Air M3 13\" (2024) 16/512GB", "resale_price": 75000, "resale_low": 65000, "resale_high": 84000, "resale_sources": "NEW=154900 (Apple India launch price of the 13in M3 16GB/512GB, SKUs MXCR3/MXCT3/MXCU3/MXCV3HN/A, from a Wayback snapshot of apple.com/in Aug-2024; 8/256 was 114,900 and 8/512 134,900 - the DB's 134,900 is the 8/512 price). Apple India now sells only M5 Airs (Amazon 13in 16/512 138,990) and the MacBook Neo (A18 Pro 8/256 79,900, Amazon 71,990-80,990), so the M3 is used-only and two generations back. OLX 2026-09-30 (thin - titles rarely state 16GB): clean M3 16/512 ask 87,000 (0d, full box; screen size not stated); repeated '16GB/512GB' ads at 39,000-42,500 from one seller are bait/parts and excluded. 13in M3 8/512 asks: 72,000 (2d), 72,400 (19d, AppleCare to 2027), 80,000, 83,000, 90,000, 95,000 (median ~81-83k, n=6-8) => sold-adj ~73k, plus a 16GB premium of ~+4-6k => ~77-79k; 13in M3 16/256 median ~80,000 (n=14); 8/256 median 84,999 (n=54, one dealer's repeats). Cashify refurb 13in M3 16/512 (upper bound, stale, all out of stock): Fair 83,399, Good 88,499, Superb 92,899. Buyer ceilings 59-60k (Cashkr 59,000; Cashify series 60,000) imply dealer resale ~70-74k, and the DB's own M3 ladder (15in 8/256 63,000) puts the 13in 16/512 ~64-72k. Blended estimate 75k; thin evidence.", "buyback_market": 59000, "buyback_source": "Cashkr exact config: MacBook Air M3 13-inch 512GB/16GB 'You get up to' 59,000 (16/256 58,000). Cashify 'MacBook Air 2024' series page 'Get Upto' 60,000 (config-agnostic ceiling); the exact-config Cashify quote sits behind a phone-number login (not entered).", "confidence": "low"}, {"key": "vivo_x300_pro_16_512", "display_name": "Vivo X300 Pro 16/512GB", "resale_price": 76000, "resale_low": 70000, "resale_high": 84000, "resale_sources": "NEW=119999 (Amazon.in and Flipkart both list X300 Pro 16GB/512GB at 119,999 on 2026-09-30; India launch price was 109,999 (DB 109,998); Cashify MRP field 119,999). Single India variant 16/512. OLX 2026-09-30 X300 Pro asks (sealed/new/global ads and ~28k bait ads excluded): n=79, min 70,000, Q1 80,000, median 85,000, Q3 92,000, max 115,000; 73 of them posted within 14 days => sold-adj (-8..-12%) median ~76.5k (Q1 72k, Q3 83k). ORU (8 listings, thin/old): 512GB Like New >9 months warranty 61,740-63,160 (Jun) and 62,200 (Dec), Excellent no warranty 60,000 (Jul 7) and 46,310 (Jun 4). Cashify refurb (upper bound; only Good Dune Gold 94,499 and Superb Elight Black 98,399 in stock): Fair 90,799, Good 94,499, Superb 98,399 => x0.85 = ~77k. Buyer ceilings 61.5-62.5k /0.8 = ~77k. The three anchors converge at ~76-77k. About 10 months on sale in India, no successor listed on vivo.com/in.", "buyback_market": 61500, "buyback_source": "Cashify sell page ...used-vivo-x300-pro-16-gb-512-gb 'Get Upto' 61,500 (top-condition ceiling, 2026-09-30). Cashkr Vivo X300 Pro 16GB/512GB 'up to' 62,500.", "confidence": "medium"}, {"key": "google_pixel_10_pro_xl_512", "display_name": "Google Pixel 10 Pro XL 512GB", "resale_price": 72000, "resale_low": 62000, "resale_high": 82000, "resale_sources": "DOES NOT EXIST as an official India SKU (hard evidence, hand-verify before removing): Google Store India configurator (store.google.com/in/config/pixel_10_pro, Pixel 10 Pro XL selected, viewed 2026-09-30) shows storage 128GB Unavailable, 256GB Rs1,24,999 (out of stock - get notified), 512GB Unavailable, 1TB Unavailable. Flipkart lists the 10 Pro XL only in 256GB (Jade/Obsidian/Moonstone), Amazon.in only 256GB (117,999, MRP 124,999), Cashify and Cashkr price only the 256GB (their 512GB URLs render an empty page with no quote). 512GB units on OLX/ORU are therefore grey/import units. NEW=n/a for 512GB (official India 256GB = 124999; the DB's 139,999 is not an India price). If the entry is kept for grey-import walk-ins: OLX 2026-09-30 512GB asks n=5 (78,500 new-ish, 83,500, 85,000, 95,000 new-ish, 100,000; median 85,000, posted 5-15 days ago = after the Pixel 11 launch on 08-12) => sold-adj ~70-76k; official 256GB asks n=65, median 79,999, IQR 75,000-85,000 => sold-adj ~72k (the DB's 256GB 66,000 looks low). ORU: 512GB 66,050 (Apr, Like New, no box); 256GB 68,190-75,000 (Like New/Good, warranty) and 60,000 (Sep 30 Good, no warranty); 256GB sold-out 69,700 (Apr). Cashify refurb 256GB (upper bound): Best Value 78,699, Fair 82,699, Good 86,099, Superb 89,699; no 512GB price. Pixel 11 shipped 2026-08-12 (49 days) so the 10 Pro XL is outgoing. Import units carry no India warranty, so 72k sits below the 256GB-plus-step figure.", "buyback_market": null, "buyback_source": "No 512GB buyer quote on Cashify or Cashkr (the 512GB URLs render no price): Cashify 256GB 'Get Upto' 69,400, Cashkr 256GB 'up to' 72,000.", "confidence": "low"}, {"key": "vivo_x_fold5_16_512", "display_name": "Vivo X Fold5 16GB/512GB", "resale_price": 82000, "resale_low": 72000, "resale_high": 93000, "resale_sources": "NEW=159999 (Amazon.in MRP 1,59,999, street 1,39,999 for 16/512 Titanium Gray on 2026-09-30; India launch price 1,49,999; DB has no new price). OLX 2026-09-30 X Fold5 16/512 asks (a CN-import 42,000 ad and 'new condition' ads excluded): n=20, min 69,900, Q1 75,000, median 90,000, Q3 ~100,000, max 120,000. Honest-condition asks cluster 70-77k (69.9k Good, 73k x2, 75k x3, several noting crease/inner lines), mid 84-91k, optimistic 95-120k => sold-adj (-10%) median ~81k, low cluster ~66-70k. ORU carries no X Fold5 (only Fold3 / Fold3 Pro at 43-60k). Cashify refurb (upper bound, all out of stock): Best Value 87,099, Fair 91,599, Good 95,399, Superb 99,199. Both buyers' ceilings (78.5k and 80k) are consistent with dealer resale of ~85k+, so 82k is a balanced estimate. Foldables trade thinly.", "buyback_market": 78520, "buyback_source": "Cashify sell page ...used-vivo-x-fold-5-16-gb-512-gb 'Get Upto' 78,520 (top-condition ceiling, 2026-09-30). Cashkr Vivo X Fold 5 16GB/512GB 'up to' 80,000.", "confidence": "medium"}, {"key": "macbook_air_m4_13_2025_16_256", "display_name": "MacBook Air M4 13\" (2025) 16/256GB", "resale_price": 82000, "resale_low": 74000, "resale_high": 91000, "resale_sources": "NEW=99900 (Apple India launch price of the 13in M4 16GB/256GB, Mar 2025; education 89,900). Apple now sells only M5 Airs (13in 149,900; Amazon 138,990) and the MacBook Neo (79,900); Flipkart's remaining M4 24/512 is now 151,900 - the M4 is used-only and demand is firm. OLX 2026-09-30 13in M4 16/256: 87 ads incl. ~40 identical repeats by one dealer at 92,000 (counted once), bait ads at 37-39k and sealed 117.9k excluded. 31 individual asks: min 80,000, Q1 88,000, median 90,000, Q3 98,000, max 110,000 => sold-adj (-8..-12%) ~79-83k (Q1 79k, Q3 88k); dealer ask 92,000. Same pass: 13in M4 16/512 asks n=13, median 105,000. Cashify refurb 13in M4 16/256 (upper bound, stale, all out of stock): Fair 83,399, Good 88,399, Superb 92,399 (16/512: 89,499-99,599). Buyer ceilings: Cashkr 16/256 75,000 (16/512 85,000), Cashify series 70,000. Estimate 82k; the DB's 73,000 looks stale (the DB's M4 16/512 84,000 also sits below Cashkr's own 85,000 ceiling).", "buyback_market": 75000, "buyback_source": "Cashkr exact config: MacBook Air M4 13-inch 256GB/16GB 'You get up to' 75,000 (16/512 85,000). Cashify 'MacBook Air 2025' series page 'Get Upto' 70,000 (config-agnostic ceiling; exact quote is behind a phone-number login, not entered).", "confidence": "medium"}, {"key": "samsung_galaxy_tab_s11_ultra_wifi_256", "display_name": "Samsung Galaxy Tab S11 Ultra WiFi 256GB", "resale_price": 73000, "resale_low": 63000, "resale_high": 84000, "resale_sources": "NEW=135999 (Samsung India Tab S11/S11 Ultra buy-page banner 'Get at 130,999 (MRP 135,999) with 5,000 bank discount'; S11 Ultra Wi-Fi 12/256 PDP shows launch date Sept 4 2025; it is now delisted from the samsung.com/in tablet list). SUCCESSOR: Galaxy Tab S12 Ultra Wi-Fi 12/256 (SM-X940, MRP 149,999; 5G 164,999) shows launch date 2026-09-30 on samsung.com/in - every datapoint here predates that launch, so expect softening. OLX 2026-09-30 (only 3 Wi-Fi 256 asks; 5G/512GB ads excluded): 80,000 (10d, with S Pen), 90,000 (10d, Andheri), 95,000 (1d, dealer, 6 months warranty); 5G/512GB asks are 92,000-117,000 (brand-new/open-box 110,000). Sold-adj ~72-85k, median ~81k. Ratio check: verified DB resale to Cashify refurb is 0.64 for the S10 Ultra (50,000/77,999) and 0.74 for the S11 Wi-Fi 128 (51,000/68,599); Cashify refurb S11 Ultra Wi-Fi 256 (upper bound, out of stock) Best Value 100,899 => 65-75k. ORU has one S11 Ultra listing: 512GB Like New >9 months warranty ask 110,000 (Apr 30, unsold). Blended 73k (successor launching today, thin asks); low confidence.", "buyback_market": 66120, "buyback_source": "Cashify sell page ...used-samsung-galaxy-tab-s11-ultra-wi-fi-only-12-gb-256-gb 'Get Upto' 66,120 (ceiling; Wi-Fi 512GB 69,600; 5G 256GB 74,570). Cashkr lists only the S11 Ultra 5G: 256GB 'up to' 63,000.", "confidence": "low"}]}
const R = (() => {
const DIR = '/Users/shane/Documents/Claude/Projects/rt buyback tool'
const N = 12

const BRAIN = `RT (Rajdhani Telecom, Moradabad) BUYBACK BRAIN — how Shane actually prices:
- RESALE price = what RT can ACTUALLY re-sell a mint (A1) used unit for in the LOCAL Indian second-hand market. This is NOT Cashify's "buy refurbished" retail price for older phones — Cashify's refurb price includes their warranty + brand premium and is INFLATED vs what a local shop gets. Real resale for older/less-popular phones is BELOW Cashify refurb retail. For current hot phones (in demand) real resale is close to Cashify refurb retail. Triangulate from OLX recent SOLD (not asking) + local used-market + Cashify refurb (as an upper bound).
- BUYBACK-MARKET rate = what buyers currently PAY for the exact variant and condition. Store it for reference only; RT is not required to beat it. Shane deliberately pays less on slow older models. Public 'Get Upto' headlines are ceilings, not condition-specific offers; identify them explicitly and never fabricate a payout from a fraction of resale.
- RT computes A1 from real resale/(1+margin_by_age), with resale*0.92 and trusted-new*0.85 ceilings. Never raise resale or A1 merely to beat a competitor. Preserve existing authoritative net_new_inr; new-price research is contextual only for existing models.
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
        resale_price: { type: ['number', 'null'] },
        resale_low: { type: ['number', 'null'] },
        resale_high: { type: ['number', 'null'] },
        resale_sources: { type: 'string' },
        buyback_market: { type: ['number', 'null'] },
        buyback_source: { type: 'string' },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      },
      required: ['key', 'resale_price', 'buyback_market', 'resale_sources', 'buyback_source', 'confidence'],
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
        resale_final: { type: ['number', 'null'] },
        buyback_final: { type: ['number', 'null'] },
        resale_verdict: { type: 'string', enum: ['confirmed', 'corrected', 'rejected'] },
        buyback_verdict: { type: 'string', enum: ['confirmed', 'corrected', 'rejected'] },
        note: { type: 'string' },
        confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      },
      required: ['key', 'resale_final', 'buyback_final', 'resale_verdict', 'buyback_verdict', 'confidence'],
    } },
  },
  required: ['batch_index', 'models'],
}

function fetchPrompt(i) {
  return `You research the REAL Indian second-hand market for Rajdhani Telecom. TODAY is 2026-09-30.

${BRAIN}

Get your batch's phone keys + names:
  python3 -c "import json; d=json.load(open('${DIR}/phone_db.json')); ks=json.load(open('${DIR}/_ov_batches.json'))[${i}]; print({k:d[k]['display_name'] for k in ks})"

For EACH distinct model (storage variants share one lookup, then scale), find TWO numbers via web search/fetch:
  1) RESALE_PRICE = realistic price a LOCAL shop can re-sell a mint (excellent, with-box) used unit for TODAY in India.
     Triangulate: OLX recent listings (discount asking by ~8-12% for real sold), Cashify "buy refurbished" retail (UPPER bound — real local resale is 5-20% below this for older phones), 2gud/Amazon Renewed. Give resale_low, resale_high, and resale_price = your best single realistic figure.
  2) BUYBACK_MARKET = what sellers are actually PAID today, from a REAL sell/exchange quote flow only (never the 40%-template "Approx. Buyback Value" box on a price-in-india page): Cashify "sell old phone" / exchange value is the primary benchmark (web_search "Cashify <model> <storage> sell price" or fetch cashify.in/sell-old-mobile-phone/...). Note if other buyers differ.
Scale storage variants (256 > 128). Only report numbers you actually find; null if none.

CRITICAL — BRAND-NEW / THIN-MARKET MODELS: some entries are 2026 launches whose used market barely exists. For any model launched in the last ~6 months you MUST:
  (a) CONFIRM the model actually is ON SALE IN INDIA under that exact name and storage config. Only claim it does not exist if you have HARD evidence (brand India site lineup / major India outlet listing the real variants). A missing Cashify page or a thin OLX result is NOT evidence of non-existence — say 'unverified', not 'does not exist'. False 'does not exist' verdicts have repeatedly been wrong on this DB.
  (b) These are ALREADY HAND-VERIFIED REAL — never flag them as non-existent: Samsung Galaxy Z Fold8 / Z Fold8 Ultra / Z Flip8 (India 2026-07-22 — now 70 days old, so a used market EXISTS: do not return 80% of new without datapoints), Motorola Razr Fold and Motorola Signature (India 2026-05-13), Google Pixel 11 / 11 Pro / 11 Pro XL / 11 Pro Fold (India 2026-08-12 — now 49 days old: a used market EXISTS, and the DB's current Pixel 11 figures are exactly 80% of round-number new prices, i.e. placeholders — verify the OFFICIAL google store India price per storage and research used resale from datapoints), Redmi 17 5G (India 2026-09-03).
  (c) Find the OFFICIAL India launch price from the brand's own India site / mainstream India coverage, and report it in resale_sources as 'NEW=<num>'.
  (e) SUCCESSOR SHIPPED: iPhone 18 Pro / 18 Pro Max went ON SALE in India on 2026-09-18 (12 days ago), and the Galaxy S26 FE the same day. The iPhone 17 Pro / 17 Pro Max and the Galaxy S25 FE are now the OUTGOING generation, with ~2 weeks of post-launch used trading. Report the used resale you actually OBSERVE today (OLX listings posted AFTER 09-18 discounted to sold, local dealer/used-shop listings) — NOT Cashify "buy refurbished" retail (warranty-inflated) and NOT a figure from before 09-18. A just-superseded flagship softens; if your datapoints predate 09-18, say so in resale_sources. Price EACH storage on its own datapoints where they exist (the 17 Pro Max 2TB trades thinly — do not extrapolate it off the 1TB).
  (f) iPhone Air (2025): the DB's stored new prices for it look wrong. Get the OFFICIAL apple.com/in price for the EXACT storage (256GB / 512GB / 1TB) and report it as 'NEW=<num>'. Price each storage on its own datapoints — the Air has a thin, soft used market; do not scale off the 17 Pro.
  (g) PLACEHOLDER ANCHORS: many entries in this batch were originally priced at EXACTLY 80% of an unverified (often round-number) new price. Treat any existing DB value as UNRESEARCHED. Find the real used resale from scratch from actual datapoints (OLX sold-adjusted, local dealer listings, Cashify refurb as an upper bound) — never derive it as a fixed fraction of new, that is how the placeholder was made — and the OFFICIAL India new price (real India prices end in 999/990 — report it as 'NEW=<num>').
  (d) ONLY a phone first sold in India <30 days ago has genuinely no used market: there, and only there, resale may be ~78-85% of official new (say 'PLACEHOLDER' in resale_sources) and buyback_market null. From ~30 days on, used units trade — find real datapoints (OLX sold-adjusted, ORUphones, local dealers, Cashify refurb as the upper bound). Returning 78-85% of new for an older phone is the convention, not an observation, and on this DB it has overpaid every time it was checked (31 of 31 came down on 2026-09-21).

Write ${DIR}/_ov_updates/fetch_${i}.json AND return:
{"batch_index":${i},"models":[{"key":...,"display_name":...,"resale_price":<num|null>,"resale_low":<num|null>,"resale_high":<num|null>,"resale_sources":"<olx/cashify/... + numbers>","buyback_market":<num|null>,"buyback_source":"<cashify sell + number>","confidence":"high|medium|low"}, ...]}
Every key exactly once.`
}

function criticPrompt(i, fetchJson) {
  return `You are an adversarial MARKET-PRICE CRITIC for Rajdhani Telecom. TODAY is 2026-09-30. Assume the fetcher may have erred — catch it.

${BRAIN}

Fetcher output:
${JSON.stringify(fetchJson)}

For EACH model, independently sanity-check and CORRECT:
1. RESALE_FINAL: Is resale_price a REALISTIC local re-sale price (what a Moradabad shop actually gets), NOT (a) an OLX ASKING price (inflated ~10%), NOR (b) Cashify's warranty-inflated refurb-retail for an OLDER phone. For older/unpopular models pull it DOWN toward real used value. For current hot models it can sit near refurb retail.
2. BUYBACK_FINAL: Is it a real current Cashify/market buyback (what sellers get paid)?
3. EXISTENCE (2026 launches): does this exact model+storage actually ship in India? Reject ONLY on hard evidence (brand India site / major India outlet showing the real variant list). Thin OLX/Cashify coverage is NOT evidence — a brand-new phone legitimately has no used listings. If you cannot confirm either way, keep the prices and write 'unverified existence' in the note; do NOT write 'DOES NOT EXIST'. These are hand-verified REAL and must never be rejected: Samsung Z Fold8 / Fold8 Ultra / Flip8, Motorola Razr Fold, Motorola Signature, Google Pixel 11 / 11 Pro / 11 Pro XL / 11 Pro Fold, Redmi 17 5G. Report the official India NEW price in the note as 'NEW=<num>' when confirmed.
4. Hard sanity: RESALE_FINAL > BUYBACK_FINAL (a reseller must buy below resale). If violated, fix. Typical gap: buyback ≈ 55-80% of resale. If you have no real buyback datapoint, set buyback_final null — NEVER back into it as a round fraction of resale, and never echo the fetcher's number without a source.
5. OUTGOING GENERATION (iPhone 17 Pro / Pro Max, Galaxy S25 FE — successors on sale since 2026-09-18, 12 days): reject any resale taken from Cashify refurb retail or from listings dated before 09-18; the superseded model's local resale softens. Never raise resale to beat a competitor quote — the brain forbids back-solving resale from what Cashify pays.
6. UPWARD BIAS CHECK: OLX asking prices and Cashify refurb retail both run ABOVE what a Moradabad shop really gets. If resale_price looks like an asking price or a warranty-backed refurb price, pull it DOWN. Overpaying costs RT money on every unit; underpaying only loses one deal.
Set *_final to the correct value (yours if fetcher wrong -> 'corrected', theirs if right -> 'confirmed', null -> 'rejected').

Write ${DIR}/_ov_updates/verified_${i}.json AND return:
{"batch_index":${i},"models":[{"key":...,"resale_final":<num|null>,"buyback_final":<num|null>,"resale_verdict":"confirmed|corrected|rejected","buyback_verdict":"...","note":"<what & why + source>","confidence":"high|medium|low"}, ...]}
Every key exactly once.`
}


return { criticPrompt, CRITIC_SCHEMA }
})()
const G = (() => {
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
  return `You audit Rajdhani Telecom's used-phone DB for MISSING models. TODAY is 2026-09-30. Find India phones that SHOULD be in the DB but are MISSING. The DB was gap-audited on 2026-09-26 (prev run 2026-09-21), so the PRIMARY target is anything that launched or went on sale in India from 2026-09-24 onward (the last ~6 days, incl. Flipkart Big Billion Days / Amazon Great Indian Festival launch drops) — new launches, new storage/RAM variants of recent phones, and India availability of models announced earlier. SECONDARY: any notable 2025-2026 model still absent. Do not re-propose models already in the DB.

Get your unit scope + what's already in the DB:
  python3 -c "import json; u=json.load(open('${DIR}/_audit_units.json'))[${i}]; inv=json.load(open('${DIR}/_db_inventory.json')); print('SCOPE:',u[2]); [print('---',b,'MODELS:',inv.get(b,{}).get('models')) for b in u[1]]"

Web-research the India lineup for your scope with heavy emphasis on SEPTEMBER 2026 launches (GSMArena/91mobiles/Smartprix/official brand India sites; check 'launched in India September 2026' / 'launch date 2026' style queries). Diff against the MODELS already listed. A model is MISSING only if not already present (account for name variants).

ALREADY HANDLED ELSEWHERE — do NOT propose: Lava Virat Curve 5G, Oppo K14 Plus 5G, Redmi 17C 5G, iPhone Duo (a separate unit re-verifies these held models this week). Already in the DB (added 09-26): Redmi Note 17 Pro Max 5G, OnePlus N6 Lite, Realme 16 Pro 5G Harry Potter Edition, Lava Bold N4 Pro 5G, itel Zeno 300, Nothing Phone (3a) Lite, Oppo A6s 5G 4/128 + 6/128; and iPhone 18 Pro/Pro Max, Apple Watch S11/S12/SE 3/Ultra 3/Ultra 4, Galaxy S26 FE, Redmi Note 17 Pro, Vivo Y31t, Oppo K14 Lite. NEVER propose a model whose India FIRST SALE date is after 2026-09-30 — an announced-but-not-on-sale phone has no used market; if you see one, you may list it with its real first-sale date in launch_date so it is held.

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
  return `You verify HELD launches for Rajdhani Telecom's used-phone DB. TODAY is 2026-09-30.
On 2026-09-26 these models were HELD out of the DB because they were announced but NOT YET ON SALE in India (an unsold phone has no used market). Read them:
  python3 -c "import json; [print(h['key'],'|',h['name'],'| launch',h.get('launch_date'),'| first_sale',h.get('first_sale_date'),'| new',h.get('new_price_verified')) for h in json.load(open('${DIR}/_held_future_2026-09-26.json'))]"
Existing sibling entries already in the DB (for key naming + tier):
  python3 -c "import json; d=json.load(open('${DIR}/phone_db.json')); [print(k,d[k].get('tier'),d[k].get('display_name')) for k in d if k.startswith(('lava_virat','lava_bold','oppo_k14','oppo_k13','redmi_15c','redmi_14c','iphone_air','iphone_18'))]"

For EACH held key:
  1) Confirm whether it is NOW actually ON SALE in India (deliveries / open sale started) — give the real first-sale date as launch_date (YYYY-MM-DD). If first sale is still after 2026-09-30, put that future date in launch_date so it stays held.
  2) Confirm the OFFICIAL India new price for EACH real config (brand India store / major India retailer). Oppo K14 Plus and Redmi 17C had NO confirmed price on 09-26 — find their real India configs and prices now. List only configs you can see on sale (no phantom RAM/storage pairings); a held entry with no storage in its key (oppo_k14_plus, redmi_17c_5g) must be replaced by one entry per real config, keyed like the DB's siblings (e.g. oppo_k14_plus_5g_8_128, redmi_17c_5g_4_128).
  3) resale_price: these went on sale only days ago, so a real used market barely exists. If you find genuine used/sealed-resale listings (OLX, dealers), report the realistic mint-used figure. If not, you MAY use new x 0.80 and MUST write 'PLACEHOLDER 0.80' in source. buyback_market: a real Cashify sell-flow quote only, else null.
  4) Keep the held key names (except the storage split above); tier = the DB's existing tier for that series (Lava = D, Oppo K-series = C, Redmi C-series = D, iPhone = S).
Output every held key as an entry in "missing" (display_name from the held file). Skip nothing — if one is still not on sale, keep it with its future launch_date so the pipeline holds it again.

Write ${DIR}/_gaps/find_${i}.json AND return: {"unit_id":"held_carryforward","missing":[{...}]}.`
}
function criticPrompt(i, findJson) {
  return `Adversarial CRITIC for Rajdhani Telecom gap-audit. TODAY is 2026-09-30. A finder proposed missing India models with prices; independently VERIFY each.
Finder output:
${JSON.stringify(findJson)}

For EACH proposed model, web-check:
1. real_india_launch: Did this EXACT model actually launch/sell in India? Reject fakes, rumors, non-India variants, phantom storage configs.
2. new_price_final: correct official India new price (not MRP-inflated, not wrong variant). resale_price_final: realistic used resale (< new; ONLY for a phone first sold in India <30 days ago ≈ new×0.78-0.82; older phones must carry researched used value). buyback_market_final: real Cashify buyback or null.
3. Sanity: resale < new; buyback < resale (if present); storage ordering (256>128).
4. PHANTOM CHECK: reject any variant whose storage tier is paired with the wrong RAM for that line-up (big storage ships only with top RAM). Confirm the exact config on the brand's India store / a major India retailer.
5. ROUND-NUMBER CHECK: a new_price that is a round thousand (40000, 25000) is a fabrication signature — real India prices end in 999/990. Re-source it or null it.
6. FIRST SALE: launch_date must be the India FIRST-SALE date if sale started after the announcement. If a model is not yet on sale in India as of 2026-09-30, keep real_india_launch=true but correct launch_date to the future first-sale date (the pipeline holds it). For phones on sale <30 days, resale ~= new x0.78-0.82 is acceptable ONLY if marked as a placeholder; otherwise require real datapoints.
7. Do NOT reject a price merely for being far above its predecessor — 2026 India budget pricing genuinely stepped up. Verify on the brand's India store instead of assuming an MRP.
Set *_final to correct values (corrected if finder wrong, confirmed if right, rejected+real_india_launch=false if fake/unverifiable).

Write ${DIR}/_gaps/verified_${i}.json AND return: {"unit_id":"<name>","verified":[{...}]}. Every proposed key exactly once.`
}


return { findPrompt, criticPrompt, FIND_SCHEMA, CRITIC_SCHEMA }
})()
phase('Rerun')
const out = await parallel([
  () => agent(R.criticPrompt(3, FETCH3), { label: 'reprice-critic:3', phase: 'Rerun', schema: R.CRITIC_SCHEMA, model: 'sonnet', agentType: 'general-purpose' }),
  () => agent(G.findPrompt(0), { label: 'gap-find:0', phase: 'Rerun', schema: G.FIND_SCHEMA, model: 'sonnet', agentType: 'general-purpose' })
          .then(f => f ? agent(G.criticPrompt(0, f), { label: 'gap-critic:0', phase: 'Rerun', schema: G.CRITIC_SCHEMA, model: 'sonnet', agentType: 'general-purpose' }) : null),
])
const [rc, gc] = out
log(`reprice critic:3 -> ${rc ? (rc.models || []).length + ' models' : 'FAILED'}; gap unit 0 -> ${gc ? (gc.verified || []).length + ' verified' : 'FAILED'}`)
return { reprice_critic_3: rc ? (rc.models || []).length : null, gap_unit_0: gc ? (gc.verified || []).length : null }
