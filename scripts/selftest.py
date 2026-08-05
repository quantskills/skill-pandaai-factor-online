#!/usr/bin/env python3
"""Self-test for the scripts in this skill. No network, no compute credits.

    python3 scripts/selftest.py

Covers the failures that cost real money or produce wrong research conclusions: resuming a
state file that no longer matches its candidates, re-running a failure, ranking a payload
that has no long side, reading the long side of the wrong decile, and the two environment
crashes (Python 3.9, non-UTF-8 default encoding) that stop the skill before it says why.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import analyze  # noqa: E402
import batch  # noqa: E402
import bootstrap  # noqa: E402


def run_payload(long_excess="10.00%", turnover="60.00%", short_excess="-5.00%",
                groups=("分组1", "分组10")) -> dict:
    rows = [{"group": g,
             "excessAnnualized": long_excess if g == "分组10" else short_excess,
             "turnoverRate": turnover} for g in groups]
    return {"success": True, "results": {"factor_analysis": {
        "query_factor_analysis_data": [
            {"indicator": "IC_mean", "factor1": 0.02},
            {"indicator": "Rank_IC", "factor1": 0.05},
            {"indicator": "IC_IR", "factor1": 0.3},
            {"indicator": "p-value", "factor1": 0.01},
            {"indicator": "单调性", "factor1": 0.7},
        ],
        "query_group_return_analysis": rows}}}


class Args:
    """Stands in for the argparse namespace batch.py passes around."""
    start, end, cycle, round_trip = "20230101", "20231231", 5, 0.003
    prefix, create_only, report_only = "", False, False
    retry_failed, max_runs, hypotheses = False, 0, 0
    file = Path("candidates.txt")


class FormulaLint(unittest.TestCase):
    def test_rejects_look_ahead(self):
        self.assertIn("future", batch.lint("FUTURE_RETURNS(CLOSE,5)"))

    def test_rejects_constant_window(self):
        self.assertIn("MEAN", batch.lint("MEAN(CLOSE, 20)"))

    def test_accepts_the_rolling_forms(self):
        for formula in ("MA(CLOSE,20)", "TS_MEAN(CLOSE, 20)", "MEAN(CLOSE, OPEN)",
                        "BIAS(CLOSE,5)/MA(VOLUME,20)"):
            self.assertIsNone(batch.lint(formula), formula)


class CandidateFile(unittest.TestCase):
    def parse(self, text: str) -> list[dict]:
        path = Path(self.tmp) / "candidates.txt"
        path.write_text(text, encoding="utf-8")
        return batch.parse_candidates(path)

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_reads_chinese_names_whatever_the_locale(self):
        parsed = self.parse("五日反转 ~ BIAS(CLOSE,5) ~ 0\n")
        self.assertEqual(parsed[0]["name"], "五日反转")

    def test_rejects_duplicate_names(self):
        with self.assertRaises(SystemExit) as caught:
            self.parse("a ~ BIAS(CLOSE,5) ~ 0\na ~ BIAS(CLOSE,20) ~ 0\n")
        self.assertIn("already used", str(caught.exception))

    def test_rejects_a_look_ahead_formula_before_it_costs_anything(self):
        with self.assertRaises(SystemExit):
            self.parse("peek ~ FUTURE_RETURNS(CLOSE,5) ~ 1\n")

    def test_rejects_a_bad_direction(self):
        with self.assertRaises(SystemExit):
            self.parse("a ~ BIAS(CLOSE,5) ~ 2\n")

    def test_python_mode_requires_a_valid_factor_file(self):
        factor = Path(self.tmp) / "factor.py"
        factor.write_text("class Demo(Factor):\n    def calculate(self, factors):\n        return factors['close']\n", encoding="utf-8")
        manifest = Path(self.tmp) / "python-candidates.txt"
        manifest.write_text("demo ~ factor.py ~ 1\n", encoding="utf-8")
        parsed = batch.parse_candidates(manifest, "python")
        self.assertEqual(parsed[0]["mode"], "python")
        self.assertIn("class Demo", parsed[0]["content"])

    def test_python_mode_rejects_missing_calculate(self):
        factor = Path(self.tmp) / "bad.py"
        factor.write_text("class Demo(Factor):\n    pass\n", encoding="utf-8")
        manifest = Path(self.tmp) / "python-candidates.txt"
        manifest.write_text("bad ~ bad.py ~ 1\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            batch.parse_candidates(manifest, "python")


class Fingerprint(unittest.TestCase):
    def setUp(self):
        self.cand = {"name": "a", "formula": "BIAS(CLOSE,5)", "direction": "0"}
        self.base = batch.fingerprint(self.cand, Args())

    def test_stable_across_calls(self):
        self.assertEqual(self.base, batch.fingerprint(self.cand, Args()))

    def test_changes_with_anything_that_changes_the_run(self):
        for field, value in (("formula", "BIAS(CLOSE,20)"), ("direction", "1")):
            changed = dict(self.cand, **{field: value})
            self.assertNotEqual(self.base, batch.fingerprint(changed, Args()), field)
        for field, value in (("start", "20200101"), ("end", "20241231"), ("cycle", 10)):
            args = Args()
            setattr(args, field, value)
            self.assertNotEqual(self.base, batch.fingerprint(self.cand, args), field)

    def test_survives_a_trading_cost_change(self):
        # Cost is applied locally at report time, so changing it must not force a paid re-run.
        args = Args()
        args.round_trip = 0.005
        self.assertEqual(self.base, batch.fingerprint(self.cand, args))


class Extract(unittest.TestCase):
    def test_direction_picks_the_matching_end(self):
        payload = run_payload(long_excess="10.00%", short_excess="-5.00%")
        self.assertEqual(batch.extract(payload, "1")["long_excess"], 10.0)
        self.assertEqual(batch.extract(payload, "0")["long_excess"], -5.0)

    def test_p_value_is_named_for_the_statistic_it_belongs_to(self):
        metrics = batch.extract(run_payload(), "1")
        self.assertEqual(metrics["ic_p_value"], 0.01)
        self.assertNotIn("p_value", metrics)

    def test_accepts_the_live_cli_factor_value_field(self):
        payload = run_payload()
        for row in payload["results"]["factor_analysis"]["query_factor_analysis_data"]:
            row["factor_value"] = row.pop("factor1")
        metrics = batch.extract(payload, "1")
        self.assertEqual(metrics["rank_ic"], 0.05)
        self.assertEqual(metrics["ic_p_value"], 0.01)

    def test_accepts_factor_result_top_level_shape(self):
        payload = run_payload()
        payload = {"success": True, "factor_analysis": payload["results"]["factor_analysis"]}
        metrics = batch.extract(payload, "1")
        self.assertEqual(metrics["long_excess"], 10.0)

    def test_refuses_a_payload_without_the_long_side(self):
        with self.assertRaises(ValueError):
            batch.extract(run_payload(groups=("分组1",)), "1")

    def test_refuses_an_unparseable_return(self):
        with self.assertRaises(ValueError):
            batch.extract(run_payload(long_excess=None), "1")

    def test_cost_matches_the_documented_formula(self):
        metrics = batch.extract(run_payload(turnover="60.00%"), "1")
        self.assertAlmostEqual(batch.cost_of(metrics, 5, 0.003), 60 * 0.003 * 2 * (252 / 5))


class BatchRun(unittest.TestCase):
    """Drives main() with the CLI stubbed out, so nothing leaves the machine."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.file = self.tmp / "candidates.txt"
        self.state = self.tmp / "candidates.txt.state.json"
        self.calls = []
        self.results = {}
        real_cli = batch.cli

        def fake_cli(*args, **kwargs):
            self.calls.append(args)
            if args[0] == "factor_create":
                return {"success": True, "factor_id": f"f{len(self.calls)}"}
            return self.results.get("run", run_payload())

        batch.cli = fake_cli
        self.addCleanup(setattr, batch, "cli", real_cli)

    def main(self, *extra: str) -> int:
        old, sys.argv = sys.argv, ["batch.py", str(self.file), "--start", "20230101",
                                   "--end", "20231231", "--cycle", "5", *extra]
        self.out = io.StringIO()
        try:
            with contextlib.redirect_stdout(self.out), contextlib.redirect_stderr(self.out):
                return batch.main()
        finally:
            sys.argv = old

    def runs(self) -> int:
        return sum(1 for c in self.calls if c[0] == "factor_run")

    def test_resume_skips_finished_candidates(self):
        self.file.write_text("a ~ BIAS(CLOSE,5) ~ 0\nb ~ BIAS(CLOSE,20) ~ 0\n", encoding="utf-8")
        self.assertEqual(self.main(), 0)
        self.assertEqual(self.runs(), 2)
        self.assertEqual(self.main(), 0)
        self.assertEqual(self.runs(), 2)

    def test_an_edited_formula_stops_the_batch_instead_of_reusing_the_result(self):
        self.file.write_text("a ~ BIAS(CLOSE,5) ~ 0\n", encoding="utf-8")
        self.main()
        self.file.write_text("a ~ BIAS(CLOSE,60) ~ 0\n", encoding="utf-8")
        self.assertEqual(self.main(), 1)
        self.assertEqual(self.runs(), 1)

    def test_a_new_window_stops_the_batch_too(self):
        # This is the out-of-sample path: same candidates, a reserved earlier window.
        self.file.write_text("a ~ BIAS(CLOSE,5) ~ 0\n", encoding="utf-8")
        self.main()
        self.assertEqual(self.main("--start", "20200101", "--end", "20201231"), 1)
        self.assertEqual(self.runs(), 1)

    def test_a_failure_is_not_retried_unless_asked(self):
        self.file.write_text("a ~ BIAS(CLOSE,5) ~ 0\n", encoding="utf-8")
        self.results["run"] = {"success": False, "error": {"message": "boom"}}
        self.main()
        self.assertEqual(self.runs(), 1)
        self.main()
        self.assertEqual(self.runs(), 1)
        self.main("--retry-failed")
        self.assertEqual(self.runs(), 2)

    def test_max_runs_caps_the_spend(self):
        self.file.write_text("".join(f"c{i} ~ BIAS(CLOSE,{i}) ~ 0\n" for i in range(5)),
                             encoding="utf-8")
        self.main("--max-runs", "2")
        self.assertEqual(self.runs(), 2)

    def test_complex_factor_uses_cli_file_mode_and_returns_metrics(self):
        # Prompt-level decision: rolling state plus conditional logic is clearer as Python than
        # as one opaque formula. The stub confirms the exact CLI path without spending credits.
        source = self.tmp / "complex_factor.py"
        source.write_text(
            "class ComplexFactor(Factor):\n"
            "    def calculate(self, factors):\n"
            "        close = factors['close']\n"
            "        return close.rolling(20).mean()\n",
            encoding="utf-8",
        )
        self.file.write_text("complex state ~ complex_factor.py ~ 1\n", encoding="utf-8")
        self.assertEqual(self.main("--mode", "python"), 0)
        create = next(call for call in self.calls if call[0] == "factor_create")
        self.assertIn("--file", create)
        self.assertNotIn("--formula", create)
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertIn("metrics", state["complex state"])

    def test_an_unusable_result_is_a_failure_not_a_ranked_row(self):
        self.file.write_text("a ~ BIAS(CLOSE,5) ~ 0\n", encoding="utf-8")
        self.results["run"] = run_payload(groups=("分组10",))  # direction 0 wants 分组1
        self.main()
        entry = json.loads(self.state.read_text(encoding="utf-8"))["a"]
        self.assertIn("result:", entry["error"])
        self.assertNotIn("metrics", entry)

    def test_state_survives_chinese_names_and_stays_valid_json(self):
        self.file.write_text("五日反转 ~ BIAS(CLOSE,5) ~ 0\n", encoding="utf-8")
        self.main()
        saved = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertIn("五日反转", saved)
        self.assertFalse(list(self.tmp.glob("*.tmp")), "atomic write left a temporary file behind")


class Spearman(unittest.TestCase):
    def rho(self, a: dict, b: dict):
        return analyze.spearman(a, b, min_names=1)

    def test_perfect_agreement(self):
        a = {f"s{i}": float(i) for i in range(10)}
        self.assertAlmostEqual(self.rho(a, a), 1.0)

    def test_perfect_disagreement(self):
        a = {f"s{i}": float(i) for i in range(10)}
        b = {f"s{i}": float(-i) for i in range(10)}
        self.assertAlmostEqual(self.rho(a, b), -1.0)

    def test_ties_take_the_average_rank(self):
        # Ordinal ranks would break the tie arbitrarily and report |rho| = 1.
        a = {"x": 1.0, "y": 1.0, "z": 2.0}
        b = {"x": 5.0, "y": 6.0, "z": 7.0}
        self.assertAlmostEqual(self.rho(a, b), 0.8660254, places=6)

    def test_all_tied_is_undefined_not_zero_variance_division(self):
        flat = {"x": 1.0, "y": 1.0, "z": 1.0}
        self.assertIsNone(self.rho(flat, {"x": 1.0, "y": 2.0, "z": 3.0}))

    def test_ranks_average_within_a_tied_block(self):
        got = analyze.ranks({"a": 1.0, "b": 1.0, "c": 3.0}, ["a", "b", "c"])
        self.assertEqual(got, {"a": 0.5, "b": 0.5, "c": 2.0})


class Turnover(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def csv(self, rows) -> Path:
        path = self.tmp / "factor.csv"
        path.write_text("date,symbol,factor1\n" + "".join(rows), encoding="utf-8")
        return path

    def test_direction_selects_the_side_actually_held(self):
        # 1000 names over two dates. The bottom decile holds exactly the same names on both,
        # while the top decile turns over completely: names 800-899 climb past 900-999. So a
        # direction-0 factor must report no turnover and a direction-1 factor total turnover.
        rows = []
        for i in range(1000):
            second = i + 200 if 800 <= i < 900 else i - 100 if i >= 900 else i
            rows.append(f"20230101,s{i},{i}\n20230108,s{i},{second}\n")
        path = self.csv(rows)

        class A:
            file, cycle, sample, round_trip = str(path), 1, 5, 0.003
            direction = 0

        for direction, expected, side in ((0, "0.0%", "bottom"), (1, "100.0%", "top")):
            A.direction = direction
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                analyze.cmd_turnover(A)
            text = out.getvalue()
            self.assertIn(f"{side}-decile turnover {expected}", text, text)

    def test_non_finite_values_are_dropped(self):
        path = self.csv(["20230101,a,nan\n", "20230101,b,1.0\n", "20230101,c,\n"])
        self.assertEqual(analyze.read_days(path, {"20230101"}), {"20230101": {"b": 1.0}})


class Environment(unittest.TestCase):
    """The two crashes that stop the skill before it can explain itself."""

    def test_scripts_declare_an_encoding_for_every_file_they_touch(self):
        # The default encoding is GBK on a Chinese Windows install, and every reference file
        # and candidate name here is UTF-8.
        text_io = {"read_text", "write_text", "open"}
        offenders = []
        for path in sorted(SCRIPTS.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                called = getattr(node.func, "attr", getattr(node.func, "id", None))
                if called in text_io and not any(k.arg == "encoding" for k in node.keywords):
                    offenders.append(f"{path.name}:{node.lineno}: {called}()")
        self.assertEqual(offenders, [], "\n".join(["missing encoding='utf-8':"] + offenders))

    def test_cli_version_probe_stays_quiet_when_it_cannot_run(self):
        # It runs an interpreter parsed out of a shebang, which may be anything or gone.
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            bootstrap.report_cli_version("/nonexistent/python")
            bootstrap.report_cli_version(sys.executable)  # real, but without pandaai-cli installed
        self.assertNotIn("fail", out.getvalue())

    def test_references_load_under_an_ascii_locale(self):
        env = {**os.environ, "LC_ALL": "C", "LANG": "C",
               "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0", "PYTHONIOENCODING": "utf-8"}
        proc = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, r'%s'); import bootstrap; bootstrap.check_references()"
             % SCRIPTS],
            capture_output=True, text=True, env=env, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("fields available", proc.stdout)

    def test_preflight_explains_itself_on_python_39(self):
        python39 = which39()
        if not python39:
            self.skipTest("no Python 3.9 available; `uv python install 3.9` to run this")
        proc = subprocess.run([python39, str(SCRIPTS / "bootstrap.py")],
                              capture_output=True, text=True, cwd=ROOT)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("3.10 or newer", proc.stdout)

    def test_installer_explains_itself_on_python_39(self):
        python39 = which39()
        if not python39:
            self.skipTest("no Python 3.9 available; `uv python install 3.9` to run this")
        if not (SCRIPTS / "install.py").exists():
            self.skipTest("install.py ships with the repository, not with the skill package")
        target = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, target)
        proc = subprocess.run([python39, str(SCRIPTS / "install.py"), "project", target],
                              capture_output=True, text=True, cwd=ROOT)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("3.10 or newer", proc.stdout)


def which39() -> str | None:
    found = shutil.which("python3.9")
    if found:
        return found
    if shutil.which("uv"):
        proc = subprocess.run(["uv", "python", "find", "3.9"], capture_output=True, text=True)
        if proc.returncode == 0:
            return proc.stdout.strip()
    return None


if __name__ == "__main__":
    unittest.main(verbosity=2)
