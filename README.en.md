# 🧩 PandaAI Factor Online

[简体中文](README.md) | **English**

> A portable agent skill that encodes the PandaAI factor-competition onboarding path and its
> undocumented sharp edges, so any AI tool can take you from a bare machine to a submittable factor.

![type](https://img.shields.io/badge/type-agent--skill-blue)
![license](https://img.shields.io/badge/license-GPLv3-blue)
![platforms](https://img.shields.io/badge/platforms-claude--code%20%7C%20cursor%20%7C%20codex%20%7C%20openclaw-lightgrey)

---

## 📖 What this is

A portable agent skill for mining quantitative factors on the
[PandaAI](https://www.pandaaiquant.com) platform through `pandaai-cli`. Works with Claude Code,
Cursor, Codex, Kimi Code, Gemini CLI, and any agent that reads `AGENTS.md`.

Getting started on PandaAI has a few sharp edges that cost real time and real compute credits, none
of them documented:

- `pandaai-cli login` fails on a clean machine, because the CLI loads its config file before
  dispatching the command that creates it.
- `MEAN(CLOSE, 20)` is not a 20-day moving average. It parses, runs, and hands you a
  plausible-looking factor that measures something else entirely.
- Decile labels are ordered by ascending factor value, so the long side follows
  `--factor-direction` rather than the label. Read the wrong end and every conclusion inverts.
- The platform headlines a long-short annualized return, which assumes a short leg A-share
  participants cannot build, and reports turnover separately instead of folding it into returns.
- Backtests are capped at three years, which makes in-sample overfitting easy and out-of-sample
  validation an explicit extra step rather than a wider date range.

The skill carries those findings, a full reference for 348 fields and 137 operators, and a research
loop that keeps an agent from spending a whole credit balance on a hundred variants of one idea.

Sibling repository:
[skill-factor-mining-pandaai](https://github.com/quantskills/skill-factor-mining-pandaai) extracts
factor hypotheses from papers and reports; this one runs, evaluates, and iterates them on the
platform.

## 🚀 Quick start

```bash
git clone https://github.com/quantskills/skill-pandaai-factor-online.git
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

### One prompt to start

Skip the manual install: paste this whole block into your AI tool (Claude Code, Cursor, Codex, and
Kimi Code all work).

```text
Install this skill from https://github.com/quantskills/skill-pandaai-factor-online and help me
start mining PandaAI factors.

Steps:
1. git clone the repository, cd into it, run ./install.sh
2. Read SKILL.md
3. Run python3 scripts/bootstrap.py, resolve whatever it flags, and re-run it after each fix
   until every line reads ok
4. Then follow the "First interaction" section of SKILL.md: tell me how many runs my balance
   affords, confirm the rebalance cycle, backtest window, and budget with me, and show me a
   probe batch for approval
```

The skill's "First interaction" section is an explicit contract, so the flow comes out the same
across tools: preflight, fix what is missing, report the balance, settle three parameters, and show
a candidate list for approval — spending no credits before you say go.

Everyday prompts once installed:

```text
Check my PandaAI environment and credit balance, then start mining
Mine a batch of reversal factors at a 5-day rebalance over 2023-2025, ranked net of turnover cost
Validate these candidates out of sample on the earlier three-year window
How correlated are these factors with market cap?
```

### Install per tool

| Tool | Command | Where it lands |
| --- | --- | --- |
| Claude Code | `./install.sh claude` | `~/.claude/skills/skill-pandaai-factor-online` |
| Cursor | `./install.sh cursor` | `~/.cursor/skills/skill-pandaai-factor-online` |
| Codex | `./install.sh codex` | pointer appended to `~/.codex/AGENTS.md` |
| Gemini CLI | `./install.sh gemini` | pointer appended to `~/.gemini/GEMINI.md` |
| One project | `./install.sh project [DIR]` | project-local skill dirs plus an `AGENTS.md` pointer |

Kimi Code, opencode, Aider, and other agents that read `AGENTS.md` pick the skill up from the
project pointer. Installs are symlinks by default, so `git pull` updates every tool at once; pass
`--copy` to vendor a snapshot instead.

## 📦 Layout

```text
skill-pandaai-factor-online/
├── SKILL.md                  Skill body (English, agent entrypoint)
├── SKILL.zh-CN.md            Chinese mirror
├── AGENTS.md                 Working agreement for AGENTS.md-based agents
├── install.sh                Cross-tool installer
├── agents/
│   └── openai.yaml           Codex-style adapter
├── references/
│   ├── cli.md                Commands, result JSON shape, known CLI bugs
│   ├── fields.md             348 formula-mode fields, plus the catalog index
│   ├── fields-*.md           Backtest factor catalog, 14 tables, 949 entries
│   ├── operators.md          The official operator manual in full
│   ├── pitfalls.md           Traps that produce valid-but-wrong factors
│   ├── playbook.md           Credit budget, retrospective worksheet, falsification menu
│   └── source_boundary.md    Data, credential, and research boundaries
└── scripts/
    ├── bootstrap.py          Preflight: environment, config, login, balance, factor count
    ├── batch.py              Batch create / run / tabulate, resumable, ranked net of cost
    ├── analyze.py            Local correlation and turnover from downloaded CSVs
    └── validate-qsh-form.mjs qsh-form self-check
```

The Python scripts need only the standard library.

## 📐 Core constraints

| Constraint | Detail |
| --- | --- |
| 🔐 Credentials belong to the user | The user runs the login command; never print or commit the config file, token, or uid |
| 💰 Every run costs credits | Check `balance`, validate formulas on a short window, batch the rest |
| 📅 Three-year backtest cap | Out-of-sample validation needs a second factor object, not a wider range |
| 📊 Judge on net long-side excess | The long-short headline is not the conclusion; convert turnover to an annual cost first |
| 🧪 Statistical discipline | Keep every candidate tested, failures included, as the multiple-testing denominator |
| 🚫 Description, not recommendation | Research structure and factual summaries only, never investment advice |

## ⚠️ Disclaimer

Research-method material only. Unaffiliated with PandaAI, verifies no return claim, and constitutes
no investment advice. `pandaai-cli` is a third-party package whose commands, billing, and platform
behaviour change over time, so verify before relying on anything here.

## 📜 License

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE).

## 🐼 PandaAI / QUANTSKILLS community

<div align="center">
  <img src="https://raw.githubusercontent.com/quantskills/.github/main/profile/assets/pandaai-community-qr.jpg" alt="PandaAI community QR" width="220">
  <br>
  <sub>Scan to join the PandaAI community for QUANTSKILLS skills, agent workflows, and quant research practice.</sub>
</div>

## qsh-form (optional enhancement)

The ` ```json qsh-form ` block in SKILL.md declares this skill's custom run form on quantskillhub:
stage, backtest window, rebalance cycle, and round-trip cost are assembled straight into the prompt.
CI validates it on push; locally, run `node scripts/validate-qsh-form.mjs SKILL.md`.
