# v6.42 iPhone 17 front camera back on the estimate, 19 November 2026

**Live:** https://rt-buyback-tool.netlify.app serves v6.42 (Netlify deploy `6aff0d65d0c456424ff65a1e`, ready, production, published 2026-11-19 14:53 UTC). All seven live files were read back and match the published set.

**Shane's request:** v6.40 priced the iPhone 17 front camera from a single listing, appleproductsfix ₹21,500 + ₹500 fitting = ₹22,000. That looked like an Apple-serialised part, since the plain 17 Pro part costs ₹5,999. Asked whether to drop it, Shane answered "Yes, drop it".

## What changed
- **iPhone 17 front camera:** the market record is removed from both variants, so the deduction is back on the tier-% estimate.

  | Variant | Before | After |
  |---|---:|---:|
  | 256GB | ₹22,000 | ₹4,500 |
  | 512GB | ₹22,000 | ₹5,100 |

- **No other deduction changed** (`deduction-changes.json`, `other_changed: 0`).
- **Re-run guard:** the new field `_meta.part_price_market_exclusions` lists this pair.
  - The v6.40 market builder (`../2026-11-19-v6.40-iphone-market-parts/build_market.py`) now skips listed pairs.
  - The template README (Stage 3b) says to never re-price them.
  - `test_part_prices.cjs` checks that no excluded pair carries a market price and that the iPhone 17 front camera uses the percentage.

## Tests
All 12 JS suites pass on the candidate (`tests.log`) and on the installed files (`tests-installed.log`).
