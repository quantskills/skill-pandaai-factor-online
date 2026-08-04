---
name: skill-pandaai-factor-online
description: Set up pandaai-cli, log in to PandaAI, and mine, backtest, and iterate quantitative factors on the platform. Use when the user works on the PandaAI factor competition, installs or logs in to pandaai-cli, asks which fields or operators are available, writes or debugs factor formulas, runs factor analysis, or interprets IC / group-return / turnover results.
license: MIT
---

# PandaAI Factor Online

Everything needed to go from a bare machine to a running factor analysis on PandaAI, then to iterate
without wasting compute credits.

中文版见 [SKILL.zh-CN.md](SKILL.zh-CN.md)。

## Start here

```bash
python3 scripts/bootstrap.py
```

It checks the Python environment, the CLI install, the config file, login state, compute balance,
the number of factors already on the account, and the bundled field and operator lists — and prints
the exact next command whenever a step is not satisfied. Work through the steps below in order; the
first four are onboarding and only need doing once.

## Step 1: Python environment

`pandaai-cli` needs Python 3.10 or newer. Install it as an isolated tool so it stays on `PATH`
regardless of which virtualenv is active:

```bash
uv tool install pandaai-cli        # or: pipx install pandaai-cli
```

If the user prefers a project virtualenv, `uv venv && uv pip install pandaai-cli` works too, but
then every later command must run with that environment activated. Mixing the two is the usual cause
of "command not found" after a successful install: `pip install` can place the script in a user bin
directory that is not on `PATH`.

`bootstrap.py` prints both the interpreter running the script and the one behind the `pandaai-cli`
executable, so confirm they are the environment the project should be using before going further.

## Step 2: Log in

```bash
pandaai-cli login --phone <phone> --password <password>
```

Omitting both flags prompts for them instead, which keeps the password out of shell history. The
account is the one registered on the PandaAI website; the token is written to
`~/.pandaai/config.yaml` and every later command reuses it.

**No password, or forgot it?** Set one at <https://www.pandaaiquant.com/personalcenter?id=1>. Accounts
created by SMS code alone have no password until this is done.

**If the AI tool refuses to handle the password**, do not fight it. Ask the user to run the full
command themselves in a terminal — PowerShell on Windows — and then continue. The token lands in the
config file, so the agent can do everything else without ever seeing the credentials.

**Login fails on a clean machine with `CONFIG_ERROR: 配置文件不存在`.** In pandaai-cli 0.1.x, `cli.py`
loads the config before dispatching any subcommand, and the loader exits when the file is missing —
so `login`, the command that creates it, never gets to run. `bootstrap.py` seeds the file; to do it
by hand:

```yaml
# ~/.pandaai/config.yaml
gateway_url: https://www.pandaaiquant.com/pandaApi
country_code: '86'
```

## Step 3: Check the account before mining

```bash
pandaai-cli --json balance                          # compute credits
pandaai-cli --json factor_list --limit 1 --no-detail  # `total` is the factor count
```

Each run costs roughly 2 credits, so the balance translates directly into how many experiments are
affordable — divide by two and plan the batch sizes against that number. The factor count matters
because names collide and old experiments pile up; give each batch a distinct name prefix so
`factor_delete --pattern <prefix>` can clean it up later.

## Step 4: Know what you can use

348 data fields and 137 operators are available. Both lists ship with this skill and should be
consulted before writing any formula, since a wrong name costs a run to discover:

- [references/fields.md](references/fields.md) — 8 price/volume fields plus 340 fundamentals
- [references/operators.md](references/operators.md) — the official operator manual in full:
  signatures, semantics, and a worked example per function, in eleven categories

Two authoring modes. **Formula mode** (`--formula`) may span several lines with intermediate
variables; the platform takes the last line as the factor value, and field names are
case-insensitive. **Python mode** (`--code` or `--file`) subclasses `Factor` and implements
`calculate(self, factors)`, returning a Series named `value` indexed by `[symbol, date]`, with the
same operators available:

```python
class ComplexFactor(Factor):
    def calculate(self, factors):
        close, volume = factors['close'], factors['volume']
        momentum = RANK((close / DELAY(close, 20)) - 1)
        vol_signal = IF(STDDEV(close / DELAY(close, 1) - 1, 20) > 0.02, 1, -1)
        return momentum * vol_signal
```

Formula mode is faster to iterate and enough for most candidates; Python mode is easier to maintain
once a factor needs several intermediate steps.

What the CLI can actually do:

| Capability | Command |
|---|---|
| Define a factor from a formula or Python code | `factor_create` |
| Inspect or change a definition | `factor_info`, `factor_update` |
| Run the analysis and get results | `factor_run` |
| Re-query a finished run | `factor_result` |
| Download raw per-stock factor values as CSV | `factor_result <run_id> --download PATH` |
| List factors with one-line performance summaries | `factor_list` |
| Check credits | `balance` |
| Clean up by id or name prefix | `factor_delete` |

A completed run returns IC statistics (IC_mean, Rank_IC, IC_IR, t-statistic, p-value, monotonicity),
per-decile annualized and excess returns with turnover and win rates, the current top-ranked names,
and ten chart series. Full flag reference and known CLI bugs: [references/cli.md](references/cli.md).

## Platform constraints

| Constraint | Value |
|---|---|
| Backtest window | **3 years maximum**, longer ranges are rejected at creation |
| Groups | Fixed at 10 |
| Universe | Fixed at 沪深全A |
| Rebalance cycle | 1–10 days, set at creation |
| Compute | Fixed cpu=4 / mem=8 / gpu=4 |

If the competition locks the rebalance cycle once you submit, choose it **before** mining and
evaluate every candidate at that cycle. A factor that looks strong at 1-day rebalancing can be
unusable at 5.

## Writing formulas

The most expensive trap, because it fails silently:

```
MA(CLOSE, 20)        # rolling 20-day mean   ← usually what you want
TS_MEAN(CLOSE, 20)   # identical
MEAN(CLOSE, OPEN)    # mean across two series, NOT a rolling window
```

`MEAN(CLOSE, 20)` parses, runs, and returns a plausible-looking factor that measures price level
instead. Read [references/pitfalls.md](references/pitfalls.md) before writing anything with a
lookback window — it also covers look-ahead operators, cross-sectional versus time-series functions,
the direction flag, and why nearly everything correlates with market cap.

**Validate cheaply.** Before a 3-year run, create the same formula over a ~3-month window and run it
once. Syntax and field errors surface at the same credit cost but a fraction of the wall-clock time.

## Running

```bash
pandaai-cli --json factor_create --formula "BIAS(CLOSE,20)" --name "20d bias" \
  --start-date 20230101 --end-date 20251231 --adjustment-cycle 5 --factor-direction 0
pandaai-cli --json factor_run <factor_id>
```

For anything beyond one candidate, use the batch script. It creates, runs, tabulates, and
checkpoints after each step so an interruption never re-spends credits:

```bash
python3 scripts/batch.py candidates.txt --start 20230101 --end 20251231 --cycle 5 --prefix "probe-"
```

Each line of the input file is `name ~ formula ~ direction`:

```
20d bias ~ BIAS(CLOSE,20) ~ 0
60d high distance ~ CLOSE/TS_MAX(HIGH,60) ~ 0
```

## Reading results

The platform headlines a long-short annualized return, which assumes a short leg A-share
participants cannot build. Judge candidates on the long side instead:

1. **Long-decile excess return.** Groups are ordered by ascending factor value, so 分组10 is the
   long side when `--factor-direction 1` and 分组1 when it is `0`. Reading the wrong end inverts
   every conclusion.
2. **Monotonicity** across the ten groups — a factor that only fires in the extreme group is fragile.
3. **p-value** of the IC t-statistic, subject to the multiple-testing caveat below.
4. **Turnover**, converted into a cost rather than quoted as a rate:

```
annual cost ≈ turnover × round_trip_cost × (252 / rebalance_days)
```

The reported `turnoverRate` is the share of the decile replaced each rebalance, so with ten groups it
saturates near 90%. At a 5-day cycle and a 0.3% round trip, 60% turnover costs about 9 points a year.
`batch.py` applies this and ranks by the net figure.

## Research loop

Run this after **every** batch, not once at the end.

**Attribute.** Name the economic mechanism of each winner in one sentence; if you cannot, treat it as
noise. Then check what it duplicates — download factor values and compute cross-sectional Spearman
correlation against the existing set (`scripts/analyze.py corr`). A "new" factor correlating 0.85
with one you already hold is not new.

**Falsify.** State what would disprove the finding, then test that: exclude the smallest 20% by
market cap, split by calendar year, vary the lookback by ±50%, change the rebalance cycle. Record
falsified ideas so they stop coming back.

**Cost-check.** Apply the turnover haircut and re-rank. Some leaders do not survive it.

**Decide.** Escalate, orthogonalize, or abandon — one of the three, written down. Without an explicit
abandon step, dead directions get re-explored a week later.

Worksheet and falsification menu: [references/playbook.md](references/playbook.md).

## Statistical hygiene

- **Multiple testing.** Testing N factors on one dataset makes small p-values inevitable. At ~100
  candidates a nominal p < 0.05 means nothing; use p < 0.05/N as a rough filter. `batch.py` prints
  the threshold for the batch size.
- **Hold out data.** Under the 3-year cap, out-of-sample means re-creating survivors as new factor
  objects over an earlier three-year range and confirming the sign and magnitude hold.
- **Keep the failures.** They are the denominator of the correction.
- **Prefer few uncorrelated axes.** Five factors at 0.9 mutual correlation is one factor with extra
  steps.

## Scripts

Execute these; they are not reference reading. Standard library only.

| Script | Purpose |
|---|---|
| `scripts/bootstrap.py` | Preflight: environment, config, login state, balance, factor count |
| `scripts/batch.py` | Batch create / run / tabulate, resumable, ranked net of cost |
| `scripts/analyze.py` | Local Spearman correlation and turnover from downloaded CSVs |

## Safety

- Prefer the interactive prompt over passing `--password`; if the tool balks, hand the command to the
  user rather than working around the refusal. Never commit or print the config file, token, or uid.
- Every run costs credits: check `balance`, probe on short windows, batch the rest.
- Community-maintained and unaffiliated with PandaAI. `pandaai-cli` is a third-party package whose
  behaviour changes, so verify against the platform. Nothing here is investment advice.
