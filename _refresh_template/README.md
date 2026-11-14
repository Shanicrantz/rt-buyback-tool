# Weekly new-price refresh: template

Used by the Thursday scheduled task `rt-buyback-weekly-refresh`, and by hand. Saved new prices expire after 7 days (`AGE_VALUE_POLICY.priceDays`). Once they expire, actual-age quotes fall back to the higher saved-resale rate, so this has to run every week.

Run from the project folder:

1. `zsh _refresh_template/new_run.sh` stops if today's folder already exists, a collector is running, `phone_db.json`/`index.html`/`sw.js` have uncommitted changes, or less than 5 GB is free. Otherwise it creates `_weekly_refresh/<date>-v<next>-weekly/` with `run.json` (version, dates, sw.js cache names, git head) and the baseline and scope. It prints `RUN FOLDER: …`.
2. In that folder, run two background processes (about 20 min on 2026-11-14):
   - `python3 collect_a.py flipkart > flipkart.log 2>&1`
   - `{ python3 collect_a.py saved && python3 collect_a.py reliance; } > saved_reliance.log 2>&1`
3. `python3 prepare_obs.py`, then `zsh finalize.sh`. Finalize runs the quote-safety resolver, makes the compact pair and the runtime files, runs all 11 JS suites one at a time (it stops on a failure), runs `compare.cjs` and `compare_age.cjs`, then `release_check.py`. Deploy only if the last line is `RELEASE CHECK OK`.
4. Install `candidate/{phone_db.json,index.html,sw.js}`, deploy with `_build_public.cjs` and the Netlify MCP, read the live site back, then commit and push (see the task prompt).

Scope: new cash prices only. Resale, `net_new_inr`, International rows and the engine are untouched. 2+-year-old models listed above RT's known new price are reported in `old-model-markup-review.json`, not held (Shane, 2026-11-06).

Dry run without touching the project: `RT_ROOT=<scratch git copy> RT_TODAY=<date> zsh _refresh_template/new_run.sh`. The collectors still read the real `phone_db.json`; they only read it.

History: rebuilt 2026-11-14 from the v6.32 run (its folder was on the damaged 1TB drive). Fixes made since then: resale is labelled `estimated` only inside the 10-day window, the tests run one at a time, and `release_check.py` was added.

Known stale test: `test_quote_safety_solver.py` is hard-wired to `/Volumes/my1tb` and asserts the pre-2026-11-06 "-21% must block" rule. It is not part of the gate.
