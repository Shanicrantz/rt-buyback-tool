#!/usr/bin/env python3
"""Shane-flagged gap: add missing Redmi Note 15 SE 5G 6/128GB (real India base variant, MRP Rs24,999).
Anchored just below the 8/128 sibling. Syncs both files, verifies, v5.2->v5.3."""
import json, shutil, os, re
DIR=os.path.dirname(os.path.abspath(__file__)); DB=os.path.join(DIR,"phone_db.json"); INDEX=os.path.join(DIR,"index.html"); TODAY="2026-07-06"
for src,dst in [(DB,"phone_db.backup-2026-07-06-v52.json"),(INDEX,"index.backup-2026-07-06-v52.html")]:
    dp=os.path.join(DIR,dst)
    if not os.path.exists(dp): shutil.copy2(src,dp); print("backup ->",dst)
db=json.load(open(DB,encoding="utf-8"))
K="redmi_note_15_se_5g_6_128"
assert K not in db, "already exists"
db[K]={"display_name":"Redmi Note 15 SE 5G 6/128GB","tier":"C","discontinued":False,"launch_date":"2026-04-09",
 "net_new_inr":18000,"resale_target_a1":14000,"target_margin":0.2,"calibration_status":"verified","calibration_date":TODAY,
 "live_source":"Redmi Note 15 SE 5G 6/128GB = real India BASE variant, MRP Rs24,999 (Flipkart/Mi.in/91mobiles/Beebom; launched Apr 2026, SD 6 Gen 3). Effective new ~Rs18,000 after intro/bank offers. Resale A1 set just below the 8/128 sibling. Shane-flagged missing variant."}
# reorder so the 6_128 sits before its 8_128 sibling (cosmetic; dict order)
order=list(db.keys()); order.remove(K)
i=order.index("redmi_note_15_se_5g_8_128"); order.insert(i,K)
db={k:db[k] for k in order}
db["_meta"]["version"]="5.3"; db["_meta"]["last_calibration"]=TODAY
db["_meta"]["v5_3_changelog"]="Gap fill (2026-07-06, Shane-flagged): added missing Redmi Note 15 SE 5G 6/128GB (real India base variant, MRP Rs24,999, tier C, A1 ~Rs11,700 — just below the 8/128 sibling). Base Note 15 5G confirmed 8/128+8/256 only (no 6/128)."
json.dump(db,open(DB,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
compact="const DB = "+json.dumps(db,ensure_ascii=False,separators=(",",":"))+";"
lines=open(INDEX,encoding="utf-8").read().split("\n"); n=0
for i,l in enumerate(lines):
    if l.startswith("const DB = {"): lines[i]=compact; n+=1
assert n==1
open(INDEX,"w",encoding="utf-8").write("\n".join(lines))
html=open(INDEX,encoding="utf-8").read(); m=re.search(r'^const DB = (\{.*\});$',html,re.M)
assert json.loads(m.group(1))==json.load(open(DB,encoding="utf-8")),"MISMATCH"
DEFAULT_MARGIN={'C':0.25}
def a1(e): return round(e['resale_target_a1']/(1+e.get('target_margin',0.25))/100)*100
fam=[(s,a1(db[f'redmi_note_15_se_5g_{s}'])) for s in ['6_128','8_128','8_256']]
print("phones:",len([k for k in db if not k.startswith('_')]),"| INLINE==DISK True | v",db["_meta"]["version"])
print("SE family A1:",fam,"| monotonic:",all(fam[i][1]<=fam[i+1][1] for i in range(len(fam)-1)))
print("A1 < net_new:", a1(db[K]),'<',db[K]['net_new_inr'], a1(db[K])<db[K]['net_new_inr'])
