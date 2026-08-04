---
name: skill-pandaai-factor-online
description: "Set up pandaai-cli, log in to PandaAI, and mine, backtest, and iterate quantitative factors on the platform. Use when an agent needs to onboard a user to the PandaAI factor competition, install or log in to pandaai-cli, look up available fields and operators, write or debug factor formulas, run and batch factor analyses, or interpret IC / group-return / turnover results on portable agent platforms such as Claude Code, Cursor, OpenClaw, or Codex-style skill systems."
license: GPL-3.0-only
quantSkills:
  organization: https://github.com/quantskills
  repository: quantskills/skill-pandaai-factor-online
  repository_url: https://github.com/quantskills/skill-pandaai-factor-online
  project_type: skill
  collection: factor-analysis
  license: GPL-3.0-only
  category: factor
  tags: [pandaai, factor-mining, pandaai-cli, a-shares, backtest, onboarding]
  platforms: [claude-code, codex, cursor, openclaw]
  language: zh-en
  status: stable
  validation_level: runnable
  maintainer_type: community
  requires: []
  summary_zh: PandaAI 因子大赛上手与在线挖掘：环境体检、登录、字段算子速查、可续跑批量回测，以及按交易成本折算的复盘流程。
  summary_en: "Onboarding and online factor mining for PandaAI: environment preflight, login, field and operator lookup, resumable batch backtests, and a cost-adjusted research loop."
---

<!-- qsh-form：quantskillhub 运行页的定制表单声明 -->
```json qsh-form
{
  "version": 1,
  "task": {
    "placeholder": "例如：帮我挖一批 5 日调仓、低换手的反转类因子，并按扣除成本后的多头超额排序",
    "required": true
  },
  "fields": [
    {
      "key": "stage",
      "type": "select",
      "label": "阶段",
      "options": [
        { "value": "onboarding", "label": "上手：环境体检与登录" },
        { "value": "probe", "label": "试探：短区间广撒网" },
        { "value": "full", "label": "全区间：只跑幸存者" },
        { "value": "falsify", "label": "证伪：变体与分年拆解" },
        { "value": "oos", "label": "样本外：更早三年重建" },
        { "value": "review", "label": "复盘：相关性与换手成本" }
      ]
    },
    { "key": "start_date", "type": "date", "label": "回测开始日期" },
    { "key": "end_date", "type": "date", "label": "回测结束日期（区间不得超过 3 年）" },
    { "key": "cycle", "type": "number", "label": "调仓周期（1-10 个交易日）" },
    { "key": "round_trip", "type": "number", "label": "双向交易成本（小数，如 0.003）" }
  ],
  "prompt_template": "任务：{{task}}\n阶段：{{stage}}\n回测区间：{{start_date}} 至 {{end_date}}（不得超过 3 年）\n调仓周期：{{cycle}} 日\n双向成本：{{round_trip}}\n附件：{{#attachments}}\n\n先运行 scripts/bootstrap.py 确认环境与算力，再按 SKILL.md 的流程执行；候选排序用扣除换手成本后的多头分组超额收益。"
}
```

# PandaAI Factor Online

Everything needed to go from a bare machine to a running factor analysis on PandaAI, then to iterate
without wasting compute credits.

中文版见 [SKILL.zh-CN.md](SKILL.zh-CN.md)。

## First interaction

When a user invokes this skill for the first time in a session, follow this sequence before any
mining work. Do not skip ahead to writing formulas, and do not spend a single run until step 3.

**1. Preflight.** Run it, do not paraphrase it:

```bash
python3 scripts/bootstrap.py
```

It checks the Python environment, the CLI install, the config file, login state, compute balance,
the number of factors on the account, and the bundled field and operator references, printing the
exact next command whenever a step is unsatisfied.

**2. Resolve whatever it flags, then stop and wait.**

| Preflight says | Do this |
|---|---|
| `pandaai-cli not found on PATH` | Show `uv tool install pandaai-cli` and wait for the user to run it |
| `not logged in` | Show `pandaai-cli login --phone <phone> --password <password>`, mention <https://www.pandaaiquant.com/personalcenter?id=1> for setting a password, and ask the user to run it themselves in a terminal. Never invent credentials, never guess a phone number |
| `balance query failed` | The token expired; ask the user to log in again |

Re-run preflight after the user reports back. Only continue when every line reads `ok`.

**3. Report the account, in the user's terms.** Convert the balance into experiments —
roughly 2 credits per run, so state how many runs are affordable — and mention how many factors are
already on the account.

**4. Fix the three parameters before writing any formula.** Ask the user, and do not guess:

- **Rebalance cycle** (1–10 days). If the competition locks it at submission, it must be decided now
  and every candidate evaluated at that cycle.
- **Backtest window**, at most three years, plus which earlier window is reserved for out-of-sample
  validation and will not be looked at during mining.
- **Batch budget**, how many runs this session may spend.

**5. Propose a probe batch** of 10–15 candidates spanning *different* hypotheses, and show the list
for approval before creating anything. Run it on a short window first to catch formula errors
cheaply, then take only the survivors to the full window.

The rest of this document covers each of those stages in detail. Steps 1 and 2 are onboarding and
only need doing once per machine.

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

Consult these before writing any formula, since a wrong name costs a run to discover:

- [references/fields.md](references/fields.md) — the 348 formula-mode base fields, plus an index to
  the full backtest factor catalog: 1050 entries across fifteen tables covering the three financial
  statements, valuation and derived metrics, technical indicators, the complete alpha101
  expressions, Barra risk factors, and daily and intraday calculated factors
- [references/operators.md](references/operators.md) — the official operator manual in full:
  signatures, semantics, and a worked example per function, in eleven categories

The alpha101 table is the fastest source of tested starting points: the expressions are already
written in this operator dialect and can go straight into `--formula`. Availability in formula mode
can differ from the data API, so validate an unfamiliar field on a short window first.

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

## References

| File | Contents |
|---|---|
| [references/cli.md](references/cli.md) | Commands, flags, result JSON shape, and known CLI bugs |
| [references/fields.md](references/fields.md) | 348 formula-mode fields, indexing the 1050-entry backtest catalog in `references/fields-*.md` |
| [references/operators.md](references/operators.md) | The official operator manual in full |
| [references/pitfalls.md](references/pitfalls.md) | Traps that produce valid-but-wrong factors |
| [references/playbook.md](references/playbook.md) | Credit budget, retrospective worksheet, falsification menu |
| [references/source_boundary.md](references/source_boundary.md) | Data, credential, and research boundaries |

## Safety

- Read [references/source_boundary.md](references/source_boundary.md) before a live run.
- Prefer the interactive prompt over passing `--password`; if the tool balks, hand the command to the
  user rather than working around the refusal. Never commit or print the config file, token, or uid.
- Every run costs credits: check `balance`, probe on short windows, batch the rest.
- Community-maintained and unaffiliated with PandaAI. `pandaai-cli` is a third-party package whose
  behaviour changes, so verify against the platform. Nothing here is investment advice.
