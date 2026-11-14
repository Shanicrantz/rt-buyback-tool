#!/bin/zsh
# Weekly finalize: quote-safety resolver -> compact candidate -> runtime files -> tests (sequential, stop on failure) -> quote comparison.
set -e
ROOT="/Users/shane/Documents/Claude/Projects/rt buyback tool"
W="${0:A:h}"
cd "$W"
VER=$(python3 -c "import json;print(json.load(open('run.json'))['version'])")
OLD_CACHE=$(python3 -c "import json;print(json.load(open('run.json'))['old_cache'])")
NEW_CACHE=$(python3 -c "import json;print(json.load(open('run.json'))['new_cache'])")
grep -q "\"$OLD_CACHE\"" "$ROOT/sw.js" || { echo "sw.js cache name moved since new_run.sh - stop"; exit 1; }
node "$ROOT/_resolve_quote_safety.cjs" "$W" "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" "$VER" "$(python3 -c "import json;print(json.load(open('observations.json'))['changelog'])")" > resolve.log
# Resolver writes pretty JSON; production keeps both copies compact and identical.
node -e '
const fs=require("fs");const h=fs.readFileSync("candidate/index.html","utf8");
const m=h.match(/^const DB = (\{[^\n]+\});$/m);const db=JSON.parse(m[1]);
const pretty=JSON.parse(fs.readFileSync("candidate/phone_db.json","utf8"));
if(JSON.stringify(pretty)!==JSON.stringify(db))throw new Error("candidate pair mismatch");
fs.writeFileSync("candidate/phone_db.json",JSON.stringify(db));
const out=fs.readFileSync("candidate/index.html","utf8").replace(/^const DB = (\{[^\n]+\});$/m,()=>"const DB = "+JSON.stringify(db)+";");
fs.writeFileSync("candidate/index.html",out);console.log("compact ok",db._meta.version);'
for f in manifest.webmanifest icon-192.png icon-512.png apple-touch-icon.png; do cp "$ROOT/$f" candidate/; done
sed "s/$OLD_CACHE/$NEW_CACHE/" "$ROOT/sw.js" > candidate/sw.js
grep -q "\"$NEW_CACHE\"" candidate/sw.js
for t in "$ROOT"/test_*.cjs "$ROOT/_resolve_quote_safety.cjs"; do cp "$t" candidate/; done
cp -R "$ROOT/_test_fixtures" candidate/
[ -e candidate/_weekly_refresh ] || ln -s "$ROOT/_weekly_refresh" candidate/_weekly_refresh
cd candidate
: > ../tests.log; fails=0; n=0
for t in test_*.cjs; do n=$((n+1)); out=$(node "$t" 2>&1) && rc=0 || rc=$?; [ $rc -eq 0 ] || fails=$((fails+1)); echo "$t [exit $rc] $(echo "$out" | grep -v '^Node.js v' | tail -1 | cut -c1-160)" >> ../tests.log; done
echo "SUITES $n FAILED $fails" >> ../tests.log
cd "$W"; cat tests.log; grep -q "FAILED 0$" tests.log || { echo "TEST FAILURE - stop"; exit 1; }
node compare.cjs > compare.log; head -c 400 compare.log; echo
node compare_age.cjs launch 0 > compare_age.log; cat compare_age.log
tail -8 resolve.log
python3 "$W/release_check.py"
