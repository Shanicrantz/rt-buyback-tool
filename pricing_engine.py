"""
Rajdhani Telecom — Buyback Pricing Engine v2
============================================
Anchor-based pricing with 4-tier priority:

1. rt_buyback_a1_override          — explicit Shane override (highest priority)
2. resale_target_a1 + target_margin — resale-anchored (recommended for hot models)
3. refurb_retail_anchor + factors   — refurb-anchored (for DISCONTINUED phones)
4. net_new_inr + formula            — new-anchored (for in-production phones)

Why this matters:
- iPhone 13 Pro is DISCONTINUED → "NEW price" doesn't exist → can't use formula
  Anchor on Cashify Store/Budli refurb retail × market factor × margin instead.
- Vivo Y300 Plus 5G is IN-PRODUCTION → has Amazon NET, formula works.
- Hot models: Shane sets resale_target_a1 directly, formula bypassed.
"""

import json
from datetime import date
from pathlib import Path

# ─────────────────────────────────────────────────────────────────
# CALIBRATION COEFFICIENTS
# ─────────────────────────────────────────────────────────────────

# Mode 4: Depreciation curve for IN-PRODUCTION phones (formula fallback)
DEPRECIATION_CURVE = [
    (3,   0.65), (6,   0.58), (12,  0.50), (18,  0.43),
    (24,  0.35), (36,  0.27), (48,  0.20), (999, 0.15),
]
TIER_FACTOR = {"S": 1.20, "A": 1.05, "B": 0.95, "C": 0.85, "D": 0.55}
TIER_PREMIUM = {"S": 0.10, "A": 0.08, "B": 0.06, "C": 0.04, "D": 0.00}

# Mode 3: Refurb-retail to local-resale conversion factor
# Cashify Store / Budli sell with warranty + 32-pt QC at premium.
# Shane's local resale (no warranty, individual unit) is ~12% below.
DEFAULT_MARKET_FACTOR = 0.88

# Cashify shows "Fair" condition prices on landing pages.
# Excellent tier is ~18% higher than Fair. Use this if only Fair is captured.
FAIR_TO_EXCELLENT_MULTIPLIER = 1.18

# Default target margin by tier (used if entry doesn't specify)
DEFAULT_TARGET_MARGIN = {
    "S": 0.18,  # iPhone, Samsung flagship — high turnover, thin margin OK
    "A": 0.20,
    "B": 0.22,
    "C": 0.25,  # Slow movers, more capital risk
    "D": 0.30,
}

# Grade multipliers — applied on A1 anchor
GRADE_MULT = {"A1": 1.00, "A2": 0.90, "B": 0.80, "C": 0.65, "D": 0.45}

# No-kit deductions (cumulative)
DEDUCTION = {"no_box": 0.03, "no_charger": 0.02, "no_bill": 0.05}

# ─────────────────────────────────────────────────────────────────
# CORE FUNCTIONS
# ─────────────────────────────────────────────────────────────────

def months_between(launch_iso: str, today: date | None = None) -> int:
    today = today or date.today()
    y, m, d = map(int, launch_iso.split("-"))
    diff = (today.year - y) * 12 + (today.month - m)
    if today.day < d: diff -= 1
    return max(0, diff)

def depreciation_fraction(months: int) -> float:
    for max_m, frac in DEPRECIATION_CURVE:
        if months <= max_m: return frac
    return 0.15

def round100(n: float) -> int:
    return int(round(n / 100) * 100)

def compute_a1_buyback(entry: dict, today: date | None = None) -> tuple[int, str, dict]:
    """
    Compute Grade A1 buyback using highest-priority anchor available.
    Returns (a1_buyback_inr, source_label, debug_info).
    """
    today = today or date.today()
    tier = entry["tier"]
    margin = entry.get("target_margin", DEFAULT_TARGET_MARGIN[tier])
    debug = {"tier": tier, "margin": margin}

    # Mode 1: explicit override
    if entry.get("rt_buyback_a1_override"):
        return round100(entry["rt_buyback_a1_override"]), "override", debug

    # Mode 2: resale-anchored (best for hot in-production models)
    if entry.get("resale_target_a1"):
        resale = entry["resale_target_a1"]
        a1 = resale / (1 + margin)
        debug.update({"resale_a1": resale, "calc": f"{resale} / (1+{margin})"})
        return round100(a1), "resale_anchored", debug

    # Mode 3: refurb-anchored (for DISCONTINUED phones)
    refurb = entry.get("refurb_retail_anchor_excellent")
    if not refurb and entry.get("refurb_retail_anchor_fair"):
        refurb = entry["refurb_retail_anchor_fair"] * FAIR_TO_EXCELLENT_MULTIPLIER
    if refurb:
        market_factor = entry.get("market_factor", DEFAULT_MARKET_FACTOR)
        local_resale = refurb * market_factor
        a1 = local_resale / (1 + margin)
        debug.update({
            "refurb_retail_excellent": int(refurb),
            "market_factor": market_factor,
            "implied_local_resale_a1": int(local_resale),
            "calc": f"{int(refurb)} x {market_factor} / (1+{margin})",
        })
        return round100(a1), "refurb_anchored", debug

    # Mode 4: formula fallback (in-production phones without resale data)
    if entry.get("net_new_inr") and entry.get("launch_date"):
        net_new = entry["net_new_inr"]
        months = months_between(entry["launch_date"], today)
        cashify_est = net_new * depreciation_fraction(months) * TIER_FACTOR[tier]
        a1 = cashify_est * (1 + TIER_PREMIUM[tier])
        debug.update({
            "net_new": net_new,
            "months": months,
            "depreciation_factor": depreciation_fraction(months),
            "tier_factor": TIER_FACTOR[tier],
            "tier_premium": TIER_PREMIUM[tier],
        })
        return round100(a1), "formula", debug

    return 0, "no_data", debug

def grade_quote(a1_buyback: int, grade: str,
                no_box=False, no_charger=False, no_bill=False) -> int:
    pre = a1_buyback * GRADE_MULT[grade]
    ded = 0.0
    if no_box:     ded += DEDUCTION["no_box"]
    if no_charger: ded += DEDUCTION["no_charger"]
    if no_bill:    ded += DEDUCTION["no_bill"]
    return round100(pre * (1 - ded))

def full_quote(entry: dict, today: date | None = None) -> dict:
    """Generate full grade-wise quote card."""
    today = today or date.today()
    a1, source, debug = compute_a1_buyback(entry, today)

    grades = {}
    for g in ["A1", "A2", "B", "C", "D"]:
        grades[g] = {
            "with_kit":    grade_quote(a1, g),
            "no_box_bill": grade_quote(a1, g, no_box=True, no_bill=True),
        }

    # Implied resale for each grade
    margin = entry.get("target_margin", DEFAULT_TARGET_MARGIN[entry["tier"]])
    resale_a1 = a1 * (1 + margin)
    implied_resale = {g: round100(resale_a1 * GRADE_MULT[g]) for g in GRADE_MULT}

    return {
        "model":          entry.get("display_name", "?"),
        "tier":           entry["tier"],
        "discontinued":   entry.get("discontinued", False),
        "anchor_source":  source,
        "a1_buyback":     a1,
        "target_margin":  margin,
        "as_of":          today.isoformat(),
        "debug":          debug,
        "grades":         grades,
        "implied_resale": implied_resale,
        "open_offer":     grades["B"]["with_kit"],
        "walk_away_max":  grades["A2"]["with_kit"],
        "floor":          grades["C"]["with_kit"],
    }

# ─────────────────────────────────────────────────────────────────
# DB lookup
# ─────────────────────────────────────────────────────────────────

CACHE_FILE = Path(__file__).parent / "phone_db.json"

def load_db() -> dict:
    if not CACHE_FILE.exists(): return {}
    return json.loads(CACHE_FILE.read_text())

def lookup(query: str) -> dict | None:
    db = load_db()
    q = query.lower().strip().replace("-", "_")
    # Direct key match (fast path)
    q_compact = q.replace(" ", "_")
    if q_compact in db: return {**db[q_compact], "_key": q_compact}
    # Tokenize and find best fuzzy match
    tokens = [t for t in q.replace("_", " ").split() if t]
    if not tokens: return None
    candidates = []
    for k, v in db.items():
        if k.startswith("_"): continue
        k_lower = k.lower()
        # Split key into segments separated by _
        key_segments = set(k_lower.split("_"))
        name_lower = v.get("display_name", "").lower()
        # Match: each query token must appear EXACTLY as a key segment OR in name
        match_count = 0
        for tok in tokens:
            if tok in key_segments:
                match_count += 1
            elif tok in name_lower.split():
                match_count += 1
        if match_count == len(tokens):
            # Score: full match preferred, shorter keys (less specific phones) win ties
            candidates.append((match_count, -len(k_lower), k, v))
    if candidates:
        candidates.sort(reverse=True)
        _, _, k, v = candidates[0]
        return {**v, "_key": k}
    # Fallback: substring match on key
    for k, v in db.items():
        if k.startswith("_"): continue
        if q_compact in k or k in q_compact:
            return {**v, "_key": k}
    return None

def quote(query: str, today: date | None = None) -> dict | None:
    entry = lookup(query)
    return full_quote(entry, today) if entry else None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        r = quote(" ".join(sys.argv[1:]))
        print(json.dumps(r, indent=2, ensure_ascii=False) if r else "NOT IN CACHE")
