#!/usr/bin/env python3
"""Preflight for PandaAI factor mining: environment, config, login state, and account status.

Run this first, and again whenever something stops working. It checks in order:

  1. Python version and which interpreter this project will use
  2. whether pandaai-cli is installed, and where it came from
  3. ~/.pandaai/config.yaml (pandaai-cli 0.1.x cannot create it on its own)
  4. login state, compute balance, and how many factors the account already has
  5. the bundled field and operator references

Prints the exact next command whenever a step is not satisfied. Never prints credentials.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

GATEWAY_URL = "https://www.pandaaiquant.com/pandaApi"
LOGIN_PAGE = "https://www.pandaaiquant.com/login"
COMPETITION = "https://www.pandaaiquant.com/factorhub/fourthFactorCompetition/"
PERSONAL_CENTER = "https://www.pandaaiquant.com/personalcenter?id=1"
DEFAULT_CONFIG = Path.home() / ".pandaai" / "config.yaml"
REFS = Path(__file__).resolve().parent.parent / "references"

OK, WARN, BAD = "ok  ", "note", "fail"
WINDOWS = sys.platform == "win32"


def say(status: str, message: str) -> None:
    print(f"[{status}] {message}")


def check_python() -> bool:
    version = sys.version_info
    say(OK if version >= (3, 10) else BAD,
        f"python {version.major}.{version.minor}.{version.micro} at {sys.executable}")
    if version < (3, 10):
        say(BAD, "pandaai-cli needs Python 3.10 or newer")
        return False
    return True


def check_cli() -> str | None:
    path = shutil.which("pandaai-cli")
    if not path:
        say(BAD, "pandaai-cli not found on PATH")
        if shutil.which("uv"):
            print("\n  Install it in an isolated environment so it stays on PATH:")
            print("    uv tool install pandaai-cli")
        elif shutil.which("pipx"):
            print("\n  Install it in an isolated environment so it stays on PATH:")
            print("    pipx install pandaai-cli")
        else:
            print("\n  Neither uv nor pipx is installed. Either get uv first, which keeps the CLI")
            print("  in its own environment and on PATH:")
            print("    curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS / Linux"
                  if not WINDOWS else
                  '    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"   # Windows')
            print("    uv tool install pandaai-cli")
            print("\n  Or install straight into this Python, which is simpler but can leave the")
            print("  command off PATH depending on how Python was installed:")
            print(f"    {sys.executable} -m pip install --user pandaai-cli")
        return None

    say(OK, f"pandaai-cli at {path}")
    # On Unix the console script is a text file whose shebang names the interpreter that will
    # actually run the CLI. On Windows it is a binary launcher with nothing to read.
    if not WINDOWS:
        try:
            shebang = Path(path).read_text(errors="ignore").splitlines()[0]
            if shebang.startswith("#!"):
                say(OK, f"running under {shebang[2:].strip()}")
        except (OSError, IndexError):
            pass
    return path


def check_config(path: Path, country_code: str) -> bool:
    """Seed a minimal config if absent, because the CLI exits before login can create it."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"gateway_url: {GATEWAY_URL}\ncountry_code: '{country_code}'\n")
        path.chmod(0o600)
        say(OK, f"created {path} (pandaai-cli cannot create it itself)")
        return False
    text = path.read_text()
    if "gateway_url" not in text:
        path.write_text(f"gateway_url: {GATEWAY_URL}\n" + text)
        say(OK, f"added gateway_url to {path}")
    else:
        say(OK, f"config present: {path}")
    return bool(re.search(r"^token:\s*\S", text, re.M))


def login_help() -> None:
    print("\n  Work through whichever of these you have not done yet:")
    print(f"\n  1. No PandaAI account? Register with a phone number at {LOGIN_PAGE}")
    print(f"\n  2. Registered but not entered the competition? Enter at")
    print(f"     {COMPETITION}")
    print("     Compute credits are granted on entry. Without it you can log in but run nothing.")
    print(f"\n  3. No password? Signing up with an SMS code does not create one. Set it at")
    print(f"     {PERSONAL_CENTER}")
    print("\n  4. Then log in. This asks for the phone and password interactively, which keeps")
    print("     the password out of your shell history:")
    print("       pandaai-cli login")
    print("     Or pass them as flags: pandaai-cli login --phone 13800138000 --password yourpass")
    print("\n  If your AI tool refuses to handle the password, run the command yourself in a")
    print("  terminal (PowerShell on Windows). The token is saved to the config file, and the")
    print("  agent can continue from there without ever seeing the credentials.")


def cli_json(*args: str, timeout: int = 90) -> dict:
    try:
        proc = subprocess.run(["pandaai-cli", "--json", *args],
                              capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"success": False, "error": {"message": str(exc)}}
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return {"success": False, "error": {"message": (proc.stdout + proc.stderr).strip()[:200]}}


def check_account() -> bool:
    balance = cli_json("balance")
    if not balance.get("success"):
        say(BAD, f"balance query failed: {balance.get('error', {}).get('message', balance)}")
        say(WARN, "the token may have expired; log in again")
        return False
    power = (balance.get("balance") or {}).get("computingPower")
    say(OK, f"compute balance: {power}")
    if isinstance(power, (int, float)):
        # Runs cost roughly 2 credits, and a balance is only meaningful as experiments.
        say(OK if power >= 20 else WARN,
            f"that is about {int(power // 2)} runs left at roughly 2 credits each")
        if power <= 0:
            say(WARN, "a zero balance usually means the account has not entered the competition")
            print(f"       Enter at {COMPETITION} — credits are granted on entry.")

    listing = cli_json("factor_list", "--limit", "1", "--no-detail")
    if listing.get("success"):
        say(OK, f"factors already on this account: {listing.get('total')}")
    else:
        say(WARN, f"factor count unavailable: {listing.get('error', {}).get('message', listing)}")
    return True


def check_references() -> None:
    # fields.md lists names in backticks; operators.md keeps the official `NAME(args)` tables.
    for name, label, row in (("fields.md", "fields", r"^\| `"),
                             ("operators.md", "operators", r"^\| [A-Z][A-Z_0-9]*\(")):
        path = REFS / name
        if not path.exists():
            say(WARN, f"{path} missing")
            continue
        count = len(re.findall(row, path.read_text(), re.M))
        say(OK, f"{count} {label} available in references/{name}")

    catalog = sorted(REFS.glob("fields-*.md"))
    if catalog:
        entries = sum(len(re.findall(r"^\| `", p.read_text(), re.M)) for p in catalog)
        say(OK, f"{entries} backtest catalog entries across {len(catalog)} tables in references/fields-*.md")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--country-code", default="86")
    args = ap.parse_args()

    if not check_python():
        return 1
    if not check_cli():
        return 1

    logged_in = check_config(args.config, args.country_code)
    # References are local, so report them even when the account checks cannot run: they are what
    # tells a user the skill itself installed correctly.
    check_references()
    if not logged_in:
        say(WARN, "not logged in")
        login_help()
        return 0

    ready = check_account()

    if ready:
        print("\nReady. Read SKILL.md, then start with a short-window probe batch:")
        print(f"  {sys.executable} scripts/batch.py candidates.txt"
              " --start <YYYYMMDD> --end <YYYYMMDD> --cycle 5")
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
