#!/usr/bin/env python3
"""Create, run, and tabulate a batch of PandaAI factor candidates.

Input is a text file with one candidate per line: `name ~ formula ~ direction`.
Blank lines and lines starting with `#` are ignored.

Progress is checkpointed to <input>.state.json after every step, so an interrupted
batch resumes without re-creating or re-running anything -- which matters because every
run costs compute credits.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Groups are ordered by ascending factor value, so 分组1 holds the lowest values and 分组10 the
# highest. Which end is the long side follows --factor-direction: 1 means higher is better.
# Verified by checking that 多空组合 equals long minus short for both direction settings.
LOW, HIGH = "分组1", "分组10"


def cli(*args: str, timeout: int = 1800) -> dict:
    """Run pandaai-cli in JSON mode and return the parsed payload."""
    proc = subprocess.run(
        ["pandaai-cli", "--json", *args], capture_output=True, text=True, timeout=timeout
    )
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return {"success": False, "error": {"message": (proc.stdout + proc.stderr).strip()[:300]}}


def parse_candidates(path: Path) -> list[dict]:
    out = []
    for lineno, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("~")]
        if len(parts) != 3:
            sys.exit(f"{path}:{lineno}: expected `name ~ formula ~ direction`, got {len(parts)} fields")
        name, formula, direction = parts
        if direction not in ("0", "1"):
            sys.exit(f"{path}:{lineno}: direction must be 0 or 1, got {direction!r}")
        out.append({"name": name, "formula": formula, "direction": direction})
    return out


def pct(text) -> float:
    """'12.34%' -> 12.34, tolerating missing values."""
    try:
        return float(str(text).rstrip("%"))
    except (TypeError, ValueError):
        return float("nan")


def extract(payload: dict, direction: str, cycle: int, round_trip: float) -> dict:
    """Pull the metrics worth comparing out of a factor_run payload."""
    analysis = (payload.get("results") or {}).get("factor_analysis") or {}
    indicators = {r["indicator"]: r.get("factor1") for r in analysis.get("query_factor_analysis_data", [])}
    groups = {r["group"]: r for r in analysis.get("query_group_return_analysis", [])}

    long_side = groups.get(HIGH if direction == "1" else LOW, {})
    short_side = groups.get(LOW if direction == "1" else HIGH, {})
    turnover = pct(long_side.get("turnoverRate"))
    excess = pct(long_side.get("excessAnnualized"))
    # Each rebalance replaces `turnover` of the holdings, costing one round trip on that slice.
    cost = turnover * round_trip * (252.0 / cycle)
    return {
        "rank_ic": indicators.get("Rank_IC"),
        "ic_ir": indicators.get("IC_IR"),
        "p_value": indicators.get("p-value"),
        "monotonicity": indicators.get("单调性"),
        "long_excess": excess,
        "short_excess": pct(short_side.get("excessAnnualized")),
        "turnover": turnover,
        "cost": round(cost, 2),
        "net_excess": round(excess - cost, 2),
    }


def report(state: dict, candidates: list[dict]) -> None:
    header = (f"{'name':<28} {'Rank_IC':>8} {'p':>7} {'mono':>6} "
              f"{'long%':>8} {'turn%':>7} {'cost%':>7} {'net%':>8}")
    print("\n" + header)
    print("-" * len(header))
    rows = [(state[c["name"]], c["name"]) for c in candidates if state.get(c["name"], {}).get("metrics")]
    for entry, name in sorted(rows, key=lambda r: -r[0]["metrics"]["net_excess"]):
        m = entry["metrics"]
        print(f"{name[:28]:<28} {str(m['rank_ic']):>8} {str(m['p_value']):>7} "
              f"{str(m['monotonicity']):>6} {m['long_excess']:>8.2f} {m['turnover']:>7.2f} "
              f"{m['cost']:>7.2f} {m['net_excess']:>8.2f}")
    print("\nlong% is the excess return of the long-side decile, net% subtracts the turnover cost.")

    failed = [c["name"] for c in candidates if state.get(c["name"], {}).get("error")]
    if failed:
        print(f"\nfailed ({len(failed)}):")
        for name in failed:
            print(f"  {name}: {state[name]['error'][:120]}")
    print(f"\ntested {len(candidates)} candidates -> multiple-testing threshold p < {0.05 / max(len(candidates), 1):.4f}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", type=Path)
    ap.add_argument("--start", required=True, help="YYYYMMDD")
    ap.add_argument("--end", required=True, help="YYYYMMDD")
    ap.add_argument("--cycle", type=int, default=5, help="rebalance cycle in days, 1-10")
    ap.add_argument("--round-trip", type=float, default=0.003,
                    help="round-trip trading cost as a fraction, default 0.3%% for A-shares")
    ap.add_argument("--prefix", default="", help="prepended to every factor name, eases bulk cleanup")
    ap.add_argument("--create-only", action="store_true", help="create factors without spending runs")
    ap.add_argument("--report-only", action="store_true", help="re-print the table from saved state")
    args = ap.parse_args()

    candidates = parse_candidates(args.file)
    state_path = args.file.with_suffix(args.file.suffix + ".state.json")
    state = json.loads(state_path.read_text()) if state_path.exists() else {}

    if args.report_only:
        report(state, candidates)
        return 0

    for i, cand in enumerate(candidates, 1):
        name = cand["name"]
        entry = state.setdefault(name, {})
        if entry.get("metrics"):
            print(f"[{i}/{len(candidates)}] {name}: done", file=sys.stderr)
            continue

        if not entry.get("factor_id"):
            created = cli("factor_create", "--formula", cand["formula"],
                          "--name", args.prefix + name,
                          "--start-date", args.start, "--end-date", args.end,
                          "--adjustment-cycle", str(args.cycle),
                          "--factor-direction", cand["direction"])
            if not created.get("success"):
                entry["error"] = f"create: {created.get('error', {}).get('message', created)}"
                state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1))
                print(f"[{i}/{len(candidates)}] {name}: create failed", file=sys.stderr)
                continue
            entry["factor_id"] = created["factor_id"]
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1))

        if args.create_only:
            print(f"[{i}/{len(candidates)}] {name}: created {entry['factor_id']}", file=sys.stderr)
            continue

        result = cli("factor_run", entry["factor_id"])
        if result.get("success"):
            entry["run_id"] = result.get("factor_run_id")
            entry["metrics"] = extract(result, cand["direction"], args.cycle, args.round_trip)
            entry.pop("error", None)
            print(f"[{i}/{len(candidates)}] {name}: net {entry['metrics']['net_excess']:+.2f}%", file=sys.stderr)
        else:
            entry["error"] = f"run: {result.get('error', {}).get('message', result)}"
            print(f"[{i}/{len(candidates)}] {name}: run failed", file=sys.stderr)
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1))

    if not args.create_only:
        report(state, candidates)
    return 0


if __name__ == "__main__":
    sys.exit(main())
