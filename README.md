# 🧩 PandaAI 在线因子挖掘

**简体中文** | [English](README.en.md)

> 把 PandaAI 因子大赛的上手链路与踩坑经验固化成一个技能，让任意 AI 工具带你从空机器走到可提交的因子。

![type](https://img.shields.io/badge/type-agent--skill-blue)
![license](https://img.shields.io/badge/license-GPLv3-blue)
![platforms](https://img.shields.io/badge/platforms-claude--code%20%7C%20cursor%20%7C%20codex%20%7C%20openclaw-lightgrey)

---

## 📖 这是什么

一个可移植的 Agent 技能，通过 `pandaai-cli` 在
[PandaAI](https://www.pandaaiquant.com/factorhub/fourthFactorCompetition/) 平台挖掘量化因子。
适配 Claude Code、Cursor、Codex、Kimi Code、Gemini CLI，以及任何读 `AGENTS.md` 的 Agent。

上手 PandaAI 有几处文档里查不到、却实打实消耗时间和算力的坎：

- 新机器上 `pandaai-cli login` 必然失败：CLI 在分发子命令之前先加载配置文件，而创建该文件的
  正是登录命令本身。
- `MEAN(CLOSE, 20)` 不是 20 日均线。它能解析、能运行，返回一个看起来合理、实际测量另一回事的因子。
- 分组编号按因子值升序固定，多头端由 `--factor-direction` 决定而非跟随编号。看错一端，全部结论反号。
- 平台头条是多空年化，隐含了 A 股参与者建不起来的空头腿；换手率单独列出，没有折进收益。
- 回测最长三年，样本内过拟合因此很容易，样本外验证必须显式另建因子对象。

技能内置这些结论、348 个字段与 137 个算子的完整参考，以及一套研究流程，
防止 Agent 把算力全花在同一个想法的上百个变体上。

## 🚀 快速开始

### 一句话安装（推荐）

把这句贴给 Claude Code、Cursor、Codex 或 Kimi Code：

```text
参考这个链接 https://github.com/quantskills/skill-pandaai-factor-online 帮我装上 skill，带我参加 PandaAI 因子大赛，开始挖掘因子。
```

不需要补充步骤。Agent clone 后读到仓库根目录的 `AGENTS.md`，冷启动三件事：确认仓库落在持久目录、
运行安装脚本、按 SKILL 的**核心流程**执行。核心流程是一段显式契约，不同工具的表现因此一致。

它先做一次零算力体检，逐项补齐缺口——Python 版本、CLI 安装、账号注册、大赛报名、账号密码——
再引导你登录，密码始终由你在终端输入，Agent 不接触。体检全绿后，它把算力余额换算成可跑次数，
与你确认调仓周期、回测区间和本轮预算，最后给出候选清单等你过目。**你批准之前不花任何算力。**

### 手动安装

前置只有 Python 3.10 或更新。没有或版本过旧时，`uv` 是最短路径，它自身不依赖 Python：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh                  # macOS / Linux
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"       # Windows

uv python install 3.12
uv tool install pandaai-cli
```

不用 uv 也可以：Python 从 [python.org](https://www.python.org/downloads/)、`brew install python`、
`sudo apt install python3` 或 `winget install Python.Python.3.12` 获取；CLI 用
`pipx install pandaai-cli`，保底是 `pip install --user pandaai-cli`——后者是否落在 PATH 上
取决于 Python 的安装方式，体检脚本会指出来。

```bash
# clone 到持久目录。安装用的是软链接，/tmp 之类的临时目录被系统清理后，
# 会把技能从所有 AI 工具里静默摘掉。
git clone https://github.com/quantskills/skill-pandaai-factor-online.git
cd skill-pandaai-factor-online
python3 scripts/install.py     # 装进本机检测到的全部 AI 工具
python3 scripts/bootstrap.py   # 体检：环境、配置、登录状态、算力、因子数量
```

Windows 用 PowerShell，把 `python3` 换成 `python`；macOS 与 Linux 也可用 `./install.sh`，
它转发给同一个 Python 脚本，并在找不到 Python 时说明如何安装。

### 账号与登录

算力随大赛报名发放，**只注册不报名的账号能登录却一次都跑不了**。按顺序确认这五步：

1. 在[官网](https://www.pandaaiquant.com/login)用手机号注册。
2. 到[大赛页](https://www.pandaaiquant.com/factorhub/fourthFactorCompetition/)报名，领取算力。
3. 短信验证码注册的账号没有密码，到[个人中心](https://www.pandaaiquant.com/personalcenter?id=1)设一个。
4. `pandaai-cli login`，交互式输入手机号与密码。
5. 再跑一次 `python3 scripts/bootstrap.py`，这次会报出算力余额、因子数量与可用算子。

AI 工具拒绝执行带密码的命令时，自己在终端跑第 4 步。token 存入配置文件，
Agent 从已登录状态继续，全程不接触凭据。

### 分工具安装

| 工具 | 命令 | 安装位置 |
| --- | --- | --- |
| Claude Code | `python3 scripts/install.py claude` | `~/.claude/skills/pandaai-factor-online` |
| Cursor | `python3 scripts/install.py cursor` | `~/.cursor/skills/pandaai-factor-online` |
| Codex | `python3 scripts/install.py codex` | 在 `~/.codex/AGENTS.md` 追加指引 |
| Gemini CLI | `python3 scripts/install.py gemini` | 在 `~/.gemini/GEMINI.md` 追加指引 |
| 单个项目 | `python3 scripts/install.py project [目录]` | 项目内的技能目录 + `AGENTS.md` 指引 |

Kimi Code、opencode、Aider 等读 `AGENTS.md` 的 Agent，通过项目内的指引识别该技能。

默认软链接安装，`git pull` 一次即更新所有工具，`--copy` 则固化为快照。Windows 未开开发者模式时
不允许软链接，安装器自动改为复制并提示，此时每次 `git pull` 后需重跑安装。安装器不会删除
不是它创建的东西：目标位置已有真实目录时报出并跳过，只有 `--force` 才覆盖。

### 常用指令

```text
帮我检查 PandaAI 环境和算力，然后开始挖因子
挖一批 5 日调仓的反转类因子，2023 到 2025，按扣除换手成本后的多头超额排序
把这几个候选做样本外验证，区间用更早的三年
我这批因子和市值的相关性有多高？帮我算一下
```

## 📦 目录结构

```text
skill-pandaai-factor-online/
├── SKILL.md                  技能正文（英文，Agent 入口）
├── SKILL.zh-CN.md            中文镜像
├── AGENTS.md                 面向 AGENTS.md 类 Agent 的工作约定
├── install.sh                install.py 的 Unix 便捷入口
├── agents/
│   └── openai.yaml           Codex 风格适配
├── references/
│   ├── cli.md                命令、返回结构与已知 CLI bug
│   ├── fields.md             348 个公式模式字段 + 回测因子目录索引
│   ├── fields-*.md           回测因子目录 14 张表，949 条
│   ├── operators.md          官方算子手册全文，含用法与示例
│   ├── pitfalls.md           会产出「能跑但跑错」因子的陷阱
│   ├── playbook.md           算力预算、复盘表、证伪菜单
│   └── source_boundary.md    数据、凭据与研究边界
└── scripts/
    ├── install.py            跨工具安装器（Windows / macOS / Linux）
    ├── bootstrap.py          体检：环境、配置、登录、算力、因子数量
    ├── batch.py              批量创建 / 运行 / 汇总，可续跑，按成本折算排序
    ├── analyze.py            用下载的 CSV 本地算相关性与换手率
    ├── selftest.py           脚本离线自检（不联网、不扣算力）
    └── validate-qsh-form.mjs qsh-form 自检
```

Python 脚本只依赖标准库。改过 `scripts/` 后跑一次 `python3 scripts/selftest.py`：不联网、不扣算力，
覆盖续跑指纹、失败不重试、预算上限、结果校验与统计口径，并在装有 Python 3.9 时真实运行一次，
确认预检给出提示而不是崩溃。

## 📐 核心约束

| 约束 | 说明 |
| --- | --- |
| 🔐 凭据归用户 | 登录命令交给用户执行；不打印、不提交配置文件、token 与 uid |
| 💰 每次运行扣 5 算力 | 创建因子免费；先查 `balance`，先用短区间验证公式，其余批量跑 |
| 📅 回测最长三年 | 样本外验证必须另建因子对象，不能靠拉长区间 |
| 📊 按多头净超额评判 | 多空年化不作为结论；换手率一律折算成年化成本后再排序 |
| 🧪 统计纪律 | 保留全部候选（含失败）作为多重检验的分母 |
| 🚫 只述不荐 | 输出研究结构与事实归纳，不构成任何投资建议 |

## ⚠️ 免责声明

本仓库仅作研究方法层面的整理，非官方、不隶属 PandaAI，不验证任何收益声明，不构成任何投资建议。
`pandaai-cli` 是第三方包，命令、计费与平台行为会随时间变化，依赖本仓库任何内容前请先自行核对。

## 📜 License

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE).

## 🐼 PandaAI / QUANTSKILLS 社群

<div align="center">
  <img src="https://raw.githubusercontent.com/quantskills/.github/main/profile/assets/pandaai-community-qr.jpg" alt="PandaAI 社群二维码" width="220">
  <br>
  <sub>扫码加入 PandaAI 社群，交流 QUANTSKILLS 技能、Agent 工作流与量化研究实践。</sub>
</div>

## qsh-form 表单声明（可选增强）

SKILL.md 中的 ` ```json qsh-form ` 围栏块声明该技能在 quantskillhub 运行页的定制表单：阶段、回测区间、调仓周期与双向成本会直接组装进提示词。推送时 CI 自动校验声明合法性；本地自检：`node scripts/validate-qsh-form.mjs SKILL.md`。无此块时技能页退化为通用主输入框，功能不受影响。
