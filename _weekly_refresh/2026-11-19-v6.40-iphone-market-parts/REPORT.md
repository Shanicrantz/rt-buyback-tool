# v6.40 iPhone market part prices, second pass, 19 November 2026

**Live:** https://rt-buyback-tool.netlify.app serves v6.40 (Netlify deploy `6aff09a799384a8814238c6e`, ready, production, published 2026-11-19 14:37 UTC). All seven live files were read back and match the published set.

**Shane's request:** after v6.39 replaced Apple's part prices with market rates, he was asked whether to add market rates for the older iPhones and the other parts too, and answered "Yes, add those". The rule is the same as in v6.39: an Original / OG part plus fitting.

## What changed
- **New prices:** 460 iPhone part prices on 134 catalogue variants of 42 models moved from the tier-percentage estimate to an India market rate.
  - **Older iPhones:** 6 → XS Max, SE (2016), 11 Pro / Pro Max, all parts a seller lists. Back glass and rear camera are also added on the iPhone 11, and the back on the SE (2020).
  - **Every iPhone from 8 Plus to 17 Pro Max and Air:** front camera, charging port and speaker.
- **v6.39 prices are unchanged** (`existing_records_changed: 0`). Apple's kept estimates (17e, 18 Pro / Pro Max, Duo and the batteries listed in v6.39) are also untouched.
- **58 model-parts still use the percentage**, because no seller lists an original-grade part for them:
  - 17e, 18 Pro / Pro Max and Duo: front camera, charging and speaker.
  - Air: charging and speaker.
  - iPhone 6 / 6 Plus / 6s / 6s Plus / 7 / 7 Plus / 8 and SE (2016 / 2020 / 2022): most cameras, charging and speaker, where only ungraded parts are listed.
  - The 6 Plus, 6s and 6s Plus displays.
- **Engine:** the hover text leaves out the "Apple service" figure when there is none. Nothing else changed.

## Rule (v6.39 rule, extended)
- **Quote per seller:** the highest in-stock listing explicitly graded original for exactly that model. The median of (part + fitting) across sellers is rounded up to ₹100.
- **Fitting:**
  - **Display:** ₹500, as listed by iFonewala.
  - **Back glass / back cover / housing:** ₹2,000, as listed by iFonewala.
  - **Battery, cameras, charging port and speaker:** ₹500 (assumed).
- **Back:** the plain back-cover listing is preferred. A cover bundled with the flash or wireless-charging module comes next. A full body housing is used only when the seller lists no cover, as on the SE (2016) and SE (2020).
- **Speaker** ("Speaker / mic bad"): the higher of the plain ear speaker and the loudspeaker. A speaker with a Face ID or proximity sensor flex is used only if nothing plain is listed.
- **Front camera:** the plain original part is preferred over Apple-serialised "Support Repair Assistant" parts (₹19,000–24,000).
- **Charging port:** the port flex only, never the wireless / NFC / power flex.
- **Excluded:** ungraded, copy / GX / OLED, Foxconn and "OEM grade", shared-model ("12/12 Pro", "XS to 15 Pro") and out-of-stock listings.

## Sources
- **New in this pass:** 218 more appleproductsfix.com pages, saved in `research/appleproductsfix/`, covering front cameras, charging flexes, ear and loud speakers, and older-model displays, batteries, backs and cameras.
- **Reused from v6.39:** the abest.in, touchlcdbaba.com and iFonewala evidence, from `../2026-11-19-v6.39-apple-market-parts/research/`.
- **How fetched:** plain page requests from each site's public sitemap, all read on 19 Nov 2026.

## Result per model (₹; old %-estimate across storage variants → market; `·` = already priced in v6.39, `% kept` = no original-grade listing)
| Model | Display | Battery | Back | Rear cam | Front cam | Charging | Speaker |
|---|---|---|---|---|---|---|---|
| iPhone 6 | 1,600–2,200 → **2,200** | 400–500 → **3,000** | 500–700 → **3,900** | % kept | % kept | % kept | % kept |
| iPhone 6 Plus | % kept | 400–600 → **3,000** | 600–900 → **3,900** | % kept | % kept | % kept | % kept |
| iPhone 6s | % kept | 400–500 → **3,000** | 600–800 → **3,900** | % kept | % kept | % kept | % kept |
| iPhone 6s Plus | % kept | 400–600 → **3,000** | 600–900 → **3,900** | % kept | % kept | % kept | % kept |
| iPhone SE (2016) | 1,300–1,800 → **2,700** | 300–400 → **2,100** | 400–600 → **4,300** | % kept | % kept | % kept | % kept |
| iPhone 7 | 1,000–1,300 → **3,200** | 200–300 → **2,700** | 300–400 → **3,900** | % kept | % kept | % kept | % kept |
| iPhone 7 Plus | 1,800–2,300 → **3,700** | 400–500 → **3,000** | 600–700 → **3,900** | % kept | % kept | % kept | % kept |
| iPhone 8 | 2,000–2,200 → **2,700** | 500 → **2,900** | 600–700 → **2,900** | % kept | % kept | % kept | % kept |
| iPhone 8 Plus | 2,600–2,900 → **2,300** | 600–700 → **3,000** | 800–900 → **2,900** | 1,200–1,300 → **2,700** | 600–700 → **1,400** | 500 → **1,500** | 300–400 → **1,400** |
| iPhone X | 3,600–4,100 → **7,300** | 800–900 → **4,400** | 1,200–1,300 → **2,900** | 1,700–1,900 → **2,300** | 800–900 → **1,400** | 700 → **1,500** | 500–600 → **1,400** |
| iPhone XR | 3,200–3,700 → **3,500** | 700–800 → **3,200** | 1,000–1,200 → **2,900** | 1,500–1,700 → **2,400** | 700–800 → **1,900** | 600–700 → **1,500** | 400–500 → **1,400** |
| iPhone XS | 4,100–4,800 → **7,300** | 900–1,100 → **3,400** | 1,300–1,500 → **2,900** | 1,900–2,200 → **3,400** | 900–1,100 → **2,000** | 700–900 → **1,500** | 600–700 → **1,600** |
| iPhone XS Max | 4,700–5,400 → **8,100** | 1,100–1,200 → **5,300** | 1,500–1,700 → **2,900** | 2,100–2,500 → **3,400** | 1,100–1,200 → **2,000** | 800–1,000 → **1,300** | 600–700 → **1,800** |
| iPhone SE (2020) | · | · | 900–1,200 → **4,000** | % kept | % kept | % kept | % kept |
| iPhone SE (2022) | · | · | % kept | % kept | % kept | % kept | % kept |
| iPhone 11 | · | · | 1,200–1,600 → **2,500** | 1,800–2,400 → **2,300** | 900–1,200 → **2,000** | 700–900 → **1,800** | 500–700 → **1,400** |
| iPhone 11 Pro | 4,200–5,600 → **8,500** | 1,000–1,300 → **4,600** | 1,300–1,800 → **2,900** | 1,900–2,600 → **4,500** | 1,000–1,300 → **1,600** | 800–1,000 → **3,300** | 600–800 → **1,700** |
| iPhone 11 Pro Max | 4,800–6,300 → **9,100** | 1,100–1,400 → **4,800** | 1,500–2,000 → **2,900** | 2,200–2,900 → **4,500** | 1,100–1,400 → **1,600** | 900–1,100 → **3,500** | 700–900 → **1,500** |
| iPhone 12 mini | · | · | · | · | 900–1,200 → **1,800** | 700–900 → **1,600** | 500–700 → **1,400** |
| iPhone 12 | · | · | · | · | 1,000–1,300 → **2,400** | 800–1,000 → **2,400** | 600–800 → **1,400** |
| iPhone 12 Pro | · | · | · | · | 1,500–5,500 → **2,400** | 1,200–4,400 → **2,400** | 900–3,300 → **1,400** |
| iPhone 12 Pro Max | · | · | · | · | 1,600–2,000 → **2,300** | 1,200–1,600 → **2,300** | 900–1,200 → **1,900** |
| iPhone 13 mini | · | · | · | · | 1,200–1,600 → **2,300** | 900–1,200 → **2,800** | 700–900 → **1,600** |
| iPhone 13 | · | · | · | · | 1,600–2,500 → **2,500** | 1,200–2,000 → **1,800** | 900–1,500 → **2,000** |
| iPhone 13 Pro | · | · | · | · | 2,100–2,900 → **3,500** | 1,600–2,300 → **2,500** | 1,200–1,700 → **2,000** |
| iPhone 13 Pro Max | · | · | · | · | 2,300–3,100 → **3,300** | 1,800–2,500 → **3,500** | 1,400–1,900 → **2,000** |
| iPhone 14 | · | · | · | · | 2,700–4,100 → **3,300** | 2,200–3,300 → **2,400** | 1,600–2,500 → **1,800** |
| iPhone 14 Plus | · | · | · | · | 1,800–2,300 → **3,600** | 1,400–1,900 → **3,300** | 1,100–1,400 → **2,300** |
| iPhone 14 Pro | · | · | · | · | 2,800–3,700 → **3,300** | 2,200–3,000 → **4,900** | 1,700–2,200 → **3,400** |
| iPhone 14 Pro Max | · | · | · | · | 3,100–4,100 → **3,700** | 2,500–3,200 → **3,300** | 1,900–2,400 → **3,400** |
| iPhone 15 | · | · | · | · | 3,000–4,400 → **3,300** | 2,400–3,600 → **4,000** | 1,800–2,700 → **2,300** |
| iPhone 15 Plus | · | · | · | · | 3,500–4,700 → **3,900** | 2,800–3,800 → **6,000** | 2,100–2,800 → **2,300** |
| iPhone 15 Pro | · | · | · | · | 4,100–6,100 → **4,300** | 3,300–4,800 → **4,000** | 2,500–3,600 → **1,600** |
| iPhone 15 Pro Max | · | · | · | · | 3,700–10,000 → **4,000** | 2,900–8,000 → **5,100** | 2,200–6,000 → **2,000** |
| iPhone 16e | · | · | · | · | 3,000–3,900 → **4,300** | 2,400–3,100 → **4,500** | 1,800–2,300 → **2,300** |
| iPhone 16 | · | · | · | · | 3,500–4,800 → **4,300** | 2,800–3,900 → **4,500** | 2,100–2,900 → **3,200** |
| iPhone 16 Plus | · | · | · | · | 4,000–5,100 → **5,100** | 3,200–4,100 → **7,000** | 2,400–3,100 → **3,200** |
| iPhone 16 Pro | · | · | · | · | 4,000–5,200 → **5,000** | 3,200–4,100 → **5,800** | 2,400–3,100 → **2,300** |
| iPhone 16 Pro Max | · | · | · | · | 6,000–7,000 → **7,400** | 4,800–5,600 → **7,100** | 3,600–4,200 → **2,300** |
| iPhone 17 | · | · | · | · | 4,500–5,100 → **22,000** | 3,600–4,100 → **7,500** | 2,700–3,100 → **4,900** |
| iPhone Air | · | · | · | · | 4,700–8,000 → **6,800** | % kept | % kept |
| iPhone 17 Pro | · | · | · | · | 6,400–8,600 → **6,500** | 5,100–6,900 → **8,800** | 3,800–5,100 → **2,700** |
| iPhone 17 Pro Max | · | · | · | · | 7,000–11,200 → **6,500** | 5,600–9,000 → **8,900** | 4,200–6,700 → **2,800** |
| iPhone 17e | · | · | · | · | % kept | % kept | % kept |
| iPhone 18 Pro | · | · | · | · | % kept | % kept | % kept |
| iPhone 18 Pro Max | · | · | · | · | % kept | % kept | % kept |
| iPhone Duo | · | · | · | · | % kept | % kept | % kept |

## Effect: this pass mostly RAISES deductions
Unlike v6.39, where market prices were lower than Apple's, these parts replace a percentage estimate. That estimate was a small share of a low current price on older phones, so original parts plus fitting usually cost more. Of 460 deductions, **391 go up and 63 go down**, and 6 are unchanged. Damaged older iPhones will get **lower offers**, which is the conservative direction.

| Part | Variants | Median before | Median after |
|---|---:|---:|---:|
| Display | 35 | ₹2,900 | ₹3,500 |
| Battery | 47 | ₹500 | ₹3,000 |
| Back | 53 | ₹800 | ₹3,900 |
| Rear camera | 22 | ₹2,100 | ₹3,400 |
| Front camera | 103 | ₹3,000 | ₹3,300 |
| Charging port | 100 | ₹2,300 | ₹3,300 |
| Speaker | 100 | ₹1,700 | ₹2,000 |

Examples:
- **iPhone 7 32GB:** battery ₹200 → ₹2,700 and back ₹300 → ₹3,900. On a phone this old, an original-part repair can cost more than the phone is worth.
- **iPhone XS Max 64GB:** battery ₹1,100 → ₹5,300.

## For Shane to check
1. **Do you want original-part prices on very old iPhones?** The shop market fits Foxconn or aftermarket batteries in these, and those cost about ₹500–1,100 plus fitting. If you'd rather use that grade for older models, or keep the percentage wherever the market is higher, either is a small rule change.
2. **The iPhone 17 front camera is ₹22,000.** It is the only listing (appleproductsfix, ₹21,500), and it is probably an Apple-serialised part even though its title doesn't say so. The 17 Pro is ₹6,500. This raises the deduction from about ₹4,500 to ₹22,000.
3. **130 of the 149 model-part rates rest on one seller**, mostly appleproductsfix, whose prices run high.
4. **Fitting of ₹500 is assumed** for battery, cameras, charging port and speaker.

## Tests
All 12 JS suites pass on the candidate (`tests.log`) and on the installed files (`tests-installed.log`). `test_part_prices.cjs` changes:
- A market record without an Apple price is allowed.
- A spot-check confirms coverage for older models and the extra parts.
- At least 700 market records must exist (792 now).

## Re-running
1. Re-fetch the appleproductsfix pages from `research/appleproductsfix/urls.txt` (plus the v6.39 lists).
2. `python3 -I parse_appleproductsfix.py research/appleproductsfix/html research/appleproductsfix/appleproductsfix-rows.json`
3. `python3 -I build_market.py`, then `python3 -I prepare_candidate.py` (fresh `baseline/`, with VERSION / cache names updated), then `node compare_market.cjs`.
