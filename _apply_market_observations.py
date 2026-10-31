#!/usr/bin/env python3
"""Apply reviewed, exact-variant market evidence to BOTH databases. Dry-run by default.

Usage: python3 _apply_market_observations.py observations.json [--apply]
The input contains checked_at, release_version, and models. Each model must record
new_price_status and resale_status, including honest unavailable/unverified cases.
Do research first: this writer never fetches prices or invents observations.
"""
import argparse, copy, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
PATTERN = re.compile(r'^const DB = (\{[^\r\n]*\});[ \t]*$', re.M)

def validate(ref, entry, new, now):
    assert ref['variant_name'] == entry['display_name'], 'Wrong exact variant'
    assert ref['market'] == ('International' if entry.get('international') else 'India'), 'Wrong market'
    amount = ref['amount_inr']
    assert type(amount) in (int, float) and 0 < amount <= 2_000_000, 'Invalid price'
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})', ref['observed_at']), 'Use ISO timestamp with milliseconds or seconds (browser-compatible)'
    stamp = datetime.fromisoformat(ref['observed_at'].replace('Z', '+00:00'))
    assert stamp.tzinfo and 0 <= (now-stamp).total_seconds() <= (7 if new else 10)*86400, 'Stale/future price'
    url = urlparse(ref['source_url'])
    assert url.scheme == 'https' and url.netloc and not url.username and not url.password, 'Invalid source'
    if new:
        assert ref['kind'] == 'retail_cash_price' and ref['available'] is True
        assert ref['condition'] == 'new' and ref['requires_bank_offer'] is False and ref['requires_exchange'] is False
        assert ref['amount_inr'] == ref['selling_price_inr'] + ref.get('mandatory_fees_inr', 0), 'Cash total excludes fees'
    else:
        assert ref['kind'] in ('local_resale_observed', 'local_resale_estimate') and ref['grade'] == 'A1'
        if ref['kind'] == 'local_resale_estimate':
            assert ref.get('method') and ref.get('evidence'), 'Estimate assumptions/evidence missing'
            assert all(e['kind'] != 'assessed_quote' for e in ref['evidence']), 'Cannot backsolve resale from buyback'

def build(payload, db, now):
    # A refresh defaults to the full catalogue. A separately requested targeted
    # correction must be explicitly named and explained, never masquerade as it.
    scope_policy=payload.get('scope_policy','all-catalogue-v1')
    if scope_policy=='all-catalogue-v1':
        from _market_refresh_runner import validate_scope_coverage
        validate_scope_coverage(payload,db)
    elif scope_policy=='targeted-correction':
        assert payload.get('scope_reason'), 'Explain the separately requested targeted correction'
    else:
        raise ValueError('Unknown market observation scope policy')
    out = copy.deepcopy(db)
    seen = set()
    for row in payload['models']:
        key = row['key']
        assert key in db and key != '_meta' and key not in seen, 'Missing or duplicate model'
        seen.add(key)
        entry = out[key]
        assert row['new_price_status'] in ('verified', 'unverified', 'unavailable')
        assert row['resale_status'] in ('observed', 'estimated', 'unverified')
        for field, new in [('current_new_price', True), ('current_resale_price', False)]:
            ref = row.get(field)
            if ref is not None:
                validate(ref, entry, new, now)
                assert (row['new_price_status'] == 'verified') if new else (row['resale_status'] == ('estimated' if ref['kind'].endswith('estimate') else 'observed'))
                entry[field] = ref
                if not new:
                    entry.pop('price_reference_pending', None)
            elif new:
                assert row['new_price_status'] != 'verified', 'Verified price missing'
                entry.pop(field, None)
            elif row.get('invalidate_resale_reference'):
                assert row['resale_status']=='unverified' and row.get('invalidation_reason'), 'Explain withdrawn resale evidence'
                if entry.get(field):
                    entry['last_known_resale_price']=entry[field]
                entry.pop(field, None)
        entry['market_refresh'] = {k: row[k] for k in ('new_price_status', 'resale_status', 'note')}
        entry['market_refresh']['checked_at'] = payload['checked_at']
        # Preserve historical net_new_inr, launch age, calibration_date and old
        # observed resale. Fresh values have their OWN timestamp and provenance.
    out['_meta']['version'] = payload['release_version']
    out['_meta']['market_refresh_policy'] = 'Refresh includes current exact-variant NEW cash selling price AND used resale evidence; sources, stock, condition, India region and real observation dates required. MRP, bank/exchange and stale rates are not current. Inferred local resale is labelled estimated. Unknown unit age remains optional/unknown.'
    out['_meta']['last_scoped_market_refresh'] = {
        'checked_at': payload['checked_at'], 'scope': sorted(seen),
        'new_prices_verified': sum(r['new_price_status']=='verified' for r in payload['models']),
        'resale_observed': sum(r['resale_status']=='observed' for r in payload['models']),
        'resale_estimated': sum(r['resale_status']=='estimated' for r in payload['models']),
        'status': 'partial' if any(r['new_price_status']!='verified' or r['resale_status']=='unverified' for r in payload['models']) else 'checked'
    }
    summary=out['_meta']['last_scoped_market_refresh']
    summary['scope_count']=len(seen)
    summary['new_prices_pending']=len(seen)-summary['new_prices_verified']
    summary['resale_pending']=len(seen)-summary['resale_observed']-summary['resale_estimated']
    if payload.get('scope_definition'):
        summary['scope_definition']=payload['scope_definition']
        summary['research_manifest']=payload.get('research_manifest')
    if payload.get('calibration_protocol'):
        assert isinstance(payload['calibration_protocol'], str)
        out['_meta']['calibration_protocol']=payload['calibration_protocol']
    if payload.get('changelog'):
        out['_meta']['v'+payload['release_version'].replace('.','_')+'_changelog']=payload['changelog']
    return out

def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('observations', type=Path)
    args.add_argument('--apply', action='store_true')
    opts = args.parse_args()
    db = json.loads((ROOT/'phone_db.json').read_text())
    html = (ROOT/'index.html').read_text()
    matches = PATTERN.findall(html)
    assert len(matches)==1 and json.loads(matches[0])==db, 'Database pair mismatch before write'
    payload = json.loads(opts.observations.read_text())
    out = build(payload, db, datetime.now(timezone.utc))
    compact = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    candidate, count = PATTERN.subn(lambda _: 'const DB = '+compact+';', html)
    assert count == 1 and json.loads(PATTERN.search(candidate)[1]) == out
    if opts.apply:
        (ROOT/'phone_db.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n')
        (ROOT/'index.html').write_text(candidate)
        assert json.loads(PATTERN.search((ROOT/'index.html').read_text())[1]) == json.loads((ROOT/'phone_db.json').read_text())
    print(json.dumps({'applied':opts.apply, **out['_meta']['last_scoped_market_refresh']}, indent=2))

if __name__ == '__main__':
    main()
