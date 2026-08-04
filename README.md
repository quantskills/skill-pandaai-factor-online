# skill-pandaai-factor-online

A portable agent skill for mining quantitative factors on the [PandaAI](https://www.pandaaiquant.com)
platform through `pandaai-cli`. Works with Claude Code, Cursor, Codex, Kimi Code, Gemini CLI, and any
other agent that reads `AGENTS.md`.

[中文说明](README.zh-CN.md) · [Skill 正文（中文）](SKILL.zh-CN.md)

## Why

Getting started on PandaAI has a few sharp edges that cost real time and real compute credits:

- `pandaai-cli login` fails on a clean machine, because the CLI loads its config file before
  dispatching the command that creates it.
- `MEAN(CLOSE, 20)` is not a 20-day moving average. It parses, runs, and hands you a plausible-looking
  factor that measures something else entirely.
- The platform headlines a long-short annualized return, which assumes a short leg that A-share
  participants cannot build, and reports turnover separately instead of folding it into returns.
- Backtests are capped at three years, which makes in-sample overfitting easy and out-of-sample
  validation an explicit extra step rather than a wider date range.

This skill encodes those, plus a research loop that keeps an agent from spending a whole credit
balance on a hundred variants of one idea.

## Quick start

```bash
git clone https://github.com/dfkai/skill-pandaai-factor-online.git
cd skill-pandaai-factor-online
./install.sh                       # installs into every AI tool found on this machine

uv tool install pandaai-cli
python3 scripts/bootstrap.py       # checks the environment and seeds the config
pandaai-cli login --phone <phone> --password <password>
python3 scripts/bootstrap.py       # now reports balance, factor count, and available operators
```

Use the PandaAI website account. If it has no password — SMS-code signups do not — set one at
[the personal center](https://www.pandaaiquant.com/personalcenter?id=1). If your AI tool refuses to
run a command containing a password, run it yourself in a terminal; the token is saved to the config
file and the agent continues from there.

Then ask your agent to start mining. It will read `SKILL.md` and follow the loop from there.

## Install per tool

| Tool | Command | Where it lands |
|---|---|---|
| Claude Code | `./install.sh claude` | `~/.claude/skills/skill-pandaai-factor-online` |
| Cursor | `./install.sh cursor` | `~/.cursor/skills/skill-pandaai-factor-online` |
| Codex | `./install.sh codex` | pointer appended to `~/.codex/AGENTS.md` |
| Gemini CLI | `./install.sh gemini` | pointer appended to `~/.gemini/GEMINI.md` |
| One project | `./install.sh project [DIR]` | project-local skill dirs plus an `AGENTS.md` pointer |

Kimi Code, opencode, Aider, and other agents that read `AGENTS.md` pick the skill up from the
project pointer. Installs are symlinks by default, so `git pull` updates every tool at once; pass
`--copy` if you would rather vendor a snapshot.

## What is inside

```
SKILL.md              Skill body: setup, constraints, evaluation, research loop (English)
SKILL.zh-CN.md        Chinese mirror
AGENTS.md             Working agreement for AGENTS.md-based agents
references/
  cli.md              Commands, flags, and the known CLI bugs
  fields.md           348 data fields
  operators.md        137 operator signatures
  pitfalls.md         Traps that produce valid-but-wrong factors
  playbook.md         Credit budget, retrospective worksheet, falsification menu
scripts/
  bootstrap.py        Seed config, work around the login bug, verify auth
  batch.py            Batch create / run / tabulate, resumable, cost-adjusted ranking
  analyze.py          Local Spearman correlation and turnover from downloaded CSVs
```

The scripts need only the Python standard library.

## Safety

Credentials never belong in a prompt, a log, a commit, or an issue. Run `pandaai-cli login`
yourself and let the agent work from the authenticated shell. Every `factor_run` deducts compute
credits, so check `balance` and validate formulas on a short window before committing to a full
backtest.

## Contributing

Corrections to the field and operator lists, additional pitfalls, and CLI behaviour changes are all
welcome. Please include how you verified the behaviour — the value of this repository is that
everything in it was checked against the live platform rather than assumed.

## Disclaimer

Community-maintained and unaffiliated with PandaAI. `pandaai-cli` is a third-party package;
commands, billing, and platform behaviour change over time, so verify before relying on anything
here. Nothing in this repository is investment advice.

## License

[MIT](LICENSE)
