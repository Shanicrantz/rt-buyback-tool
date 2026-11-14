"""Reject optional-5G aliases when the catalogue contains separate families.
(Recovered 2026-11-14 from the v6.30 run; the original folder was on the damaged 1TB drive.)"""
import _market_refresh_runner as m
import _research_reliance_prices as reliance

def network_conflict(row, reference, scope, used=False):
    if row.get('category', 'phone') != 'phone':
        return False
    expected = m.norm(row['family'])
    if used:
        actual = m.norm(reference['title'].split(' - Refurbished')[0])
    else:
        identity = reliance.identity if reference.get('retailer') == 'Reliance Digital' else m.identity
        actual = identity(reference['selected_title'])[0]
    if expected == actual:
        return False
    families = {m.norm(r['family']) for r in scope}
    if expected.endswith('5g'):
        return actual == expected[:-2] and actual in families
    return actual == expected + '5g' and actual in families
