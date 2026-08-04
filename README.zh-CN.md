# skill-pandaai-factor-online

一个可移植的 Agent 技能，用于通过 `pandaai-cli` 在 [PandaAI](https://www.pandaaiquant.com) 平台挖掘量化因子。
适配 Claude Code、Cursor、Codex、Kimi Code、Gemini CLI，以及任何读 `AGENTS.md` 的 Agent。

[English](README.md) · [Skill 正文](SKILL.zh-CN.md)

## 解决什么问题

在 PandaAI 上手有几个会实打实消耗时间和算力的坎：

- 新机器上 `pandaai-cli login` 会失败，因为 CLI 在分发子命令之前就去加载配置文件，而创建这个文件的
  恰恰是登录命令本身。
- `MEAN(CLOSE, 20)` 不是 20 日均线。它能解析、能运行，然后交给你一个看起来很合理、
  但测的完全是另一回事的因子。
- 平台把多空年化放在最显眼的位置，而这假设了 A 股参与者建不起来的空头腿；换手率单独列出，
  没有折进收益里。
- 回测上限三年，于是样本内过拟合很容易，而样本外验证变成一个必须显式安排的额外步骤，
  不是把日期拉长就行。

这个技能把上面这些固化下来，另外给出一套研究流程，避免 Agent 把整个算力余额花在同一个想法的一百个变体上。

## 快速开始

```bash
git clone https://github.com/dfkai/skill-pandaai-factor-online.git
cd skill-pandaai-factor-online
./install.sh                       # 装进本机检测到的全部 AI 工具

uv tool install pandaai-cli
python3 scripts/bootstrap.py       # 检查环境并写好配置
pandaai-cli login --phone <官网注册手机号> --password <官网登录密码>
python3 scripts/bootstrap.py       # 这次会报出算力、因子数量和可用算子
```

用 PandaAI 官网的账号。如果账号没有密码（只用短信验证码注册的就没有），
到[个人中心](https://www.pandaaiquant.com/personalcenter?id=1)设置一个。
如果你的 AI 工具拒绝执行带密码的命令，就自己在终端里跑一遍；token 会存进配置文件，Agent 从那里继续。

然后让你的 Agent 开始挖掘。它会读 `SKILL.md` 并按流程走下去。

## 分工具安装

| 工具 | 命令 | 安装位置 |
|---|---|---|
| Claude Code | `./install.sh claude` | `~/.claude/skills/skill-pandaai-factor-online` |
| Cursor | `./install.sh cursor` | `~/.cursor/skills/skill-pandaai-factor-online` |
| Codex | `./install.sh codex` | 在 `~/.codex/AGENTS.md` 追加指引 |
| Gemini CLI | `./install.sh gemini` | 在 `~/.gemini/GEMINI.md` 追加指引 |
| 单个项目 | `./install.sh project [目录]` | 项目内的技能目录 + `AGENTS.md` 指引 |

Kimi Code、opencode、Aider 等读 `AGENTS.md` 的 Agent，通过项目内的指引识别该技能。
默认用软链接安装，所以 `git pull` 一次就能更新所有工具；想固化快照就加 `--copy`。

## 目录内容

```
SKILL.md              技能正文：环境、约束、评价、研究流程（英文）
SKILL.zh-CN.md        中文镜像
AGENTS.md             面向 AGENTS.md 类 Agent 的工作约定
references/
  cli.md              命令、参数与已知 CLI bug
  fields.md           348 个数据字段
  operators.md        137 个算子签名
  pitfalls.md         会产出「能跑但跑错」因子的陷阱
  playbook.md         算力预算、复盘表、证伪菜单
scripts/
  bootstrap.py        写配置、绕过登录 bug、校验认证
  batch.py            批量创建 / 运行 / 汇总，可续跑，按成本调整后排序
  analyze.py          用下载的 CSV 本地算 Spearman 相关与换手率
```

脚本只依赖 Python 标准库。

## 安全边界

凭据不该出现在提示词、日志、提交或 issue 里。`pandaai-cli login` 自己执行，让 Agent 在已认证的
shell 里工作。每次 `factor_run` 都扣算力，所以跑完整回测之前先查 `balance`，先在短区间验证公式。

## 参与贡献

欢迎修正字段与算子清单、补充陷阱、更新 CLI 行为变化。提交时请说明你是怎么验证的——
这个仓库的价值在于里面每一条都是在真实平台上核对过的，而不是推测的。

## 免责声明

社区维护，与 PandaAI 官方无关。`pandaai-cli` 是第三方包，命令、计费和平台行为会随时间变化，
依赖本仓库任何内容前请先自行核对。本仓库不构成投资建议。

## 许可

[MIT](LICENSE)
