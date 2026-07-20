#!/usr/bin/env python3
"""Weekly refresh 2026-07-06. Adds Galaxy M47 5G + Redmi Turbo 5 (4 variants).
Backs up both files, updates phone_db.json + inlined DB in index.html in sync, verifies."""
import json, shutil, os, re

DIR = os.path.dirname(os.path.abspath(__file__))
DB_JSON = os.path.join(DIR, "phone_db.json")
INDEX = os.path.join(DIR, "index.html")
TODAY = "2026-07-06"

# STEP 0 — backups (skip if already present)
for src, dst in [(DB_JSON, f"phone_db.backup-{TODAY}.json"), (INDEX, f"index.backup-{TODAY}.html")]:
    dp = os.path.join(DIR, dst)
    if not os.path.exists(dp):
        shutil.copy2(src, dp)
        print("backup ->", dst)
    else:
        print("backup exists ->", dst)

db = json.load(open(DB_JSON, encoding="utf-8"))

# STEP 1 — new launch entries (verified India variants only, conservative anchors)
NEW = {
  "samsung_m47_6_128": {"display_name":"Samsung Galaxy M47 5G 6/128GB","tier":"B","discontinued":False,"launch_date":"2026-06-29","resale_target_a1":15500,"calibration_status":"estimated","calibration_date":TODAY,"live_source":"Samsung Galaxy M47 5G announced India Jun 29 2026, on sale Jul 4 (Amazon Prime Day). Snapdragon 6 Gen 3, 6.7in AMOLED 120Hz, 6000mAh. 6GB/128GB MRP Rs 25,999 (GSMArena/91mobiles/Croma). A1 resale est ~60% of new (fresh M-series, conservative)."},
  "samsung_m47_8_256": {"display_name":"Samsung Galaxy M47 5G 8/256GB","tier":"B","discontinued":False,"launch_date":"2026-06-29","resale_target_a1":19000,"calibration_status":"estimated","calibration_date":TODAY,"live_source":"Samsung Galaxy M47 5G 8GB/256GB MRP Rs 31,999 (GSMArena/91mobiles, Jun 29 2026). Snapdragon 6 Gen 3. A1 resale est ~60% of new."},
  "redmi_turbo_5_8_256": {"display_name":"Redmi Turbo 5 8/256GB","tier":"B","discontinued":False,"launch_date":"2026-06-19","resale_target_a1":28000,"calibration_status":"estimated","calibration_date":TODAY,"live_source":"Redmi Turbo 5 launched India Jun 19 2026 (first Turbo under Redmi brand, ~Poco X8 Pro rebrand). Dimensity 8500 Ultra, 1.5K OLED, 7540mAh 100W. 8GB/256GB MRP Rs 37,999 (Beebom/91mobiles). A1 resale est ~74% of new (fresh perf phone)."},
  "redmi_turbo_5_12_256": {"display_name":"Redmi Turbo 5 12/256GB","tier":"B","discontinued":False,"launch_date":"2026-06-19","resale_target_a1":30000,"calibration_status":"estimated","calibration_date":TODAY,"live_source":"Redmi Turbo 5 12GB/256GB MRP Rs 40,999 (Beebom, Jun 19 2026). Dimensity 8500 Ultra. A1 resale est ~73% of new."},
}
added = []
for k, v in NEW.items():
    if k in db:
        print("SKIP (exists):", k)
    else:
        db[k] = v
        added.append(k)
print("added:", added)

# STEP 4 — meta bump + changelog
db["_meta"]["version"] = "5.0"
db["_meta"]["last_calibration"] = TODAY
db["_meta"]["v5_0_changelog"] = (
    "Weekly refresh (2026-07-06). Added 4 new India launch variants: Samsung Galaxy M47 5G "
    "(Jun 29 launch, on sale Jul 4 Prime Day; Snapdragon 6 Gen 3; 6/128 Rs 25,999 + 8/256 Rs 31,999; tier B) "
    "and Redmi Turbo 5 (Jun 19, first Turbo under Redmi brand; Dimensity 8500 Ultra; 8/256 Rs 37,999 + 12/256 Rs 40,999; tier B). "
    "No mass price refresh: only 3 days since v4.9 calibration (drift = noise) and Prime Day discounts are temporary, "
    "so permanent anchors left intact to avoid chasing sale lows. "
    "Flagged for next run (verify then add): Xiaomi 17T (Jun 4, Dimensity 8500 Ultra; price unconfirmed vs same-chip Turbo 5), "
    "Redmi A7/A7 Pro 5G (Apr, budget), Redmi 17 5G, Oppo A6c. Skipped rumored: Vivo T5 Lite, iQOO Z11 (non-x)."
)

# write phone_db.json
json.dump(db, open(DB_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("wrote phone_db.json  phones:", len([k for k in db if not k.startswith('_')]))

# replace single const DB line in index.html
compact = "const DB = " + json.dumps(db, ensure_ascii=False, separators=(",", ":")) + ";\n"
lines = open(INDEX, encoding="utf-8").read().split("\n")
n = 0
for i, line in enumerate(lines):
    if line.startswith("const DB = {"):
        lines[i] = compact.rstrip("\n")
        n += 1
assert n == 1, f"expected exactly 1 const DB line, found {n}"
open(INDEX, "w", encoding="utf-8").write("\n".join(lines))
print("replaced const DB line in index.html")

# STEP 4 verify — inlined DB equals phone_db.json
html = open(INDEX, encoding="utf-8").read()
m = re.search(r'^const DB = (\{.*\});$', html, re.M)
inlined = json.loads(m.group(1))
disk = json.load(open(DB_JSON, encoding="utf-8"))
print("INLINE==DISK:", inlined == disk)
assert inlined == disk, "MISMATCH between index.html DB and phone_db.json"
print("verify OK")
