# Agent instructions

This repository is a portable agent skill for mining quantitative factors on the PandaAI platform
through `pandaai-cli`.

**Read [SKILL.md](SKILL.md) before doing any work on PandaAI factors.** It carries the platform
constraints, the formula traps that produce valid-but-wrong results, and the research loop. The
Chinese version is [SKILL.zh-CN.md](SKILL.zh-CN.md).

Non-negotiables when acting on this skill:

- Login is `pandaai-cli login --phone <phone> --password <password>`, or the interactive prompt if
  both flags are omitted. If your tooling declines to run a command containing a password, hand the
  command to the user instead of working around the refusal. Never read, print, or commit
  `~/.pandaai/config.yaml`, the token, or the uid.
- Every `factor_run` costs compute credits. Check `pandaai-cli --json balance`, validate formulas on
  a short window first, and batch the rest through `scripts/batch.py`.
- Report a factor's top-group excess return net of turnover cost, never the platform's headline
  long-short number on its own.
- Keep the full list of candidates tested, including failures. It is the denominator of the
  multiple-testing correction.

---

本仓库是一个可移植的 Agent 技能，用于通过 `pandaai-cli` 在 PandaAI 平台挖掘量化因子。

**动手之前先读 [SKILL.zh-CN.md](SKILL.zh-CN.md)**，里面有平台约束、会产出「能跑但跑错」结果的公式陷阱，
以及研究流程。英文版是 [SKILL.md](SKILL.md)。

不可违反的几条：

- 登录命令是 `pandaai-cli login --phone <手机号> --password <密码>`，两个参数都不给则改为交互式输入。
  如果你的工具拒绝执行带密码的命令，把命令交给用户执行，不要绕过这个拒绝。
  不要读取、打印或提交 `~/.pandaai/config.yaml`、token 和 uid。
- 每次 `factor_run` 都扣算力。先查 `pandaai-cli --json balance`，先在短区间验证公式，其余用
  `scripts/batch.py` 批量跑。
- 汇报因子表现时用扣除换手成本后的多头组超额收益，不要单独引用平台头条的多空数字。
- 保留测过的全部候选清单，包括失败的。那是多重检验校正的分母。
