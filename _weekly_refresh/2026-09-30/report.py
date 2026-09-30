"""Render the evidence report from the actual candidate and deployment readbacks."""
import json
from pathlib import Path

W = Path(__file__).resolve().parent
D = json.loads((W / 'decisions.json').read_text())
V = json.loads((W / 'validation.json').read_text())
C = json.loads((W / 'completion.json').read_text()) if (W / 'completion.json').exists() else {}
fmt = lambda x: f"Rs{x:,.0f}" if isinstance(x, (int, float)) else 'unavailable'
lines = [
    '# RT Buyback weekly refresh — 30 September 2026', '',
    f"Version **{D['version']}**; **{D['total_entries']} entries**. Resumed the interrupted 30-Sep research.", '',
    f"Reviewed 96 scoped entries: {len(D['refreshed'])} accepted calibrations, {len(D['moved'])} A1 price changes, "
    f"{len(D['added'])} shipping India configurations added, {len(D['removed'])} confirmed phantom configurations removed.", '',
    'The scope is the saved high-value/recent rotation, not all 1,248 eligible catalogue entries. '
    'Twelve fetch batches and eleven saved critic batches were recovered; the missing critic batch and missing '
    'Apple/Samsung/Google launch audit were completed using independent research agents because the original Workflow tool '
    'was unavailable in this session. Saved research is in saved_pricing_research.json; final reviews are in pricing_a.json, '
    'pricing_b.json and launch_review.json.', '',
    'Resale values based on asking prices, retail bounds or analogs remain **estimated**. '
    'Existing authoritative new-price ceilings and manual overrides were preserved. '
    'Age margins and the existing C/D risk floors were applied. '
    'Unsupported rises, greater-than-20% moves, ceilings and storage-ladder conflicts were held. '
    'No price was lifted merely to beat Cashify. Historical deep-tail entries retain their dates and values.', '',
    '## Largest accepted changes', '',
    '| Model | Resale before → now | RT A1 before → now | Change |',
    '|---|---:|---:|---:|',
]
for x in sorted(D['moved'], key=lambda x: abs(x['new_a1']-x['old_a1']), reverse=True)[:15]:
    lines.append(f"| {x['name']} | {fmt(x['old_resale'])} → {fmt(x['new_resale'])} | {fmt(x['old_a1'])} → {fmt(x['new_a1'])} | {x['pct']:+.2f}% |")
lines += ['', '## Added configurations', '']
for x in D['added']:
    lines.append(f"- {x['name']}: resale {fmt(x['resale'])}; A1 {fmt(x['new_a1'])}; India launch {x['launch_date']}.")
if not D['added']:
    lines.append('None cleared the evidence and pricing checks.')
lines += ['', '## Variant repairs and deferred launches', '']
for x in D['removed']:
    lines.append(f"- Removed `{x['key']}`: {x.get('reason','')} Replacement: `{x.get('replacement_key','none')}`.")
lines.append('Full held-launch and uncertain-variant evidence is in launch_review.json. Full price holds are in decisions.json.')
lines += ['', '## Competitor comparison', '']
if V['competitor_offers']:
    for x in V['competitor_offers']:
        lines.append(f"- {x['name']}: RT {fmt(x['rt_a1'])}; verified market quote {fmt(x['market'])}.")
else:
    lines.append('No fresh condition-specific competitor payout above RT A1 was verified. This does not prove RT beats competitors.')
lines += ['', 'Public “Get Upto” amounts below are **maximum headlines, not confirmed payouts**. '
          'All are retained in the review artifacts; accepted calibrations also store market_buyback_ceiling in the DB. '
          'These flag a possible lost walk-in, including models whose RT price was held:', '',
          '| Model | RT A1 | Public maximum | Potential gap |', '|---|---:|---:|---:|']
for x in V['competitor_headline_alerts']:
    lines.append(f"| {x['name']} | {fmt(x['rt_a1'])} | {fmt(x['ceiling'])} | {fmt(x['gap'])} |")
if not V['competitor_headline_alerts']:
    lines.append('| No accepted-entry alerts | — | — | — |')
lines += ['', '## Validation and publication', '',
          f"- Full engine validation: {'PASS' if V['passed'] else 'FAIL'} across {V['entries']} entries; "
          'paired DB bytes, JavaScript syntax, grades, final offers, ceilings, weekly changes, protected fields and storage/size ladders checked.',
          '- The UI and pricing engine are unchanged; only the inline database was updated.',
          '- Baseline on production: v6.7 / 26-Sep. Local baseline: v6.8 / 28-Sep. The unpublished 28-Sep correction is included.',
          f"- Production: {C.get('deploy_state', 'pending; candidate only')}.",
          f"- Deployment ID: {C.get('deploy_id', 'pending')}.",
          f"- Live HTML and JSON hashes match candidate: {C.get('live_hashes_match', False)}.",
          f"- Site: https://rt-buyback-tool.netlify.app/", '',
          'The pushed commit is reported in the completion message and can be identified by the v6.9 weekly-refresh commit subject. '
          'A commit cannot contain its own hash.']
(W / 'REPORT.md').write_text('\n'.join(lines) + '\n')
print(W / 'REPORT.md')
