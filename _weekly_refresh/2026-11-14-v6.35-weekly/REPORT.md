# v6.35 weekly refresh, 14 November 2026

**Live:** https://rt-buyback-tool.netlify.app serves v6.35 (Netlify deploy `6af887a5c18bb2f13091d0bd`, state ready, production). Live index.html, phone_db.json, sw.js, manifest and icon hashes match the published set.

## Why this run mattered
Saved new prices expire after 7 days. Every price from the 6 Nov refresh had expired by 13 Nov, so the live tool's actual-age quotes were falling back to the higher saved-resale rate. Fresh prices put them back on the v6.34 age-scaled formula.

## What was checked
All 2,465 domestic variants (15 International rows keep their sibling derivation): Flipkart exact product pages, the Reliance Digital product sitemap, category-specific nonphone offers, and every listing saved on 6 Nov.

| | |
|---|---|
| Verified in-stock new cash prices | 562 (was 568) |
| Pending (mostly no longer sold new) | 1,903 |
| Prices changed | 130 (95 up, 35 down) |
| Back in stock / now out of stock | 23 / 29 |
| Saved 6 Nov listings still valid | 526 of 568 |
| Cross-network (4G vs 5G) aliases rejected | 10 |
| RAM-ambiguous legacy rows held | 20 (same list as before) |
| Old-model markup review (kept, not held, per Shane's 6 Nov choice) | 14: `old-model-markup-review.json` |

Resale was not re-researched and `net_new_inr` was not changed. The 7 resale estimates dated 4 Nov passed their 10-day window during this run and are now marked unverified, which is honest; the engine had already stopped using them.

## Quote effect
- **No-age quick quotes:** 2 of 2,465 changed, both down: Poco M8x 5G 4/128 13,400 → 12,900 and 6/128 14,700 → 14,300 (the fresh new price ceiling binds again).
- **Age quotes at each model's launch age:** 152 changed against the expired-price state, 142 down and 10 up. The 10 up are recent models (iPhone Duo, Vivo V80, X Fold6, S2 FE…) that had no age quote while their price was expired.
- Quote-safety caps are identical to v6.34 (88 caps, 0 drop-band flags, 0 counter blocks, 0 numeric inversions). Re-running the resolver on the candidate gives an identical result.

## Tests
- All 11 JS suites pass (`tests.log`), plus `test_market_collectors.py` and `test_nonphone_collectors.py`.
- `test_quote_safety_solver.py` is hard-wired to `/Volumes/my1tb`. It was run from a scratch copy and **fails on drop-21, against live v6.34 as well**: it still expects the "-21% must block" rule that Shane replaced on 6 Nov, and it passes with the pre-6 Nov resolver. This is pre-existing. No candidate entry takes that path.

## Tooling recovered
The v6.32 run folder was on the damaged 1TB drive. `collect_a.py`, `prepare_obs.py`, `finalize.sh` and `compare_age.cjs` were rebuilt from the 6 Nov session transcript, and `variant_guard.py` from the 7 Nov Codex session. `ram-identity-holds.json` and the header of `compare.cjs` were rebuilt from the live DB and the recovered body. Two fixes:
1. `prepare_obs.py` carries "estimated" resale only inside the 10-day window (`resale_fresh`).
2. `finalize.sh` runs the suites one at a time and stops on any failure. The old parallel loop had silently dropped the failing `test_market_refresh.cjs` line.

Reuse: copy this folder (without `research/`, `baseline/`, `candidate/`), update the version, the dates and the sw.js cache name, then run `collect_a.py init`. Then run `flipkart` and `saved` + `reliance` as two background processes (~20 min this time), then `prepare_obs.py <ver>`, then `finalize.sh`.

## Not done this run
- Resale re-research and the new-launch gap audit: the v6.30 resale assembly scripts were lost with the drive.
- The Thursday scheduled task finishes in ~10 s every week and does no refresh; its instructions predate the full-catalogue policy.
