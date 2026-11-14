#!/bin/zsh
# Official spare-part price stage (from v6.37): make its dated run folder. Not weekly - part prices do not expire in the
# engine; re-run monthly or when Shane asks. Carries the previous parts run's browser exports (realme/Xiaomi/Apple keep
# their own observed dates) so a run without a browser walk still rebuilds every brand. Prints the folder path last.
set -e
ROOT="${RT_ROOT:-/Users/shane/Documents/Claude/Projects/rt buyback tool}"
T="${0:A:h}"
cd "$ROOT"
TODAY="${RT_TODAY:-$(TZ=Asia/Kolkata date +%Y-%m-%d)}"
setopt null_glob
existing=(_weekly_refresh/${TODAY}-*-parts)
[ ${#existing} -eq 0 ] || { echo "STOP: a parts run for $TODAY already exists: ${existing[*]}"; exit 1; }
[ -z "$(git status --porcelain -- phone_db.json index.html sw.js)" ] || { echo "STOP: phone_db.json/index.html/sw.js have uncommitted changes - another session may be mid-release"; exit 1; }
RUNJSON=$(python3 - "$TODAY" <<'PY'
import json,re,sys,subprocess
from datetime import date
today=sys.argv[1];cur=json.load(open('phone_db.json'))['_meta']['version'];p=cur.split('.');ver=f"{p[0]}.{int(p[1])+1}"
m=re.search(r'const C = "([^"]+)";',open('sw.js').read());assert m,'sw.js cache name not found';d=date.fromisoformat(today)
print(json.dumps(dict(version=ver,previous_version=cur,date=today,date_label=f"{d.day} {d.strftime('%B')}",old_cache=m[1],
  new_cache=f"rt-buyback-cache-v{ver.replace('.','-')}-parts-{today.replace('-','')}",git_head=subprocess.check_output(['git','rev-parse','--short','HEAD'],text=True).strip())))
PY
)
VER=$(print -r -- "$RUNJSON" | python3 -c "import json,sys;print(json.load(sys.stdin)['version'])")
W="$ROOT/_weekly_refresh/${TODAY}-v${VER}-parts"
mkdir -p "$W/research" "$W/baseline"
for f in "$T"/*.py "$T"/*.cjs "$T"/*.txt "$T"/finalize.sh; do cp "$f" "$W/"; done
print -r -- "$RUNJSON" | python3 -c "import json,sys;json.dump(json.load(sys.stdin),open('$W/run.json','w'),indent=1)"
cp phone_db.json index.html sw.js "$W/baseline/"
prev=(_weekly_refresh/*-parts(N))
for p in ${prev}; do [ "$ROOT/$p" = "$W" ] || last="$p"; done
if [ -n "$last" ]; then for f in realme-browser.json xiaomi-browser.json apple-browser.json; do [ -f "$last/$f" ] && cp "$last/$f" "$W/" && echo "carried $f from $last"; done; fi
echo "RUN FOLDER: $W"
