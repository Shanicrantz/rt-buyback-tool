# v6.43 weekly new-price refresh — 26 November 2026

Scheduled run (`rt-buyback-weekly-refresh`), unattended. Template: `_refresh_template/`.

## Result
- **Live**: https://rt-buyback-tool.netlify.app serves `_meta.version` 6.43. Netlify deploy `6b07f2124af5fb7c20c64d0a`, state `ready`, context production.
- sha256 of live index.html, phone_db.json and sw.js match the deployed copies. sw.js cache: `rt-buyback-cache-v6-43-weekly-20261126`.
- Inline `const DB` in index.html equals phone_db.json.

## Counts
- Scope 2,469 variants: **569 verified**, 1,900 pending (mostly not sold new any more).
- New prices changed: **147** (67 up, 80 down).
- Back in stock (gained a new price): 21. Out of stock (lost it): 25.
- Identity holds 11 (RAM-ambiguous legacy rows: `ram-identity-holds.json`, 20 entries). Markup review: 13 listings, kept.
- No-age quote changes: **1** (Redmi Pad 4/128: 9,200 → 9,100; new cash 13,279 → 12,654).
- Age-quote changes at launch age: 155 (14 up, 141 down); 14 models gained an age quote, none lost one.

## Top 10 new-price moves (by %)
| Model | Before | After | Move | Source |
|---|---:|---:|---:|---|
| Samsung Galaxy F07 4/64 | 17,128 | 12,128 | −29.2% | Flipkart |
| Samsung Galaxy A57 5G 12/256 | 63,364 | 76,499 | +20.7% | Reliance |
| Samsung Galaxy F70 Pro 5G 8/128 | 40,198 | 32,198 | −19.9% | Flipkart |
| Samsung Galaxy S25 Ultra 512 | 110,298 | 131,298 | +19.0% | Flipkart |
| Samsung Galaxy F70 Pro 5G 8/256 | 45,298 | 37,198 | −17.9% | Flipkart |
| Nothing Ear (2024) | 12,148 | 10,048 | −17.3% | Flipkart |
| Samsung Galaxy F17 5G 4/128 | 24,999 | 20,928 | −16.3% | Flipkart |
| Vivo Y31 5G 4/128 | 25,078 | 29,119 | +16.1% | Flipkart |
| Poco C85x 5G 4/64 | 13,999 | 16,128 | +15.2% | Flipkart |
| Samsung Galaxy S23 FE 128 | 70,298 | 80,298 | +14.2% | Flipkart |

## Markup review (2+-year-old models listed above RT's known new price; kept, report only — Shane's rule)
iPhone 16 Plus 128 (₹79,900, 1.21×) · iPhone 16 Pro Max 256 (₹1,35,199, 1.35×) · Galaxy S24 Ultra 256 (₹1,20,298, 1.67×) · Galaxy M35 5G 8/128 (₹30,126, 1.77×) · OnePlus Nord CE 4 8/128 (₹32,189, 1.46×) · Oppo Find X8 Pro 16/512 (₹1,10,298, 1.10×) · iPhone 16 Plus 256 (₹90,199, 1.19×) · Galaxy S23 Ultra 512 (₹1,62,298, 1.73×) · OnePlus 10 Pro 128 (₹48,298, 1.35×) · Galaxy F14 5G 6/128 (₹18,619, 1.24×) · iPad mini 7 128 WiFi (₹66,400, 1.33×) · CMF Buds Pro 2 (₹4,299, 1.54×) · Redmi Buds 6 (₹2,999, 1.20×).

## Notes from review
- The S25 Ultra 512 (+19%), A57 12/256 (+20.7%) and S23 FE 128 (+14%) rises are plain Flipkart/Reliance exact listings; release check confirmed no no-age quote rose more than 8%.
- Biggest launch-age age-quote drops are very old models (OnePlus 7 at 90 months 9,900 → 2,600, iPhone 13 128 at 62 months 27,500 → 9,500, iPad 9th gen 64). Their new price did not change. The baseline prices were dated 19 Nov, so at today's date they are at the 7-day expiry and the "before" quote used the saved-resale fallback; the fresh price brings back the age-% quote. This is the designed behaviour the weekly refresh exists for.
- 14 rows gained an age quote (iPhone Duo ×4, Oppo Find X10 ×3, Vivo V80 ×3, Vivo S2 FE ×2, Vivo X Fold6 12/512, Infinix GT 50 Pro 12/256); they still have no no-age quote (no resale).

## Tests
Finalize: resolver (89 capped, 0 inversions, no manual review), 12 JS suites, 0 failed. `RELEASE CHECK OK` (all 13 checks pass; see `release-check.json`, `tests.log`).

## Held / other
- Nothing held from the release.
- Deploy note: the first `npx @netlify/mcp` run failed on a missing entry in `~/.npm/_cacache`; the retry used a throwaway npm cache in the session scratchpad (user cache untouched) and succeeded.
