"""Resale + new-launch stage (template; from v6.36, 14 Nov 2026). Run folder made by resale/new_resale_run.sh.

Rebuilt from the v6.26 prepare_observations.py (on the Mac) plus the v6.30 patches recovered from the 4 Nov Codex
guardian transcript (the v6.30 folder was on the damaged 1TB drive):
  * resale-verified.json   <- verify_resale.py (exact Cashify variant page, selected Product, Superb, InStock, Refurbished)
                              + augment_selected_resale.py (selected Product on the family page itself; never a
                              ProductGroup sibling inference)
  * special-resale-references.json <- check_special_sources.py (GudFast X60 Pro+, Mobirapid S25 256)
  * estimate = floor100(ask x (1 - allowance)); allowance 10% normal / 15% C, D or foldable (runner); no launch-age haircut
  * an exact page that was BLOCKED (HTTP 403) keeps the prior dated reference unchanged (expired => unverified, not used
    by the engine, not counted as fresh); an exact check that found NO eligible stock moves the prior reference to
    last_known_resale_price (v6.26 rule). Neither changes a quote: the engine ignores references older than 10 days.
  * RAM-ambiguous legacy rows and cross-network (4G/5G) aliases never take a resale reference.
New prices are NOT re-researched: the live new-price run's rows (run.json new_price_run, <= 6 days old) are carried verbatim and must equal the release.
Launch additions come from launch-proposals.json (probe_launches.py). Guardrails kept: no back-solving resale from
buyback (writer asserts no assessed_quote evidence), no competitor quote or sold price manufactured, quote-level +8%
rise pin and RAM/storage ordering stay with _resolve_quote_safety.cjs.
"""
import sys, json, math, re
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path('/Users/shane/Documents/Claude/Projects/rt buyback tool'); W = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(W))
import _market_refresh_runner as m
from _apply_market_observations import build
from variant_guard import network_conflict
m.WORK = W
read = lambda f: json.loads((W / f).read_text())
RUN = read('run.json'); VERSION = RUN['version']
db = read('baseline/phone_db.json')
assert db == json.loads((ROOT / 'phone_db.json').read_text()), 'production DB moved since baseline: reconcile first'
assert (W / 'baseline/index.html').read_bytes() == (ROOT / 'index.html').read_bytes(), 'production HTML moved since baseline'
assert db['_meta']['version'] == RUN['previous_version'], 'baseline is not the release this run was made from'
prev = {r['key']: r for r in json.loads((ROOT / RUN['new_price_run'] / 'observations.json').read_text())['models']}
# scope.json is regenerated below with the launch additions; re-runs start from the pre-launch manifest.
scope = read('base-scope.json') if (W / 'base-scope.json').exists() else read('scope.json'); models = scope['models']
used = {r['key']: r for r in read('resale-verified.json')}
special = read('special-resale-references.json')
ram_holds = read('ram-identity-holds.json')
launches = read('launch-proposals.json')
RESALE_SPLIT = ' Resale not re-checked in this new-price refresh'
rows, identity_holds, resale_moves = [], [], []
counts = dict(fresh_cashify=0, fresh_special=0, retained_blocked=0, withdrawn_no_stock=0, ram_hold=0, network_hold=0)
for row in models:
    key = row['key']; entry = db[key]; base = prev[key]
    assert (base.get('current_new_price') or None) == (entry.get('current_new_price') or None), 'new-price run row differs from the live release: ' + key
    note = base['note'].split(RESALE_SPLIT)[0]
    result = dict(key=key, new_price_status=base['new_price_status'], current_new_price=base.get('current_new_price'),
                  new_price_checks=base['new_price_checks'], resale_status='unverified')
    if key in ram_holds:
        counts['ram_hold'] += bool(used[key]['reference'])
        u = None
    else:
        u = used[key]['reference']
    if u and network_conflict(row, u, models, used=True):
        identity_holds.append(dict(key=key, source_url=u['source_url'], selected_title=u['title'], kind='used', reason='Separate base and 5G catalogue families; optional network alias rejected'))
        counts['network_hold'] += 1; u = None
    prior = entry.get('current_resale_price')
    if key in special and (not u or special[key]['evidence'][0]['amount_inr'] <= u['amount_inr']):
        result.update(resale_status='estimated', current_resale_price=special[key]); counts['fresh_special'] += 1
        note += ' Fresh exact-grade retailer ask; retailer-service allowance is an estimate, not an observed local sale. Moradabad delivery and achievable local resale unverified.'
    elif u:
        allowance = m.resale_retail_allowance(entry)
        evidence = {k: u[k] for k in ['kind', 'amount_inr', 'source_url', 'observed_at', 'grade', 'warranty_months', 'available', 'evidence_file', 'sha256', 'exact_variant_verified']}
        evidence.update(local_delivery_verified=False, verification_method=u.get('verification_method', 'exact variant page selected Product'))
        result.update(resale_status='estimated', current_resale_price=dict(kind='local_resale_estimate', variant_name=entry['display_name'],
            amount_inr=math.floor(u['amount_inr'] * (1 - allowance) / 100) * 100, observed_at=u['observed_at'], source_url=u['source_url'], market='India', grade='A1',
            method=f'{allowance:.0%} below available exact Superb warranty-retail ask; local sold price unverified', evidence=[evidence], assumption_discount=allowance,
            confidence='low', assumption_basis='10% retailer/service allowance for normal phones; 15% C/D or foldable. Business assumption, not an observed local sale. No model-launch-age haircut; actual device age remains separate.'))
        counts['fresh_cashify'] += 1
        note += f' Fresh exact Superb Cashify warranty-retail ask (selected product on the public page); {allowance:.0%} retailer-service allowance is an estimate, not an observed local sale. Moradabad delivery and achievable local resale unverified.'
    else:
        blocked = any(a.get('fetch', {}).get('http_status') == 403 for a in used[key]['attempts'])
        if prior and blocked and key not in ram_holds:
            counts['retained_blocked'] += 1
            note += ' Exact Cashify variant page blocked (HTTP 403) this run; prior dated resale reference retained unchanged, past its 10-day window and not used for automatic quotes. Not counted as newly verified.'
        elif prior:
            counts['withdrawn_no_stock'] += 1
            result.update(invalidate_resale_reference=True, invalidation_reason='No eligible available exact-grade resale reference substantiated in this check; original source preserved as last-known.')
            note += ' No eligible in-stock exact Superb resale offer in this check; prior reference preserved as last-known.'
        else:
            note += ' Fresh exact A1 resale unavailable; saved resale remains unverified.'
    if key in ram_holds: note += ' ' + ram_holds[key]['reason']
    result['note'] = note
    ref = result.get('current_resale_price')
    if ref or result.get('invalidate_resale_reference') or prior:
        resale_moves.append(dict(key=key, model=entry['display_name'], before=(prior or {}).get('amount_inr'), before_observed=(prior or {}).get('observed_at', '')[:10] or None,
                                 after=(ref or {}).get('amount_inr'), outcome='fresh' if ref else 'withdrawn' if result.get('invalidate_resale_reference') else 'retained_blocked' if prior else None))
    rows.append(result)
# New India launches (first sale after the last launch add); scope regenerated so coverage stays complete.
catalogue = json.loads(json.dumps(db))
for r in launches:
    assert r['key'] not in catalogue and r['observation']['new_price_status'] == 'verified', r['key']
    catalogue[r['key']] = r['entry']; rows.append(r['observation'])
full_scope = m.catalogue_scope(catalogue)
m.write(W / 'base-scope.json', scope); m.write(W / 'scope.json', dict(created_at=m.stamp(), **full_scope)); m.write(W / 'catalogue-input.json', catalogue)
changelog = (RUN['date_label'] + ' used-resale refresh and new-launch check (completes the ' + RUN['previous_version'] + ' weekly run): '
             f"{counts['fresh_cashify']} fresh exact Cashify Superb resale estimates and {counts['fresh_special']} fresh exact retailer estimates (10%/15% retailer allowance, labelled estimates, no sold prices claimed); "
             f"{counts['retained_blocked']} prior references kept unchanged where Cashify blocked the exact page (expired, not used for automatic quotes); "
             f"{counts['withdrawn_no_stock']} moved to last-known where no in-stock exact grade was found. "
             f'{len(launches)} India launches added from exact in-stock new listings: ' + ', '.join(r['entry']['display_name'] for r in launches) + '. '
             'New prices carried from the ' + RUN['previous_version'] + ' new-price check. Margins, age, warranty and quote-safety rules unchanged.')
payload = dict(checked_at=m.stamp(), release_version=VERSION, scope_policy='all-catalogue-v1', scope_definition=full_scope['definition'], research_manifest=str(W / 'scope.json'), models=rows, changelog=changelog)
m.write(W / 'observations.json', payload); m.write(W / 'coverage-validation.json', m.validate_scope_coverage(payload, catalogue))
m.write(W / 'variant-identity-holds.json', identity_holds); m.write(W / 'resale-moves.json', resale_moves)
m.write(W / 'new-price-moves.json', [dict(key=r['key'], model=catalogue[r['key']]['display_name'], before=(db.get(r['key'], {}).get('current_new_price') or {}).get('amount_inr'), after=(r.get('current_new_price') or {}).get('amount_inr')) for r in rows])
candidate = build(payload, catalogue, datetime.now(timezone.utc)); (W / 'candidate').mkdir(exist_ok=True)
compact = json.dumps(candidate, ensure_ascii=False, separators=(',', ':'))
(W / 'candidate/phone_db.json').write_text(compact)
html = (W / 'baseline/index.html').read_text()
html, n = re.subn(r'^const DB = (\{[^\r\n]*\});[ \t]*$', lambda _: 'const DB = ' + compact + ';', html, flags=re.M); assert n == 1
(W / 'candidate/index.html').write_text(html)
s = candidate['_meta']['last_scoped_market_refresh']
print(json.dumps(dict(counts, scope=s['scope_count'], new_verified=s['new_prices_verified'], resale_estimated=s['resale_estimated'], resale_pending=s['resale_pending'], launches=[r['key'] for r in launches], identity_holds=len(identity_holds)), indent=1))
