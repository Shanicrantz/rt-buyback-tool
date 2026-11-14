# v6.37 official spare-part prices, 14 November 2026

**Live:** https://rt-buyback-tool.netlify.app serves v6.37 (Netlify deploy `6af8a0ea5723bc359c8b363e`, ready, production). All seven live files were read back and match the published set.

**Shane's request:** "Parts ke price brands ke website se le kar dalo" (take part prices from the brands' websites and put them in).

## What changed
Damage deductions now use the brand's own India out-of-warranty spare-part price for that exact model wherever the brand lists the part. Before this, every deduction was a tier percentage of the new price (for example, display = 22% for S tier). Parts a brand does not list keep that percentage.

- **Engine (`index.html`):**
  - `partCost()` uses the saved `part_prices[key].amount_inr`, rounded up to ₹100.
  - Each damage button shows "<Brand> price". Hovering shows the source, date, part and labour.
  - No-damage quotes are unchanged.
- **DB:** 1,362 phone variants carry a `part_prices` record per part. Each record has the amount, part and labour split, brand model name, source URL, observation time and evidence.
- **New suite `test_part_prices.cjs`** checks that:
  - the official price wins and is rounded up;
  - a missing or invalid price falls back to the percentage;
  - every record has a source, date, brand and part + labour total;
  - International rows have no part prices;
  - no part costs more than 1.5× the phone's new price.

## Sources (all read 14 Nov 2026)
| Brand | Page | Models read | Catalogue variants priced | Basis |
|---|---|---:|---:|---|
| OnePlus | service.oneplus.com/in/spare-parts-price | 38 | 78 | part incl. 18% GST + listed labour |
| OPPO | support.oppo.com/in/spare-parts-price | 139 | 177 | part incl. 18% GST + listed labour |
| vivo | vivo.com/in/support/accessory | 231 | 236 | MRP incl. all taxes; labour not listed |
| Samsung | samsung.com/in/support/spare-part-pricing-list-for-repair/ | 134 phones | 238 | listed ex-GST, 18% GST added; labour excluded |
| realme | realme.com/in/support/spare-parts-price | 181 | 273 | incl. GST; service charge extra |
| Xiaomi/Redmi/Poco | mi.com/in/support/spare-part-prices/ | 165 | 256 | as listed |
| Apple | support.apple.com/en-in/iphone/repair | 32 | 104 | Apple out-of-warranty service estimate ("may be subject to tax") |

**Evidence:**
- **OnePlus, OPPO, vivo:** each model's price response is saved gzipped in `research/` with its sha256. These are the same requests the brand page makes when a model is opened. Model lists came from what the pages loaded: OnePlus and OPPO from the browser, vivo from the saved page HTML.
- **Samsung:** all models are embedded in the page, so the price data is parsed from one saved, hashed snapshot.
- **realme, Xiaomi, Apple:** prices load only in the browser, so they were read there. Each model was checked against its own detail page. Mapped regular prices (not offer prices) and a fingerprint of the full list are stored in `*_rows.txt` / `*-browser.json`.

**Which price is used for each part:**
- **Display:** the highest screen price listed, so foldables use the inner screen. On Samsung, the full "Main Screen Assembly" wins over the cheaper "Screen Component Repair" where both exist.
- **Back panel:** back cover / back glass.
- **Battery:** battery.
- **Rear camera:** the highest-priced rear camera.
- **Front camera:** front camera.
- **Charging port:** USB sub-board.
- **Speaker:** speaker.

## Effect on deductions (`deduction-changes.json`, at each variant's current new price)
| Part | Priced | Higher | Lower | Median new ÷ old |
|---|---:|---:|---:|---:|
| Display | 1,351 | 1,167 | 174 | 1.81× |
| Battery | 1,310 | 1,049 | 221 | 1.68× |
| Back panel | 1,336 | 986 | 299 | 1.67× |
| Rear camera | 1,038 | 809 | 199 | 1.99× |
| Front camera | 948 | 645 | 246 | 1.59× |
| Charging port | 464 | 263 | 138 | 1.25× |
| Speaker | 410 | 93 | 232 | 0.75× |

Official prices mostly **raise** deductions, so damaged phones get lower offers. This is the conservative direction. Foldable inner screens rise the most (e.g. Z Fold4 display ₹10,900 → ₹54,800; OnePlus Open ₹14,500 → ₹79,400).

## For Shane to review
1. **13 display deductions fall below half the old estimate.** These are the official prices, so I used them as listed:

   | Model | Old | New |
   |---|---:|---:|
   | Galaxy S26 Ultra 1TB | 44,000 | 19,900 |
   | Galaxy S25 Ultra 1TB | 36,600 | 18,100 |
   | Galaxy S26+ 512 | 28,600 | 13,900 |
   | Galaxy S25 512 | 23,100 | 8,800 |
   | Galaxy S26 512 | 22,100 | 9,700 |
   | Galaxy S25 FE 512 | 15,600 | 6,600 |
   | Galaxy S23 FE 256 | 15,100 | 6,300 |
   | Galaxy S26 FE 256 | 14,600 | 5,900 |
   | Galaxy S23 FE 128 | 14,100 | 6,300 |
   | Galaxy A57 12/256 | 12,700 | 5,900 |
   | Vivo T5 Lite 6/256 | 4,300 | 2,000 |
   | Redmi Note 9 128 | 2,700 | 1,200 |
   | Redmi 9 Power 64 | 2,300 | 1,000 |

   Samsung's page says its prices exclude labour and are for the premium colour and top storage. If you'd rather never let an official price fall below the old estimate, that's a one-line change in `partCost`.
2. **Xiaomi lists some very low prices on older models** (e.g. Mi 10i battery ₹399, Redmi Go display ₹699). They are used as listed.
3. **Labour is included only where the brand lists it** (OnePlus, OPPO, Apple). For vivo, Samsung, realme and Xiaomi the deduction is the part price alone.

## Not covered
- **Brands with no official India price page found or read:** Motorola, Google, Nokia/HMD, Infinix/Tecno/itel (Carlcare), Lava, Nothing, iQOO, Honor, Asus. Their deductions keep the percentage.
- **Brand models not matched (183):**
  - 143 have no catalogue family; mostly older phones the catalogue doesn't carry.
  - 26 have no listed parts.
  - 14 are ambiguous 4G/5G names, left unmatched on purpose. A brand page's unlabelled name is never attached to the wrong network edition.
  - Unmatched names are listed in `parts-match-report.json`.
- **Tablets, watches and audio:** not changed.

## Process notes
- **Blocked requests:** the auto-mode classifier refused reading OPPO's site scripts to find data endpoints. After that, only data the pages themselves load was used.
- **Discarded Samsung read:** a first browser read of Samsung mislabelled prices (it read the panel before it refreshed). It was thrown away in favour of the embedded page data.
- **Deploy:** the first deploy accidentally included a progress-log file (`deploy.log`). It held no secrets and was removed by an immediate seven-file redeploy; it now returns 404.

## Tests
All 12 JS suites pass, both on the candidate (`tests.log`) and on the installed project files: the 11 existing ones plus `test_part_prices.cjs`.

## Re-running
1. `collect_oneplus.py`, `collect_oppo.py` and `collect_vivo.py` re-fetch prices with plain requests. Model lists come from `oneplus_models.txt`, `oppo_codes.txt` and the vivo page; new models need adding to the first two lists.
2. `parse_samsung.py` reads the saved Samsung page.
3. realme, Xiaomi and Apple need the browser walk; see the session for the loop.
4. `prepare_parts.py` then builds the candidate, and `compare_parts.cjs` reports deduction changes.
