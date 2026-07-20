#!/usr/bin/env python3
"""2026-07-06 market-signal price refresh.
Signals: (1) Galaxy Z Fold 8/Flip 8 Unpacked Jul 22 -> outgoing Fold/Flip softening;
(2) S25 Ultra Amazon Prime Day flash (temporary) + structural post-S26 decline.
Auto-refresh NON-OVERRIDE Fold/Flip/S25-FE to live Cashify (with pre-launch haircut).
NEVER change overrides -> flag divergences in _review_overrides.json. Adds _meta.market_signals."""
import json, shutil, os, re

DIR = os.path.dirname(os.path.abspath(__file__))
DB_JSON = os.path.join(DIR, "phone_db.json"); INDEX = os.path.join(DIR, "index.html")
OVR = os.path.join(DIR, "_review_overrides.json"); TODAY = "2026-07-06"
DEFAULT_MARGIN = {"S":0.18,"A":0.2,"B":0.22,"C":0.25,"D":0.3}
RT_PREM = {"S":0.08,"A":0.10,"B":0.12,"C":0.14,"D":0.16}

def a1(e):
    t=e.get("tier"); m=e.get("target_margin",DEFAULT_MARGIN.get(t,0.22))
    if e.get("rt_buyback_a1_override"): return round(e["rt_buyback_a1_override"]/100)*100
    if e.get("cashify_exchange"): return round(e["cashify_exchange"]*(1+RT_PREM.get(t,0.08))/100)*100
    if e.get("resale_target_a1"): return round(e["resale_target_a1"]/(1+m)/100)*100
    if e.get("refurb_retail_anchor_excellent"): return round(e["refurb_retail_anchor_excellent"]*e.get("market_factor",0.88)/(1+m)/100)*100
    return None

for src,dst in [(DB_JSON,"phone_db.backup-2026-07-06-v51.json"),(INDEX,"index.backup-2026-07-06-v51.html")]:
    dp=os.path.join(DIR,dst)
    if not os.path.exists(dp): shutil.copy2(src,dp); print("backup ->",dst)

db=json.load(open(DB_JSON,encoding="utf-8"))
old_a1={k:a1(v) for k,v in db.items() if not k.startswith("_")}

SRC = "Live-check 2026-07-06 (Cashify refurb/exchange). Z Fold8/Flip8 Unpacked Jul-22 -> pre-launch haircut applied to outgoing gen."
# field 'r'=resale_target_a1, 'f'=refurb_retail_anchor_excellent. status: v=verified, e=estimated(scaled)
REFRESH = {
 # FOLD 7 (current, becoming outgoing) — anchor live refurb ~x0.95
 "samsung_z_fold_7_256":("r",115000,"v","Cashify refurb 256 Rs1,21,499, exchange Rs95,050; new Rs1,74,999 (sale 1,61,855). -5% pre-Fold8."),
 "samsung_z_fold_7_512":("r",123000,"e","Scaled from 256 by MRP (1,86,999/1,74,999); exchange ~Rs96,000. Pre-Fold8 trim."),
 "samsung_z_fold_7_1tb":("r",142000,"e","Scaled from 256 by MRP (2,16,999). Pre-Fold8 trim."),
 # FOLD 6 (prev gen, softening hard) — live refurb x0.93
 "samsung_z_fold_6_256":("r",78000,"v","Cashify refurb 256 Rs84,399, exchange Rs69,580; street ~Rs1,09,999 (was 1,64,999). -7% pre-Fold8."),
 "samsung_z_fold_6_512":("r",82000,"e","Cashify exchange 512 ~Rs71,600; scaled. Pre-Fold8 trim."),
 "samsung_z_fold_6_1tb":("r",86000,"v","Cashify refurb 1TB Rs93,399, exchange Rs73,870. -7% pre-Fold8 (DB was Rs108k, above live)."),
 # FOLD 4 (2022, discontinued) — was overpriced vs live exchange Rs31,240; trim + fix 256>512 inversion
 "samsung_z_fold_4_256":("f",49600,"v","Cashify exchange 256 Rs31,240; refurb anchor trimmed from Rs66,500 (stale-high) to align."),
 "samsung_z_fold_4_512":("f",50000,"e","Scaled above 256 to fix prior 256>512 inversion."),
 "samsung_z_fold_4_1tb":("f",53600,"e","Scaled; kept monotonic above 512."),
 # FLIP 7 (current, outgoing) — live refurb x0.95
 "samsung_z_flip_7_256":("r",66500,"v","Cashify refurb 256 Rs70,099; new Rs1,09,999 (sale 99,999). -5% pre-Flip8."),
 "samsung_z_flip_7_512":("r",73500,"e","Scaled from 256 by MRP (1,21,999). Pre-Flip8 trim."),
 # FLIP 7 FE (limited resale data) — modest -10% pre-launch trim
 "samsung_z_flip_7_fe_128":("r",53000,"e","Cashify exchange Rs25,560; new Rs89,999. -10% pre-Flip8 (thin refurb data)."),
 "samsung_z_flip_7_fe_256":("r",58500,"e","new Rs95,999. -10% pre-Flip8; monotonic above 128."),
 # FLIP 6 (prev gen) — live refurb x0.93
 "samsung_z_flip_6_256":("r",47000,"v","Cashify refurb 256 Rs50,699, exchange Rs20,280; street Rs74,999. -7% pre-Flip8 (DB Rs60k above live)."),
 "samsung_z_flip_6_512":("r",52000,"e","Scaled above 256 (MRP 1,21,999). Pre-Flip8 trim."),
 # FLIP 5 (2023, discontinued) — modest trim to live refurb
 "samsung_z_flip_5_256":("f",42000,"v","Cashify refurb 256 Rs42,499, exchange Rs17,000; trimmed to live."),
 "samsung_z_flip_5_512":("f",48000,"e","Scaled; kept monotonic above 256."),
 # S25 FE (prev-gen, S26 out) — -8% trim; Prime Day flash 44,999 temporary
 "samsung_s25_fe_128":("r",30500,"v","Cashify exchange Rs17,600; new Rs59,999 (Prime Day flash 44,999, temp). Prev-gen -8%."),
 "samsung_s25_fe_256":("r",38500,"v","new Rs65,999. Prev-gen -8%."),
 "samsung_s25_fe_512":("r",43500,"e","new Rs77,999. Prev-gen -8%; monotonic."),
}

changes=[]
for k,(fld,val,st,note) in REFRESH.items():
    if k not in db: print("MISSING key, skip:",k); continue
    e=db[k]
    if e.get("rt_buyback_a1_override"): print("REFUSE override key:",k); continue
    field={"r":"resale_target_a1","f":"refurb_retail_anchor_excellent"}[fld]
    before=old_a1[k]
    e[field]=val; e["calibration_status"]={"v":"verified","e":"estimated"}[st]
    e["calibration_date"]=TODAY; e["live_source"]=SRC+" "+note
    after=a1(e); changes.append((k,before,after,val,field))

# guardrails
print("\n=== refreshed (A1 before -> after) ===")
bad=[]
for k,b,af,val,field in changes:
    ratio=af/b if b else 0
    flag="" if 0.45<=ratio<=1.7 else "  <<BOUND VIOLATION"
    if flag: bad.append(k)
    print(f"{k:30} {b:>7} -> {af:>7}  ({ratio:.2f}x) {field}{flag}")
assert not bad, f"bound violations: {bad}"

# monotonicity within model families
def famcheck(prefix, order):
    vals=[(s,a1(db[f"{prefix}_{s}"])) for s in order if f"{prefix}_{s}" in db]
    ok=all(vals[i][1]<=vals[i+1][1] for i in range(len(vals)-1))
    print(("OK  " if ok else "BAD ")+prefix, vals); return ok
for p,o in [("samsung_z_fold_7",["256","512","1tb"]),("samsung_z_fold_6",["256","512","1tb"]),
            ("samsung_z_fold_4",["256","512","1tb"]),("samsung_z_flip_7",["256","512"]),
            ("samsung_z_flip_7_fe",["128","256"]),("samsung_z_flip_6",["256","512"]),
            ("samsung_z_flip_5",["256","512"]),("samsung_s25_fe",["128","256","512"])]:
    assert famcheck(p,o), f"monotonic fail {p}"

# A1 < new price for entries with net_new_inr
viol=[k for k,e in db.items() if not k.startswith("_") and e.get("net_new_inr") and (a1(e) or 0)>=e["net_new_inr"]]
print("\nA1>=net_new_inr:",len(viol),viol[:5]); assert not viol

# OVERRIDE DIVERGENCE FLAGS (do NOT change values)
ovr=json.load(open(OVR,encoding="utf-8"))
FLAGS=[
 {"key":"samsung_s25_ultra_256","display":"Samsung Galaxy S25 Ultra 256GB","current":66700,
  "live_suggestion":66700,"pct_diff":5.5,
  "source":"HOLD. Prime Day flash Rs84,999 (MRP 1,29,999) is TEMPORARY (ends Jul 6); durable street ~Rs93,500 (declining post-S26). Live Cashify exchange ~Rs65,140 -> RT+premium ~Rs70,300, so override Rs66,700 is safe/conservative. net_new_inr 104000 now stale (~93,500)."},
 {"key":"samsung_s25_ultra_512","display":"Samsung Galaxy S25 Ultra 512GB","current":63300,
  "live_suggestion":68000,"pct_diff":7.4,
  "source":"DATA ERROR: 512 override (63,300) is BELOW 256 (66,700) and 1TB (69,400) -> storage inversion. Recommend raise 512 to ~Rs68,000 (between 256 and 1TB). Shane to confirm."},
 {"key":"samsung_s25_ultra_1tb","display":"Samsung Galaxy S25 Ultra 1TB","current":69400,
  "live_suggestion":69400,"pct_diff":0.0,
  "source":"HOLD. Consistent as top variant once 512 inversion fixed. Prime Day/temp-sale context same as 256."},
 {"key":"samsung_s25_256","display":"Samsung Galaxy S25 256GB","current":39200,
  "live_suggestion":39200,"pct_diff":16.0,
  "source":"HOLD (conservative). Live Cashify refurb 256 Rs53,599 -> resale-implied A1 ~Rs45,400; override Rs39,200 sits ~16% below (safe). Prev-gen (S26 out), declining. No overpay risk."},
 {"key":"samsung_z_fold_5_256","display":"Samsung Galaxy Z Fold 5 256GB","current":51100,
  "live_suggestion":51100,"pct_diff":9.0,
  "source":"HOLD. Live Cashify exchange 256 Rs52,030 -> RT+premium ~Rs56,200; override Rs51,100 ~9% below (safe). Fold 8 imminent (Jul 22) -> extra reason to keep low."},
]
have={(f.get("key")) for f in ovr}
for f in FLAGS:
    f["flagged_date"]=TODAY
    ovr=[x for x in ovr if not (x.get("key")==f["key"] and x.get("flagged_date")==TODAY)]
    ovr.append(f)
json.dump(ovr,open(OVR,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("\noverride flags appended:",len(FLAGS),"-> _review_overrides.json now",len(ovr),"entries")
# confirm no override VALUES changed in DB
for f in FLAGS:
    assert db[f["key"]]["rt_buyback_a1_override"]==f["current"], "override mutated!"
print("override values in DB: UNCHANGED (verified)")

# _meta market signals + version bump
db["_meta"]["market_signals"]={
 "updated":TODAY,
 "successor_imminent":{
   "samsung_z_fold_8__z_flip_8":{
     "event":"Galaxy Unpacked 2026-07-22 (London); India availability ~early Aug 2026 (leak-based prices: Fold8 ~Rs1.75-1.80L, Flip8 ~Rs1.10-1.20L, not official)",
     "effect":"Outgoing Fold 7/6 & Flip 7/6 resale softening pre-launch -> buyback anchors trimmed 5-10% to live Cashify. Fold 5 (override) already conservative, held.",
     "confidence":"high (Tom's Guide/TechTimes/SamMobile/Digit + Samsung Malaysia leak; adversarially verified)"}},
 "temporary_sale_active":{
   "amazon_prime_day_2026_jul4_6":{
     "effect":"S25 Ultra 256 flash Rs84,999 (MRP 1,29,999), S25 FE Rs44,999, Z Flip 7 Rs95,990 — TEMPORARY, reverts after Jul 6. Do NOT permanently reset anchors to sale lows; cap buyback at (sale_new - margin) so RT never overpays during a live sale.",
     "s25_ultra_note":"Durable street ~Rs93,500 (declining post-S26). Override Rs66,700 held (safe vs live Cashify)."}},
 "rule":"When a successor flagship is confirmed <~4 weeks out, trim outgoing-gen resale anchors 5-10%. Festival-sale (Prime Day/BBD) lows are a TEMPORARY NET_NEW floor: cap buyback below it, but revert anchor to trend after the sale unless it is a confirmed permanent price cut."
}
db["_meta"]["version"]="5.2"; db["_meta"]["last_calibration"]=TODAY
db["_meta"]["v5_2_changelog"]=(
 "Market-signal price refresh (2026-07-06). SIGNAL 1: Galaxy Z Fold 8/Flip 8 Unpacked Jul 22 (imminent) -> "
 "trimmed outgoing NON-OVERRIDE anchors to live Cashify with 5-10% pre-launch haircut: Fold 7/6 (all storages), "
 "Fold 4 (also fixed 256>512 inversion), Flip 7/7FE/6/5. SIGNAL 2: S25 Ultra on Amazon Prime Day (Jul 4-6) flash "
 "Rs84,999 vs MRP 1,29,999 — confirmed TEMPORARY, so S25 Ultra OVERRIDE held (Rs66,700, conservative vs live); "
 "flagged 512<256 override inversion for Shane. Also trimmed S25 FE (prev-gen). 0 override values auto-changed; "
 "5 override divergences logged to _review_overrides.json. Added _meta.market_signals (successor-imminent + temporary-sale rules)."
)

json.dump(db,open(DB_JSON,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
compact="const DB = "+json.dumps(db,ensure_ascii=False,separators=(",",":"))+";"
lines=open(INDEX,encoding="utf-8").read().split("\n"); n=0
for i,l in enumerate(lines):
    if l.startswith("const DB = {"): lines[i]=compact; n+=1
assert n==1,f"const DB lines={n}"
open(INDEX,"w",encoding="utf-8").write("\n".join(lines))
html=open(INDEX,encoding="utf-8").read()
m=re.search(r'^const DB = (\{.*\});$',html,re.M)
assert json.loads(m.group(1))==json.load(open(DB_JSON,encoding="utf-8")),"MISMATCH"
print("\nphones:",len([k for k in db if not k.startswith('_')]),"| INLINE==DISK: True | version",db["_meta"]["version"])
print("refreshed",len(changes),"entries; flagged",len(FLAGS),"overrides. DONE.")
