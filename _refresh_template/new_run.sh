#!/bin/zsh
# Make this week's dated run folder from the template, after the safety checks. Prints the folder path last.
set -e
ROOT="${RT_ROOT:-/Users/shane/Documents/Claude/Projects/rt buyback tool}"  # RT_ROOT / RT_TODAY: dry-run overrides only
T="${0:A:h}"
cd "$ROOT"
TODAY="${RT_TODAY:-$(TZ=Asia/Kolkata date +%Y-%m-%d)}"
setopt null_glob
existing=(_weekly_refresh/${TODAY}-*)
[ ${#existing} -eq 0 ] || { echo "STOP: a run folder for $TODAY already exists: ${existing[*]}"; exit 1; }
! pgrep -f "collect_a.py" >/dev/null || { echo "STOP: a collector is already running (another refresh?)"; exit 1; }
[ -z "$(git status --porcelain -- phone_db.json index.html sw.js)" ] || { echo "STOP: phone_db.json/index.html/sw.js have uncommitted changes - another session may be mid-release"; exit 1; }
FREE_GB=$(df -g "$ROOT" | awk 'NR==2{print $4}')
[ "$FREE_GB" -ge 5 ] || { echo "STOP: only ${FREE_GB} GB free on the Mac (need 5 GB; each run stores ~1 GB of evidence)"; exit 1; }
RUNJSON=$(python3 - "$TODAY" <<'PY'
import json,re,sys
from datetime import date
today=sys.argv[1]
db=json.load(open('phone_db.json'));cur=db['_meta']['version']
parts=cur.split('.');assert len(parts)>=2 and all(p.isdigit() for p in parts),cur
ver=f"{parts[0]}.{int(parts[1])+1}"
m=re.search(r'const C = "([^"]+)";',open('sw.js').read());assert m,'sw.js cache name not found'
d=date.fromisoformat(today)
print(json.dumps(dict(version=ver,previous_version=cur,date=today,date_label=f"{d.day} {d.strftime('%B')}",
  old_cache=m[1],new_cache=f"rt-buyback-cache-v{ver.replace('.','-')}-weekly-{today.replace('-','')}",git_head=__import__('subprocess').check_output(['git','rev-parse','--short','HEAD'],text=True).strip())))
PY
)
VER=$(print -r -- "$RUNJSON" | python3 -c "import json,sys;print(json.load(sys.stdin)['version'])")
W="$ROOT/_weekly_refresh/${TODAY}-v${VER}-weekly"
mkdir "$W"
for f in collect_a.py prepare_obs.py finalize.sh compare.cjs compare_age.cjs variant_guard.py release_check.py ram-identity-holds.json; do cp "$T/$f" "$W/"; done
print -r -- "$RUNJSON" | python3 -c "import json,sys;json.dump(json.load(sys.stdin),open('$W/run.json','w'),indent=1)"
cd "$W" && python3 collect_a.py init | tail -2
cmp -s baseline/phone_db.json "$ROOT/phone_db.json" && cmp -s baseline/index.html "$ROOT/index.html"
echo "RUN FOLDER: $W"
