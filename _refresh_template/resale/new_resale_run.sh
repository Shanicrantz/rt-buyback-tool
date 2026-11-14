#!/bin/zsh
# Resale + new-launch stage: make its dated run folder AFTER this week's new-price release is installed and committed.
# Prints the folder path last. Needs a template new-price run (with run.json) whose version is the live DB version and
# whose new prices are at most 7 days old (the writer rejects older new-price references).
set -e
ROOT="${RT_ROOT:-/Users/shane/Documents/Claude/Projects/rt buyback tool}"  # RT_ROOT / RT_TODAY: dry-run overrides only
T="${0:A:h}"; TPL="${T:h}"
cd "$ROOT"
TODAY="${RT_TODAY:-$(TZ=Asia/Kolkata date +%Y-%m-%d)}"
setopt null_glob
existing=(_weekly_refresh/${TODAY}-*-resale)
[ ${#existing} -eq 0 ] || { echo "STOP: a resale run for $TODAY already exists: ${existing[*]}"; exit 1; }
! pgrep -f "collect_a.py|_market_refresh_runner.py|verify_resale.py" >/dev/null || { echo "STOP: a collector is already running (another refresh?)"; exit 1; }
[ -z "$(git status --porcelain -- phone_db.json index.html sw.js)" ] || { echo "STOP: phone_db.json/index.html/sw.js have uncommitted changes - another session may be mid-release"; exit 1; }
FREE_GB=$(df -g "$ROOT" | awk 'NR==2{print $4}')
[ "$FREE_GB" -ge 2 ] || { echo "STOP: only ${FREE_GB} GB free (need 2 GB)"; exit 1; }
RUNJSON=$(python3 - "$TODAY" <<'PY'
import json,re,sys,glob,subprocess
from datetime import date
today=sys.argv[1]
db=json.load(open('phone_db.json'));cur=db['_meta']['version']
parts=cur.split('.');assert len(parts)>=2 and all(p.isdigit() for p in parts),cur
# The new-price run that produced the live version (template runs carry run.json).
runs=[r for r in sorted(glob.glob('_weekly_refresh/*/run.json')) if json.load(open(r)).get('version')==cur and not r.split('/')[-2].endswith('-resale')]
if not runs: sys.exit('STOP: no template new-price run (run.json) for live version '+cur+'; run the weekly new-price refresh first')
np=runs[-1].rsplit('/',1)[0];npd=date.fromisoformat(json.load(open(runs[-1]))['date'])
age=(date.fromisoformat(today)-npd).days
if age>6: sys.exit(f'STOP: the live new prices are {age} days old (> 6); run the weekly new-price refresh first')
ver=f"{parts[0]}.{int(parts[1])+1}"
m=re.search(r'const C = "([^"]+)";',open('sw.js').read());assert m,'sw.js cache name not found'
d=date.fromisoformat(today)
print(json.dumps(dict(version=ver,previous_version=cur,date=today,date_label=f"{d.day} {d.strftime('%B')}",new_price_run=np,
  old_cache=m[1],new_cache=f"rt-buyback-cache-v{ver.replace('.','-')}-resale-{today.replace('-','')}",
  git_head=subprocess.check_output(['git','rev-parse','--short','HEAD'],text=True).strip())))
PY
)
VER=$(print -r -- "$RUNJSON" | python3 -c "import json,sys;print(json.load(sys.stdin)['version'])")
W="$ROOT/_weekly_refresh/${TODAY}-v${VER}-resale"
mkdir "$W"
for f in verify_resale.py augment_selected_resale.py check_special_sources.py probe_launches.py prepare_resale.py finalize.sh release_check.py compare.cjs compare_age.cjs; do cp "$T/$f" "$W/"; done
for f in variant_guard.py ram-identity-holds.json; do cp "$TPL/$f" "$W/"; done
print -r -- "$RUNJSON" | python3 -c "import json,sys;json.dump(json.load(sys.stdin),open('$W/run.json','w'),indent=1)"
print -r -- '[]' > "$W/launch-specs.json"
python3 "$ROOT/_market_refresh_runner.py" init --work "$W" | tail -1
cmp -s "$W/baseline/phone_db.json" "$ROOT/phone_db.json" && cmp -s "$W/baseline/index.html" "$ROOT/index.html"
echo "RUN FOLDER: $W"
