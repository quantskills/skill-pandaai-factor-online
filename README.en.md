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
[PandaAI](https://www.pandaaiquant.com/factorhub/fourthFactorCompetition/) platform through
`pandaai-cli`. Works with Claude Code, Cursor, Codex, Kimi Code, Gemini CLI, and any agent that
reads `AGENTS.md`.

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

## 🚀 Quick start

### One prompt (recommended)

Paste this into Claude Code, Cursor, Codex, or Kimi Code:

```text
Install the skill at https://github.com/quantskills/skill-pandaai-factor-online, sign me up for the PandaAI factor competition, and start mining factors.
```

Nothing else is needed. Once the agent clones the repository it reads `AGENTS.md`, where a cold
start is three actions: land the repository somewhere permanent, run the installer, then follow the
skill's **Core Workflow**. That section is an explicit contract, so the flow comes out the same
across tools.

It opens with a preflight that costs no credits and closes each gap it finds — Python version, CLI
install, account registration, competition entry, account password — then walks you through login,
which you type yourself, since the agent never handles the password. Once preflight is green it
converts the credit balance into a number of affordable runs, settles the rebalance cycle, backtest
window and budget with you, and shows a candidate list for approval. **No credits are spent before
you say go.**

### Manual install

The only prerequisite is Python 3.10 or newer. Without it, `uv` is the shortest way out, and needs
no Python of its own:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh                  # macOS / Linux
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"       # Windows

uv python install 3.12
uv tool install pandaai-cli
```

Without uv: get Python from [python.org](https://www.python.org/downloads/),
`brew install python`, `sudo apt install python3`, or `winget install Python.Python.3.12`. For the
CLI, `pipx install pandaai-cli` works and `pip install --user pandaai-cli` is the fallback — whether
that lands on PATH depends on how Python was installed, and preflight will tell you.

```bash
# Clone somewhere permanent. Installs are symlinks, so a clone under /tmp silently
# removes the skill from every AI tool the next time the system clears it.
git clone https://github.com/quantskills/skill-pandaai-factor-online.git
cd skill-pandaai-factor-online
python3 scripts/install.py     # installs into every AI tool found on this machine
python3 scripts/bootstrap.py   # preflight: environment, config, login state, balance, factor count
```

On Windows use PowerShell and say `python` instead of `python3`. On macOS and Linux `./install.sh`
also works; it forwards to the same Python script and explains how to get Python when there is none.

### Account and login

Compute credits are granted on competition entry, so **an account that registered but never entered
logs in fine and cannot run a single factor**. Work through these five in order:

1. Register with a phone number at [the website](https://www.pandaaiquant.com/login).
2. Enter the [competition](https://www.pandaaiquant.com/factorhub/fourthFactorCompetition/) to
   receive credits.
3. SMS-code signups have no password; set one at
   [the personal center](https://www.pandaaiquant.com/personalcenter?id=1).
4. Run `pandaai-cli login`, which prompts for the phone and password.
5. Run `python3 scripts/bootstrap.py` again — it now reports balance, factor count, and the
   available operators.

If your AI tool refuses to run a command containing a password, run step 4 yourself in a terminal.
The token is saved to the config file and the agent continues from an authenticated state without
ever touching the credentials.

### Install per tool

| Tool | Command | Where it lands |
| --- | --- | --- |
| Claude Code | `python3 scripts/install.py claude` | `~/.claude/skills/skill-pandaai-factor-online` |
| Cursor | `python3 scripts/install.py cursor` | `~/.cursor/skills/skill-pandaai-factor-online` |
| Codex | `python3 scripts/install.py codex` | pointer appended to `~/.codex/AGENTS.md` |
| Gemini CLI | `python3 scripts/install.py gemini` | pointer appended to `~/.gemini/GEMINI.md` |
| One project | `python3 scripts/install.py project [DIR]` | project-local skill dirs plus an `AGENTS.md` pointer |

Kimi Code, opencode, Aider, and other agents that read `AGENTS.md` pick the skill up from the
project pointer.

Installs are symlinks by default, so `git pull` updates every tool at once; `--copy` vendors a
snapshot instead. Windows forbids symlinks unless Developer Mode is on, so there the installer falls
back to copying and says so — re-run it after each `git pull` in that case. The installer never
deletes anything it did not create: a real directory already sitting at a target path is reported
and skipped, and only `--force` overwrites.

### Everyday prompts

```text
Check my PandaAI environment and credit balance, then start mining
Mine a batch of reversal factors at a 5-day rebalance over 2023-2025, ranked net of turnover cost
Validate these candidates out of sample on the earlier three-year window
How correlated are these factors with market cap?
```

## 📦 Layout

```text
skill-pandaai-factor-online/
├── SKILL.md                  Skill body (English, agent entrypoint)
├── SKILL.zh-CN.md            Chinese mirror
├── AGENTS.md                 Working agreement for AGENTS.md-based agents
├── install.sh                Unix convenience wrapper around install.py
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
    ├── install.py            Cross-tool installer (Windows / macOS / Linux)
    ├── bootstrap.py          Preflight: environment, config, login, balance, factor count
    ├── batch.py              Batch create / run / tabulate, resumable, ranked net of cost
    ├── analyze.py            Local correlation and turnover from downloaded CSVs
    ├── selftest.py           Offline self-test of the scripts (no network, no credits)
    └── validate-qsh-form.mjs qsh-form self-check
```

The Python scripts need only the standard library.

## 📐 Core constraints

| Constraint | Detail |
| --- | --- |
| 🔐 Credentials belong to the user | The user runs the login command; never print or commit the config file, token, or uid |
| 💰 Every run costs 5 credits | Creating a factor is free; check `balance`, validate formulas on a short window, batch the rest |
| 📅 Three-year backtest cap | Out-of-sample validation needs a second factor object, not a wider range |
| 📊 Judge on net long-side excess | The long-short headline is not the conclusion; convert turnover to an annual cost first |
| 🧪 Statistical discipline | Keep every candidate tested, failures included, as the multiple-testing denominator |
| 🚫 Description, not recommendation | Research structure and factual summaries only, never investment advice |

## 🛠 Development and self-test

Run the offline self-test after changing anything under `scripts/`. No network, no credits:

```bash
python3 scripts/selftest.py
```

It covers resume fingerprints, the no-silent-retry rule, budget caps, result validation and the
statistics, and where a Python 3.9 is available it runs one for real, confirming the preflight
explains itself instead of crashing.

The ` ```json qsh-form ` block in SKILL.md declares this skill's custom run form on quantskillhub:
stage, backtest window, rebalance cycle and round-trip cost are assembled straight into the prompt.
CI validates it on push; locally, run `node scripts/validate-qsh-form.mjs SKILL.md`.

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
