---
name: skill-pandaai-factor-online-zh
description: 搭建 pandaai-cli、登录 PandaAI，并在平台上挖掘、回测、迭代量化因子。当用户参加 PandaAI 因子大赛、安装或登录 pandaai-cli、询问有哪些字段与算子可用、编写与调试因子公式、运行因子分析、解读 IC / 分组收益 / 换手率结果时使用。
license: GPL-3.0-only
---

# PandaAI 因子在线挖掘

从一台干净的机器到跑出第一个因子分析，再到不浪费算力地持续迭代，需要的全部内容。

English version: [SKILL.md](SKILL.md)

## 从这里开始

```bash
python3 scripts/bootstrap.py
```

它会依次检查 Python 环境、CLI 安装、配置文件、登录状态、算力余额、账号已有的因子数量，
以及随技能附带的字段与算子清单，并在任何一步不满足时打印出确切的下一条命令。
按下面的顺序走，前四步是上手流程，只需做一次。

## 第 1 步：Python 环境

`pandaai-cli` 需要 Python 3.10 或更高。装成隔离的工具，这样无论当前激活的是哪个虚拟环境，
它都留在 `PATH` 上：

```bash
uv tool install pandaai-cli        # 或 pipx install pandaai-cli
```

如果更习惯项目虚拟环境，`uv venv && uv pip install pandaai-cli` 也可以，但之后每条命令都必须在
激活该环境的前提下运行。两种方式混用，正是「装成功了却提示 command not found」的常见原因：
`pip install` 可能把脚本放进一个不在 `PATH` 上的用户 bin 目录。

`bootstrap.py` 会同时打印运行脚本的解释器和 `pandaai-cli` 背后的解释器，继续往下之前先确认
它们就是这个项目该用的环境。

## 第 2 步：登录

```bash
pandaai-cli login --phone <官网注册手机号> --password <官网登录密码>
```

两个参数都不给则改为交互式输入，可以避免密码进入 shell 历史。账号就是在 PandaAI 官网注册的那个；
token 会写入 `~/.pandaai/config.yaml`，之后所有命令复用它。

**没有密码，或者忘了密码？** 到 <https://www.pandaaiquant.com/personalcenter?id=1> 设置。
只用短信验证码注册的账号，在设置之前是没有密码的。

**如果 AI 工具拒绝处理密码**，不要硬绕。请用户自己在终端里运行完整命令（Windows 上是 PowerShell），
然后继续即可。token 会落到配置文件里，所以 Agent 不需要接触凭据也能完成后续全部工作。

**新机器上登录报 `CONFIG_ERROR: 配置文件不存在`。** pandaai-cli 0.1.x 的 `cli.py` 在分发任何子命令
之前先加载配置，而加载器在文件缺失时直接退出——于是 `login` 这个负责创建文件的命令永远轮不到执行。
`bootstrap.py` 会把文件写好；手工处理则是：

```yaml
# ~/.pandaai/config.yaml
gateway_url: https://www.pandaaiquant.com/pandaApi
country_code: '86'
```

## 第 3 步：挖掘之前先看账号状态

```bash
pandaai-cli --json balance                            # 算力余额
pandaai-cli --json factor_list --limit 1 --no-detail  # 返回体里的 total 就是因子数量
```

每次运行约 2 算力，所以余额直接等于还能做多少次实验——除以二，按这个数字规划每批的规模。
因子数量要看，是因为名称会撞车、旧实验会堆积；给每一批起一个独立的名称前缀，
之后可以用 `factor_delete --pattern <前缀>` 清理。

## 第 4 步：搞清楚有什么可用

写任何公式之前先查下面两份，因为名字写错要花一次运行才能发现：

- [references/fields.md](references/fields.md)：348 个公式模式基础字段，并索引到完整的回测因子目录——
  十五张表共 1050 条，覆盖财报三张表、估值与各类衍生指标、技术指标、alpha101 全部表达式、
  Barra 风险因子，以及日频与日内计算因子
- [references/operators.md](references/operators.md)：官方算子手册全文，十一个类别，
  每个函数含签名、说明、用法与示例

alpha101 那张表是最快的现成起点：表达式已经用这套算子写好，可以直接塞进 `--formula`。
公式模式下的可用性可能与数据接口不同，用到陌生字段时先在短区间验证一次。

两种写法。**公式方式**（`--formula`）支持多行与中间变量，系统取最后一行作为因子值，字段名大小写均可。
**Python 方式**（`--code` 或 `--file`）继承 `Factor` 并实现 `calculate(self, factors)`，
返回值是列名为 `value`、以 `[symbol, date]` 为多级索引的 Series，同一套算子照样可用：

```python
class ComplexFactor(Factor):
    def calculate(self, factors):
        close, volume = factors['close'], factors['volume']
        momentum = RANK((close / DELAY(close, 20)) - 1)
        vol_signal = IF(STDDEV(close / DELAY(close, 1) - 1, 20) > 0.02, 1, -1)
        return momentum * vol_signal
```

公式方式迭代更快，多数候选够用；因子需要好几步中间计算时，Python 方式更好维护。

CLI 实际能做的事：

| 能力 | 命令 |
|---|---|
| 用公式或 Python 代码定义因子 | `factor_create` |
| 查看或修改定义 | `factor_info`、`factor_update` |
| 运行分析并取回结果 | `factor_run` |
| 重新查询已完成的运行 | `factor_result` |
| 下载每只股票的原始因子值 CSV | `factor_result <run_id> --download PATH` |
| 列出因子并附一行绩效摘要 | `factor_list` |
| 查算力 | `balance` |
| 按 id 或名称前缀清理 | `factor_delete` |

一次完成的运行会返回 IC 统计（IC_mean、Rank_IC、IC_IR、t 统计量、p-value、单调性）、
每个分组的年化与超额收益及换手率与胜率、当前因子值最高的股票，以及十组图表序列。
完整参数与已知 CLI bug 见 [references/cli.md](references/cli.md)。

## 平台约束

| 约束 | 取值 |
|---|---|
| 回测区间 | **最长 3 年**，超出会在创建时被拒 |
| 分组数 | 固定 10 组 |
| 股票池 | 固定沪深全A |
| 调仓周期 | 1–10 天，创建时设定 |
| 算力规格 | 固定 cpu=4 / mem=8 / gpu=4 |

如果比赛在提交后锁定调仓周期，那就在**开始挖掘之前**定好，并且所有候选都在这个周期下评估。
1 日调仓下很漂亮的因子，5 日调仓下可能完全不能用。

## 编写公式

最贵的一个陷阱，因为它是静默失败的：

```
MA(CLOSE, 20)        # 20 日滚动均值   ← 通常你想要的是这个
TS_MEAN(CLOSE, 20)   # 等价写法
MEAN(CLOSE, OPEN)    # 两个序列求均值，不是滚动窗口
```

`MEAN(CLOSE, 20)` 能解析、能运行，返回一个看起来合理、实际测的是价格水平的因子。
凡是要写回看窗口，先读 [references/pitfalls.md](references/pitfalls.md)；那里还讲了未来函数、
截面算子与时序算子的区别、方向参数，以及为什么几乎一切都和市值相关。

**先用便宜的方式验证。** 跑满 3 年之前，先用同一条公式建一个约 3 个月区间的因子跑一次。
语法和字段错误暴露出来花的算力一样，但等待时间少得多。

## 运行

```bash
pandaai-cli --json factor_create --formula "BIAS(CLOSE,20)" --name "20日乖离" \
  --start-date 20230101 --end-date 20251231 --adjustment-cycle 5 --factor-direction 0
pandaai-cli --json factor_run <factor_id>
```

超过一个候选就用批量脚本。它负责创建、运行、汇总，并在每一步之后落盘，中断后不会重复花算力：

```bash
python3 scripts/batch.py candidates.txt --start 20230101 --end 20251231 --cycle 5 --prefix "probe-"
```

输入文件每行格式为 `名称 ~ 公式 ~ 方向`：

```
20日乖离 ~ BIAS(CLOSE,20) ~ 0
距60日高点 ~ CLOSE/TS_MAX(HIGH,60) ~ 0
```

## 解读结果

平台把多空年化放在最显眼处，而这假设了 A 股参与者建不起来的空头腿。改为按多头侧评判：

1. **多头分组的超额收益。** 分组按因子值升序排列，所以 `--factor-direction 1` 时多头侧是分组10，
   为 `0` 时是分组1。看错一端，全部结论都会反过来。
2. **十组单调性**：只在极端组起作用的因子很脆弱。
3. **IC 的 t 统计量对应的 p 值**，注意下面的多重检验问题。
4. **换手率**，要折算成成本，而不是当成一个比率引用：

```
年化成本 ≈ 换手率 × 双向成本 × (252 / 调仓天数)
```

报告里的 `turnoverRate` 是每次调仓被替换掉的分组持仓比例，所以 10 分组下会逼近 90% 饱和。
5 日调仓、双向成本 0.3% 时，60% 的换手率一年约吃掉 9 个点。`batch.py` 会自动折算并按净值排序。

## 研究复盘流程

**每一批**跑完都做一遍，不要留到最后。

**归因。** 用一句话说清每个赢家的经济机制；说不清就当噪声。然后查它重复了什么——下载因子值，
与已有因子集做截面 Spearman 相关（`scripts/analyze.py corr`）。与已持有因子相关 0.85 的「新」因子不是新的。

**证伪。** 先说清什么能推翻这个结论，然后就去测：剔除市值最小的 20%、按自然年拆开、
回看窗口变动 ±50%、换调仓周期。被证伪的想法记下来，别让它们再回来。

**成本校验。** 套用换手率折算后重新排序。有些榜首撑不过这一步。

**决策。** 加码、正交化、放弃，三选一，并且写下来。没有显式的「放弃」动作，
死掉的方向一周后会被重新探索一遍。

复盘表与证伪菜单见 [references/playbook.md](references/playbook.md)。

## 统计纪律

- **多重检验。** 在同一份数据上测 N 个因子，小 p 值必然出现。候选到 100 个左右时，
  名义上的 p < 0.05 毫无意义；用 p < 0.05/N 做粗筛。`batch.py` 会按批量大小打印这个阈值。
- **留出样本。** 受 3 年上限限制，样本外意味着把幸存者在更早的三年区间上重建为新的因子对象，
  确认符号和幅度都站得住。
- **保留失败记录。** 它们是校正的分母。
- **少数不相关的轴优先。** 相互相关 0.9 的五个因子，本质上是一个因子加了四道手续。

## 脚本

这些是拿来执行的，不是拿来读的。只依赖标准库。

| 脚本 | 用途 |
|---|---|
| `scripts/bootstrap.py` | 体检：环境、配置、登录状态、算力、因子数量 |
| `scripts/batch.py` | 批量创建 / 运行 / 汇总，可续跑，按扣除成本后的净值排序 |
| `scripts/analyze.py` | 用下载的 CSV 本地算 Spearman 相关与换手率 |

## 参考文件

| 文件 | 内容 |
|---|---|
| [references/cli.md](references/cli.md) | 命令、参数、返回结构与已知 CLI bug |
| [references/fields.md](references/fields.md) | 348 个公式模式字段，并索引 `references/fields-*.md` 的 1050 条回测因子目录 |
| [references/operators.md](references/operators.md) | 官方算子手册全文 |
| [references/pitfalls.md](references/pitfalls.md) | 会产出「能跑但跑错」因子的陷阱 |
| [references/playbook.md](references/playbook.md) | 算力预算、复盘表、证伪菜单 |
| [references/source_boundary.md](references/source_boundary.md) | 数据、凭据与研究边界 |

## 安全边界

- 实盘取数前先读 [references/source_boundary.md](references/source_boundary.md)。
- 优先用交互式输入而不是 `--password`；工具拒绝处理时，把命令交给用户执行，不要绕过这个拒绝。
  不要提交或打印配置文件、token、uid。
- 每次运行都扣算力：先查 `balance`，先用短区间试探，其余批量跑。
- 社区维护，与 PandaAI 官方无关。`pandaai-cli` 是第三方包且行为会变，请自行在平台上核对。
  本文不构成投资建议。
