# RT Buyback weekly review — 28 September 2026

**Local result: v6.8 saved; one estimated rate reduced. Production was not published and Git was not pushed.**

The starting database was v6.7, refreshed manually on 26 September, with 2,362 entries. This run excluded recently researched models where possible, prioritized unresolved items and older estimates, and screened a 96-entry scope. Most search results could not support an exact, current, mint-condition resale. Only one price change cleared review; the other 95 entries keep their previous rates, statuses and calibration dates. They were **not** freshly verified.

## Accepted change

| Model | Previous A1 | New A1 | Change | Status |
|---|---:|---:|---:|---|
| Oppo Find X8 Pro 16/512GB | ₹48,200 | ₹45,000 | −₹3,200 / −6.64% | Estimated |

The primary [Mumbai seller listing](https://www.olx.in/en-in/item/mobile-phones-c1453-used-oppo-in-kandivali-west-mumbai-iid-1844380507) was opened directly on 28 September. It asks ₹55,000 for a like-new 512GB unit with box/accessories; warranty expired in July. It displayed a posting age of four days. A separate [16/512GB listing in Mira Road](https://www.olx.in/item/mobile-phones-c1453-used-oppo-in-mira-road-mumbai-iid-1854228569), also opened directly, asks ₹58,000 and describes a scratch-free unit with box and original charger. Its 31 August posting is older supporting context.

**Valuation assumption:** ₹55,000 less a 10% negotiation allowance gives estimated resale of ₹49,500. Applying the existing 9.9% age margin gives ₹45,000 A1 after ₹100 rounding. This is an asking-price adjustment, not a verified completed sale or a Moradabad transaction. The entry is therefore marked estimated, with source URLs and this limitation stored in the database. The decrease is within the weekly limit and both economic ceilings. No competitor price was invented.

The critical pass excluded a third listing that redirected to a category page. No higher-storage sibling or manual override was affected.

## Holds and source limitations

- **95 scoped entries unchanged:** exact RAM/storage, condition, kit, warranty or corroboration was insufficient. Many indexed pages were inaccessible, redirected, or mixed unrelated variants. Search discovery was not treated as a calibration.
- **Oppo A6s 4/128 and 6/128:** [TurnCash](https://www.turncash.in/sell/phone/oppo/a6s-5g/) displayed current maxima of ₹10,010 and ₹11,810, conditional on warranty and bill. These are not out-of-warranty A1 resale. The Cashify link displayed a different selected configuration, Fair condition and out-of-stock status, so it was rejected as a comparable price.
- **Samsung Z Flip 7 256GB:** a [merchant page](https://usedmobiles.lovable.app/phone/samsung-z-flip-7%20x) displayed ₹55,000 but lacked sufficient condition/warranty detail. Flagged for further checking; unchanged.
- **Vivo V50 12/512:** a [dealer page](https://mobilepriority.in/product/vivo-v50-5gstarry-night/25?stock_by=8&stock_id=7529) displayed ₹26,500 and Super Mint condition. This single retail ask did not justify raising the existing estimate.
- **Variant checks carried forward:** OnePlus 15 12/512, Poco M7 Pro 8/128, Realme C75 4/256 and Redmi Note 15 SE 8/128 need exact official India configuration evidence. None was removed merely because another configuration appeared in search.
- **Seven held launch variants remain outside the database.** [Apple India](https://www.apple.com/in/iphone-duo/) confirms iPhone Duo availability on 23 October. [Lava launch coverage](https://timesofindia.indiatimes.com/technology/mobiles-tabs/lava-virat-curve-5g-launches-with-mediatek-dimensity-7100-and-50mp-camera/articleshow/134385721.cms) gives first sale as 28 September at 7 PM, after this daytime run. OPPO K14 Plus and Redmi 17C were not confirmed on sale in India during this review. No new model was added.

## Validation and files

All 2,362 entries passed positive/finite quotes, grade order, final-offer deduction checks, new/resale ceilings, C/D margin floors, competitor coherence, comparable storage ordering and iPad size checks. Existing anchor-rounding checks allow ₹100; the accepted rate is exactly back-solved and below both ceilings without that tolerance.

Both database copies parse identically. All HTML outside the single database line is unchanged. Manual rates, warranty fields and new-price ceilings are unchanged. Original-file hashes were rechecked immediately before installation, and installed files match the validated candidate. The existing unrelated `.claude/settings.local.json` edit was preserved.

- [Accepted evidence and critical review](research/accepted.json)
- [96-entry scope](scope.json)
- [95 pending entries and reasons](pending.json)
- [Held launches](held_launches.json)
- [Search index](research/search_index.json) — discovery only; listed sources are not all verified or accepted.
- [Validation](validation.json)
- [Completion state](completion.json)
- [Verified original-file hashes](baseline.json) and original copies in `backup/`
- `publish_ready/` contains exactly the seven public assets; hashes are in [publish_manifest.json](publish_manifest.json).

The local database now has 1,767 entries labelled verified and 595 estimated. Those labels are historical except for the one entry reviewed and changed here. Publication requires Shane's authorization; live deployment state was not checked or changed by this run.
