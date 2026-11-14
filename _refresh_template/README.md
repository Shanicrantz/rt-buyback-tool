# Weekly new-price refresh: template

Used by the Thursday scheduled task `rt-buyback-weekly-refresh`, and by hand. Saved new prices expire after 7 days (`AGE_VALUE_POLICY.priceDays`). Once they expire, actual-age quotes fall back to the higher saved-resale rate, so this has to run every week.

Run from the project folder:

1. `zsh _refresh_template/new_run.sh` stops if today's folder already exists, a collector is running, `phone_db.json`/`index.html`/`sw.js` have uncommitted changes, or less than 5 GB is free. Otherwise it creates `_weekly_refresh/<date>-v<next>-weekly/` with `run.json` (version, dates, sw.js cache names, git head) and the baseline and scope. It prints `RUN FOLDER: …`.
2. In that folder, run two background processes (about 20 min on 2026-11-14):
   - `python3 collect_a.py flipkart > flipkart.log 2>&1`
   - `{ python3 collect_a.py saved && python3 collect_a.py reliance; } > saved_reliance.log 2>&1`
3. `python3 prepare_obs.py`, then `zsh finalize.sh`. Finalize runs the quote-safety resolver, makes the compact pair and the runtime files, runs every `test_*.cjs` suite one at a time (12 since v6.37) (it stops on a failure), runs `compare.cjs` and `compare_age.cjs`, then `release_check.py`. Deploy only if the last line is `RELEASE CHECK OK`.
4. Install `candidate/{phone_db.json,index.html,sw.js}`, deploy with `_build_public.cjs` and the Netlify MCP, read the live site back, then commit and push (see the task prompt).

Scope: new cash prices only. Resale, `net_new_inr`, International rows and the engine are untouched. 2+-year-old models listed above RT's known new price are reported in `old-model-markup-review.json`, not held (Shane, 2026-11-06).

Dry run without touching the project: `RT_ROOT=<scratch git copy> RT_TODAY=<date> zsh _refresh_template/new_run.sh`. The collectors still read the real `phone_db.json`; they only read it.

History: rebuilt 2026-11-14 from the v6.32 run (its folder was on the damaged 1TB drive). Fixes made since then: resale is labelled `estimated` only inside the 10-day window, the tests run one at a time, and `release_check.py` was added.

## Stage 2: resale + new launches (`resale/`, after the weekly release)

Run this after the weekly new-price release above is installed, deployed and committed, while its new prices are at most 6 days old (the writer rejects new-price references older than 7 days). It is its own release: version +1, cache name `…-resale-<date>`. It was built on 2026-11-14 (v6.36) from the v6.26 scripts on the Mac plus the v6.30 changes recovered from the 4 Nov Codex guardian transcript.

1. `zsh _refresh_template/resale/new_resale_run.sh`. It stops if today's resale folder exists, a collector is running, the DB files are uncommitted, or no template new-price run (`run.json`) produced the live version. That last stop also covers a live version that came from a parts run. It then creates `_weekly_refresh/<date>-v<next>-resale/` with `run.json` (including `new_price_run`) and the baseline and scope.
2. Resale evidence, in that folder:
   1. `python3 "$ROOT/_market_refresh_runner.py" resale --work .` (about 15 min, Cashify family pages)
   2. `python3 verify_resale.py`
   3. `python3 augment_selected_resale.py`
   4. `python3 check_special_sources.py` (GudFast X60 Pro+, Mobirapid S25 256)
3. New launches: research India phones whose **first sale** is after the last launch add and on or before today. Write each exact variant to `launch-specs.json`; the format is in `probe_launches.py`. Then run `python3 probe_launches.py`.
   - Only variants with an exact in-stock new listing fetched today are proposed. The rest go to `launch-held.json`.
   - Tier follows the series already in the DB.
   - **Every added key must also be added to `test_market_refresh.cjs`**, in the additions block (see the v6.30 Vivo and v6.36 Find X10 blocks). Otherwise that suite fails.
4. `python3 prepare_resale.py`, then `zsh finalize.sh` (the same finalize as the weekly run). The gate is `resale/release_check.py`:
   - catalogue keys may grow only by the verified launches;
   - launches must have a first sale on or before today, a non-round price, a tier and no resale;
   - fresh resale refs must be `local_resale_estimate` with a 10%/15% allowance and no `assessed_quote` evidence;
   - no competitor quote may change;
   - plus all the weekly checks (pair, suites, coverage, 8% rise pin, ≤ 40 no-age changes, no lost quotes, no new counter blocks).
5. Install, deploy, read back, commit and push as in the weekly step 4.

Resale rules (`prepare_resale.py`):
- Estimate = floor100(exact Superb ask × (1 − 10%)); 15% for C/D tiers or foldables. It is labelled an estimate and is never a sold price.
- A row whose exact page was **blocked** (HTTP 403) keeps its prior ref unchanged. It stays expired and unused.
- A row where the check found **no in-stock exact grade** moves its prior ref to `last_known_resale_price`. Neither case changes a quote, because the engine ignores refs older than 10 days.
- RAM-ambiguous rows and 4G/5G aliases never take a resale ref.

**Cashify 403s every exact variant page** (161 of 161 on 2026-11-14, also on 4 Nov). Only each family page's own selected product verifies, about 10 rows. Do not retry with other user-agents or scripted browsers; that is bot-detection evasion and the auto-mode classifier refuses it. Getting more coverage is Shane's call: approved browser checks of top models, or a second resale source.

## Stage 3: official spare-part prices (`parts/`, occasional, not weekly)

Damage deductions use `part_prices` (the brand's own India out-of-warranty part price, saved per model with source and date) wherever a brand lists the part; otherwise the tier percentage applies. Part prices do not expire in the engine, and the weekly and resale writers carry them through unchanged. Re-run monthly or when Shane asks; it was first built on 2026-11-14 (v6.37).

1. `zsh _refresh_template/parts/new_parts_run.sh`. It creates `_weekly_refresh/<date>-v<next>-parts/` with `run.json` and a baseline, and carries the last parts run's browser exports.
2. Plain-request collectors, in that folder (each saves gzipped responses with sha256):
   - `python3 collect_oneplus.py` (models in `oneplus_models.txt`)
   - `python3 collect_oppo.py` (codes in `oppo_codes.txt`)
   - `python3 collect_vivo.py` (ids read from the vivo page)
   - Samsung is fetched and parsed by `parse_samsung.py` during the build.
3. realme, Xiaomi and Apple prices load only in the browser. To refresh them, open each brand page in Chrome and walk every model, checking each detail page shows the right model. Export `name|display|back|battery|rear|front|port|speaker|fingerprint|HH:MM:SS` lines and run `python3 rows_to_json.py <rows> <brand>-browser.json <page url>`. Without a walk, the carried files keep their original dates.
   - realme: realme.com/in/support/spare-parts-price
   - Xiaomi: mi.com/in/support/spare-part-prices/ (6 pages; wait for the part rows, not the "Total ₹0" footer)
   - Apple: support.apple.com/en-in/iphone/repair, with the device and model dropdowns
   - Never read site script bundles to find APIs; the classifier refuses it.
4. `zsh finalize.sh` builds the candidate (`prepare_parts.py`), runs every suite and prints the deduction comparison (`deduction-changes.json`). Review large display drops before installing. Then install, deploy, read back, commit and push.

Rules:
- Amount = the brand's regular price (not the offer price) + its listed labour (OnePlus, OPPO). Samsung's ex-GST prices get 18% added.
- Display uses the highest screen price listed (inner screen on foldables).
- Model names match exactly. Unclear 4G/5G names stay unmatched. `ALIASES` in `build_parts.py` holds the only hand-checked mappings.
- A brand that isn't re-collected keeps its existing prices.

Known stale test: `test_quote_safety_solver.py` is hard-wired to `/Volumes/my1tb` and asserts the pre-2026-11-06 "-21% must block" rule. It is not part of the gate.
