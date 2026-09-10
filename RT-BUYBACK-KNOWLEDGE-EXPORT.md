# RT Buyback — Brain & Repo Knowledge Export

**Exported:** 2026-09-07 · **DB state:** v6.3 (calibrated 2026-08-30, 2313 entries) · **Repo:** `github.com/Shanicrantz/rt-buyback-tool` @ `7a07133`
**Owner:** Shane (Shahnawaz), Rajdhani Telecom (RT), 125 Station Road, Budh Bazar, Moradabad.

This file consolidates everything that is known about the RT buyback tool and its pricing brain, pulled from five sources that normally live in different places:

| Source | Where it lives | What it holds |
|---|---|---|
| Project memory (5 files) | `~/.claude/projects/-Users-shane-Documents-Claude-Projects-rt-buyback-tool/memory/` | Structure, pricing brain, refresh guardrails, Cashify-widget trap, commit+push rule |
| `buyback-brain` skill (Jul 6 2026) | `.../skills/buyback-brain/SKILL.md` + `references/buyback_register.xlsx` | Counter-side live-check methodology, grades, deductions, KYC, negotiation |
| Weekly scheduled task | `~/.claude/scheduled-tasks/rt-buyback-weekly-refresh/SKILL.md` (Mon 2 PM) | Autonomous refresh procedure |
| `phone_db.json` `_meta` | repo | Formula, margins, changelogs v2.4 → v6.3, market signals |
| Engine + tooling | `index.html`, `_*.py`, `_*.js` in repo | The actual math and the pipeline |

The sections are ordered so that a reader (human or AI) can price a phone after §2–§4, run the weekly refresh after §5–§7, and avoid every known trap after §8.

---

## 1. Business context

- RT is a 20+ year phone retailer in Moradabad. **Old-phone buyback is the core margin business**: 15–25% on resale vs 4–7% on new-phone sales.
- RT buys a used phone at the counter, re-sells it locally (walk-in, WhatsApp regulars, OLX, Cashify B2B for slow movers). Inventory rule: **if a phone has not resold in 30 days, dump to Cashify B2B** — capital blocked on HDFC CC at ~8% costs more than the extra margin.
- **Shane is the pricing authority.** The brain was reverse-engineered from his 100 hand-set counter rates and reproduced them at median Δ −1.1%. New-phone prices come from Shane, not the web (web values burned the project twice).
- **Conservative is the safe error.** Overpaying loses money on every unit RT buys; underpaying only loses one deal. Every guardrail in this document is asymmetric because of this.
- Customers benchmark against Cashify. RT wins the walk-in on convenience (15-min inspection, spot cash) and cross-sell, and can deliberately lowball slow old models *below* Cashify.

---

## 2. The pricing brain (how A1 is computed)

**A1** = the mint / like-new, full-kit, out-of-warranty buyback price. Everything else (grades, kit, battery, damage, warranty) cascades from A1.

### 2.1 Formula

```
A1 = resale_price ÷ (1 + margin_by_age)
A1 = min(A1, resale_price × 0.92, net_new × 0.85)      # hard economic ceilings, asserted LAST
A1 rounded to ₹100
```

- **resale_price** = the REAL price a local Moradabad shop can re-sell a mint used unit for today.
  - It is **NOT** Cashify's "buy refurbished" retail (warranty + brand premium inflate it for older phones).
  - It is **NOT** an OLX asking price (asking runs ~10% above sold).
  - Triangulate: OLX recent SOLD (asking −8–12%) + local used value + Cashify refurb as an *upper bound* + 2gud/Amazon Renewed.
  - Current hot phones: resale ≈ refurb retail. Older/unpopular phones: well below it. Getting this distinction wrong was the original failure mode (it overpriced every old phone).
  - Brand-new launches (<3 months): resale ≈ 78–85% of official new price; used market is thin.
- **margin_by_age** (stored in `_meta.margin_by_age`, auto-calibrated from Shane's overrides vs real resale):

  | Phone age (from `launch_date`) | margin |
  |---|---|
  | < 24 months | 0.099 |
  | 24–36 months | 0.19 |
  | 36–54 months | 0.19 |
  | 54+ months | 0.298 |

  Older = bigger risk buffer = lower buyback.
- **Tier floor for C/D.** `margin_by_age` was calibrated only on high-value S/A/B models. For tiers C and D the tier default is a **floor**: `margin = max(margin_by_age, default_margins_by_tier[tier])` → C ≥ 0.25, D ≥ 0.30. Without it a ₹8,000 phone carries a ~₹700 buffer that does not cover the risk of holding it. (130 gap-added C/D entries were found under-margined and repaired on 2026-08-24.)
- **net_new** = official brand India price. Used only as the `×0.85` ceiling. Round numbers (ending 000) are a fabrication signature — real India prices end in 999/990.
- **buyback_market** = what Cashify / other buyers actually PAY the seller. Stored per entry for competitiveness display. RT is *not* forced to beat it.

### 2.2 How the engine stores it

The tool's engine computes `A1 = resale_target_a1 ÷ (1 + target_margin)`. The pipeline therefore writes:

```
target_margin     = margin_by_age (with C/D floor)
resale_target_a1  = A1 × (1 + target_margin)     # BACK-SOLVED so the engine reproduces the capped A1
market_resale_observed = the actual researched resale
```

**Consequence:** after any cap binds, `resale_target_a1` is *not* observed resale. Any invariant comparing resale against buyback must use `market_resale_observed`.

### 2.3 Default tier margins (`_meta.default_margins_by_tier`)

| Tier | Brands / series | Default margin | Used as |
|---|---|---|---|
| S | Apple iPhone, Samsung S/Z/Fold, Pixel Pro | 0.18 | fallback if no `target_margin` |
| A | OnePlus flagship, premium, Samsung A7x, iPad | 0.20 | fallback |
| B | Xiaomi, Vivo X, Oppo Reno, Nord, Nothing, Moto Edge/Razr | 0.22 | fallback |
| C | Vivo Y/T, Oppo A/F, Realme C/Narzo, Redmi Note, Poco, Samsung A0x–A3x/M/F | 0.25 | **floor** |
| D | Infinix, Tecno, Lava, itel, Micromax entry | 0.30 | **floor** |

Tier is not cosmetic: it sets the C/D margin floor and the RT-premium and damage percentages. **A new entry's tier must be normalised to whatever tier the DB already uses for that series** (majority of ≥3 existing entries at ≥70%).

### 2.4 Warranty, grades and deductions (engine constants)

| Constant | Value |
|---|---|
| `GRADE_MULT` | A1 1.00 · A2 0.90 · B 0.80 · C 0.65 · D 0.45 |
| `DEDUCTION` (kit) | no box −3% · no charger −2% · no bill −5% |
| `WARRANTY_PREMIUM_DEFAULT` | +13% on A1 (or explicit `rt_buyback_a1_warranty`) |
| `WTY_LEFT` factor (share of premium granted by phone age from bill) | 0–3 mo 0.90 · 3–6 mo 0.65 · 6–9 mo 0.40 · 9–12 mo 0.15 |
| `BATT_DED` | >90% 0 · 80–90% −5% · 70–80% −10% · <70% −20% |
| `FOLDABLE_OOW_RISK` | 12% × (1 − warranty coverage). Foldable detected by name regex: fold / flip / razr / magic v / find n / oneplus open |
| Shane-confirmed warranty pairs (v3.3) | iPhone 15 128 ₹39,000 out / ₹44,000 under-warranty; S25 Ultra 256 ₹66,700 / ₹75,000 |

Final offer chain (`computeFinal`):

```
base       = A1 × GRADE_MULT[grade] × (1 − kit deductions)        # round100
afterBatt  = base × (1 − BATT_DED[band])
afterFold  = afterBatt × (1 − foldRisk)
final      = max(0, round100(afterFold − Σ partCost(damage)))
```

Damage part cost = `damageBaseValue × pct[tier]`, where damageBaseValue = `net_new_inr` → else `refurb_retail_anchor_excellent` → else `resale_target_a1 × 1.20` → else override × 1.35 → else cashify × 1.45. Part tables exist for phone, laptop, watch and audio (see §3.3).

Staff cheat sheet shown per model: **Open offer** = grade B with kit · **Walk-away ceiling** = A2 with kit · **Hard floor** = grade C with kit. Implied resale per grade = `A1 × (1+margin) × GRADE_MULT`.

### 2.5 Market-event valuation rules (`_meta.market_signals.rule`, skill §A.5)

1. **Successor imminent (< ~4 weeks, confirmed):** trim outgoing-gen resale anchors 5–10% (current flagship −5%, previous gen −7 to −10%, 2-gen-old already low → trim to live). Once the successor ships, the anticipatory trim is *spent* — re-anchor on observed resale. Never quote the unreleased successor.
2. **Festival / flash sale (Prime Day, BBD, Republic Day):** the sale price is a **temporary NET_NEW floor**. Cap buyback below `sale_new − full margin` during the sale, but do **not** reset the anchor permanently unless the low price persists outside the sale window or the model is end-of-life. Worked case: S25 Ultra flashed to ₹84,999 (MRP ₹1,29,999) on Prime Day Jul 2026; durable street was ~₹93,500; the ₹66,700 rate was held.
3. **2026 India price step-up is real.** iQOO Z10 ₹21,999 → Z11 ₹34,999; Tecno Pova 7 Pro ₹19,999 → Pova 8 Pro ₹49,999; Poco M7 ₹10,499 → M8x ₹20,999. A "2–3× its predecessor so it must be an MRP" heuristic now produces false rejections — verify against the brand's India store instead.

---

## 3. The engine (`index.html`)

Single-file app, ~1,143 lines. Line 422 is `const DB = {...};` (the whole database inlined on ONE line). **`phone_db.json` and this line must stay byte-identical in content.** Never regenerate `index.html` wholesale; only swap the DB line.

### 3.1 `computeA1` anchor priority (field precedence)

| # | Field present | Formula | Source label in UI |
|---|---|---|---|
| 1 | `rt_buyback_a1_override` | direct ₹ | SHANE RATE |
| 2 | `resale_target_a1` | `÷ (1 + margin)` | RESALE ANCHORED |
| 3 | `cashify_exchange` | `× (1 + rt_premium_over_cashify[tier])` (S8/A10/B12/C14/D16%) | CASHIFY +RT PREMIUM |
| 4 | `refurb_retail_anchor_excellent` (or `_fair × 1.18`) | `× market_factor(0.88) ÷ (1 + margin)` | REFURB RETAIL ANCHORED |
| 5 | `net_new_inr` + `launch_date` | `net_new × depFraction(age) × TIER_FACTOR × (1 + TIER_PREMIUM)` | FORMULA EST. |
| — | none | 0 | NO DATA (tool refuses to quote) |

`margin = target_margin ?? DEFAULT_MARGIN[tier] ?? 0.22`.
`DEPRECIATION_CURVE` (months → fraction of new): 3→0.68, 6→0.60, 12→0.53, 18→0.46, 24→0.38, 36→0.27, 48→0.18, else 0.12. `TIER_FACTOR` S1.20/A1.05/B0.95/C0.85/D0.55. `TIER_PREMIUM` S0.10/A0.08/B0.06/C0.04/D0.

**Live state (v6.3):** 973 entries resale-anchored, 1,340 refurb-anchored, **0 overrides** (all 100 retired 2026-08-05 and stashed as `_override_prev`, reversible), 0 in cashify mode (the 100 entries carrying `cashify_exchange` all also carry `resale_target_a1`, which outranks it), 0 in formula mode.

Python mirrors of `computeA1` exist in every pipeline script (`cur_a1` / `a1_of`) and must be kept identical to the JS, including the margin default.

### 3.2 UI features

- **Password gate**: SHA-256 hash compare in-page, `sessionStorage` key `rt_buyback_auth_v1`. Cosmetic — the DB with margins is client-side and view-source readable. Accepted risk; real fix would be Netlify visitor password or server-side.
- **Search**: tokenised (`space _ - /`), scores exact key-segment hits ×100, substring ×10, minus key length; top 20; brand filter pills by key prefix (`FILTER_PREFIX`), category pills for tablet/watch/audio; empty filter shows top-12 by A1; keyboard nav.
- **Storage-variant chips**: `familyOf(key)` strips trailing storage tokens (32/64/128/256/512/1tb/2tb); siblings sorted by storage.
- **Customer mode** (`body.customer-mode` hides `.staff-only`): single hero card with FINAL OFFER, grade, kit, battery, warranty. Staff mode shows tier, margin, source pill, calc line, 5 grade tiles (with-kit / no-kit / implied resale), cheat sheet, kit chips, battery bands, damage grid, notes, Cashify + CEIR links.
- **Sticky FINAL OFFER bar** with WhatsApp share, Copy, Receipt (staff). Quote text includes "Rajdhani Telecom, Budh Bazar, Moradabad · Ph: 9719002127".
- **Print receipt** (KYC: name, mobile, ID type/number, IMEI 1/2, address; GSTIN 09AAOPW5720F1ZA; Hindi ownership declaration; signatures).
- **Recent quotes**: `localStorage` `rt_recent_v1`, last 12.
- **Staleness banner**: >10 days since `last_calibration` → warn; >21 days → red "verify live on Cashify".
- **Stats row**: device count, verified, estimated; title shows DB version.
- **PWA**: `manifest.webmanifest` (standalone, `#0f172a`), `sw.js` network-first with cache `rt-buyback-cache-v1`, icons 192/512 + apple-touch; install hints for Android (beforeinstallprompt) and iOS (Add to Home Screen).
- Footer reminder: CEIR check · FRP/iCloud sign-out · IMEI = box = bill · 15-min function test.

### 3.3 Damage tables (% of damageBaseValue by tier S/A/B/C/D)

**Phone:** display 22/20/18/16/15 · back panel 7/6/5/5/4 · rear camera 10/8/7/6/5 · front camera 5/4/4/3/3 · battery 5/5/5/6/7 · charging port 4/4/3/3/3 · speaker/mic 3 · frame dent 10/8/7/6/5.
**Laptop:** display 30/28/25/22/20 · keyboard 12/10/10/8/8 · trackpad 10/8/8/7/6 · battery 10 · hinge 10/8/8/7/6 · body dent 8/6/5/5/4 · ports 6/5/5/4/4 · speaker 4/4/3/3/3.
**Watch:** screen 35/32/28/25/22 · battery 15/13/12/10/10 · crown 10/8/7/6/5 · back sensor 12/10/8/7/6 · strap 5 · case dent 8/6/5/5/4 · charging 6/5/5/4/4.
**Audio:** left/right bud 30/28/25/22/20 each · case 25/22/20/18/15 · battery 15/13/12/10/10 · ANC/mic 12/10/8/7/6 · cosmetic 6/5/5/4/4.
2+ major damages including display or frame → UI warns "scrap-grade risk, use grade D floor".

---

## 4. Database (`phone_db.json`)

### 4.1 Shape

Top-level object: `_meta` + one entry per key. **Key naming:** `brand_model[_ram]_storage`, lowercase, storage token last — `iphone_15_128`, `samsung_s25_ultra_256`, `vivo_v50_12_512`, `oppo_reno_13_8_128`, `google_pixel_11_pro_fold_512`. Brand prefixes in use: samsung, realme, vivo, oppo, redmi, iphone, moto, oneplus, poco, iqoo, google, nokia, infinix, tecno, xiaomi, lava, ipad, asus, nothing, honor, itel, macbook, micromax, lenovo, apple, cmf, airpods, hmd, boat, noise.

### 4.2 Entry fields

| Field | Meaning |
|---|---|
| `display_name`, `tier` (S/A/B/C/D), `launch_date` (YYYY-MM-DD), `discontinued`, `discontinued_date`, `category` (phone default; tablet/watch/laptop/audio), `notes` | Identity |
| `resale_target_a1` | Back-solved anchor: `A1 × (1+margin)`. Primary anchor for 973 entries. |
| `target_margin` | Margin the engine divides by. From `margin_by_age`, C/D floored. |
| `market_resale_observed` | The actual researched resale (257 entries). Use THIS for resale-vs-buyback checks. |
| `net_new_inr` | Official India new price = `×0.85` ceiling (539 entries). Exact, never rounded. Shane's authoritative values for current flagships (e.g. iPhone 15 128 ₹58,500 / 16 128 ₹68,500 / 16 256 ₹77,500 as of Aug 2026) must not be overwritten by scraping. |
| `buyback_market` | What Cashify/others pay (219 entries). Reference only. Dropped when fabricated/incoherent. |
| `refurb_retail_anchor_excellent` / `_fair`, `market_factor` (0.88), `refurb_retail_source` | Legacy anchor for discontinued/long-tail (1,340 entries). Inert when `resale_target_a1` exists. |
| `cashify_exchange`, `rt_premium_over_cashify` | Legacy mode-0 anchor (100 entries), inert today. |
| `rt_buyback_a1_override`, `rt_buyback_a1_warranty`, `warranty_premium` | Shane hand-set rates. Override field currently unused (0); `_override_prev` keeps the 100 retired values. |
| `calibration_status` (`verified` / `estimated`), `calibration_date`, `live_source` (≤180 chars provenance stamp) | Provenance. `estimated` = re-research next week and live-verify on first transaction. |

### 4.3 `_meta`

`version`, `last_calibration`, `schema_priority_order`, `default_margins_by_tier`, `margin_by_age`, `fair_to_excellent_multiplier` 1.18, `default_market_factor` 0.88, `warranty_premium` 0.13, `pricing_brain` (one-paragraph formula), `market_signals` (resolved events + active rules), `calibration_status_legend`, and one `vX_Y_changelog` string per release from v2.4 to v6.3 (the changelogs are the audit trail — see §9).

### 4.4 Snapshot statistics (read 2026-09-07)

| Metric | Value |
|---|---|
| Entries | 2,313 (2,146 phones, 114 tablets, 21 watches, 17 laptops, 15 audio) |
| Tiers | C 727 · B 549 · S 377 · D 369 · A 291 |
| Status | verified 1,721 · estimated 592 |
| Discontinued | 1,365 |
| Launch years | 2014 → 2026 (2024: 491, 2025: 388, 2026: 249). Pre-2014 excluded — no resale value. |
| Calibration dates | 2026-06-25 (1,576 long-tail) · 2026-08-05 (305) · 2026-07-20 (110) · 2026-08-24 (106) · 2026-08-30 (101) · others |
| Round `net_new_inr` (ending 000) | 233 remain, 0 of them bind an A1 (latent hygiene) |

---

## 5. Weekly refresh pipeline (the automation)

Scheduled task **`rt-buyback-weekly-refresh`**, Mondays 2 PM, runs fully autonomously from `~/.claude/scheduled-tasks/rt-buyback-weekly-refresh/SKILL.md`. Every script defaults to **dry-run** and needs `--apply` to write; every writer patches BOTH files and asserts exactly one `const DB = {` line.

### 5.1 Steps and scripts

| Step | Script(s) | What it does |
|---|---|---|
| 0 Backup | `cp` → `phone_db.backup-<date>.json`, `index.backup-<date>.html` | Local safety copy (git-ignored; git history is the real backup) |
| 1 Scope | `_build_scope_<date>.py` → `_ov_batches.json`, `_scope_<date>.json` | Candidates = non-override, non-discontinued, tier S/A **or** launched ≤24 mo. Picks 40 top value-at-risk (excluding last week), 32 stale-rotation (oldest calibration, highest A1), 16 recent launches ≤9 mo, 8 re-verify of last week's thin-market flagships → ~96 keys in 12 batches of 8. |
| 2 Research | `_reprice_workflow.js` (Workflow tool, 12× fetch → critic, Sonnet) → `_ov_updates/fetch_i.json`, `verified_i.json` | Fetcher finds resale + buyback per model; adversarial critic re-verifies both, checks existence for 2026 launches, reports official NEW price. Prompts embed the BRAIN text and the hand-verified-real list. |
| 3 Apply brain | `_apply_brain_weekly.py --apply` → `_brain_refresh_<date>.json` | Formula + all caps/filters (§6). Writes anchors, `market_resale_observed`, drops fabricated buyback, stamps `live_source`. Fixes storage inversions within the changed set. Reports blocked rises, echoed estimates, non-existence claims, "Cashify pays more than RT". |
| 4 Gap audit | `_gap_audit_workflow.js` (4 units from `_audit_units.json` + `_db_inventory.json`, find → critic) → `_gaps/find_i.json`, `verified_i.json`; then `_add_gaps.py --apply` → `_added_<date>.json` | Finds India launches since last calibration (primary: last ~8 days; secondary: notable 2025–26 gaps). Adds only critic-confirmed real launches with a resale; dedupes by key and name signature; brand allow-list; tier normalised to series majority; `net_new_inr` stored exact. |
| 5 Outlier verify | `_build_pending_<date>.py` → `_pending/items.json` + `batches.json` (5/batch); `_verify_pending_<date>.js` (verify → refute, **Opus**); `_apply_verified_<date>.py --apply` → `_pending/outcome_<date>.json` | Re-researches blind: capped rises, drops ≥12% or week-floored, non-existence claims, missing resale, round-price gap-adds. Verdicts grant / refuse / lower / remove / hold (§6.3). |
| 6 Sibling repair | `_repair_siblings_<date>.js` (research → refute, Opus, verdict add/skip) + `_add_siblings_<date>.py --apply` → `_added_siblings_<date>.json` | For every removed phantom, research and add the REAL config it stood in for. Tier + launch date inherited from surviving family siblings; weak provenance → `estimated` rather than no entry. |
| 7 Ceilings | `_fix_ceilings_<date>.py --apply` | Hand-verified `net_new_inr` corrections. Lower ceiling pulls A1 down; higher ceiling never lifts A1. |
| 8 Finalize | `_finalize_meta.py --apply` | Bumps `version`, `last_calibration`, writes the dated changelog + `market_signals`, runs invariants (§6.4), repairs DB-wide storage inversions, writes both files, verifies they parse to identical JSON. |
| 9 Deploy | copy the **7 publish files** into a scratch dir → `netlify deploy --prod --dir=<scratch>` (site id `7b706fe7-9260-4d82-a0ff-263413316382`) → verify `ready` + curl live `_meta.version` | Publish set = `index.html`, `phone_db.json`, `manifest.webmanifest`, `sw.js`, `icon-192.png`, `icon-512.png`, `apple-touch-icon.png`. Never move files out of the project dir (zsh trap, §8). |
| 10 Commit + push | `git add -A && git commit && git push origin main` | Always after a successful deploy. Message: `vX.Y: weekly brain refresh <date> — N repriced, M added, K phantoms removed`, ending with the Claude co-author trailer. `.gitignore` already excludes backups, audit dumps, scratch, `_pending/`, `_gaps/`, `_ov_updates/`, `.netlify/`, and iCloud `* 2.*` duplicates. |

Ad-hoc panels used when research disagrees: `_tiebreak_<date>.js` (3 lenses — brand India store / major retailer / India tech press — per disputed family), `_roundprice_audit_<date>.js` + `_apply_roundprice_<date>.py` (re-source round-price anchors; lower always, raise only with good provenance at medium/high confidence, +20% cap, idempotent via `live_source` stamp), `_gap_pricecheck_<date>.js`, `_fix_margin_floor_<date>.py`, `_repair_ceilings_<date>.py`.

### 5.2 Older / one-time tooling still in the repo

| Script | Purpose (historical) |
|---|---|
| `_rate_refresh_workflow.js` + `_apply_updates.py` | Full-DB live refresh (v4.5, 2026-06-25): 167 batches, override-protection, sanity caps (high-conf +40%, medium +25%, reject low), depreciation fallback |
| `_gap_audit_workflow.js` (old form) + `_add_missing.py` | Completeness audit (v4.7): 24 brand/series agents, +646 entries |
| `_fix_storage.py` | Storage-variant overpay cleanup (v4.6): +8%/tier storage premium, phantom removal |
| `_apply_brain.py` | One-time override → computed migration (v5.7, 2026-08-05); calibrated `margin_by_age` from the 100 overrides; stashed `_override_prev` |
| `_apply_scoped.py`, `_apply_reprice.py`, `_apply_pending_2026-08-17.py` | Hot-set refresh (v5.5) and Aug-17 follow-ups |
| `_weekly_2026-07-03/06/20.py`, `_refresh_fold8_s25_2026-07-06.py`, `_add_t4lite_*`, `_add_note15se6_*` | Early weekly runs and Shane-flagged gap fills; the Fold8/S25 script encoded the market-signal rules |
| `_review_overrides.json`, `_override_keys.json` | Override-divergence review list and the 100 override keys (historical — overrides are retired) |
| `_generate_xcode_proj.py` | Generated `ios_app/` |

### 5.3 Research prompt conventions (what the agents are told)

Every fetch/critic/verify/refute prompt embeds the same BRAIN block: resale definition, buyback definition, "buyback must sit 55–80% of resale or one number is wrong", the Cashify 40% widget trap, the round-price trap, and "conservative is the safe error". Schemas are strict JSON with `additionalProperties:false`. Agents write their batch file to disk **and** return it. Fetch/critic run on Sonnet; outlier verification and sibling repair run on Opus.

Rules baked into the prompts: existence may be rejected only on hard evidence (brand India line-up or major India outlet), never on a missing Cashify/OLX page; a phone launched <3 months ago legitimately has no used listings; never invent a buyback as a fraction of resale (null is honest); price the exact RAM/storage in the key and say so if a different trim was found; report official new price as `NEW=<num>`.

---

## 6. Guardrails (load-bearing — do not remove)

### 6.1 Move caps in `_apply_brain_weekly.py`

| Guard | Value | Why |
|---|---|---|
| Single-week DROP cap | −20% | Damps noise; market softening is the safe direction |
| Single-week RISE cap | **+8%**, remainder flagged for Shane | Web research reliably anchors to OLX asking / Cashify refurb and over-raises. On 2026-08-30 all 14 blocked rises were subsequently refused or lowered by independent verification — zero survived. Re-measure this every week. |
| Resale ceiling | A1 ≤ resale × 0.92 (≥8% margin) | Never pay more than the phone re-sells for |
| New ceiling | A1 ≤ new × 0.85 | Never pay near new price |
| **Cap ORDER** | week caps first, then **re-assert the hard ceilings LAST** | Bug found 2026-08-17: applying the −20% floor after the ceilings floored 3 models *above* resale×0.92 after a >20% resale collapse — a guaranteed loss per unit |
| Inflated-resale hold | refuse any rise when buyback < 55% of resale | A wide spread means resale is inflated |
| Incoherent-spread filter | drop buyback > 85% of resale | No buyer pays that; 16 of 23 "we lose to Cashify" alarms were bogus |
| Echoed-estimate detection | resale == existing anchor AND buyback == exactly 50% → buyback dropped, entry left `estimated` | The agent echoed the prior estimate instead of researching |
| Cashify 40% template | drop buyback == 40% of known new (±1%) | See §8.1 |
| resale ≤ buyback | skip entry | Incoherent pair |
| Non-existence verdict | **never auto-remove**; hand-verify; `VERIFIED_REAL` set is never dropped | Critic "does not exist" verdicts were wrong 5 of 6 times (2026-08-10) |
| Storage inversion (within the week's changes) | raise the bigger variant to the smaller's A1, bounded by its own ceilings | A1 must not fall as storage rises |

### 6.2 Gap-add rules (`_add_gaps.py`)

Real India launch confirmed by critic; resale present; brand in allow-list; dedupe by key and by normalised display name; tier normalised to series majority; margin via `margin_by_age` with C/D floor; A1 capped at new×0.85; `net_new_inr = int(new)` exact (the script used to round to ₹100 and manufactured the fabrication signature — fixed 2026-08-30); `triangulated:false` does **not** block a new entry (it only gates raises) — record it as `estimated` instead of leaving no quote.

### 6.3 Outlier verification rules (`_apply_verified_*.py`)

- `grant` (capped rise was too small): needs `triangulated` at medium/high confidence; bounded by resale×0.92, new×0.85 and +20% from where the model started the week.
- `refuse` or `hold` on a rise: roll back to week-start A1.
- `lower`: always applied (no confidence bar), bounded by −20% band from week-start but never pushed back above the hard ceilings.
- `remove`: only when `exists_final == 'no'` **and** confidence high, with the brand's line-up named.
- Verification pays in both directions: 2026-08-24 rolled back 10 unsupported rises and granted 15 moves the caps had wrongly suppressed.

### 6.4 Invariants checked at finalize (must all be 0)

`a1_above_new` (A1 ≥ net_new) · `zero_or_broken` A1 · `storage_inversion` (bigger storage computing below smaller; repaired by raising the bigger variant within its own ceilings, else pulling the stale smaller sibling DOWN — never levelling UP onto fresh research) · `resale_le_buyback` using `market_resale_observed` · both files parse to identical JSON · 0 overrides auto-changed.

---

## 7. Provenance vocabulary

`live_source` prefixes tell you which pass last touched an entry: `BRAIN <date>` (weekly refresh), `VERIFIED <date> (<verdict>)` (outlier pass), `Added <date> (gap-audit+critic)`, `SIBLING REPAIR <date>`, `CEILING FIX <date>`, `ANCHOR AUDIT <date>`, `Cashify ...` (legacy live refresh), `| margin floored to tier X default` (suffix). The bracketed tag at the end (`[margin]`, `[resale*0.92]`, `[new*0.85]`, `[week-cap-down]`, `[rise-cap+flagged]`, `+hard-ceiling`, `+inv-fix`, `+band±20%`) names the cap that bound.

---

## 8. Traps and lessons (chronological, with the fix)

1. **Cashify refurb retail ≠ resale** (pre-v5.7). Using it as resale overpriced every old phone. Fix: the resale definition in §2.1.
2. **Web new prices are unreliable** (v5.6, Aug 2026). Agents grabbed too-low iPhone 15/16 prices and false-flagged Shane's rates as "above new". Shane's prices are authoritative; store in `net_new_inr`.
3. **OLX asking ≠ sold.** Research inflates upward. Fix: +8% rise cap, −20% drop cap, refurb-cohort caps (+40% high-conf / +25% medium / reject low) in the old full refresh.
4. **Critic "does not exist" is usually wrong** (2026-08-10: 5/6). Fix: never auto-remove; `VERIFIED_REAL` list (Razr Fold, Moto Signature, Z Fold8 family, Pixel 11 family, ROG Phone 9 12/256).
5. **Cap order bug** (2026-08-17): week floor after hard ceilings → paying above resale. Fix: ceilings re-asserted last. Same class in `_finalize_meta.py`: storage-inversion repair levelled the bigger variant UP to a stale sibling → now bounded by own ceilings, else lower the smaller sibling.
6. **Cashify "Approx. Buyback Value" widget is a template** (2026-08-17): exactly 40% of the listed price on Fold8, Fold8 Ultra and iPhone 17 Pro Max. Since resale ≈ 80% of new, it lands at exactly 50% of resale — which is what the echo detector had been catching for two weeks. Those Cashify price pages also show wrong new prices (iPhone 17 Pro Max ₹1,37,900 vs Apple's ₹1,49,900). A competitor buyback is real only from a `cashify.in/sell-old-mobile-phone/...` quote flow.
7. **Margin decomposition**: the 0.18 → 0.099 margin shift alone is +7.4% on A1, so most "market moved" rises were a margin artifact. Decompose before believing a rise.
8. **Round `net_new_inr` = fabrication signature** (2026-08-24): 47 gap-added entries had `new=40,000 / resale=32,000` (exactly 80%). Re-sourcing 38 corrected 16 and removed ₹48,200 of buyback (Samsung F70 Pro "₹42,000" was ₹30–40k; Infinix Note Edge "₹25,000" was ₹19,999). Scan `new % 1000 == 0` after every gap-add — but the Pixel 11 family passed unchanged, so it flags suspicion, not guilt.
9. **Do not reject a launch price for being 2–3× its predecessor** (2026-08-24): a 9-agent, 3-lens panel confirmed the 2026 budget step-up is real (iQOO Z11, Pova 8 Pro, Poco M8x). Verify against the brand India store.
10. **Tier drift on new entries** (2026-08-24): the finder gave iQOO Z11 and Pova 8 Pro tier B against 14/14 and 22/22 existing C entries; OnePlus 15R got A while 12R/13R are B. Fix: series-majority normalisation.
11. **C/D margin floor missed by gap-adds** (2026-08-24): 130 entries at 0.099 instead of 0.25/0.30. Fix: floor applied in every script.
12. **Phantom variants and round prices are ONE bug** (2026-08-30): a past gap audit invented the next storage tier and priced it by extrapolation. **Tell: a 512GB or 1TB tier paired with the WRONG RAM** (Find X9 12/512, Neo 10 Pro 12/512, Phone 3a Pro 12/512, Reno 13 8/512, Pixel 10 Pro 16/1TB, F7 Ultra 12/512, V50 8/512, Realme 14 Pro+ 8/512). Scan for it directly.
13. **Removal and repair are one operation** (2026-08-30): deleting a phantom leaves a hole where a real variant belongs (RT loses a counter-quote). 8 removed → 6 real variants researched and added.
14. **`_add_gaps.py` was rounding new prices to ₹100** → ₹34,999 stored as ₹35,000, manufacturing the very signature the audit hunts. Fixed; many of the 233 remaining round entries are ₹1 artifacts, and 0 bind an A1 — measure whether a ceiling binds before spending research on it.
15. **`triangulated:false` must not gate a new entry** the way it gates a raise (no live price to protect).
16. **`resale_target_a1` is back-solved after a cap** → use `market_resale_observed` for any resale comparison.
17. **iPhone 16 256GB quote was really the 128GB price; Pixel 10a was priced off its ₹49,999 MRP sticker** (2026-08-24 refuter catches) — variant match and MRP-vs-street are standard refute checks.
18. **zsh word-split trap**: `for k in $KEEP` does not split in zsh; a keep-list loop silently moved the whole publish set into the stash. Deploy by copying the 7 files to a scratch dir; use `${=KEEP}` or an explicit list if looping.
19. **Deploy without commit left git 4 versions stale** (v5.4 vs live v5.8, Aug 2026). Always commit + push after deploy.
20. **iCloud duplicates** (`* 2.*`, `* 2/`) appear next to tracked files and are git-ignored; several project files are iCloud-evicted (0 B on disk until read).

---

## 9. Version history (from `_meta` changelogs and git)

| Version | Date | What |
|---|---|---|
| v2.4–2.9 | Apr–May 2026 | Filled 2018–2022 eras; removed fake 2TB / 512 variants; Vivo V50 family corrected ("V50 Pro" does not exist) |
| v3.0 | May 2026 | 96 hot models live-verified on Cashify refurb; anchors dropped 10–28% |
| v3.1 | May 2026 | Mode 0: `cashify_exchange × (1 + RT premium S8/A10/B12/C14/D16)` |
| v3.2 | May 2026 | Shane-calibrated: 100 `rt_buyback_a1_override` rates (iPhone 14 128 ₹26,500, iPhone 12 64 ₹16,000, S24 Ultra 256 ₹55,000); RT multipliers over Cashify 1.52–1.80 iPhone, 1.38–1.45 Android |
| v3.3 | May 2026 | Warranty tier (+13%); iPhone 15 128 ₹39,000/₹44,000; S25 Ultra ₹66,700/₹75,000 |
| v3.4 | May 2026 | Rate trim 0.90 / 0.88 Pro / 0.855 Pro Max & Ultra; Shane-confirmed rates protected |
| v3.5–3.6 | May–Jun 2026 | Vivo V60 variants; +55 entries incl. Infinix/Tecno/Lava first added |
| v4.0–4.3 | Jun 2026 | Full recalibration; Flipkart iPhone price-drop (−25–35%); iPhone 13 to resale-anchored; iPhone 17 family reset (A1 was above MRP) |
| v4.5 | 2026-06-25 | Full-DB live refresh: 1,566 attempted, 1,224 verified, 100 overrides protected, 56 flagged |
| v4.6 | 2026-06-25 | Storage-variant cleanup: 3 phantoms removed, 53 stale variants repriced at +8%/tier storage premium |
| v4.7 | 2026-06-25 | Gap audit +646 → 2,209 entries |
| v4.8–5.3 | Jul 2026 | Oppo F31, N6/Reno 16, M47/Turbo 5, T4 Lite, Note 15 SE; **v5.2 market-signal refresh** (Fold8 imminent haircut; S25 Ultra Prime Day held) |
| v5.4 | 2026-07-20 | Live refresh, UI overhaul, customer single-offer mode, iOS app project |
| v5.5–5.6 | 2026-08-05 | Hot-set refresh (449 models, 311 updated); Shane-corrected iPhone 15/16 new prices |
| **v5.7** | **2026-08-05** | **BRAIN**: 100 overrides → computed A1 from real resale; `margin_by_age` calibrated; `_override_prev` stashed |
| v5.8 | 2026-08-07 | Gap audit +67 → 2,293; PWA + app scaffolds |
| v5.9 | 2026-08-10 | Weekly: 86 repriced, 3 added; Razr Fold falsely flagged non-existent → kept; phantom F70 Pro rejected |
| v6.0 | 2026-08-17 | Weekly: 87 repriced, 16 added (Pixel 11 family); asymmetric caps; cap-order bug fixed; 34 rises capped; 9 existence claims held |
| v6.1 | 2026-08-17 | Hand-verified: 7 phantoms removed, Fold8 confirmed, Cashify widget proven fake, iPhone 17 Pro rises refused |
| v6.2 | 2026-08-24 | Weekly: 86 repriced, 10 added; 3 verification passes (outliers, round-price anchor audit, tie-break panel); 6 phantoms removed; C/D floor on 133 entries; tier normalisation |
| **v6.3** | **2026-08-30** | Weekly: 89 repriced, 7 added, 8 phantoms removed, 6 sibling variants added, 7 ceilings corrected; rounding bug fixed; all 14 blocked rises refuted |

---

## 10. Counter-side skill (`buyback-brain` SKILL.md, Jul 6 2026)

This is the **manual live-quote methodology** Claude follows when Shane asks "iPhone 13 ka rate" in chat. It predates the DB brain and uses Cashify + tier premium; the DB brain (§2) supersedes it *for DB pricing*. Both coexist: the skill for one-off live quotes and inspection, the DB for the counter tool.

### 10.1 Hard enforcement
No quote from memory, ever. First response to any rate query = three parallel live calls: Amazon India price search, Flipkart price search, `cashify.in/sell-old-mobile-phone/<brand>/<model>` fetch (fallback: search "Cashify <model> sell price"). Re-check if 30+ min passed, a different model, or a reused earlier quote. If all three fail: say so; xlsx fallback only with the "stale April 2026 baseline, live-verify before commit" disclaimer.

### 10.2 Five steps
- **A — New anchor:** `NET_NEW = min(Amazon listed − bank discount − coupon, Flipkart listed − bank − coupon − SuperCoins)`. Ignore exchange offers and no-cost EMI. Discontinued → Cashify Store refurb as proxy ceiling. Platforms >15% apart → take the lower. Apply §2.5 market-event rules.
- **B — Cashify benchmark:** the "Get up to ₹X" quote for the *same* condition tier. Grade map: A1/A2 = Excellent, B = Good, C = Good-lower/Fair, D = Fair, E = Not working. Cross-check OLX sold, Cashify Store, Quikr; >25% Cashify-vs-OLX gap → investigate.
- **C — RT quote:** `RT_QUOTE = Cashify × (1 + tier premium)`: S +8–12%, A +6–10%, B +4–8%, C +3–5%, D match or below. Rationale: convenience + trust + cross-sell; Cashify's pickup inspection typically cuts 10–20%.
- **D — Sanity:** `RT_RESALE_TARGET = RT_QUOTE × 1.20` must be `< NET_NEW × 0.80`; else reduce premium in 2% steps, then match Cashify, then reject.
- **E — Final:** `× grade multiplier (1.00 / 0.90 / 0.80 / 0.65 / 0.45 / E 0.15–0.25) × (1 − Σ deductions)`, round down for clean optics.

### 10.3 Deduction matrix (skill)
No box −3 · no charger −2 · no bill −5 · light screen scratches −5 · heavy −10 · single dent −5 each · 3+ dents −15 · battery 80–89 −5 / 70–79 −10 / <70 −20 · front lens scratch −5 · rear lens crack −10 · rear camera dead −25 · charging port −10 · speaker −10 · mic −10 · touch dead zone −15 · display dot/line/pressure mark −25 · cracked back (functional) −8 · hairline screen crack −30 · heavy crack −50 · rooted/jailbroken −15. **REJECT:** FRP/iCloud locked, CEIR blacklisted, IMEI mismatch box/bill, customer refuses ID/signature.

### 10.4 Verification protocol (before money changes hands)
1. IMEI `*#06#` = box sticker = bill (both IMEIs on dual SIM); mismatch → reject.
2. CEIR check at `ceir.gov.in` → BLOCKED/STOLEN = reject, say "system mein issue hai", never reveal suspicion.
3. Account locks: Apple ID + Find My off; Samsung/Google accounts; Mi account; factory reset → FRP screen = reject; Huawei ID; Vivo/Oppo/Realme brand accounts.
4. 15-minute function test in front of the customer: touch corners, white/black screens, all cameras + flash + 4K, speaker/earpiece/mic, charging (wired + wireless), sensors, SIM 4G/5G, BT/WiFi, buttons, vibration.
5. Battery health: iPhone Settings → Battery; Samsung Members diagnostics; Android `*#*#4636#*#*` or AccuBattery. <80% deduction, <70% major.
6. Kit audit: box (IMEI match) −3%, charger −2%, cable −1%, earphones −1%, SIM pin −₹50, bill −5%.

### 10.5 Red flags → reject politely
No ID; IMEI mismatch; CEIR blacklisted; refuses unlock/reset; bill in another name; hurry / "kuch bhi de do"; multiple phones at once; nervous behaviour; ID/face mismatch; unusual region/language settings. Then: return phone, note ID + IMEI in register, note CCTV timestamp, inform police on repeat patterns.

### 10.6 KYC and receipt
ID copy (Aadhaar/PAN/DL front+back), IMEI register entry, duplicate receipt, ownership declaration signature, customer photo with phone for >₹25k. Receipt template = the one printed by the tool (§3.2). Note: the skill's template lists phone 7895721271 while the tool prints 9719002127 — confirm which is current.

### 10.7 Negotiation playbook (short)
Show live screens. "Cashify ₹X de raha hai" → live-check in front of them, then Cashify + premium. "₹Y ka liya tha" → show current new price. "Online ₹Z" → OLX asking ≠ sold, 30-day-old listings. Keep a ₹500–1,000 cushion, release as "final for today". Walk away at +10% over base (90% return) or after 30 min. Exchange with a new phone → up to +5% extra premium.

### 10.8 Resale channels
In-store 20–25% (1–4 wk) · WhatsApp regulars 18–22% (1–2 wk) · OLX/Quikr 15–20% (1–3 wk) · Cashify B2B 8–12% (same day) · Delhi/Meerut refurbisher 10–15% (repair grade) · Karol Bagh/Gaffar parts (grade E). Resale target = `min(Cashify Store × 0.95, OLX sold avg × 1.05)`, default `RT_QUOTE × 1.20`.

### 10.9 Register
`references/buyback_register.xlsx`: Active Inventory (auto days-held, yellow >15 d, red >30 d), Sold History (margin ₹/% formulas), Indicative Rates (60+ models, April 2026 baseline — fallback only), Monthly Summary (KPIs by brand and channel). Buyback → Active; resold → move to Sold; month-end review; >30 days → discount or B2B.

### 10.10 Tier reference (skill)
S: iPhone, Samsung S/Z (60–70% 1-yr hold; aggressive buy). A: OnePlus flagship, Pixel, Samsung A75, iPad (45–55%). B: Xiaomi 14/15, Nord, Vivo X, Reno, Nothing, Moto Edge/Razr (35–45%; verify hot model). C: Vivo Y/V, Oppo A, Realme C/Narzo, Redmi Note, Poco (25–35%; low quote, fast resale). D: itel, Lava, Micromax, Karbonn, Tecno/Infinix entry (15–25%; avoid). X: old Honor, smuggled, China-only ROM → reject.

Note: the skill's tier premiums (S +8–12 …) differ from the engine's `RT_PREMIUM_OVER_CASHIFY` (S8/A10/B12/C14/D16) — the engine's table applies only to the (now inert) cashify_exchange mode.

---

## 11. Operations and infrastructure

| Item | Value |
|---|---|
| Project dir | `/Users/shane/Documents/Claude/Projects/rt buyback tool` (iCloud-synced) |
| Live site | `https://rt-buyback-tool.netlify.app` — Netlify site `rt-buyback-tool`, id `7b706fe7-9260-4d82-a0ff-263413316382`, `.netlify/state.json` |
| Custom domain (planned) | `buyback.rajdhanitelecom.com` via CNAME → `rt-buyback-tool.netlify.app` (`_SUBDOMAIN-SETUP.md`). Needs Shane's Netlify + DNS access; not verified live as of this export. |
| GitHub | `https://github.com/Shanicrantz/rt-buyback-tool.git`, branch `main`, 91 tracked files |
| Local preview | `.claude/launch.json` → `python3 -m http.server 8471` (`rt-buyback-static`) |
| Publish set | exactly 7 files (see §5.1 step 9) |
| Backups | `*.backup-<date>.{json,html}`, `*.prefill-backup.*` — git-ignored, local only |
| Commit trailer | `Co-Authored-By: Claude <model> <noreply@anthropic.com>` (memory says Opus 4.8; current sessions use Fable 5.1) |
| Scheduled task | `rt-buyback-weekly-refresh`, Mon 2 PM, prompt at `~/.claude/scheduled-tasks/rt-buyback-weekly-refresh/SKILL.md` (updated 2026-08-07) |
| Password gate | in-page SHA-256; not a security boundary |
| Mobile app (Capacitor) | `_mobile-app/` — app id `com.rajdhanitelecom.buyback`, name "RT Buyback", loads the custom-domain URL, `offline.html` fallback. `RUNBOOK.md` covers Play (AAB, keystore) and App Store (Apple 4.2.2 minimum-functionality risk; mitigations: bundle offline, add native share / Face ID). Recommended order: PWA → Google Play → App Store. |
| iOS project | `ios_app/RTBuyback.xcodeproj` — SwiftUI + `WKWebView` loading a bundled `www/` copy (opens `whatsapp:`, `tel:`, `mailto:`, `wa.me` externally). **Bundled copy is stale: v5.4 / 2026-07-20 vs live v6.3.** |
| Register | `buyback_register.xlsx` inside the skill's `references/` (not in repo) |

Permissions already granted in `.claude/settings.local.json`: backup `cp` commands, `git diff`, `python3 -c` one-liners, reads under `~/.claude`.

---

## 12. Open items and known risks

1. **Client-side DB** with margins is readable by anyone with the URL; password gate is cosmetic. Shane has not asked for a fix.
2. **Custom domain** `buyback.rajdhanitelecom.com` — CNAME status unknown; the Capacitor app points at it and will fail until it resolves.
3. **iOS bundled `www/index.html` is 4 versions stale** (v5.4). Either re-copy on each deploy or switch the shell to the live URL.
4. **592 entries still `estimated`** — live-verify on first transaction; the weekly scope rotates them in by value.
5. **233 round `net_new_inr` values** remain (0 binding) — latent hygiene.
6. **`_review_overrides.json` is historical** (Aug 5 divergences against overrides that no longer exist).
7. **Phone number discrepancy** between skill receipt (7895721271) and tool receipt (9719002127).
8. **Skill vs DB brain**: the skill's Cashify + premium method and the DB's resale ÷ (1+margin) method can give different numbers for the same phone; the DB is the calibrated one.
9. **Research upward bias is structural** — every week re-measure how many capped rises survive verification; if that number stops being ~0, the cap can be loosened, not before.
10. Long-tail (~1,576 entries) still carries its 2026-06-25 calibration; the weekly scope only touches S/A and ≤24-month models plus stale rotation.

---

## 13. Quick-reference card

```
A1 = resale ÷ (1 + margin_by_age)          margin: <24mo .099 | 24–54mo .19 | 54mo+ .298 ; C ≥ .25, D ≥ .30
A1 ≤ resale × 0.92 ; A1 ≤ new × 0.85       (assert LAST, after the ±week caps)
week move: drop ≤ 20%, rise ≤ 8% (flag rest) ; verify capped rises, big drops, existence, missing, round prices
resale = local SOLD price (not OLX asking, not Cashify refurb) ; buyback_market must be 55–80% of resale
Cashify "Approx. Buyback Value" = 40% template → null ; round new price (…000) → re-source
phantom tell = 512GB/1TB with wrong RAM ; remove only on brand line-up evidence ; then add the real variant
new entry: tier = series majority ; net_new exact ; weak provenance → 'estimated', never 'skip'
grades A1 1.00 / A2 .90 / B .80 / C .65 / D .45 ; kit −3/−2/−5 ; batt 0/−5/−10/−20 ; wty +13% × age factor ; foldable −12% × (1−wty)
files: phone_db.json == const DB line in index.html ; publish 7 files via scratch dir ; then commit + push
```
