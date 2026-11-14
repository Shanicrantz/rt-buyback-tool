# v6.36 resale + new-launch refresh, 14 November 2026

**Live:** https://rt-buyback-tool.netlify.app serves v6.36 (Netlify deploy `6af88c0c3d20a1e7c657ea8e`, state ready, production, published 2026-11-14T16:28:02Z). All seven live files (index.html, phone_db.json, sw.js, manifest, three icons) were read back and match the published set byte for byte.

This run covers the two parts of the weekly refresh that v6.35 could not do this morning: used-resale estimates and the new-launch gap check. New prices were not researched again. The v6.35 rows observed earlier today were carried over unchanged, and the script asserts that each one matches the release.

## Counts

| | |
|---|---|
| Catalogue records | 2,484 (2,469 domestic + 15 International, which are derived, not researched) |
| Verified new cash prices | 566 (562 from v6.35 + 4 launches); 1,903 pending |
| **Fresh resale estimates dated today** | **11** (9 Cashify Superb + 2 other retailers) |
| Prior refs kept unchanged (Cashify exact page blocked, HTTP 403) | 67, expired and not used for automatic quotes |
| Prior refs moved to last-known (no in-stock exact grade found) | 16 |
| Fresh ask ignored (RAM-ambiguous legacy row) | 1 (OnePlus Nord CE 2 128GB) |
| Sold prices or competitor quotes claimed | 0 |
| Launches added | 4 |

### Fresh resale estimates (A1, retailer ask − 10%/15% allowance, rounded down to ₹100)
| Model | Ask | Estimate | Previous ref |
|---|---:|---:|---|
| iPhone 11 64GB | 18,299 | 16,400 | 16,300 (30 Oct) |
| iPhone 11 Pro 64GB | 24,599 | 22,100 | none |
| iPhone 17 Pro 256GB | 1,08,899 | 98,000 | none |
| iPhone 17e 256GB | 57,499 | 51,700 | none |
| Samsung Galaxy S21 FE 256GB | 24,299 | 21,800 | 21,500 (30 Oct) |
| Samsung Galaxy S26+ 256GB | 77,199 | 69,400 | 69,300 (4 Nov) |
| OnePlus Nord CE 2 Lite 128GB (C, 15%) | 12,899 | 10,900 | none |
| Oppo Reno 15 Pro 5G 12/256GB | 55,899 | 50,300 | 49,900 (30 Oct) |
| Vivo X300 Ultra 16/512GB | 1,32,099 | 1,18,800 | none |
| Samsung Galaxy S25 256GB (Mobirapid, ask incl. 18% GST) | 59,000 | 53,100 | 53,100 (4 Nov) |
| Vivo X60 Pro+ 12/256GB (GudFast Superb) | 39,999 | 35,900 | 35,900 (4 Nov) |

Moved to last-known: iPhone 12 mini 128, 13 mini 128, 14 Pro 1TB, 17 Pro Max 512 and 2TB, S22 Ultra 512, S23 128, S24 Ultra 512, S25 Ultra 1TB, A56 8/128, Pixel 10 Pro XL 256, Vivo X300 Pro 16/512, Oppo F33 8/256, Reno 15 Pro 12/512, Mi 11X 128, Nord 5 12/512. None of these changes a quote, because the engine ignores any ref older than 10 days.

## Quote effect
- **No-age quick quotes:** 9 changed, all inside the +8% rise pin. Seven went up: iPhone 17e 256 44,900 → 47,000 (+4.7%), Nord CE 2 Lite 8,400 → 8,700, iPhone 11 Pro 64 16,100 → 16,500, S21 FE 256 17,900 → 18,100, X300 Ultra 1,07,400 → 1,08,000, Reno 15 Pro 12/256 45,400 → 45,700, iPhone 11 64 12,500 → 12,600. S26+ 256 went 63,000 → 63,100, and iPhone 17 Pro 256 went down, 89,800 → 89,100.
- **Quote safety:** 0 pinned rises, 0 drop-band flags, 0 counter blocks, 0 numeric inversions. Caps went from 88 to 89: iPhone 11 Pro 64 got a sibling-ordering cap at raw ₹16,599, and its quote of 16,500 sits under it.
- **Age quotes at each model's launch age:** 12 changed, all up. Four are the new launches, which now quote once an age is entered (for example, Find X10 12/256 at 1 month: ₹1,16,600). The other eight are the resale rows above, with small changes.

## New launches (first sale after the last add)
Added from exact in-stock new listings fetched today, each with a hashed first-sale receipt. Tier follows the series already in the DB. They carry no resale and have `price_reference_pending` set, like the v6.30 Vivo adds.

| Key | First sale | Tier | Current new cash | Source |
|---|---|---|---:|---|
| Oppo Find X10 12/256GB | 29 Oct | A | 1,39,999 | Reliance Digital (Flipkart same) |
| Oppo Find X10 12/512GB | 29 Oct | A | 1,69,999 | Reliance Digital |
| Oppo Find X10 Pro Max 12/512GB | 29 Oct | A | 1,99,999 | Reliance Digital |
| Infinix GT 50 Pro 12/256GB | 30 Oct | C | 70,298 (69,999 + ₹299 fee) | Flipkart |

Sale dates come from TechEnclave ("Sales begin on 29 October"), the OPPO India store terms (22 Oct launch livestream) and GSMArena ("Official sales are set to begin on October 30"). Reliance demo-unit listings were excluded.

`test_market_refresh.cjs` lists every catalogue addition by key, as v6.30 did for the Vivo adds, so it gained a block for these four keys.

## Held for Shane
1. **Cashify blocks exact variant pages.** The family pages loaded (962 HTTP 200), but all 161 exact-variant fetches returned 403, as on 4 Nov. Only each family page's own selected product could be verified. Sibling data from the family page (ProductGroup) is still not trusted. I did not try other user-agents or browser scraping to get past the block. To get more of the 67 back, choose either a browser check of the top-value models with your approval, or a second resale source.
2. **Infinix GT 50 Pro at ₹69,999 is real** (Flipkart in stock, launch press agrees) but far above earlier Infinix GT prices. As a C-tier phone at 1 month, the age formula gives ₹58,500. Please verify at the counter.
3. **Not added:**
   - Karbonn Rebel / Rebel Pro: 4G, sold only on Amazon.in (off-limits to scripted checks), and a brand new to the catalogue.
   - Tecno Spark 50s 5G: first sale 21 Nov, in the future.
   - Motorola Signature 27, Vivo X500 series, iQOO 16: no India sale yet.
4. **Gaps found before the window (not added, for the next gap audit):**
   - Samsung Galaxy F70 5G 4/128 and 6/128: sale 20 Oct, ₹19,999 / ₹22,999.
   - Samsung Galaxy A08 4G 4/64: 1 Oct, ₹18,499; the reported M08 and F08 siblings too.
   - Oppo K14 Plus: held on 26 Sep, still missing.

## Tests
- All 11 JS suites pass, both on the candidate (`tests.log`) and again on the installed project files. `test_market_collectors.py` and `test_nonphone_collectors.py` pass too.
- `test_quote_safety_solver.py` was not run. It is the known `/Volumes/my1tb`-hard-wired suite that v6.35 reported.

## Tooling recovered
The v6.30 resale scripts on the 1TB drive are gone. The resale steps were rebuilt from the v6.26 copies on the Mac (18 Oct) plus the v6.30 changes, recovered from the 4 Nov Codex guardian transcript:
- `verify_resale.py`
- `augment_selected_resale.py`
- `check_special_sources.py` (now limited to GudFast and Mobirapid)
- `prepare_resale.py`, which carries the v6.26 logic plus v6.30's rule to keep the prior ref when the exact page is 403-blocked
- `probe_launches.py`

`finalize.sh`, `compare.cjs` and `compare_age.cjs` come from v6.35. `compare_age.cjs` now treats a key missing from the baseline as having no prior quote.

**Run order:**
1. `_market_refresh_runner.py init --work <dir>`
2. `_market_refresh_runner.py resale --work <dir>` (~15 min)
3. `verify_resale.py`
4. `augment_selected_resale.py`
5. `check_special_sources.py`
6. `probe_launches.py` (edit `SPECS`)
7. `prepare_resale.py <ver>`
8. `finalize.sh`

`prepare_resale.py` expects that same day's new-price `observations.json`.
