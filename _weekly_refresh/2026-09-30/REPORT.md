# RT Buyback weekly refresh — 30 September 2026

Version **6.9**; **2365 entries**. Resumed the interrupted 30-Sep research.

Reviewed 96 scoped entries: 44 accepted calibrations, 40 A1 price changes, 4 shipping India configurations added, 1 confirmed phantom configurations removed.

The scope is the saved high-value/recent rotation, not all 1,248 eligible catalogue entries. Twelve fetch batches and eleven saved critic batches were recovered; the missing critic batch and missing Apple/Samsung/Google launch audit were completed using independent research agents because the original Workflow tool was unavailable in this session. Saved research is in saved_pricing_research.json; final reviews are in pricing_a.json, pricing_b.json and launch_review.json.

Resale values based on asking prices, retail bounds or analogs remain **estimated**. Existing authoritative new-price ceilings and manual overrides were preserved. Age margins and the existing C/D risk floors were applied. Unsupported rises, greater-than-20% moves, ceilings and storage-ladder conflicts were held. No price was lifted merely to beat Cashify. Historical deep-tail entries retain their dates and values.

## Largest accepted changes

| Model | Resale before → now | RT A1 before → now | Change |
|---|---:|---:|---:|
| Google Pixel 11 Pro Fold 16/512GB | Rs147,000 → Rs126,000 | Rs133,800 → Rs114,600 | -14.35% |
| iPhone Air 1TB | Rs108,000 → Rs88,000 | Rs98,300 → Rs80,100 | -18.51% |
| Google Pixel 11 Pro 512GB | Rs111,000 → Rs96,000 | Rs101,000 → Rs87,400 | -13.47% |
| iPhone 17 Pro 1TB | Rs122,000 → Rs108,000 | Rs111,000 → Rs98,300 | -11.44% |
| Samsung Galaxy Z Fold 6 1TB | Rs85,000 → Rs70,000 | Rs71,400 → Rs58,800 | -17.65% |
| Google Pixel 11 Pro XL 512GB | Rs120,000 → Rs107,000 | Rs109,200 → Rs97,400 | -10.81% |
| Google Pixel 11 512GB | Rs85,000 → Rs72,000 | Rs77,300 → Rs65,500 | -15.27% |
| iPhone 17 Pro 512GB | Rs112,000 → Rs100,000 | Rs101,900 → Rs91,000 | -10.70% |
| iPhone 17 Pro Max 256GB | Rs115,000 → Rs104,000 | Rs104,600 → Rs94,600 | -9.56% |
| Samsung Galaxy Z Fold 6 512GB | Rs76,000 → Rs65,000 | Rs63,900 → Rs54,600 | -14.55% |
| iPhone 17 Pro Max 1TB | Rs133,000 → Rs123,000 | Rs121,000 → Rs111,900 | -7.52% |
| iPhone 17 Pro Max 512GB | Rs124,000 → Rs114,000 | Rs112,800 → Rs103,700 | -8.07% |
| Google Pixel 11 Pro XL 256GB | Rs110,000 → Rs101,000 | Rs100,100 → Rs91,900 | -8.19% |
| iPhone 17 Pro 256GB | Rs104,000 → Rs95,000 | Rs94,600 → Rs86,400 | -8.67% |
| Samsung Galaxy Z Fold 6 256GB | Rs70,000 → Rs61,000 | Rs58,800 → Rs51,300 | -12.76% |

## Added configurations

- Lava Virat Curve 5G 6/128GB: resale Rs16,000; A1 Rs12,300; India launch 2026-09-21.
- Lava Shark 2 Pro 5G 6/128GB: resale Rs12,500; A1 Rs9,600; India launch 2026-09-29.
- OnePlus 15 16/512GB: resale Rs52,000; A1 Rs47,300; India launch 2025-11-13.
- Poco M7 Pro 5G 6/128GB: resale Rs10,000; A1 Rs8,000; India launch 2024-12-17.

## Variant repairs and deferred launches

- Removed `oneplus_15_12_512`: Official India configuration list and India launch release both explicitly enumerate only 12/256 and 16/512. Replace wrong-RAM 12/512 atomically with fully specified oneplus_15_16_512 above, preserving Rs79,999 authoritative new and Rs52,000 resale anchors. If replacement validation fails, hold removal. Replacement: `oneplus_15_16_512`.
Full held-launch and uncertain-variant evidence is in launch_review.json. Full price holds are in decisions.json.

## Competitor comparison

No fresh condition-specific competitor payout above RT A1 was verified. This does not prove RT beats competitors.

Public “Get Upto” amounts below are **maximum headlines, not confirmed payouts**. All are retained in the review artifacts; accepted calibrations also store market_buyback_ceiling in the DB. These flag a possible lost walk-in, including models whose RT price was held:

| Model | RT A1 | Public maximum | Potential gap |
|---|---:|---:|---:|
| MacBook Pro 16" M4 Pro (2024) 24/512GB | Rs118,300 | Rs160,000 | Rs41,700 |
| iPhone 17 Pro 512GB | Rs91,000 | Rs108,000 | Rs17,000 |
| iPhone 17 Pro 256GB | Rs86,400 | Rs102,000 | Rs15,600 |
| iPhone 17 Pro Max 256GB | Rs94,600 | Rs110,000 | Rs15,400 |
| Samsung Galaxy Z Fold 6 256GB | Rs51,300 | Rs65,560 | Rs14,260 |
| iPhone 17 Pro Max 512GB | Rs103,700 | Rs117,000 | Rs13,300 |
| Samsung Galaxy Z Fold 6 512GB | Rs54,600 | Rs66,240 | Rs11,640 |
| iPhone 17 Pro 1TB | Rs98,300 | Rs109,000 | Rs10,700 |
| Samsung Galaxy S26+ 256GB | Rs51,000 | Rs61,500 | Rs10,500 |
| Vivo X Fold5 16GB/512GB | Rs68,200 | Rs78,520 | Rs10,320 |
| Samsung Galaxy Z Fold 6 1TB | Rs58,800 | Rs68,830 | Rs10,030 |
| MacBook Air M4 13" (2025) 16/256GB | Rs66,400 | Rs75,000 | Rs8,600 |
| iPhone 17 512GB | Rs58,100 | Rs66,500 | Rs8,400 |
| iPhone Air 1TB | Rs80,100 | Rs87,000 | Rs6,900 |
| iPhone 17 Pro Max 1TB | Rs111,900 | Rs118,700 | Rs6,800 |
| OnePlus 15R 12/512GB | Rs29,400 | Rs36,100 | Rs6,700 |
| Oppo Reno 15 Pro 5G 12/256GB | Rs34,200 | Rs40,400 | Rs6,200 |
| Samsung Galaxy S25 FE 512GB | Rs32,800 | Rs38,380 | Rs5,580 |
| iPhone Air 256GB | Rs63,700 | Rs69,000 | Rs5,300 |
| Vivo V70 Elite 8GB/256GB | Rs28,700 | Rs33,720 | Rs5,020 |
| Nothing Phone 3a 8/128GB | Rs14,300 | Rs19,150 | Rs4,850 |
| Vivo V50e 5G 8/128GB | Rs14,300 | Rs18,790 | Rs4,490 |
| Samsung Galaxy S25 FE 256GB | Rs30,500 | Rs34,930 | Rs4,430 |
| OnePlus Nord CE 5 8/256GB | Rs14,800 | Rs19,050 | Rs4,250 |
| iPhone 17 Pro Max 2TB | Rs119,200 | Rs123,000 | Rs3,800 |
| iPhone 17e 512GB | Rs50,000 | Rs53,400 | Rs3,400 |
| Redmi Note 14 Pro 5G 8/128GB | Rs12,300 | Rs15,600 | Rs3,300 |
| Samsung Galaxy S25 Ultra 512GB | Rs65,500 | Rs68,780 | Rs3,280 |
| Motorola Signature (12GB+256GB) | Rs32,200 | Rs35,420 | Rs3,220 |
| Samsung Galaxy S25 Ultra 256GB | Rs61,000 | Rs63,970 | Rs2,970 |
| iQOO Z10 5G 8/256GB | Rs14,000 | Rs16,730 | Rs2,730 |
| Oppo A6s 5G 6/128GB | Rs11,200 | Rs13,810 | Rs2,610 |
| Oppo A6 Pro 5G 8/128GB | Rs12,000 | Rs14,520 | Rs2,520 |
| iPhone 16 Plus 256GB | Rs51,300 | Rs53,760 | Rs2,460 |
| Vivo Y400 5G 8/256GB | Rs14,400 | Rs16,830 | Rs2,430 |
| Oppo F29 Pro 5G 8/256GB | Rs14,300 | Rs16,580 | Rs2,280 |
| Samsung Galaxy A57 5G 12/256GB | Rs31,300 | Rs33,550 | Rs2,250 |
| Tecno Camon 50 Ultra 5G 8/256GB | Rs24,600 | Rs26,520 | Rs1,920 |
| Oppo Find X8 Pro 16/512GB | Rs43,200 | Rs44,880 | Rs1,680 |
| Oppo A6s 5G 4/128GB | Rs10,400 | Rs12,000 | Rs1,600 |
| Samsung Galaxy S25 FE 128GB | Rs29,600 | Rs31,000 | Rs1,400 |
| Motorola Edge 60 Stylus (8GB+256GB) | Rs14,100 | Rs15,280 | Rs1,180 |
| Xiaomi 17T 5G (12GB/512GB) | Rs38,200 | Rs39,360 | Rs1,160 |
| Vivo V70 12GB/256GB | Rs32,400 | Rs33,390 | Rs990 |
| Xiaomi 17T 5G (12GB/256GB) | Rs35,000 | Rs35,920 | Rs920 |
| Realme P3 Ultra 5G 8/256GB | Rs14,800 | Rs15,550 | Rs750 |
| Motorola Edge 70 Pro Plus 5G (12GB+256GB) | Rs30,300 | Rs31,000 | Rs700 |
| iQOO 15R 12/256GB | Rs30,100 | Rs30,700 | Rs600 |
| Oppo F27 5G 8/256GB | Rs14,000 | Rs14,560 | Rs560 |
| iQOO 15R 8/256GB | Rs28,300 | Rs28,730 | Rs430 |
| Oppo Reno 15 Pro Mini 5G 12/512GB | Rs37,200 | Rs37,390 | Rs190 |
| Samsung Galaxy Z Flip 7 256GB | Rs52,800 | Rs52,940 | Rs140 |

## Validation and publication

- Full engine validation: PASS across 2365 entries; paired DB bytes, JavaScript syntax, grades, final offers, ceilings, weekly changes, protected fields and storage/size ladders checked.
- The UI and pricing engine are unchanged; only the inline database was updated.
- Baseline on production: v6.7 / 26-Sep. Local baseline: v6.8 / 28-Sep. The unpublished 28-Sep correction is included.
- Production: ready.
- Deployment ID: 6abd29db300260625a0f550e.
- Live HTML and JSON hashes match candidate: True.
- Site: https://rt-buyback-tool.netlify.app/

The pushed commit is reported in the completion message and can be identified by the v6.9 weekly-refresh commit subject. A commit cannot contain its own hash.
