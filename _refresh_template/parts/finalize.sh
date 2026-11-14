#!/bin/zsh
# Parts stage finalize: candidate -> every JS suite one at a time (stop on failure) -> deduction comparison.
set -e
ROOT="/Users/shane/Documents/Claude/Projects/rt buyback tool"; W="${0:A:h}"; cd "$W"
python3 prepare_parts.py
cd candidate; : > ../tests.log; fails=0; n=0
for t in test_*.cjs; do n=$((n+1)); out=$(node "$t" 2>&1) && rc=0 || rc=$?; [ $rc -eq 0 ] || fails=$((fails+1)); echo "$t [exit $rc] $(echo "$out" | grep -v '^Node.js v' | tail -1 | cut -c1-160)" >> ../tests.log; done
echo "SUITES $n FAILED $fails" >> ../tests.log
cd "$W"; cat tests.log; grep -q "FAILED 0$" tests.log || { echo "TEST FAILURE - stop"; exit 1; }
node compare_parts.cjs
cmp -s baseline/phone_db.json "$ROOT/phone_db.json" || { echo "STOP: production DB moved since this run started"; exit 1; }
echo "PARTS CANDIDATE OK - review deduction-changes.json, then install candidate/{phone_db.json,index.html,sw.js}"
