# v6.39 iPhone market part prices, 19 November 2026

**Live:** https://rt-buyback-tool.netlify.app serves v6.39 (Netlify deploy `6afef5962ffd8daf427c469d`, ready, production, published 2026-11-19 13:11 UTC). All seven live files were read back and match the published set.

**Shane's request:** "parts ke rates apple ki jagah market ke laga do" (use market part rates instead of Apple's). His choices when asked:
- **Quality:** Original / OG, meaning a pulled or new original part. Copy, soft-OLED and other aftermarket parts are excluded.
- **Price:** with fitting (part + fitting).

## What changed
- **iPhone damage deductions:** 332 iPhone part prices now use the India market rate, across 90 catalogue variants and 28 models. They replace the Apple out-of-warranty service estimate that v6.37 saved.
- **Parts covered:** display, battery, back glass and rear camera, which are the four parts Apple's page listed.
- **Where Apple's estimate stays (66 part prices):**
  - **No original-grade market part listed yet:** iPhone 17e, 18 Pro, 18 Pro Max and Duo (all four parts), and the SE (2022) battery.
  - **Market price is higher than Apple's:** the 17 Pro and 17 Pro Max batteries (₹14,400 / ₹15,400 market against ₹12,900 Apple). Here Apple's service is the cheaper genuine option.
- **Engine (`index.html`):**
  - Damage buttons for these parts now say **"Market price"**.
  - The hover text shows part + fitting, each seller's price and the old Apple figure.
  - No-damage quotes are unchanged.
- **Other brands:** no Android brand price changed (`non_apple_rows_changed: 0` in `compare_market.cjs`).
- **Template:** `_refresh_template/parts/build_parts.py` now keeps `market: true` records, so a future Apple browser walk cannot overwrite them. The README has a new Stage 3b section.

## Rule
For each iPhone model and part:
1. **Collect listings.** From each seller, take the in-stock listings that are explicitly graded original ("Original", "100% Original", "Set Removed Original", "Pulled Original", "Genuine") for exactly that model. The seller's quote is its highest such listing.
   - **Excluded grades:** copy, OLED/GX/DD/HQ, Foxconn, "OEM grade", and any listing with no grade.
   - **Also excluded:** out-of-stock listings and shared-model titles.
   - **Back glass:** a glass-only listing is preferred over one that bundles the flash or wireless-charging module.
2. **Add fitting.**
   - **Display:** ₹500, as listed by iFonewala in Gaffar Market.
   - **Back glass:** ₹2,000, iFonewala's listed back-housing fitting. iFonewala's own all-in laser back-glass price for each series also counts as one quote.
   - **Battery and rear camera:** ₹500. **This is an assumption**, because no source lists fitting for these. It matches the display fitting.
3. **Rate:** the median of these all-in rates, rounded up to ₹100.
4. **Apple fallback:** Apple's estimate stays when there is no quote or the market rate is not below Apple's.

## Sources (all read 19 Nov 2026; raw pages saved gzipped in `research/*/html` locally, not committed; parsed rows with each page's sha256 prefix are committed)
| Seller | What | Pages | Rows file |
|---|---|---:|---|
| abest.in | "Set Removed Original" / "Original" displays, original rear cameras (part only) | 275 | `research/abest/abest-rows.json` |
| touchlcdbaba.com (S.S. Spare Parts) | "100% Original" display combos and batteries (part only) | 45 | `research/touchlcdbaba/touchlcdbaba-rows.json` |
| appleproductsfix.com | "Original" displays, batteries, back glass and main rear cameras (part only, sale price incl. tax) | 126 | `research/appleproductsfix/appleproductsfix-rows.json` |
| ifonewala.com (Gaffar Market, Delhi) | "Pulled Original" displays (14 Pro Max, 15 Pro Max), "Genuine" 14 Pro Max battery, ₹500 / ₹2,000 fitting, laser back-glass price for each series | 14 | `research/ifonewala/ifonewala-quotes.json` (hand-read, line refs) |

All pages were fetched with plain GET requests, the same pages a browser opens. Product lists came from each site's public sitemap. No site scripts were read.

## Result per model (₹, Apple → market, the deduction for every storage variant)
| Model | Display | Battery | Back glass | Rear camera |
|---|---|---|---|---|
| iPhone SE (2020) | 14,900 → **4,000** | 7,900 → **4,100** | — | — |
| iPhone SE (2022) | 14,900 → **4,000** | 7,900 (Apple kept) | — | — |
| iPhone 11 | 18,900 → **4,000** | 9,900 → **3,500** | — | — |
| iPhone 12 mini | 22,900 → **7,900** | 9,900 → **5,700** | 32,900 → **2,700** | 18,900 → **5,000** |
| iPhone 12 | 27,900 → **8,500** | 9,900 → **4,600** | 35,900 → **2,700** | 18,900 → **3,100** |
| iPhone 12 Pro | 27,900 → **11,000** | 9,900 → **4,600** | 47,900 → **2,700** | 21,900 → **7,100** |
| iPhone 12 Pro Max | 36,900 → **14,500** | 9,900 → **6,400** | 58,900 → **2,700** | 21,900 → **7,100** |
| iPhone 13 mini | 22,900 → **14,300** | 9,900 → **7,000** | 38,900 → **2,900** | 18,900 → **2,700** |
| iPhone 13 | 27,900 → **9,500** | 9,900 → **5,100** | 41,900 → **3,100** | 18,900 → **3,400** |
| iPhone 13 Pro | 27,900 → **13,000** | 9,900 → **5,700** | 53,900 → **3,000** | 21,900 → **9,300** |
| iPhone 13 Pro Max | 36,900 → **17,200** | 9,900 → **7,400** | 65,900 → **3,200** | 21,900 → **7,000** |
| iPhone 14 | 27,900 → **10,000** | 10,900 → **6,600** | 16,900 → **3,400** | 18,900 → **4,400** |
| iPhone 14 Plus | 36,900 → **16,500** | 10,900 → **6,600** | 16,900 → **3,400** | 18,900 → **5,000** |
| iPhone 14 Pro | 36,900 → **19,000** | 10,900 → **5,900** | 65,900 → **3,400** | 22,900 → **7,400** |
| iPhone 14 Pro Max | 42,900 → **20,000** | 10,900 → **5,000** | 72,900 → **3,400** | 22,900 → **6,200** |
| iPhone 15 | 27,900 → **15,300** | 10,900 → **6,400** | 16,900 → **4,000** | 18,900 → **6,300** |
| iPhone 15 Plus | 36,900 → **15,900** | 10,900 → **7,300** | 16,900 → **4,000** | 18,900 → **5,900** |
| iPhone 15 Pro | 36,900 → **22,300** | 10,900 → **8,100** | 16,900 → **3,900** | 22,900 → **7,400** |
| iPhone 15 Pro Max | 42,900 → **21,500** | 10,900 → **8,300** | 16,900 → **3,900** | 28,900 → **7,400** |
| iPhone 16e | 27,900 → **16,200** | 10,900 → **5,600** | 16,900 → **4,700** | 15,900 → **7,300** |
| iPhone 16 | 27,900 → **21,000** | 10,900 → **5,600** | 16,900 → **6,600** | 18,900 → **6,300** |
| iPhone 16 Plus | 36,900 → **19,000** | 10,900 → **7,100** | 16,900 → **7,000** | 18,900 → **6,800** |
| iPhone 16 Pro | 36,900 → **25,300** | 12,900 → **10,400** | 16,900 → **5,600** | 28,900 → **9,400** |
| iPhone 16 Pro Max | 42,900 → **29,000** | 12,900 → **8,700** | 16,900 → **6,000** | 28,900 → **9,400** |
| iPhone 17 | 36,900 → **28,300** | 10,900 → **7,700** | 16,900 → **4,800** | 18,900 → **8,300** |
| iPhone Air | 36,900 → **33,000** | 12,900 → **9,700** | 16,900 → **11,800** | 18,900 → **10,300** |
| iPhone 17 Pro | 36,900 → **35,000** | 12,900 (Apple kept) | 16,900 → **6,600** | 28,900 → **10,400** |
| iPhone 17 Pro Max | 42,900 → **36,000** | 12,900 (Apple kept) | 16,900 → **6,600** | 28,900 → **10,400** |
| iPhone 17e | 27,900 (Apple kept) | 10,900 (Apple kept) | 16,900 (Apple kept) | 15,900 (Apple kept) |
| iPhone 18 Pro | 36,900 (Apple kept) | 13,900 (Apple kept) | 16,900 (Apple kept) | 28,900 (Apple kept) |
| iPhone 18 Pro Max | 42,900 (Apple kept) | 13,900 (Apple kept) | 16,900 (Apple kept) | 28,900 (Apple kept) |
| iPhone Duo | 149,900 (Apple kept) | 24,900 (Apple kept) | 20,900 (Apple kept) | 26,900 (Apple kept) |

Full quotes per model and part are in `market-parts.json`, and per-variant before/after figures are in `deduction-changes.json`.

**Effect:** every changed deduction went down, and the average drop is ₹15,338. Median new ÷ old by part:

| Part | Ratio |
|---|---:|
| Display | 0.50 |
| Battery | 0.61 |
| Back glass | 0.23 |
| Rear camera | 0.32 |

The biggest falls are the 13/14 Pro back glass: Apple quoted ₹53,900–72,900 because it swaps the whole unit, while a market laser back-glass job costs ₹3,000–3,400. Damaged iPhones will therefore get **higher offers** than in v6.37.

## For Shane to check
1. **47 of the 103 market rates rest on one seller.** These are mostly batteries and rear cameras for the 12–17 series, which only appleproductsfix lists as "Original". Its battery prices are high next to the other sellers: for the 14 Pro Max, appleproductsfix asks ₹6,950 against iFonewala's genuine ₹1,990. These single-seller rates therefore lean conservative.
2. **Battery and camera fitting of ₹500 is assumed.** If your technician charges differently, it is one number in `build_market.py`.
3. **Some display rates come from two sellers who disagree.** The iPhone 13 mini gets ₹14,300 from appleproductsfix ₹18,600 and Touch LCD Baba ₹8,990.
4. **The newest models sit close to Apple.** The 17 Pro display is ₹35,000 against Apple's ₹36,900, because original 17-series parts are still scarce.

## Not covered
- **Older iPhones without saved Apple prices** (6 to XS Max, 11 Pro / 11 Pro Max): they still use the tier-percentage estimate. The saved pages hold market quotes for several of them; adding them is a one-line scope change if wanted.
- **Front camera, charging port and speaker** on all iPhones keep the percentage estimate, because Apple didn't list them.
- **iPads, Watches and Macs:** not changed.

## Tests
All 12 JS suites pass on the candidate (`tests.log`) and on the installed project files (`tests-installed.log`). `test_part_prices.cjs` gained three checks:
- Market records are iPhone-only, original grade, fitted, rounded, below Apple's price, and sourced.
- A model never mixes Apple and market prices for the same part across its storage variants.
- The policy text names the rule.

## Re-running
1. `bash fetch_abest.sh`. Re-fetch the touchlcdbaba and appleproductsfix pages from their `urls.txt` the same way, then re-read the iFonewala pages.
2. `python3 -I parse_abest.py research/abest/html research/abest/abest-rows.json`, and the same for the `parse_touchlcdbaba.py` / `parse_appleproductsfix.py` equivalents.
3. `python3 -I build_market.py`, then `python3 -I prepare_candidate.py` (copy `baseline/` first and update VERSION / cache names), then `node compare_market.cjs`.
