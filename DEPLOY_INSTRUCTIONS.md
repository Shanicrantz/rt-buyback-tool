# Claude Code — Deploy Instructions for RT Buyback Tool

Yeh package Rajdhani Telecom Buyback Pricing Tool ka latest build hai (v2.8, 1371 phones).
Claude Code se Netlify pe deploy karna hai — sandbox ka network restriction yahan nahi hai,
to direct deploy ho jayega.

## Files in this folder

| File | Purpose |
|------|---------|
| `index.html` | The buyback tool — single-file app, 1371-phone DB embedded. THIS deploys. |
| `buyback_tool.html` | Identical copy of index.html (backup) |
| `phone_db.json` | Standalone DB (also embedded in HTML — not needed for deploy) |
| `pricing_engine.py` | Python pricing engine (reference only — not deployed) |

## Target site

- **Netlify project:** `rt-buyback-tool`
- **Site ID:** `7b706fe7-9260-4d82-a0ff-263413316382`
- **Team ID:** `69983de98d415bf5f85dd30c`
- **Live URL:** https://rt-buyback-tool.netlify.app
- **Password:** `rajdhani2026` (site-level password protection — already set, don't change)

## Deploy command (Claude Code — run in this folder)

The deploy is a **drag-drop / zip-deploy** style site (no Git repo, no build step).
Use the Netlify CLI:

```bash
# 1. Make sure Netlify CLI is installed
npm install -g netlify-cli

# 2. Login (opens browser for OAuth — one time)
netlify login

# 3. Deploy index.html to production
#    --dir=.  → deploys current folder (index.html is the entry)
#    --prod   → publishes to the live URL (not a preview)
netlify deploy --site=7b706fe7-9260-4d82-a0ff-263413316382 --dir=. --prod
```

If `netlify deploy` says "Project not found", link it explicitly first:

```bash
netlify link --id 7b706fe7-9260-4d82-a0ff-263413316382
netlify deploy --dir=. --prod
```

### Important: only index.html should deploy

`--dir=.` will upload everything in the folder. To keep the deploy clean
(only the HTML), either:

**Option A** — put index.html in its own subfolder and deploy that:
```bash
mkdir -p dist && cp index.html dist/
netlify deploy --site=7b706fe7-9260-4d82-a0ff-263413316382 --dir=dist --prod
```

**Option B** — deploy as-is; phone_db.json and pricing_engine.py being uploaded
is harmless (they just sit there unused — the HTML has the DB embedded).
Option A is cleaner.

## Verify after deploy

1. Open https://rt-buyback-tool.netlify.app
2. Enter password `rajdhani2026`
3. Search test queries — all should resolve:
   - `oppo f29 pro` → Oppo F29 Pro 5G
   - `iphone 11 pro max 256` → iPhone 11 Pro Max 256GB
   - `samsung s22 ultra 128` → Samsung Galaxy S22 Ultra 128GB
   - `vivo v40 pro` → Vivo V40 Pro
   - `iphone 17e 256` → iPhone 17e 256GB
4. Confirm footer/header shows the phone count is 1371

## What's in this build (v2.8)

- **1371 phones**, full coverage 2016–2026
- Year spread: 2020=134, 2021=166, 2022=203, 2023=193, 2024=311, 2025=193, 2026=40
- Fixed data errors: removed fake 2TB iPhone/Samsung variants, corrected
  iPhone 11/12 and Samsung S22 base max-storage entries
- Added missing: iPhone 11 Pro/Pro Max, iPhone 12 mini variants, iPhone Air 1TB,
  iPhone 17e, Samsung S22+, S20+/S20 Ultra/S22 Ultra missing storage tiers,
  Vivo V40 Pro/V40e/T3 Ultra
- All entries `calibration_status: "estimated"` — live-verify on first transaction

## Notes

- This is a static single-file site. No build, no framework, no env vars.
- `index.html` has the entire phone DB embedded as a JS const — `phone_db.json`
  is just a standalone copy for reference / future edits.
- Password protection is set at the Netlify project level (Site config →
  Access control). The deploy does NOT change it.
