#!/usr/bin/env python3
"""Create, run, and tabulate a batch of PandaAI factor candidates.

Input is a text file with one candidate per line: `name ~ formula ~ direction`.
Blank lines and lines starting with `#` are ignored.

Progress is checkpointed to <input>.state.json after every step, so an interrupted
batch resumes without re-creating or re-running anything -- which matters because every
run costs compute credits. Each entry carries a fingerprint of the formula, direction,
window and cycle it was produced with, so an edited candidate is never resumed as if
nothing had changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

# Groups are ordered by ascending factor value, so 分组1 holds the lowest values and 分组10 the
# highest. Which end is the long side follows --factor-direction: 1 means higher is better.
# Verified by checking that 多空组合 equals long minus short for both direction settings.
LOW, HIGH = "分组1", "分组10"

# Two formula traps worth catching before they cost a run. FUTURE_RETURNS reads the answer;
# MEAN(X, 20) averages X with the constant 20 instead of taking a 20-day window, and the
# result looks entirely plausible. See references/pitfalls.md.
LOOKAHEAD = re.compile(r"\bFUTURE_\w+\s*\(", re.I)
CONSTANT_WINDOW = re.compile(r"\bMEAN\s*\(\s*[^,()]+,\s*\d+\s*\)", re.I)


def lint(formula: str) -> str | None:
    if LOOKAHEAD.search(formula):
        return "uses a future function, so its backtest cannot mean anything"
    if CONSTANT_WINDOW.search(formula):
        return "MEAN(X, N) averages X with the constant N; use MA or TS_MEAN for a rolling window"
    return None


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
    out, seen = [], {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("~")]
        if len(parts) != 3:
            sys.exit(f"{path}:{lineno}: expected `name ~ formula ~ direction`, got {len(parts)} fields")
        name, formula, direction = parts
        if direction not in ("0", "1"):
            sys.exit(f"{path}:{lineno}: direction must be 0 or 1, got {direction!r}")
        # Names key the state file, so duplicates would have two formulas share one result.
        if name in seen:
            sys.exit(f"{path}:{lineno}: candidate name {name!r} already used on line {seen[name]}")
        if (problem := lint(formula)) is not None:
            sys.exit(f"{path}:{lineno}: {name}: {problem}")
        seen[name] = lineno
        out.append({"name": name, "formula": formula, "direction": direction})
    return out


def fingerprint(cand: dict, args) -> str:
    """Everything that changes what a run means. Trading cost is absent on purpose: it is
    applied locally at report time, so changing it never needs another run."""
    spec = json.dumps([cand["formula"], cand["direction"], args.start, args.end, args.cycle],
                      ensure_ascii=False)
    return hashlib.sha256(spec.encode("utf-8")).hexdigest()[:16]


def save(path: Path, state: dict) -> None:
    """Write through a temporary file, so an interrupt cannot truncate the whole batch."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def pct(text) -> float:
    """'12.34%' -> 12.34, tolerating missing values."""
    try:
        return float(str(text).rstrip("%"))
    except (TypeError, ValueError):
        return float("nan")


def extract(payload: dict, direction: str) -> dict:
    """Pull the metrics worth comparing out of a factor_run payload.

    Raises ValueError rather than returning NaN: a candidate missing its long side has not
    produced a weak result, it has produced no result, and ranking it would be a fiction.
    """
    analysis = (payload.get("results") or {}).get("factor_analysis") or {}
    indicators = {r["indicator"]: r.get("factor1") for r in analysis.get("query_factor_analysis_data", [])}
    groups = {r["group"]: r for r in analysis.get("query_group_return_analysis", [])}

    long_name = HIGH if direction == "1" else LOW
    short_name = LOW if direction == "1" else HIGH
    if long_name not in groups:
        raise ValueError(f"no {long_name} row in the group returns")
    turnover = pct(groups[long_name].get("turnoverRate"))
    excess = pct(groups[long_name].get("excessAnnualized"))
    if not (math.isfinite(turnover) and math.isfinite(excess)):
        raise ValueError(f"{long_name} returned no usable excess return or turnover")
    return {
        "ic_mean": indicators.get("IC_mean"),
        "rank_ic": indicators.get("Rank_IC"),
        "ic_ir": indicators.get("IC_IR"),
        # The platform's p-value belongs to the IC_mean t-statistic, not to Rank_IC.
        "ic_p_value": indicators.get("p-value"),
        "monotonicity": indicators.get("单调性"),
        "long_excess": excess,
        "short_excess": pct(groups.get(short_name, {}).get("excessAnnualized")),
        "turnover": turnover,
    }


def cost_of(metrics: dict, cycle: int, round_trip: float) -> float:
    """Each rebalance replaces `turnover` of the holdings, costing one round trip on that slice."""
    return metrics["turnover"] * round_trip * (252.0 / cycle)


def report(state: dict, candidates: list[dict], cycle: int, round_trip: float,
           hypotheses: int) -> None:
    header = (f"{'name':<28} {'IC_mean':>8} {'Rank_IC':>8} {'IC_p':>7} {'mono':>6} "
              f"{'long%':>8} {'turn%':>7} {'cost%':>7} {'net%':>8}")
    print("\n" + header)
    print("-" * len(header))
    rows = []
    for cand in candidates:
        metrics = state.get(cand["name"], {}).get("metrics")
        if metrics:
            cost = cost_of(metrics, cycle, round_trip)
            rows.append((cand["name"], metrics, cost, metrics["long_excess"] - cost))
    for name, m, cost, net in sorted(rows, key=lambda r: -r[3]):
        print(f"{name[:28]:<28} {str(m.get('ic_mean')):>8} {str(m['rank_ic']):>8} "
              f"{str(m.get('ic_p_value')):>7} {str(m['monotonicity']):>6} {m['long_excess']:>8.2f} "
              f"{m['turnover']:>7.2f} {cost:>7.2f} {net:>8.2f}")
    print(f"\nlong% is the excess return of the long-side decile; net% subtracts the turnover cost"
          f" at {round_trip:.2%} round trip.")
    print("IC_p is the p-value of the IC_mean t-statistic. Rank_IC has no p-value of its own.")

    failed = [c["name"] for c in candidates if state.get(c["name"], {}).get("error")]
    if failed:
        print(f"\nfailed ({len(failed)}, not retried unless you pass --retry-failed):")
        for name in failed:
            print(f"  {name}: {state[name]['error'][:120]}")
    threshold = 0.05 / max(hypotheses, 1)
    scope = "in this file" if hypotheses == len(candidates) else "in this study"
    print(f"\ntested {hypotheses} candidate{'s' if hypotheses != 1 else ''} {scope}"
          f" -> multiple-testing threshold p < {threshold:.4f}")
    if hypotheses == len(candidates):
        print("Pass --hypotheses with the running total once a study spans several files,"
              " or this threshold resets every batch.")


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
    ap.add_argument("--retry-failed", action="store_true",
                    help="run the candidates that failed last time; each retry costs credits again")
    ap.add_argument("--max-runs", type=int, default=0,
                    help="stop after this many runs, whatever remains in the file (0 = no cap)")
    ap.add_argument("--hypotheses", type=int, default=0,
                    help="candidates tested in the whole study so far, for the multiple-testing "
                         "threshold (0 = just this file)")
    args = ap.parse_args()

    candidates = parse_candidates(args.file)
    hypotheses = max(args.hypotheses, len(candidates))
    state_path = args.file.with_suffix(args.file.suffix + ".state.json")
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}

    if args.report_only:
        report(state, candidates, args.cycle, args.round_trip, hypotheses)
        return 0

    # Check every fingerprint before spending anything: a stale entry reused as if it were
    # fresh is how an in-sample result ends up reported as out-of-sample.
    stale, unverified = [], []
    for cand in candidates:
        entry = state.get(cand["name"], {})
        if not entry:
            continue
        if saved := entry.get("spec"):
            if saved != fingerprint(cand, args):
                stale.append(cand["name"])
        elif entry.get("metrics"):
            unverified.append(cand["name"])
    if unverified:
        print(f"note: {len(unverified)} saved result(s) predate fingerprinting and cannot be "
              f"checked against\nthe current settings. Delete their entries to re-run them."
              , file=sys.stderr)
    if stale:
        print("These candidates were last run with a different formula, direction, window or "
              "cycle:", file=sys.stderr)
        for name in stale:
            print(f"  {name}", file=sys.stderr)
        print(f"\nReusing their saved results would misreport them. Either restore the old "
              f"settings, or\nstart a separate state file by copying the candidates into a new "
              f"filename.\n(state file: {state_path})", file=sys.stderr)
        return 1

    runs = 0
    for i, cand in enumerate(candidates, 1):
        name = cand["name"]
        entry = state.setdefault(name, {})
        if entry.get("metrics"):
            print(f"[{i}/{len(candidates)}] {name}: done", file=sys.stderr)
            continue
        # A failure already cost a run. Repeating it on the next invocation costs another one,
        # which is not what someone re-running an interrupted batch is asking for.
        if entry.get("error") and not args.retry_failed:
            print(f"[{i}/{len(candidates)}] {name}: failed before, skipping", file=sys.stderr)
            continue
        if args.max_runs and runs >= args.max_runs and not args.create_only:
            print(f"\nstopping at the {args.max_runs}-run cap;"
                  f" re-run to continue from here", file=sys.stderr)
            break
        entry["spec"] = fingerprint(cand, args)

        if not entry.get("factor_id"):
            created = cli("factor_create", "--formula", cand["formula"],
                          "--name", args.prefix + name,
                          "--start-date", args.start, "--end-date", args.end,
                          "--adjustment-cycle", str(args.cycle),
                          "--factor-direction", cand["direction"])
            if not created.get("success"):
                entry["error"] = f"create: {created.get('error', {}).get('message', created)}"
                save(state_path, state)
                print(f"[{i}/{len(candidates)}] {name}: create failed", file=sys.stderr)
                continue
            entry["factor_id"] = created["factor_id"]
            save(state_path, state)

        if args.create_only:
            print(f"[{i}/{len(candidates)}] {name}: created {entry['factor_id']}", file=sys.stderr)
            continue

        result = cli("factor_run", entry["factor_id"])
        runs += 1
        if result.get("success"):
            entry["run_id"] = result.get("factor_run_id")
            try:
                entry["metrics"] = extract(result, cand["direction"])
                entry.pop("error", None)
                net = entry["metrics"]["long_excess"] - cost_of(entry["metrics"], args.cycle,
                                                                args.round_trip)
                print(f"[{i}/{len(candidates)}] {name}: net {net:+.2f}%", file=sys.stderr)
            except ValueError as exc:
                entry["error"] = f"result: {exc}"
                print(f"[{i}/{len(candidates)}] {name}: unusable result -- {exc}", file=sys.stderr)
        else:
            entry["error"] = f"run: {result.get('error', {}).get('message', result)}"
            print(f"[{i}/{len(candidates)}] {name}: run failed", file=sys.stderr)
        save(state_path, state)

    if not args.create_only:
        report(state, candidates, args.cycle, args.round_trip, hypotheses)
    return 0


if __name__ == "__main__":
    sys.exit(main())
