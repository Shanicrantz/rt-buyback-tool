"""INTERNATIONAL-VARIANT RULE (Shane, 2026-10-01) — shared by _apply_intl_fix_2026-10-01.py and the weekly finalize.

A row flagged `international: true` is a RAM/storage config never sold in India. It is kept quotable (imported units
walk in) and priced off the nearest India config of the same phone, named in `intl_sibling`:

    A1 = min( (1 - intl_discount) x A1(intl_sibling),  the row's current A1 )      intl_discount = 0.10

The min() makes the rule a ceiling that follows the India sibling DOWN but never raises a quote on its own — a 4GB
international unit priced off an 8GB India sibling must not gain from the RAM it lacks. Research is never run on
these rows: there is no India market for the config to observe."""
import json, math, os, subprocess, tempfile

DIR = os.path.dirname(os.path.abspath(__file__))
INTL_DISCOUNT = 0.10

def r100(n):
    """Math.round(n/100)*100 exactly as the engine does (Python's round() is banker's rounding)."""
    return int(math.floor(n / 100.0 + 0.5)) * 100

def engine_a1(db, day='2026-10-01'):
    """{key: A1} from the real computeA1() in index.html (via _engine_quote.cjs)."""
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(db, f, ensure_ascii=False)
        p = f.name
    try:
        out = subprocess.check_output(['node', os.path.join(DIR, '_engine_quote.cjs'), p, day])
    finally:
        os.unlink(p)
    return json.loads(out)

def set_a1(e, target):
    """Write `target` as the entry's A1 through the resale anchor, never landing above it after rounding."""
    m = e['target_margin']
    e['resale_target_a1'] = r100(target * (1 + m))
    while r100(e['resale_target_a1'] / (1 + m)) > target:
        e['resale_target_a1'] -= 100
    return r100(e['resale_target_a1'] / (1 + m))

def recompute_international(db, stamp, day='2026-10-01'):
    """Apply the rule to every international row in `db` (dict incl. _meta). Returns [(key, old, new, sibling_a1)]."""
    a1 = engine_a1(db, day)
    out = []
    for k, e in db.items():
        if k == '_meta' or not e.get('international'):
            continue
        sib = e.get('intl_sibling')
        sa = a1.get(sib)
        if not sa:
            continue
        disc = e.get('intl_discount', INTL_DISCOUNT)
        old = a1.get(k) or 0
        tgt = r100(sa * (1 - disc))
        if old > 0:
            tgt = min(tgt, old)
        new = set_a1(e, tgt)
        e['live_source'] = (f"INTERNATIONAL {stamp}: A1 = min({1 - disc:.2f} x India {db[sib].get('display_name')} "
                            f"A1 ₹{sa:,}, prior ₹{old:,}) = ₹{new:,} — config never sold in India")[:180]
        out.append((k, old, new, sa))
    return out
