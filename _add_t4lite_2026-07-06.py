#!/usr/bin/env python3
"""Shane-requested gap fill 2026-07-06: add Vivo T4 Lite 5G (3 variants, tier D).
Backs up current v5.0 state, adds entries, syncs both files, verifies. Bumps v5.0->v5.1."""
import json, shutil, os, re

DIR = os.path.dirname(os.path.abspath(__file__))
DB_JSON = os.path.join(DIR, "phone_db.json")
INDEX = os.path.join(DIR, "index.html")
TODAY = "2026-07-06"

# backup current (v5.0) state to distinct names
for src, dst in [(DB_JSON, "phone_db.backup-2026-07-06-v50.json"), (INDEX, "index.backup-2026-07-06-v50.html")]:
    dp = os.path.join(DIR, dst)
    if not os.path.exists(dp):
        shutil.copy2(src, dp); print("backup ->", dst)

db = json.load(open(DB_JSON, encoding="utf-8"))

NEW = {
  "vivo_t4_lite_5g_4_128": {"display_name":"Vivo T4 Lite 5G 4/128GB","tier":"D","discontinued":False,"launch_date":"2025-07-02","resale_target_a1":6500,"calibration_status":"estimated","calibration_date":TODAY,"live_source":"Vivo T4 Lite 5G launched India Jul 2 2025, Dimensity 6300, 6.74in 90Hz IPS, 6000mAh, IP64/MIL-STD. 4GB/128GB MRP Rs 9,999 (Mobigyaan/91mobiles/Smartprix). Budget tier D; A1 anchored below T4x sibling. Shane-flagged gap. Est — live-verify at counter."},
  "vivo_t4_lite_5g_6_128": {"display_name":"Vivo T4 Lite 5G 6/128GB","tier":"D","discontinued":False,"launch_date":"2025-07-02","resale_target_a1":7000,"calibration_status":"estimated","calibration_date":TODAY,"live_source":"Vivo T4 Lite 5G 6GB/128GB MRP Rs 10,999 (Mobigyaan/91mobiles, Jul 2 2025). Dimensity 6300. Budget tier D."},
  "vivo_t4_lite_5g_8_256": {"display_name":"Vivo T4 Lite 5G 8/256GB","tier":"D","discontinued":False,"launch_date":"2025-07-02","resale_target_a1":8500,"calibration_status":"estimated","calibration_date":TODAY,"live_source":"Vivo T4 Lite 5G 8GB/256GB MRP Rs 12,999 (Mobigyaan/91mobiles, Jul 2 2025). Dimensity 6300. Budget tier D."},
}
added = []
for k, v in NEW.items():
    if k in db: print("SKIP (exists):", k)
    else: db[k] = v; added.append(k)
print("added:", added)

db["_meta"]["version"] = "5.1"
db["_meta"]["last_calibration"] = TODAY
db["_meta"]["v5_1_changelog"] = (
    "Same-day gap fill (2026-07-06, Shane-flagged): added Vivo T4 Lite 5G 4/128 + 6/128 + 8/256 "
    "(launched India Jul 2 2025, Dimensity 6300 budget; MRP Rs 9,999/10,999/12,999; tier D, A1 anchored below the T4x sibling). "
    "T4 family now complete (T4, T4x, T4 Lite, T4 Ultra)."
)

json.dump(db, open(DB_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("wrote phone_db.json  phones:", len([k for k in db if not k.startswith('_')]))

compact = "const DB = " + json.dumps(db, ensure_ascii=False, separators=(",", ":")) + ";"
lines = open(INDEX, encoding="utf-8").read().split("\n")
n = 0
for i, line in enumerate(lines):
    if line.startswith("const DB = {"):
        lines[i] = compact; n += 1
assert n == 1, f"expected 1 const DB line, found {n}"
open(INDEX, "w", encoding="utf-8").write("\n".join(lines))
print("replaced const DB line in index.html")

# verify sync
html = open(INDEX, encoding="utf-8").read()
m = re.search(r'^const DB = (\{.*\});$', html, re.M)
assert json.loads(m.group(1)) == json.load(open(DB_JSON, encoding="utf-8")), "MISMATCH"
print("INLINE==DISK: True  verify OK")

# A1 sanity for new entries
DEFAULT_MARGIN={'S':0.18,'A':0.2,'B':0.22,'C':0.25,'D':0.3}
def a1(e):
    m=e.get('target_margin', DEFAULT_MARGIN[e['tier']]); return round(e['resale_target_a1']/(1+m)/100)*100
mrp={'vivo_t4_lite_5g_4_128':9999,'vivo_t4_lite_5g_6_128':10999,'vivo_t4_lite_5g_8_256':12999}
for k in mrp: v=a1(db[k]); print(f'{k:26} A1={v} MRP={mrp[k]} <MRP={v<mrp[k]} ({round(100*v/mrp[k])}%)')
print('monotonic:', a1(db['vivo_t4_lite_5g_4_128'])<=a1(db['vivo_t4_lite_5g_6_128'])<=a1(db['vivo_t4_lite_5g_8_256']))
