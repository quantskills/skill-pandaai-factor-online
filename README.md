# 🧩 PandaAI 在线因子挖掘

**简体中文** | [English](README.en.md)

> 一句话定位：把 PandaAI 因子大赛的上手链路和踩坑经验固化成一个技能，让任意 AI 工具都能带你从装环境一路走到可提交的因子。

![type](https://img.shields.io/badge/type-agent--skill-blue)
![license](https://img.shields.io/badge/license-GPLv3-blue)
![platforms](https://img.shields.io/badge/platforms-claude--code%20%7C%20cursor%20%7C%20codex%20%7C%20openclaw-lightgrey)

---

## 📖 这是什么

一个可移植的 Agent 技能，用于通过 `pandaai-cli` 在
[PandaAI](https://www.pandaaiquant.com/factorhub/fourthFactorCompetition/) 平台挖掘量化因子。
适配 Claude Code、Cursor、Codex、Kimi Code、Gemini CLI，以及任何读 `AGENTS.md` 的 Agent。

上手 PandaAI 有几个会实打实消耗时间和算力、而文档里查不到的坎：

- 新机器上 `pandaai-cli login` 会失败，因为 CLI 在分发子命令之前就去加载配置文件，
  而创建这个文件的恰恰是登录命令本身。
- `MEAN(CLOSE, 20)` 不是 20 日均线。它能解析、能运行，然后交给你一个看起来合理、
  但测的完全是另一回事的因子。
- 分组编号固定按因子值升序，多头侧由 `--factor-direction` 决定而不是跟着编号走。看错一端，
  所有结论都会反过来。
- 平台把多空年化放在最显眼处，而这假设了 A 股参与者建不起来的空头腿；换手率单独列出，
  没有折进收益里。
- 回测上限三年，于是样本内过拟合很容易，而样本外验证变成一个必须显式安排的额外步骤。

技能里内置了这些结论、348 个字段与 137 个算子的完整参考，以及一套研究流程，
避免 Agent 把整个算力余额花在同一个想法的一百个变体上。

## 🚀 快速开始

唯一的前置是 Python 3.10 或更新。先确认一下：

```bash
python3 --version
```

**没有 Python，或者版本太旧**，最省事的是装 `uv`。它自己不需要 Python，装完既能装 Python
也能装 PandaAI CLI，一条链走完：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh                  # macOS / Linux
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"       # Windows

uv python install 3.12
uv tool install pandaai-cli
```

不想用 uv 也行：Python 从 [python.org](https://www.python.org/downloads/) 装，或 macOS
`brew install python`、Ubuntu `sudo apt install python3`、Windows `winget install Python.Python.3.12`；
CLI 则用 `pipx install pandaai-cli`，或者保底的 `pip install --user pandaai-cli`——
后者取决于 Python 的安装方式，命令可能不在 PATH 上，体检脚本会告诉你。

**Python 就绪之后：**

```bash
# 先 cd 到一个长期存在的目录再 clone。安装用的是软链接，
# clone 在 /tmp 之类的临时目录下，重启后会把技能从所有 AI 工具里静默摘掉。
git clone https://github.com/quantskills/skill-pandaai-factor-online.git
cd skill-pandaai-factor-online
python3 scripts/install.py         # 装进本机检测到的全部 AI 工具

python3 scripts/bootstrap.py       # 检查环境并写好配置，缺什么它会说
pandaai-cli login                  # 交互式输入手机号和密码
python3 scripts/bootstrap.py       # 这次会报出算力、因子数量和可用算子
```

Windows 用 PowerShell，把 `python3` 换成 `python`。macOS 和 Linux 也可以用 `./install.sh`，
它只是转发给同一个 Python 脚本，并在找不到 Python 时告诉你怎么装。

登录用 PandaAI 官网的账号。还没有账号的话，先在[官网](https://www.pandaaiquant.com/login)用手机号注册，
再到[大赛页](https://www.pandaaiquant.com/factorhub/fourthFactorCompetition/)报名——算力是随报名发放的。
如果账号没有密码（只用短信验证码注册的就没有），到[个人中心](https://www.pandaaiquant.com/personalcenter?id=1)设一个。
如果你的 AI 工具拒绝执行带密码的命令，就自己在终端里跑一遍；token 会存进配置文件，Agent 从那里继续。

### 懒人版：一句话开始

不想手动装的话，把这一句贴给你的 AI 工具（Claude Code、Cursor、Codex、Kimi Code 都行）：

```text
参考这个链接 https://github.com/quantskills/skill-pandaai-factor-online 帮我装上 skill，带我参加 PandaAI 因子大赛，开始挖掘因子。
```

不用写步骤。Agent clone 完会读到仓库根目录的 `AGENTS.md`，那里写着冷启动只做两件事：
运行安装脚本，然后按 SKILL 的**核心流程**走。核心流程是一段确定的契约，所以不同工具的表现是一致的。

它会先做一次只读体检，缺什么补什么：Python 版本不够就给下载地址，没装 `pandaai-cli` 就给安装命令，
没注册就给注册链接和大赛报名链接，注册了但没设密码就给个人中心链接，凭据齐了才让你去登录——
密码始终由你自己在终端输入，Agent 不碰。体检全绿之后，它会把算力余额换算成"还能跑多少次"告诉你，
跟你确认调仓周期、回测区间和本轮预算，再给出候选清单等你点头。你批准之前不花一点算力。

装好之后的日常触发：

```text
帮我检查 PandaAI 环境和算力，然后开始挖因子
挖一批 5 日调仓的反转类因子，2023 到 2025，按扣除换手成本后的多头超额排序
把这几个候选做样本外验证，区间用更早的三年
我这批因子和市值的相关性有多高？帮我算一下
```

### 分工具安装

| 工具 | 命令 | 安装位置 |
| --- | --- | --- |
| Claude Code | `python3 scripts/install.py claude` | `~/.claude/skills/skill-pandaai-factor-online` |
| Cursor | `python3 scripts/install.py cursor` | `~/.cursor/skills/skill-pandaai-factor-online` |
| Codex | `python3 scripts/install.py codex` | 在 `~/.codex/AGENTS.md` 追加指引 |
| Gemini CLI | `python3 scripts/install.py gemini` | 在 `~/.gemini/GEMINI.md` 追加指引 |
| 单个项目 | `python3 scripts/install.py project [目录]` | 项目内的技能目录 + `AGENTS.md` 指引 |

Kimi Code、opencode、Aider 等读 `AGENTS.md` 的 Agent，通过项目内的指引识别该技能。

默认用软链接安装，所以 `git pull` 一次就能更新所有工具；想固化快照就加 `--copy`。
Windows 默认不允许建软链接（除非开了开发者模式），安装器会自动改成复制并提示你，
那种情况下每次 `git pull` 之后要重跑一遍安装。
安装器不会删除不是它自己建的东西：目标位置已经有真实目录时它会报出来并跳过，你确认后加 `--force` 才覆盖。

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
    └── validate-qsh-form.mjs qsh-form 自检
```

Python 脚本只依赖标准库。

## 📐 核心约束

| 约束 | 说明 |
| --- | --- |
| 🔐 凭据归用户 | 登录命令交给用户执行；不打印、不提交配置文件、token 与 uid |
| 💰 每次运行扣算力 | 先查 `balance`，先用短区间验证公式，其余批量跑 |
| 📅 回测最长三年 | 样本外验证必须另建因子对象，不能靠拉长区间 |
| 📊 按多头净超额评判 | 多空年化不作为结论；换手率一律折算成年化成本后再排序 |
| 🧪 统计纪律 | 保留全部候选（含失败）作为多重检验的分母 |
| 🚫 只述不荐 | 输出研究结构与事实归纳，不构成任何投资建议 |

## ⚠️ 免责声明

本仓库仅作研究方法层面的整理，非官方、不隶属 PandaAI，不验证任何收益声明，不构成任何投资建议。
`pandaai-cli` 是第三方包，命令、计费和平台行为会随时间变化，依赖本仓库任何内容前请先自行核对。

## 📜 License

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE).

## 🐼 PandaAI / QUANTSKILLS 社群

<div align="center">
  <img src="https://raw.githubusercontent.com/quantskills/.github/main/profile/assets/pandaai-community-qr.jpg" alt="PandaAI 社群二维码" width="220">
  <br>
  <sub>扫码加入 PandaAI 社群，交流 QUANTSKILLS 技能、Agent 工作流与量化研究实践。</sub>
</div>

## qsh-form 表单声明（可选增强）

SKILL.md 中的 ` ```json qsh-form ` 围栏块声明该技能在 quantskillhub 运行页的定制表单：
阶段选择、回测区间、调仓周期与双向成本会直接组装进提示。推送时 CI 自动校验；
本地自检：`node scripts/validate-qsh-form.mjs SKILL.md`。
