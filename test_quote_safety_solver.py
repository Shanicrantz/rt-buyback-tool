#!/usr/bin/env python3
"""Integration fixtures for the real quote-safety resolver and candidate engine.

Parent must verify the external volume before running, for example:
  python3 test_quote_safety_solver.py /Volumes/my1tb/Projects/General/fixture-root \
      --candidate-html /path/to/resolved/candidate/index.html

The fixture root must already exist on /Volumes/my1tb. Each run creates a unique
temporary child there, retained for inspection. No production inputs are edited.
Report provenance is intentionally excluded from idempotence: a rerun currently
replaces the original proposed quotes/pinned list with already-resolved values.
"""

import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import tempfile


STAMP = "2026-10-31T06:00:00.000Z"
DEFAULT_HTML = Path(
    "/Volumes/my1tb/Projects/General/rt-buyback-tool/refresh/"
    "2026-10-31-resolved/candidate/index.html"
)
DB_PATTERN = re.compile(r"^const DB = (\{[^\r\n]*\});[ \t]*$", re.MULTILINE)


def check(value, message):
    if not value:
        raise AssertionError(message)


def entry(key, base):
    # Legacy markup .25 means resale / 1.25, not a 25% gross deduction.
    return {
        "display_name": key,
        "tier": "B",
        "target_margin": 0.25,
        "margin_basis": "markup",
        "market_resale_estimate": base * 1.25,
        "calibration_date": "2026-10-31",
    }


def scope_row(key, storage, family="Fixture", ram=8):
    return {"key": key, "family": family, "category": "phone",
            "storage": storage, "ram": ram}


def patched_html(template, db):
    result, count = DB_PATTERN.subn(
        lambda _: "const DB = " + json.dumps(db, separators=(",", ":")) + ";",
        template,
    )
    check(count == 1, "Expected exactly one inline DB in actual candidate HTML")
    return result


def run_case(root, name, template, resolver, old_prices, new_prices, scope):
    work = root / name
    work.mkdir()
    original = {"_meta": {}, **{k: entry(k, v) for k, v in new_prices.items()}}
    baseline = {"_meta": {}, **{k: entry(k, v) for k, v in old_prices.items()}}
    for folder, db in (("candidate", original), ("baseline", baseline)):
        target = work / folder
        target.mkdir()
        (target / "phone_db.json").write_text(json.dumps(db), encoding="utf-8")
        (target / "index.html").write_text(patched_html(template, db), encoding="utf-8")
    (work / "scope.json").write_text(json.dumps({"models": scope}), encoding="utf-8")

    def resolve():
        run = subprocess.run(
            ["node", str(resolver), str(work), STAMP],
            capture_output=True, text=True, timeout=60,
        )
        check(run.returncode == 0, f"{name}: resolver failed\n{run.stdout}\n{run.stderr}")
        db = json.loads((work / "candidate/phone_db.json").read_text())
        html = (work / "candidate/index.html").read_text()
        check(json.loads(DB_PATTERN.search(html).group(1)) == db, name + ": inline DB mismatch")
        report = json.loads((work / "pricing-resolution.json").read_text())
        check(report["numeric_inversions"] == 0, name + ": remaining numeric inversion")
        check(report["source_prices_unchanged"] is True, name + ": missing evidence assertion")
        for key, source in original.items():
            if key == "_meta":
                continue
            actual = {k: v for k, v in db[key].items()
                      if k not in ("quote_safety", "price_reference_pending")}
            check(actual == source, f"{name}: source changed for {key}")
        return db, report, html

    db, report, html = resolve()
    frozen = copy.deepcopy(db)
    again, repeated, repeated_html = resolve()
    check(again == frozen, name + ": frozen-date DB rerun not idempotent")
    check(repeated_html == html, name + ": frozen-date HTML rerun not idempotent")
    for field in ("manual_review_models", "pending_pairs", "numeric_inversions", "capped_models"):
        check(repeated[field] == report[field], name + ": rerun changed " + field)
    outcomes = lambda r: {x["key"]: (x["valid"], x["final"], x["safety"]) for x in r["rows"]}
    check(outcomes(repeated) == outcomes(report), name + ": rerun changed quote outcomes")
    return db, report, {r["key"]: r for r in report["rows"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture_root", type=Path)
    parser.add_argument("--candidate-html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--resolver", type=Path,
                        default=Path(__file__).resolve().with_name("_resolve_quote_safety.cjs"))
    args = parser.parse_args()
    parent = args.fixture_root.resolve(strict=True)
    check(parent.is_dir() and parent.is_relative_to(Path("/Volumes/my1tb")),
          "Fixture root must be an existing external directory under /Volumes/my1tb")
    template = args.candidate_html.read_text(encoding="utf-8")
    check("quoteSafetyApplied" in template and "requires_counter_review" in template,
          "Supply the actual patched candidate engine")
    root = Path(tempfile.mkdtemp(prefix="quote-safety-solver-", dir=parent))
    print("Retained fixtures:", root, flush=True)

    def case(name, old, new, scope):
        return run_case(root, name, template, args.resolver.resolve(), old, new, scope)

    prices = {"small": 10000, "medium": 9500, "large": 9000}
    db, report, rows = case("three-variant", prices, prices,
                            [scope_row("small", 128), scope_row("medium", 256),
                             scope_row("large", 512)])
    check([rows[k]["final"] for k in prices] == [9000, 9000, 9000], "Chain did not converge")
    check(report["passes"] >= 2 and not report["pending_pairs"], "Chain not fully checked")
    check(all(r["valid"] for r in rows.values()), "Chain unexpectedly gated")

    db, report, rows = case("rise-boundaries", {"eight": 10000, "nine": 10000},
                            {"eight": 10800, "nine": 10900},
                            [scope_row("eight", 128, "Eight"), scope_row("nine", 128, "Nine")])
    check(rows["eight"]["final"] == 10800 and "quote_safety" not in db["eight"], "+8% must remain")
    check(rows["nine"]["final"] == 10000 and report["pinned_increases"] == ["nine"], "+9% must pin")
    check(db["nine"]["quote_safety"]["max_raw_a1"] == 10000, "Pin used wrong raw base")

    for percent, target in ((20, 8000), (21, 7900)):
        # The drop is caused by ordering, not by changing the source observation.
        prices = {"small": 10000, "large": target}
        db, report, rows = case(f"drop-{percent}", prices, prices,
                                [scope_row("small", 128), scope_row("large", 256)])
        check(rows["large"]["final"] == target, "Larger sibling unexpectedly changed")
        if percent == 20:
            check(rows["small"]["valid"] and rows["small"]["final"] == 8000,
                  "Exactly -20% must retain numeric quote")
            check(not report["manual_review_models"] and not report["pending_pairs"],
                  "Exactly -20% incorrectly gated")
        else:
            check(not rows["small"]["valid"] and rows["small"]["final"] is None,
                  "-21% must gate instead of publishing a numeric quote")
            check(db["small"]["quote_safety"]["requires_counter_review"] is True
                  and bool(db["small"]["price_reference_pending"]), "Missing pending reason")
            check(report["manual_review_models"] == ["small"], "Missing manual review model")
            check(len(report["pending_pairs"]) == 1, "Null pair silently counted as resolved")
            pair = report["pending_pairs"][0]
            check((pair["small"], pair["big"]) == ("small", "large")
                  and "no numeric ordering claim" in pair["reason"],
                  "Reporter must distinguish pending pair from resolved market ordering")

    prices = {"four_g": 10000, "five_g": 7000}
    db, report, rows = case("network-families", prices, prices,
                            [scope_row("four_g", 128, "Fixture 4G"),
                             scope_row("five_g", 256, "Fixture 5G")])
    check(all(rows[k]["final"] == v and "quote_safety" not in db[k] for k, v in prices.items()),
          "Different network families incorrectly ordered")
    check(not report["pending_pairs"] and report["capped_models"] == 0, "Cross-family pair created")
    print(json.dumps({"passed": True, "cases": 5, "idempotence_replays": 5,
                      "fixture_directory": str(root)}))


if __name__ == "__main__":
    main()
