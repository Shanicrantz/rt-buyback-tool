# v6.41 Foxconn-grade batteries on older iPhones, 19 November 2026

**Live:** https://rt-buyback-tool.netlify.app serves v6.41 (Netlify deploy `6aff0bc7b35e5c5d6be6f2dc`, ready, production, published 2026-11-19 14:46 UTC). All seven live files were read back and match the published set.

**Shane's request:** v6.40 priced older iPhones' batteries at original grade, which put a typical deduction around ₹3,000. Asked whether to keep that or switch to Foxconn grade, Shane answered "Use Foxconn grade".

## What changed
- **Battery deductions:** on 47 variants of 15 older models, the battery deduction now uses the **Foxconn-grade** market rate plus ₹500 fitting.
  - **Models:** iPhone 6 / 6 Plus / 6s / 6s Plus, SE (2016), 7 / 7 Plus, 8 / 8 Plus, X / XR / XS / XS Max and 11 Pro / 11 Pro Max.
  - **Direction:** every one of them went down.
- **No other deduction changed** (`other_deductions_changed: 0`):
  - **Newer iPhones** (11, 12 onwards and the SE 2020 / 2022) keep original-grade batteries.
  - **Every other part** keeps original grade.
- **Hover text:** shows "Foxconn part + fitting" for these batteries.
- **New field:** each record keeps its old original-grade figure in `original_grade_inr`.

## Rule
- **Quote:** each seller's highest in-stock "Foxconn" battery listing for exactly that model, plus ₹500 fitting. This is the same assumption as in v6.39 and v6.40.
- **Rate:** the median across sellers, rounded up to ₹100.
- **Source:** only abest.in lists Foxconn iPhone batteries among the four sellers used, so every rate rests on that one seller.
- **iPhone XS:** abest.in shows its listed price (₹650) but marks the battery out of stock. That price is used and flagged in the record.
- **iPhone SE (2016):** abest.in sells it as "iPhone 5SE", the Indian trade name for the first SE. The page does not name the generation.

## Result (₹ deduction, same for every storage variant)
| Model | Original grade (v6.40) | Foxconn (v6.41) | Foxconn listing |
|---|---:|---:|---|
| iPhone 6 | ₹3,000 | **₹1,000** | abest.in ₹499 + ₹500 fitting |
| iPhone 6 Plus | ₹3,000 | **₹1,100** | abest.in ₹525 + ₹500 fitting |
| iPhone 6s | ₹3,000 | **₹1,000** | abest.in ₹499 + ₹500 fitting |
| iPhone 6s Plus | ₹3,000 | **₹1,100** | abest.in ₹525 + ₹500 fitting |
| iPhone SE (2016) | ₹2,100 | **₹1,100** | abest.in ₹550 + ₹500 fitting |
| iPhone 7 | ₹2,700 | **₹1,100** | abest.in ₹525 + ₹500 fitting |
| iPhone 7 Plus | ₹3,000 | **₹1,100** | abest.in ₹549 + ₹500 fitting |
| iPhone 8 | ₹2,900 | **₹1,100** | abest.in ₹549 + ₹500 fitting |
| iPhone 8 Plus | ₹3,000 | **₹1,200** | abest.in ₹625 + ₹500 fitting |
| iPhone X | ₹4,400 | **₹1,200** | abest.in ₹650 + ₹500 fitting |
| iPhone XR | ₹3,200 | **₹1,300** | abest.in ₹800 + ₹500 fitting |
| iPhone XS | ₹3,400 | **₹1,200** | abest.in ₹650 (out of stock) + ₹500 fitting |
| iPhone XS Max | ₹5,300 | **₹1,300** | abest.in ₹749 + ₹500 fitting |
| iPhone 11 Pro | ₹4,600 | **₹1,300** | abest.in ₹730 + ₹500 fitting |
| iPhone 11 Pro Max | ₹4,800 | **₹1,600** | abest.in ₹1,050 + ₹500 fitting |

The result sits close to the old percentage estimate from before v6.40. Example: XS Max ₹1,100 before v6.40, ₹5,300 at original grade, ₹1,300 now. It is still slightly higher on 46 of 47 variants. Per-variant figures for all three versions are in `deduction-changes.json`.

## Evidence
- **New pages:** the abest.in "5SE" and XS pages were re-read on 19 Nov 2026 and saved in `research/abest/`.
- **Earlier pages:** the other Foxconn pages come from the v6.39 evidence (`../2026-11-19-v6.39-apple-market-parts/research/abest/`), read the same day.

## Tests
All 12 JS suites pass on the candidate and on the installed files. `test_part_prices.cjs` checks:
- Older-iPhone batteries are Foxconn grade, cheaper than their original-grade rate, and carry ₹500 fitting.
- Every other market record stays original grade.
- The policy text names the rule.
