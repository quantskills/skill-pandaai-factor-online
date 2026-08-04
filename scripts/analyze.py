#!/usr/bin/env python3
"""Local analysis of downloaded PandaAI factor values -- no compute credits spent.

Input files are the CSVs written by `pandaai-cli factor_result <run_id> --download`
(columns: date,symbol,factor1). Remember to omit --json or nothing is written to disk.

  corr      cross-sectional Spearman correlation between factors, to catch redundancy
  turnover  decile churn and rank autocorrelation at a given rebalance cycle

Both sample a subset of dates, because these files run to millions of rows.
"""

import argparse
import csv
import statistics
import sys
from pathlib import Path


def read_dates(path: Path) -> list[str]:
    with path.open() as fh:
        reader = csv.reader(fh)
        next(reader, None)
        return sorted({row[0] for row in reader if row})


def read_days(path: Path, wanted: set[str]) -> dict[str, dict[str, float]]:
    """Load {date: {symbol: value}} for the requested dates only."""
    out: dict[str, dict[str, float]] = {d: {} for d in wanted}
    with path.open() as fh:
        reader = csv.reader(fh)
        next(reader, None)
        for row in reader:
            if len(row) < 3 or row[0] not in out:
                continue
            try:
                out[row[0]][row[1]] = float(row[2])
            except ValueError:
                continue  # NaN / empty factor value
    return out


def ranks(values: dict[str, float], keys) -> dict[str, int]:
    return {s: i for i, s in enumerate(sorted(keys, key=lambda s: values[s]))}


def spearman(a: dict[str, float], b: dict[str, float], min_names: int = 300) -> float | None:
    common = set(a) & set(b)
    if len(common) < min_names:
        return None
    ra, rb = ranks(a, common), ranks(b, common)
    n = len(common)
    mid = (n - 1) / 2
    num = sum((ra[s] - mid) * (rb[s] - mid) for s in common)
    den = sum((ra[s] - mid) ** 2 for s in common)
    return num / den if den else None


def sample_dates(dates: list[str], count: int) -> list[str]:
    if len(dates) <= count:
        return dates
    step = len(dates) / count
    return [dates[int(i * step)] for i in range(count)]


def label(path: Path) -> str:
    """Downloaded files are all named factor_data_<timestamp>, so fall back to the folder."""
    return path.parent.name if path.stem.startswith("factor_data") else path.stem


def cmd_corr(args) -> int:
    paths = [Path(p) for p in args.files]
    base = sample_dates(read_dates(paths[0]), args.sample)
    loaded = {}
    for path in paths:
        name = label(path)
        loaded[name] = read_days(path, set(base))
        covered = [len(v) for v in loaded[name].values() if v]
        print(f"{name}: {len(covered)} sampled days, "
              f"{int(statistics.mean(covered)) if covered else 0} names/day", file=sys.stderr)

    names = list(loaded)
    width = min(max(len(n) for n in names), 16)
    cell = max(width, 6)
    print("\ncross-sectional Spearman, averaged over sampled days\n")
    print(" " * width + "  " + "  ".join(f"{n[:cell]:>{cell}}" for n in names))
    for a in names:
        cells = []
        for b in names:
            if a == b:
                cells.append(f"{1.0:>{cell}.2f}")
                continue
            vals = [c for d in base
                    if (c := spearman(loaded[a].get(d, {}), loaded[b].get(d, {}))) is not None]
            cells.append(f"{statistics.mean(vals):>{cell}.2f}" if vals else f"{'--':>{cell}}")
        print(f"{a[:width]:<{width}}  " + "  ".join(cells))
    print("\nAbove ~0.6 the two factors are largely the same bet.")
    return 0


def cmd_turnover(args) -> int:
    path = Path(args.file)
    dates = read_dates(path)
    anchors = sample_dates(dates[: -args.cycle or None], args.sample)
    index = {d: i for i, d in enumerate(dates)}
    pairs = [(d, dates[index[d] + args.cycle]) for d in anchors if index[d] + args.cycle < len(dates)]

    data = read_days(path, {d for pair in pairs for d in pair})
    churn, autocorr, coverage = [], [], []
    for first, second in pairs:
        a, b = data.get(first, {}), data.get(second, {})
        if len(a) < 300 or len(b) < 300:
            continue
        coverage.append(len(a))
        size = max(1, len(a) // 10)
        top_a = set(sorted(a, key=lambda s: -a[s])[:size])
        top_b = set(sorted(b, key=lambda s: -b[s])[:size])
        churn.append(1 - len(top_a & top_b) / size)
        if (rho := spearman(a, b)) is not None:
            autocorr.append(rho)

    if not churn:
        print("not enough overlapping data to measure turnover", file=sys.stderr)
        return 1

    turnover = statistics.mean(churn)
    cost = turnover * args.round_trip * (252 / args.cycle)
    print(f"{path.name}")
    print(f"  sampled rebalances     {len(churn)} at a {args.cycle}-day cycle")
    print(f"  names per day          {int(statistics.mean(coverage))}")
    print(f"  top-decile turnover    {turnover:.1%} replaced per rebalance")
    print(f"  rank autocorrelation   {statistics.mean(autocorr):+.2f} over {args.cycle} days")
    print(f"  implied annual cost    {cost:.1%} at {args.round_trip:.2%} round trip")
    print("\nSubtract the cost from the top-group excess return before ranking candidates.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("corr", help="pairwise cross-sectional Spearman between factor CSVs")
    c.add_argument("files", nargs="+")
    c.add_argument("--sample", type=int, default=30, help="number of days to sample")
    c.set_defaults(func=cmd_corr)

    t = sub.add_parser("turnover", help="decile churn and rank autocorrelation for one factor CSV")
    t.add_argument("file")
    t.add_argument("--cycle", type=int, default=5, help="rebalance cycle in trading days")
    t.add_argument("--sample", type=int, default=30, help="number of rebalances to sample")
    t.add_argument("--round-trip", type=float, default=0.003, help="round-trip trading cost")
    t.set_defaults(func=cmd_turnover)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
