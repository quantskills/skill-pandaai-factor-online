# pandaai-cli Reference / 命令参考

Verified against pandaai-cli 0.1.1. `pandaai-cli` is a third-party package; verify against the
installed version before relying on any flag.
对照 pandaai-cli 0.1.1 核对。`pandaai-cli` 为第三方包，依赖任何参数前请对照本机版本确认。

## Install / 安装

```bash
uv tool install pandaai-cli     # recommended: isolated tool environment
pipx install pandaai-cli        # equivalent
pip install pandaai-cli         # works, but pollutes the interpreter
```

Requires Python >= 3.10. If the `pandaai-cli` binary is not found after `pip install`, the script
landed in a user bin directory outside `PATH`; `uv tool install` avoids this entirely.
需要 Python >= 3.10。若 `pip install` 后找不到 `pandaai-cli`，是脚本装到了不在 `PATH` 上的用户 bin 目录；
用 `uv tool install` 可以完全避开这个问题。

## Global flags / 全局参数

| Flag | Default | Meaning |
|---|---|---|
| `--config PATH` | `~/.pandaai/config.yaml` | Config file location / 配置文件位置 |
| `--json` | off | JSON-only output, suppresses INFO logs / 仅输出 JSON，不打印日志 |

## Commands / 命令

### login

```bash
pandaai-cli login --phone <phone> --password <password>
pandaai-cli login                                        # prompts instead, keeps it out of history
```

The account is the one registered on the PandaAI website. Set or reset the password at
<https://www.pandaaiquant.com/personalcenter?id=1> — accounts created with an SMS code alone have no
password until then. On success `token` and `uid` are written to the config file and every later
command reuses them. See "Known issues" for the fresh-machine failure mode.

账号就是 PandaAI 官网注册的那个。密码在 <https://www.pandaaiquant.com/personalcenter?id=1> 设置或重置——
只用短信验证码注册的账号在此之前没有密码。成功后 `token` 与 `uid` 写入配置文件，之后所有命令复用。
新机器上的失败模式见「已知问题」。

If an AI tool declines to run a command containing a password, have the user run it in their own
terminal (PowerShell on Windows). The token persists in the config file, so the agent continues from
an authenticated state without handling the credentials.
如果 AI 工具拒绝执行带密码的命令，请用户在自己的终端里运行（Windows 上是 PowerShell）。
token 会留在配置文件里，Agent 从已认证状态继续，不需要接触凭据。

### factor_create

```bash
pandaai-cli --json factor_create (--formula F | --code C | --file PATH)
  [--name NAME] [--start-date YYYYMMDD] [--end-date YYYYMMDD]
  [--adjustment-cycle N] [--factor-direction D]
```

| Flag | Default | Meaning |
|---|---|---|
| `--formula` / `--code` / `--file` | — | Formula string, Python code, or a file holding either / 公式、Python 代码，或存放两者之一的文件 |
| `--name` | 新建因子分析 | Display name / 名称 |
| `--start-date` | yesterday − 60d | Start of the construction window / 构建开始日期 |
| `--end-date` | yesterday | End of the construction window / 构建结束日期 |
| `--adjustment-cycle` | 1 | Rebalance cycle, 1–10 days / 调仓周期 1–10 天 |
| `--factor-direction` | 1 | 1 = higher is better, 0 = lower is better / 1 正向，0 负向 |

Groups are fixed at 10 and the universe is fixed at 沪深全A. A window longer than three years is
rejected at creation.
分组固定 10 组，股票池固定沪深全A。超过三年的区间在创建时即被拒绝。

Returns `{"success": true, "factor_id": "..."}`.

### factor_run

```bash
pandaai-cli --json factor_run <factor_id> [--download [PATH]] [--poll-interval SEC] [--timeout SEC]
```

Starts the run, polls until it settles, and returns results. Defaults: poll every 2s, time out at
600s. Each run deducts compute credits whether it succeeds or fails.
启动、轮询到结束并返回结果。默认 2 秒轮询、600 秒超时。无论成功失败都会扣算力。

Success payload carries `results.factor_analysis` with IC statistics and per-group returns;
failure payload carries `error.node_errors` with the formula parse or runtime error.
成功返回体的 `results.factor_analysis` 含 IC 统计与分组收益；失败返回体的 `error.node_errors`
含公式解析或运行错误。

### factor_result

```bash
pandaai-cli factor_result <run_id> [--download [PATH]]     # omit --json to actually download
```

Queries a completed run: core performance, IC metrics, ten-group returns plus the long-short
combination, top-ranked names, and chart series.
查询已完成的运行：核心绩效、IC 指标、10 组收益与多空组合、因子值最高的股票、图表序列。

Result shape worth knowing when parsing JSON:
解析 JSON 时值得知道的结构：

| Path | Contents |
|---|---|
| `factor_analysis.query_factor_analysis_data` | Ten rows keyed by `indicator`: `IC_mean`, `Rank_IC`, `IC_std`, `IC_IR`, `IR`, `P(IC<-0.02)`, `P(IC>0.02)`, `t统计量`, `p-value`, `单调性` |
| `factor_analysis.query_group_return_analysis` | Twelve rows: `分组1`–`分组10`, `多空组合`, `多空组合2`, each with `annualizedReturn`, `excessAnnualized`, `turnoverRate`, `sharpeRatio`, `monthlyWinRate`, `maxDrawdown` |
| `factor_analysis.query_last_date_top_factor` | Highest factor values on the most recent date |

Groups are ordered by ascending factor value: `分组1` holds the lowest values, `分组10` the highest.
The direction flag decides which end is the long side, which is why `多空组合` equals
`分组10 − 分组1` at `--factor-direction 1` and `分组1 − 分组10` at `0`. Reading the wrong end inverts
every conclusion.

分组按因子值升序排列：`分组1` 是最低的一组，`分组10` 是最高的一组。方向参数决定哪一端是多头侧，
所以 `--factor-direction 1` 时 `多空组合` 等于 `分组10 − 分组1`，为 `0` 时等于 `分组1 − 分组10`。
看错一端，全部结论都会反过来。

### factor_info / factor_update / factor_list / factor_delete / balance

```bash
pandaai-cli factor_info <factor_id>
pandaai-cli factor_update <factor_id> [--name | --formula | --code | --file |
                                       --start-date | --end-date |
                                       --adjustment-cycle | --factor-direction]
pandaai-cli --json factor_list [--limit N] [--offset N] [--no-detail]
pandaai-cli factor_delete <factor_id>... | --pattern PREFIX [--yes]
pandaai-cli --json balance
```

`factor_list` returns at most 100 per page and includes a one-line analysis summary unless
`--no-detail` is passed. `factor_delete --pattern` matches on name prefix, which makes throwaway
probes easy to clean up if you name them with a common prefix.
`factor_list` 每页最多 100 条，除非加 `--no-detail`，否则附带一行分析摘要。`factor_delete --pattern`
按名称前缀匹配，所以试探性因子起个统一前缀便于批量清理。

## Known issues / 已知问题

**Login fails on a clean machine.** `cli.py` calls `load_config()` before dispatching subcommands,
and `load_config()` prints `CONFIG_ERROR: 配置文件不存在` and exits when the file is missing. Since
`login` is the command that creates the file, it can never run first. Seed the file manually (or
run `scripts/bootstrap.py`) with `gateway_url` and `country_code`, then log in.
**新机器上无法登录。** `cli.py` 在分发子命令之前先调用 `load_config()`，文件缺失时它打印
`CONFIG_ERROR: 配置文件不存在` 并退出。而 `login` 恰恰是创建该文件的命令，于是永远排不到它执行。
先手工写入 `gateway_url` 与 `country_code`（或运行 `scripts/bootstrap.py`），再登录。

**`--json` silently disables `--download`.** The CSV write happens only on the human-readable code
path, so `factor_result <id> --download --json` prints JSON and writes nothing. Drop `--json` when
you want files.
**`--json` 会静默关闭 `--download`。** 写 CSV 只发生在人类可读的分支上，所以
`factor_result <id> --download --json` 只打印 JSON，不落盘。要文件就别加 `--json`。

**`factor_update` drops parameters when several change at once.** Updating, say, `--name` and
`--factor-direction` in one call can apply only one of them. Issue one change per call and confirm
with `factor_info` before spending a run.
**`factor_update` 一次改多个参数会丢。** 例如同时改 `--name` 和 `--factor-direction`，可能只生效一个。
一次只改一项，花算力运行前用 `factor_info` 确认。

**`factor_delete --pattern` can fail with HTTP 422.** The CLI collects matching ids across pages
without de-duplicating, and the API rejects a list containing repeats
(`工作流ID列表中不能有重复的ID`), deleting nothing. Collect the ids yourself from `factor_list` and
pass unique ones positionally:
**`factor_delete --pattern` 可能报 HTTP 422。** CLI 跨页收集匹配 id 时没有去重，而接口拒绝含重复项的列表
（`工作流ID列表中不能有重复的ID`），结果一个都删不掉。自己从 `factor_list` 取 id 去重后按位置参数传：

```bash
pandaai-cli --json factor_list --limit 100 --no-detail \
  | python3 -c "import json,sys;print(' '.join(sorted({f['_id'] for f in json.load(sys.stdin)['factors'] if f['name'].startswith('probe-')})))" \
  | xargs pandaai-cli factor_delete --yes
```

**Some formulas fail to parse for non-obvious reasons.** A trailing `-1` on a division has been seen
to fail (`CLOSE/MA(CLOSE,20)-1`) where the equivalent canonical operator works (`BIAS(CLOSE,20)`).
Nested operator calls are also less reliable than intermediate variables across multiple lines.
Prefer a canonical operator when one exists, and split deep nesting into lines.
**有些公式会因为不明显的原因解析失败。** 出现过除法后跟 `-1` 失败的情况（`CLOSE/MA(CLOSE,20)-1`），
而等价的标准算子可以（`BIAS(CLOSE,20)`）。深层嵌套调用也不如多行中间变量稳。有标准算子就用标准算子，
嵌套太深就拆成多行。
