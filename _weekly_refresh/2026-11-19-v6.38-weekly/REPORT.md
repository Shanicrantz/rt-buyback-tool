# v6.38 weekly new-price refresh — 19 November 2026

Live: yes, https://rt-buyback-tool.netlify.app (Netlify deploy `6afeb712792306110b581fac`, state ready; live index.html, phone_db.json, sw.js sha256 match the build).

## Counts
- Scope 2469 variants; verified 573, pending 1896.
- New prices changed: 119 (67 up, 52 down).
- Back in stock: 29. Out of stock: 22.
- RAM/identity holds: 10. Markup review listings: 14 (kept, report only).
- No-age quote changes: 2 (Poco M8x 5G 4/128 Rs12900 -> 13400; Poco M8x 5G 6/128 Rs14300 -> 14700). No rise above 8%, no quote lost.
- Age-quote changes (launch age): 30 (17 up, 13 down). 89 age quotes capped by the resolver; 0 pinned, 0 inversions.

## Top 10 price moves
- Samsung Galaxy F07 4GB/64GB: Rs12128 -> Rs17128 (+41.2%, www.flipkart.com)
- Samsung Galaxy F70 Pro 5G 8/128GB: Rs29128 -> Rs40198 (+38.0%, www.flipkart.com)
- OnePlus 10 Pro 128GB: Rs35897 -> Rs49298 (+37.3%, www.flipkart.com)
- Samsung Galaxy F70 Pro 5G 8/256GB: Rs34198 -> Rs45298 (+32.5%, www.flipkart.com)
- Samsung Galaxy F17 5G 4/128GB: Rs19979 -> Rs24999 (+25.1%, Reliance Digital)
- Samsung Galaxy F70e 5G 4GB/128GB: Rs16878 -> Rs20628 (+22.2%, www.flipkart.com)
- Samsung Galaxy A36 5G 8/128GB: Rs24128 -> Rs29128 (+20.7%, www.flipkart.com)
- Poco C85x 5G 4GB/128GB: Rs14999 -> Rs17999 (+20.0%, Reliance Digital)
- Samsung Galaxy S25 256GB: Rs61298 -> Rs73298 (+19.6%, www.flipkart.com)
- Samsung Galaxy F70e 5G 6GB/128GB: Rs19878 -> Rs23628 (+18.9%, www.flipkart.com)

## Old-model markup review (kept as listed, Shane's rule)
- iPhone 16 Plus 128GB: Rs79900 — Review: 26-month-old model listed at Rs79900 (1.21x RT known new price Rs66000). Likely third-party old-stock listing.
- iPhone 16 Pro Max 256GB: Rs135199 — Review: 26-month-old model listed at Rs135199 (1.35x RT known new price Rs100000). Likely third-party old-stock listing.
- Samsung Galaxy S24 Ultra 256GB: Rs120298 — Review: 34-month-old model listed at Rs120298 (1.67x RT known new price Rs71999). Likely third-party old-stock listing.
- Samsung Galaxy M35 5G 8/128GB: Rs31198 — Review: 28-month-old model listed at Rs31198 (1.84x RT known new price Rs17000). Likely third-party old-stock listing.
- OnePlus Nord CE 4 8/128GB: Rs32189 — Review: 31-month-old model listed at Rs32189 (1.46x RT known new price Rs22000). Likely third-party old-stock listing.
- Oppo Find X8 Pro 16/512GB: Rs110298 — Review: 24-month-old model listed at Rs110298 (1.10x RT known new price Rs99999). Likely third-party old-stock listing.
- Oppo F27 5G 8/128GB: Rs32198 — Review: 26-month-old model listed at Rs32198 (1.53x RT known new price Rs21000). Likely third-party old-stock listing.
- iPhone 16 Plus 256GB: Rs90199 — Review: 26-month-old model listed at Rs90199 (1.19x RT known new price Rs76000). Likely third-party old-stock listing.
- Samsung Galaxy S23 Ultra 512GB: Rs162298 — Review: 45-month-old model listed at Rs162298 (1.73x RT known new price Rs93999). Likely third-party old-stock listing.
- OnePlus 10 Pro 128GB: Rs49298 — Review: 55-month-old model listed at Rs49298 (1.38x RT known new price Rs35749). Likely third-party old-stock listing.
- Samsung Galaxy F14 5G 6/128GB: Rs18619 — Review: 44-month-old model listed at Rs18619 (1.24x RT known new price Rs14990). Likely third-party old-stock listing.
- iPad mini 7 (A17 Pro) 128GB WiFi: Rs66400 — Review: 25-month-old model listed at Rs66400 (1.33x RT known new price Rs49900). Likely third-party old-stock listing.
- CMF Buds Pro 2: Rs4299 — Review: 28-month-old model listed at Rs4299 (1.54x RT known new price Rs2799). Likely third-party old-stock listing.
- Redmi Buds 6: Rs2999 — Review: 26-month-old model listed at Rs2999 (1.20x RT known new price Rs2499). Likely third-party old-stock listing.

## Review notes
- Several large Samsung Flipkart rises (F07 +41%, F70 Pro +38%/+32%, F70e +22%/+19%, A36 +21%/+18%, S25 256 +20%). These are listed seller prices; the no-age quote did not change for any of them and the release gate's 8% rise pin passed.
- OnePlus 10 Pro 128 rose 37% on Flipkart and is also in the markup review list (55-month-old model at 1.38x RT known new price).
- compare.log lists 15 'added' rows (Infinix GT 50 Pro, iPhone Duo, Oppo Find X10, Vivo V80/X Fold6, ...) with no quote before or after and unchanged new cash; catalogue keys are unchanged (2484).

## Tests
- All 12 JS suites passed; RELEASE CHECK OK (see release-check.json, tests.log).

## Held
- Nothing held beyond the 10 identity holds above.
