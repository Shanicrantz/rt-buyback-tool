import json, re, math
from pathlib import Path

STAGE = Path(__file__).resolve().parent
db = json.loads((STAGE / 'backup/phone_db.json').read_text())
accepted = json.loads((STAGE / 'research/accepted.json').read_text())
for item in accepted:
    e = db[item['key']]
    assert not e.get('rt_buyback_a1_override')
    assert item['after_a1'] <= item['resale_estimate'] * .92
    assert item['after_a1'] <= e['net_new_inr'] * .85
    assert item['before_a1'] * .8 <= item['after_a1'] <= item['before_a1'] * 1.08
    e['target_margin'] = item['margin']
    # Exact back-solve, rather than rounding the anchor and changing the intended quote.
    e['resale_target_a1'] = round(item['after_a1'] * (1 + item['margin']), 2)
    e['market_resale_observed'] = item['resale_estimate']
    e['market_resale_basis'] = 'asking-price-adjusted estimate; not a verified completed sale'
    e['calibration_status'] = 'estimated'
    e['calibration_date'] = '2026-09-28'
    e['live_source'] = 'REVIEW 2026-09-28: OLX asks 55k/58k; 55k less assumed 10% negotiation = resale estimate 49,500 -> A1 45,000. Not sold evidence; estimated. URLs in calibration_evidence.'
    e['calibration_evidence'] = item['sources']
    e.pop('buyback_market', None)

db['_meta']['version'] = '6.8'
db['_meta']['last_calibration'] = '2026-09-28'
db['_meta']['v6_8_changelog'] = (
    'Limited weekly update 2026-09-28. 96 entries scoped and market-search screened; '
    'recent 2026-09-26 research excluded except unresolved carry-forwards. '
    'Only one conservative candidate accepted after direct page checks and critical review: '
    'Oppo Find X8 Pro 16/512 A1 Rs48,200 -> Rs45,000 (-6.64%). '
    'Resale Rs49,500 is an explicit estimate from a current Rs55,000 out-of-warranty, '
    'like-new seller ask less a 10% negotiation allowance; a separate Rs58,000 ask is supporting context. '
    'No completed sale verified; entry changed from verified to estimated with dated source URLs. '
    'Other 95 scoped entries retained unchanged, including their original calibration dates: '
    'insufficient corroborated exact-condition evidence, inaccessible/redirected pages, variant or warranty mismatches. '
    'No increases, new models or removals. Future launches remain held; Lava first sale is after this daytime check, '
    'iPhone Duo remains unavailable before 23 Oct. 2362 entries remain. All unchanged entries are NOT freshly verified. '
    'Validated locally only; production publication and Git push not performed.'
)

html = (STAGE / 'backup/index.html').read_text()
line = 'const DB = ' + json.dumps(db, ensure_ascii=False, separators=(',', ':')) + ';'
html, count = re.subn(r'^const DB = \{[^\r\n]*\};[ \t]*$', lambda _: line, html, flags=re.M)
assert count == 1
(STAGE / 'candidate/phone_db.json').write_text(json.dumps(db, ensure_ascii=False, indent=2))
(STAGE / 'candidate/index.html').write_text(html)
print('Built staged v6.8: one estimated decrease; 95 scoped entries unchanged.')
